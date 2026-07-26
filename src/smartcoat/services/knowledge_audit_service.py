"""Governed Knowledge mutation orchestration with atomic canonical audit."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from smartcoat.domain.base import LifecycleState
from smartcoat.domain.evidence_provenance import (
    KnowledgeObjectV2EvidenceComposition,
)
from smartcoat.domain.knowledge_audit import (
    GovernedKnowledgeCreateCommand,
    GovernedKnowledgeUpdateCommand,
    KnowledgeAuditAppendRequest,
    KnowledgeAuditChangedField,
    KnowledgeAuditEvent,
    KnowledgeAuditEventType,
    audit_request_from_deletion_plan,
    audit_request_from_lifecycle_plan,
)
from smartcoat.domain.knowledge_lifecycle import (
    DeleteDraftCommand,
    LifecycleTransitionCommand,
)
from smartcoat.services.knowledge_lifecycle_service import (
    KnowledgeLifecyclePlanner,
)
from smartcoat.storage.repositories.knowledge_audit_repository import (
    KnowledgeAuditParticipant,
    KnowledgeAuditRepository,
)
from smartcoat.storage.repositories.knowledge_v2_repository import (
    KnowledgeObjectV2RepositoryError,
)
from smartcoat.storage.unit_of_work import KnowledgeUnitOfWork


class AuditClock(Protocol):
    def now(self) -> datetime: ...


class SystemAuditClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class KnowledgeAuditServiceError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class KnowledgeAuditMutationResult:
    knowledge: KnowledgeObjectV2EvidenceComposition | None
    audit_event: KnowledgeAuditEvent | None


type UnitOfWorkFactory = Callable[..., KnowledgeUnitOfWork]
type AuditParticipantFactory = Callable[[], KnowledgeAuditParticipant]


_CREATE_CHANGED_FIELDS = (
    KnowledgeAuditChangedField.TITLE,
    KnowledgeAuditChangedField.DESCRIPTION,
    KnowledgeAuditChangedField.KNOWLEDGE_TYPE,
    KnowledgeAuditChangedField.OWNER,
    KnowledgeAuditChangedField.CONFIDENTIALITY,
    KnowledgeAuditChangedField.UNCERTAINTY,
    KnowledgeAuditChangedField.TAGS,
    KnowledgeAuditChangedField.CONTENT,
    KnowledgeAuditChangedField.CONTEXT,
    KnowledgeAuditChangedField.EVIDENCE,
    KnowledgeAuditChangedField.PROVENANCE,
    KnowledgeAuditChangedField.KNOWLEDGE_RELATIONSHIPS,
    KnowledgeAuditChangedField.DECISION_RELATIONSHIPS,
    KnowledgeAuditChangedField.REVISION,
)

_STATE_CHANGED_FIELDS = (
    ("title", KnowledgeAuditChangedField.TITLE),
    ("description", KnowledgeAuditChangedField.DESCRIPTION),
    ("knowledge_type", KnowledgeAuditChangedField.KNOWLEDGE_TYPE),
    ("owner", KnowledgeAuditChangedField.OWNER),
    ("confidentiality", KnowledgeAuditChangedField.CONFIDENTIALITY),
    ("uncertainty", KnowledgeAuditChangedField.UNCERTAINTY),
    ("tags", KnowledgeAuditChangedField.TAGS),
    ("content", KnowledgeAuditChangedField.CONTENT),
    ("context", KnowledgeAuditChangedField.CONTEXT),
    (
        "knowledge_relationships",
        KnowledgeAuditChangedField.KNOWLEDGE_RELATIONSHIPS,
    ),
    (
        "decision_relationships",
        KnowledgeAuditChangedField.DECISION_RELATIONSHIPS,
    ),
)


def _canonical_json(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _changed_fields(
    before: KnowledgeObjectV2EvidenceComposition,
    after: KnowledgeObjectV2EvidenceComposition,
) -> tuple[KnowledgeAuditChangedField, ...]:
    before_state = before.core.mutable_state.to_mutable_state().model_dump(mode="json")
    after_state = after.core.mutable_state.to_mutable_state().model_dump(mode="json")
    changed = [
        audit_field
        for field_name, audit_field in _STATE_CHANGED_FIELDS
        if _canonical_json(before_state[field_name]) != _canonical_json(after_state[field_name])
    ]

    before_evidence = tuple(reference.canonical_metadata_json for reference in before.evidence)
    after_evidence = tuple(reference.canonical_metadata_json for reference in after.evidence)
    if (
        before_state["evidence_ids"] != after_state["evidence_ids"]
        or before_evidence != after_evidence
    ):
        changed.append(KnowledgeAuditChangedField.EVIDENCE)

    if _canonical_json(before.provenance) != _canonical_json(after.provenance):
        changed.append(KnowledgeAuditChangedField.PROVENANCE)
    return tuple(changed)


def _validate_update_preconditions(
    current: KnowledgeObjectV2EvidenceComposition,
    command: GovernedKnowledgeUpdateCommand,
) -> None:
    if command.update.object_id != current.core.object_id:
        raise KnowledgeObjectV2RepositoryError(
            "knowledge_object_target_mismatch",
            "the update command target does not match the current record",
        )
    if command.update.expected_revision != current.core.revision:
        raise KnowledgeObjectV2RepositoryError(
            "stale_revision",
            "the update command expected revision does not match the current record",
        )
    if current.core.lifecycle_state is not LifecycleState.DRAFT:
        raise KnowledgeAuditServiceError(
            "knowledge_update_lifecycle_forbidden",
            "governed material updates are permitted only while lifecycle is draft",
        )


class KnowledgeAuditService:
    """The only Release 1.8 mutation path claiming mutation-plus-audit."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        *,
        clock: AuditClock | None = None,
        participant_factory: AuditParticipantFactory = KnowledgeAuditParticipant,
        unit_of_work_factory: UnitOfWorkFactory = KnowledgeUnitOfWork,
    ) -> None:
        self._session_factory = session_factory
        self._clock = clock or SystemAuditClock()
        self._participant_factory = participant_factory
        self._unit_of_work_factory = unit_of_work_factory
        self._lifecycle_planner = KnowledgeLifecyclePlanner(self._clock)

    def _trusted_now(self) -> datetime:
        occurred_at = self._clock.now()
        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise KnowledgeAuditServiceError(
                "knowledge_audit_clock_invalid",
                "the trusted audit clock must return a timezone-aware timestamp",
            )
        return occurred_at.astimezone(UTC)

    def _unit_of_work(
        self,
        participant: KnowledgeAuditParticipant,
    ) -> KnowledgeUnitOfWork:
        return self._unit_of_work_factory(
            self._session_factory,
            participants=(participant,),
        )

    def create(
        self,
        command: GovernedKnowledgeCreateCommand,
    ) -> KnowledgeAuditMutationResult:
        participant = self._participant_factory()
        with self._unit_of_work(participant) as unit_of_work:
            created = unit_of_work.knowledge_objects.stage_create(
                command.create,
                evidence=command.evidence,
                provenance=command.provenance,
            )
            participant.queue(
                KnowledgeAuditAppendRequest(
                    organization_id=created.core.organization_id,
                    object_id=created.core.object_id,
                    event_type=KnowledgeAuditEventType.CREATE,
                    lifecycle_action=None,
                    actor_id=command.actor.actor_id,
                    actor_role=command.actor.role,
                    occurred_at=self._trusted_now(),
                    correlation_id=command.correlation_id,
                    previous_lifecycle=None,
                    resulting_lifecycle=LifecycleState.DRAFT,
                    previous_revision=None,
                    resulting_revision=1,
                    reason_or_note=command.reason_or_note,
                    changed_fields=_CREATE_CHANGED_FIELDS,
                )
            )
            unit_of_work.commit()
        return KnowledgeAuditMutationResult(
            knowledge=created,
            audit_event=participant.single_appended_event(),
        )

    def update(
        self,
        command: GovernedKnowledgeUpdateCommand,
    ) -> KnowledgeAuditMutationResult:
        participant = self._participant_factory()
        with self._unit_of_work(participant) as unit_of_work:
            current = unit_of_work.knowledge_objects.load_for_controlled_mutation(
                object_id=command.update.object_id,
                organization_id=command.organization_id,
            )
            _validate_update_preconditions(current, command)
            updated = unit_of_work.knowledge_objects.stage_material_update(
                organization_id=command.organization_id,
                object_id=command.update.object_id,
                command=command.update,
                evidence=command.evidence,
                provenance=command.provenance,
            )
            if updated.core.revision == current.core.revision:
                unit_of_work.commit()
                return KnowledgeAuditMutationResult(
                    knowledge=updated,
                    audit_event=None,
                )

            changed_fields = _changed_fields(current, updated)
            if not changed_fields:
                raise KnowledgeAuditServiceError(
                    "knowledge_audit_change_summary_empty",
                    "a material repository update must identify a safe changed field",
                )
            participant.queue(
                KnowledgeAuditAppendRequest(
                    organization_id=command.organization_id,
                    object_id=updated.core.object_id,
                    event_type=KnowledgeAuditEventType.UPDATE,
                    lifecycle_action=None,
                    actor_id=command.actor.actor_id,
                    actor_role=command.actor.role,
                    occurred_at=self._trusted_now(),
                    correlation_id=command.correlation_id,
                    previous_lifecycle=current.core.lifecycle_state,
                    resulting_lifecycle=updated.core.lifecycle_state,
                    previous_revision=current.core.revision,
                    resulting_revision=updated.core.revision,
                    reason_or_note=command.reason_or_note,
                    changed_fields=changed_fields,
                )
            )
            unit_of_work.commit()
        return KnowledgeAuditMutationResult(
            knowledge=updated,
            audit_event=participant.single_appended_event(),
        )

    def transition(
        self,
        *,
        organization_id: str,
        command: LifecycleTransitionCommand,
        correlation_id: UUID,
    ) -> KnowledgeAuditMutationResult:
        participant = self._participant_factory()
        with self._unit_of_work(participant) as unit_of_work:
            current = unit_of_work.knowledge_objects.load_for_controlled_mutation(
                object_id=command.object_id,
                organization_id=organization_id,
            )
            history = unit_of_work.knowledge_objects.lifecycle_history_facts(
                object_id=command.object_id,
                organization_id=organization_id,
            )
            plan = self._lifecycle_planner.plan_transition(
                current.core,
                command,
                history,
            )
            updated = unit_of_work.knowledge_objects.stage_lifecycle_transition(
                organization_id=organization_id,
                plan=plan,
            )
            participant.queue(
                audit_request_from_lifecycle_plan(
                    organization_id=organization_id,
                    plan=plan,
                    correlation_id=correlation_id,
                )
            )
            unit_of_work.commit()
        return KnowledgeAuditMutationResult(
            knowledge=updated,
            audit_event=participant.single_appended_event(),
        )

    def delete_draft(
        self,
        *,
        organization_id: str,
        command: DeleteDraftCommand,
        correlation_id: UUID,
    ) -> KnowledgeAuditMutationResult:
        participant = self._participant_factory()
        with self._unit_of_work(participant) as unit_of_work:
            current = unit_of_work.knowledge_objects.load_for_controlled_mutation(
                object_id=command.object_id,
                organization_id=organization_id,
            )
            history = unit_of_work.knowledge_objects.lifecycle_history_facts(
                object_id=command.object_id,
                organization_id=organization_id,
            )
            deletion_facts = (
                unit_of_work.knowledge_objects.compute_inbound_governed_reference_facts(
                    object_id=command.object_id,
                    organization_id=organization_id,
                )
            )
            plan = self._lifecycle_planner.plan_draft_deletion(
                current.core,
                command,
                history,
                deletion_facts,
            )
            unit_of_work.knowledge_objects.stage_eligible_draft_deletion(
                organization_id=organization_id,
                plan=plan,
            )
            participant.queue(
                audit_request_from_deletion_plan(
                    organization_id=organization_id,
                    plan=plan,
                    correlation_id=correlation_id,
                )
            )
            unit_of_work.commit()
        return KnowledgeAuditMutationResult(
            knowledge=None,
            audit_event=participant.single_appended_event(),
        )

    def history_for_object(
        self,
        *,
        organization_id: str,
        object_id: UUID,
    ) -> tuple[KnowledgeAuditEvent, ...]:
        with self._session_factory() as session:
            return KnowledgeAuditRepository(session).history_for_object(
                organization_id=organization_id,
                object_id=object_id,
            )

    def get_event(
        self,
        *,
        organization_id: str,
        object_id: UUID,
        event_id: UUID,
    ) -> KnowledgeAuditEvent | None:
        with self._session_factory() as session:
            return KnowledgeAuditRepository(session).get_event(
                organization_id=organization_id,
                object_id=object_id,
                event_id=event_id,
            )
