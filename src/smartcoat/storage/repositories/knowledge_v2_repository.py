from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import CursorResult, and_, delete, func, select, update
from sqlalchemy.orm import Session

from smartcoat.domain.base import LifecycleState
from smartcoat.domain.evidence_provenance import (
    EvidenceReference,
    KnowledgeObjectV2EvidenceComposition,
    ProvenanceV2,
)
from smartcoat.domain.knowledge_lifecycle import (
    DraftDeletionFacts,
    DraftDeletionPlan,
    LifecycleHistoryFacts,
    LifecycleMutationPlan,
)
from smartcoat.domain.knowledge_objects_v2 import (
    KnowledgeObjectUpdateError,
    KnowledgeObjectV2CoreRecord,
    KnowledgeObjectV2CreateCommand,
    KnowledgeObjectV2PersistedStateSnapshot,
    KnowledgeObjectV2UpdateCommand,
    evaluate_knowledge_object_update,
)
from smartcoat.storage.database.knowledge_v2_models import (
    KnowledgeObjectV2ContextRecord,
    KnowledgeObjectV2DecisionRelationshipRecord,
    KnowledgeObjectV2EvidenceRecord,
    KnowledgeObjectV2KnowledgeRelationshipRecord,
    KnowledgeObjectV2ProvenanceRecord,
    KnowledgeObjectV2Record,
    KnowledgeObjectV2TagRecord,
)
from smartcoat.storage.database.models import DecisionObjectRecord, KnowledgeObjectRecord
from smartcoat.storage.repositories.knowledge_v2_mappers import (
    LegacyKnowledgeObjectPersistenceAssessment,
    assess_legacy_persistence_record,
    composition_to_persistence_records,
    mutable_state_values,
    persistence_records_to_composition,
)


class KnowledgeObjectV2RepositoryError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class _KnowledgeObjectV2ChildRecords:
    tags: tuple[KnowledgeObjectV2TagRecord, ...]
    evidence: tuple[KnowledgeObjectV2EvidenceRecord, ...]
    provenance: KnowledgeObjectV2ProvenanceRecord | None
    context: tuple[KnowledgeObjectV2ContextRecord, ...]
    knowledge_relationships: tuple[KnowledgeObjectV2KnowledgeRelationshipRecord, ...]
    decision_relationships: tuple[KnowledgeObjectV2DecisionRelationshipRecord, ...]


def _canonical_provenance_json(provenance: ProvenanceV2) -> str:
    return json.dumps(
        provenance.model_dump(mode="json"),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


class KnowledgeObjectV2Repository:
    """PostgreSQL staging primitives. Transaction commit belongs to the Unit of Work."""

    _MAX_AGGREGATE_READ_ATTEMPTS = 3

    def __init__(self, session: Session) -> None:
        self._session = session

    def stage_create(
        self,
        command: KnowledgeObjectV2CreateCommand,
        *,
        evidence: Sequence[EvidenceReference],
        provenance: ProvenanceV2,
    ) -> KnowledgeObjectV2EvidenceComposition:
        object_id = uuid4()
        provisional_now = datetime.now(UTC)
        provisional_core = KnowledgeObjectV2CoreRecord(
            object_id=object_id,
            organization_id=command.organization_id,
            revision=1,
            lifecycle_state=LifecycleState.DRAFT,
            created_at=provisional_now,
            updated_at=provisional_now,
            mutable_state=KnowledgeObjectV2PersistedStateSnapshot.from_mutable_state(
                command.mutable_state
            ),
        )
        KnowledgeObjectV2EvidenceComposition(
            core=provisional_core,
            evidence=tuple(evidence),
            provenance=provenance,
        )

        root = KnowledgeObjectV2Record(
            object_id=object_id,
            organization_id=command.organization_id,
            contract_version="2",
            revision=1,
            lifecycle_state=LifecycleState.DRAFT.value,
            has_ever_left_draft=False,
            last_pre_deprecation_lifecycle=None,
            **mutable_state_values(command.mutable_state),
        )
        self._session.add(root)
        self._session.flush()
        self._session.refresh(root)

        core = KnowledgeObjectV2CoreRecord(
            object_id=root.object_id,
            organization_id=root.organization_id,
            revision=root.revision,
            lifecycle_state=LifecycleState(root.lifecycle_state),
            created_at=root.created_at,
            updated_at=root.updated_at,
            mutable_state=KnowledgeObjectV2PersistedStateSnapshot.from_mutable_state(
                command.mutable_state
            ),
        )
        composition = KnowledgeObjectV2EvidenceComposition(
            core=core,
            evidence=tuple(evidence),
            provenance=provenance,
        )
        records = composition_to_persistence_records(composition)
        self._session.add_all(records.all_records()[1:])
        self._session.flush()
        return self.load_for_controlled_mutation(
            object_id=root.object_id,
            organization_id=root.organization_id,
        )

    def get(
        self,
        *,
        object_id: UUID,
        organization_id: str,
    ) -> KnowledgeObjectV2EvidenceComposition | None:
        for _ in range(self._MAX_AGGREGATE_READ_ATTEMPTS):
            root = self._root(object_id=object_id, organization_id=organization_id)
            if root is None:
                return None

            children = self._load_child_records(root)
            verified_revision = self._current_revision(
                object_id=object_id,
                organization_id=organization_id,
            )
            if verified_revision == root.revision:
                return persistence_records_to_composition(
                    root,
                    tags=children.tags,
                    evidence=children.evidence,
                    provenance=children.provenance,
                    context=children.context,
                    knowledge_relationships=children.knowledge_relationships,
                    decision_relationships=children.decision_relationships,
                )
            self._session.expire_all()

        raise KnowledgeObjectV2RepositoryError(
            "aggregate_read_retry_exhausted",
            "the Knowledge Object v2 changed during every bounded aggregate read attempt",
        )

    def list_object_ids_by_type_and_tag(
        self,
        *,
        organization_id: str,
        knowledge_type: str,
        required_tag: str,
        limit: int,
        offset: int,
    ) -> tuple[UUID, ...]:
        organization_id = organization_id.strip()
        knowledge_type = knowledge_type.strip()
        required_tag = required_tag.strip()
        if not organization_id:
            raise KnowledgeObjectV2RepositoryError(
                "invalid_organization_id",
                "organization_id must not be blank",
            )
        if not knowledge_type:
            raise KnowledgeObjectV2RepositoryError(
                "invalid_knowledge_type",
                "knowledge_type must not be blank",
            )
        if not required_tag:
            raise KnowledgeObjectV2RepositoryError(
                "invalid_required_tag",
                "required_tag must not be blank",
            )
        if not 1 <= limit <= 101:
            raise KnowledgeObjectV2RepositoryError(
                "invalid_list_limit",
                "list limit must be between 1 and 101",
            )
        if offset < 0:
            raise KnowledgeObjectV2RepositoryError(
                "invalid_list_offset",
                "list offset must be zero or greater",
            )

        statement = (
            select(KnowledgeObjectV2Record.object_id)
            .join(
                KnowledgeObjectV2TagRecord,
                and_(
                    KnowledgeObjectV2TagRecord.organization_id
                    == KnowledgeObjectV2Record.organization_id,
                    KnowledgeObjectV2TagRecord.object_id == KnowledgeObjectV2Record.object_id,
                ),
            )
            .where(
                KnowledgeObjectV2Record.organization_id == organization_id,
                KnowledgeObjectV2Record.knowledge_type == knowledge_type,
                KnowledgeObjectV2TagRecord.tag == required_tag,
            )
            .order_by(
                KnowledgeObjectV2Record.created_at.desc(),
                KnowledgeObjectV2Record.object_id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return tuple(self._session.scalars(statement).all())

    def load_for_controlled_mutation(
        self,
        *,
        object_id: UUID,
        organization_id: str,
    ) -> KnowledgeObjectV2EvidenceComposition:
        composition = self.get(object_id=object_id, organization_id=organization_id)
        if composition is None:
            raise KnowledgeObjectV2RepositoryError(
                "knowledge_object_not_found",
                "no Knowledge Object v2 exists at the supplied organization boundary",
            )
        return composition

    def lifecycle_history_facts(
        self,
        *,
        object_id: UUID,
        organization_id: str,
    ) -> LifecycleHistoryFacts:
        root = self._required_root(object_id=object_id, organization_id=organization_id)
        return LifecycleHistoryFacts(
            has_ever_left_draft=root.has_ever_left_draft,
            last_pre_deprecation_lifecycle=(
                LifecycleState(root.last_pre_deprecation_lifecycle)
                if root.last_pre_deprecation_lifecycle is not None
                else None
            ),
        )

    def stage_material_update(
        self,
        *,
        organization_id: str,
        object_id: UUID,
        command: KnowledgeObjectV2UpdateCommand,
        evidence: Sequence[EvidenceReference] | None = None,
        provenance: ProvenanceV2 | None = None,
    ) -> KnowledgeObjectV2EvidenceComposition:
        current = self.load_for_controlled_mutation(
            object_id=object_id,
            organization_id=organization_id,
        )
        try:
            evaluate_knowledge_object_update(current.core, command)
        except KnowledgeObjectUpdateError as error:
            raise KnowledgeObjectV2RepositoryError(error.code, str(error)) from error

        replacement_evidence = tuple(evidence) if evidence is not None else current.evidence
        if (
            evidence is None
            and command.replacement.evidence_ids != current.core.mutable_state.evidence_ids
        ):
            raise KnowledgeObjectV2RepositoryError(
                "replacement_evidence_required",
                "changed evidence IDs require a complete structured evidence replacement",
            )
        replacement_provenance = provenance if provenance is not None else current.provenance
        desired_core = KnowledgeObjectV2CoreRecord(
            object_id=current.core.object_id,
            organization_id=current.core.organization_id,
            revision=current.core.revision,
            lifecycle_state=current.core.lifecycle_state,
            created_at=current.core.created_at,
            updated_at=current.core.updated_at,
            mutable_state=KnowledgeObjectV2PersistedStateSnapshot.from_mutable_state(
                command.replacement
            ),
        )
        desired_composition = KnowledgeObjectV2EvidenceComposition(
            core=desired_core,
            evidence=replacement_evidence,
            provenance=replacement_provenance,
        )
        if self._materially_identical(current, desired_composition):
            return current

        provisional_core = desired_core.model_copy(
            update={
                "revision": current.core.revision + 1,
                "updated_at": datetime.now(UTC),
            }
        )
        state_composition = KnowledgeObjectV2EvidenceComposition(
            core=provisional_core,
            evidence=replacement_evidence,
            provenance=replacement_provenance,
        )

        result = self._session.execute(
            update(KnowledgeObjectV2Record)
            .where(
                KnowledgeObjectV2Record.object_id == current.core.object_id,
                KnowledgeObjectV2Record.organization_id == organization_id,
                KnowledgeObjectV2Record.revision == command.expected_revision,
            )
            .values(
                **mutable_state_values(command.replacement),
                revision=command.expected_revision + 1,
                updated_at=func.clock_timestamp(),
            )
            .execution_options(synchronize_session=False)
        )
        self._require_atomic_match(
            result,
            object_id=current.core.object_id,
            organization_id=organization_id,
            expected_revision=command.expected_revision,
        )
        self._replace_mutable_children(
            object_id=current.core.object_id,
            organization_id=organization_id,
            state_composition=state_composition,
        )
        self._session.flush()
        self._session.expire_all()
        return self.load_for_controlled_mutation(
            object_id=current.core.object_id,
            organization_id=organization_id,
        )

    def stage_lifecycle_transition(
        self,
        *,
        organization_id: str,
        plan: LifecycleMutationPlan,
    ) -> KnowledgeObjectV2EvidenceComposition:
        current = self.load_for_controlled_mutation(
            object_id=plan.object_id,
            organization_id=organization_id,
        )
        if current.core.revision != plan.expected_revision:
            raise KnowledgeObjectV2RepositoryError(
                "stale_revision",
                "the lifecycle plan expected revision is no longer current",
            )
        if current.core.lifecycle_state is not plan.from_lifecycle:
            raise KnowledgeObjectV2RepositoryError(
                "lifecycle_plan_source_mismatch",
                "the persisted lifecycle does not match the accepted plan source",
            )
        result = self._session.execute(
            update(KnowledgeObjectV2Record)
            .where(
                KnowledgeObjectV2Record.object_id == plan.object_id,
                KnowledgeObjectV2Record.organization_id == organization_id,
                KnowledgeObjectV2Record.revision == plan.expected_revision,
                KnowledgeObjectV2Record.lifecycle_state == plan.from_lifecycle.value,
            )
            .values(
                lifecycle_state=plan.to_lifecycle.value,
                revision=plan.resulting_revision,
                has_ever_left_draft=True,
                last_pre_deprecation_lifecycle=(
                    plan.from_lifecycle.value
                    if plan.to_lifecycle is LifecycleState.DEPRECATED
                    else None
                ),
                updated_at=func.clock_timestamp(),
            )
            .execution_options(synchronize_session=False)
        )
        self._require_atomic_match(
            result,
            object_id=plan.object_id,
            organization_id=organization_id,
            expected_revision=plan.expected_revision,
        )
        self._session.flush()
        self._session.expire_all()
        return self.load_for_controlled_mutation(
            object_id=plan.object_id,
            organization_id=organization_id,
        )

    def compute_inbound_governed_reference_facts(
        self,
        *,
        object_id: UUID,
        organization_id: str,
    ) -> DraftDeletionFacts:
        knowledge_reference = self._session.scalar(
            select(KnowledgeObjectV2KnowledgeRelationshipRecord.source_object_id)
            .where(
                KnowledgeObjectV2KnowledgeRelationshipRecord.organization_id == organization_id,
                KnowledgeObjectV2KnowledgeRelationshipRecord.target_object_id == object_id,
            )
            .limit(1)
        )
        decision_reference = self._session.scalar(
            select(DecisionObjectRecord.object_id)
            .where(DecisionObjectRecord.related_knowledge.contains([str(object_id)]))
            .limit(1)
        )
        return DraftDeletionFacts(
            has_inbound_governed_references=(
                knowledge_reference is not None or decision_reference is not None
            )
        )

    def stage_eligible_draft_deletion(
        self,
        *,
        organization_id: str,
        plan: DraftDeletionPlan,
    ) -> DraftDeletionPlan:
        root = self._required_root(
            object_id=plan.object_id,
            organization_id=organization_id,
        )
        if root.revision != plan.expected_revision:
            raise KnowledgeObjectV2RepositoryError(
                "stale_revision",
                "the draft deletion plan expected revision is no longer current",
            )
        if root.lifecycle_state != LifecycleState.DRAFT.value:
            raise KnowledgeObjectV2RepositoryError(
                "trusted_record_hard_delete_forbidden",
                "only a persisted draft can use the hard-delete primitive",
            )
        if root.has_ever_left_draft:
            raise KnowledgeObjectV2RepositoryError(
                "draft_delete_ineligible",
                "a correction draft cannot use the hard-delete primitive",
            )
        facts = self.compute_inbound_governed_reference_facts(
            object_id=plan.object_id,
            organization_id=organization_id,
        )
        if facts.has_inbound_governed_references:
            raise KnowledgeObjectV2RepositoryError(
                "inbound_reference_blocks_deletion",
                "an inbound governed reference blocks draft deletion",
            )

        result = self._session.execute(
            delete(KnowledgeObjectV2Record)
            .where(
                KnowledgeObjectV2Record.object_id == plan.object_id,
                KnowledgeObjectV2Record.organization_id == organization_id,
                KnowledgeObjectV2Record.revision == plan.expected_revision,
                KnowledgeObjectV2Record.lifecycle_state == LifecycleState.DRAFT.value,
                KnowledgeObjectV2Record.has_ever_left_draft.is_(False),
            )
            .execution_options(synchronize_session=False)
        )
        self._require_atomic_match(
            result,
            object_id=plan.object_id,
            organization_id=organization_id,
            expected_revision=plan.expected_revision,
        )
        self._session.flush()
        return plan

    def assess_legacy(self, *, object_id: UUID) -> LegacyKnowledgeObjectPersistenceAssessment:
        record = self._session.get(KnowledgeObjectRecord, str(object_id))
        if record is None:
            raise KnowledgeObjectV2RepositoryError(
                "legacy_knowledge_object_not_found",
                "the legacy Knowledge Object does not exist",
            )
        return assess_legacy_persistence_record(record)

    def _root(
        self,
        *,
        object_id: UUID,
        organization_id: str,
    ) -> KnowledgeObjectV2Record | None:
        return self._session.scalar(
            select(KnowledgeObjectV2Record).where(
                KnowledgeObjectV2Record.object_id == object_id,
                KnowledgeObjectV2Record.organization_id == organization_id,
            )
        )

    def _required_root(
        self,
        *,
        object_id: UUID,
        organization_id: str,
    ) -> KnowledgeObjectV2Record:
        root = self._root(object_id=object_id, organization_id=organization_id)
        if root is None:
            raise KnowledgeObjectV2RepositoryError(
                "knowledge_object_not_found",
                "no Knowledge Object v2 exists at the supplied organization boundary",
            )
        return root

    def _load_child_records(
        self,
        root: KnowledgeObjectV2Record,
    ) -> _KnowledgeObjectV2ChildRecords:
        organization_id = root.organization_id
        object_id = root.object_id
        tags = tuple(
            self._session.scalars(
                select(KnowledgeObjectV2TagRecord).where(
                    KnowledgeObjectV2TagRecord.organization_id == organization_id,
                    KnowledgeObjectV2TagRecord.object_id == object_id,
                )
            ).all()
        )
        evidence = tuple(
            self._session.scalars(
                select(KnowledgeObjectV2EvidenceRecord).where(
                    KnowledgeObjectV2EvidenceRecord.organization_id == organization_id,
                    KnowledgeObjectV2EvidenceRecord.object_id == object_id,
                )
            ).all()
        )
        provenance = self._session.scalar(
            select(KnowledgeObjectV2ProvenanceRecord).where(
                KnowledgeObjectV2ProvenanceRecord.organization_id == organization_id,
                KnowledgeObjectV2ProvenanceRecord.object_id == object_id,
            )
        )
        context = tuple(
            self._session.scalars(
                select(KnowledgeObjectV2ContextRecord).where(
                    KnowledgeObjectV2ContextRecord.organization_id == organization_id,
                    KnowledgeObjectV2ContextRecord.object_id == object_id,
                )
            ).all()
        )
        knowledge_relationships = tuple(
            self._session.scalars(
                select(KnowledgeObjectV2KnowledgeRelationshipRecord).where(
                    KnowledgeObjectV2KnowledgeRelationshipRecord.organization_id == organization_id,
                    KnowledgeObjectV2KnowledgeRelationshipRecord.source_object_id == object_id,
                )
            ).all()
        )
        decision_relationships = tuple(
            self._session.scalars(
                select(KnowledgeObjectV2DecisionRelationshipRecord).where(
                    KnowledgeObjectV2DecisionRelationshipRecord.organization_id == organization_id,
                    KnowledgeObjectV2DecisionRelationshipRecord.source_object_id == object_id,
                )
            ).all()
        )
        return _KnowledgeObjectV2ChildRecords(
            tags=tags,
            evidence=evidence,
            provenance=provenance,
            context=context,
            knowledge_relationships=knowledge_relationships,
            decision_relationships=decision_relationships,
        )

    def _current_revision(
        self,
        *,
        object_id: UUID,
        organization_id: str,
    ) -> int | None:
        return self._session.scalar(
            select(KnowledgeObjectV2Record.revision).where(
                KnowledgeObjectV2Record.object_id == object_id,
                KnowledgeObjectV2Record.organization_id == organization_id,
            )
        )

    @staticmethod
    def _materially_identical(
        current: KnowledgeObjectV2EvidenceComposition,
        desired: KnowledgeObjectV2EvidenceComposition,
    ) -> bool:
        return (
            current.core.mutable_state.canonical_state_json
            == desired.core.mutable_state.canonical_state_json
            and tuple(reference.canonical_metadata_json for reference in current.evidence)
            == tuple(reference.canonical_metadata_json for reference in desired.evidence)
            and _canonical_provenance_json(current.provenance)
            == _canonical_provenance_json(desired.provenance)
        )

    def _replace_mutable_children(
        self,
        *,
        object_id: UUID,
        organization_id: str,
        state_composition: KnowledgeObjectV2EvidenceComposition,
    ) -> None:
        for record_type, object_column in (
            (KnowledgeObjectV2TagRecord, KnowledgeObjectV2TagRecord.object_id),
            (KnowledgeObjectV2EvidenceRecord, KnowledgeObjectV2EvidenceRecord.object_id),
            (KnowledgeObjectV2ContextRecord, KnowledgeObjectV2ContextRecord.object_id),
            (
                KnowledgeObjectV2KnowledgeRelationshipRecord,
                KnowledgeObjectV2KnowledgeRelationshipRecord.source_object_id,
            ),
            (
                KnowledgeObjectV2DecisionRelationshipRecord,
                KnowledgeObjectV2DecisionRelationshipRecord.source_object_id,
            ),
        ):
            self._session.execute(
                delete(record_type).where(
                    record_type.organization_id == organization_id,
                    object_column == object_id,
                )
            )
        self._session.execute(
            delete(KnowledgeObjectV2ProvenanceRecord).where(
                KnowledgeObjectV2ProvenanceRecord.organization_id == organization_id,
                KnowledgeObjectV2ProvenanceRecord.object_id == object_id,
            )
        )
        replacement = composition_to_persistence_records(state_composition)
        self._session.add_all(replacement.all_records()[1:])

    def _require_atomic_match(
        self,
        result: Any,
        *,
        object_id: UUID,
        organization_id: str,
        expected_revision: int,
    ) -> None:
        cursor = cast(CursorResult[Any], result)
        if cursor.rowcount == 1:
            return
        actual_revision = self._session.scalar(
            select(KnowledgeObjectV2Record.revision).where(
                KnowledgeObjectV2Record.object_id == object_id,
                KnowledgeObjectV2Record.organization_id == organization_id,
            )
        )
        if actual_revision is None:
            raise KnowledgeObjectV2RepositoryError(
                "knowledge_object_not_found",
                "no Knowledge Object v2 exists at the supplied organization boundary",
            )
        raise KnowledgeObjectV2RepositoryError(
            "stale_revision",
            f"expected revision {expected_revision}, persisted revision is {actual_revision}",
        )
