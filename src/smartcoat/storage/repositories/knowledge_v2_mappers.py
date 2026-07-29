from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from smartcoat.domain.base import LifecycleState
from smartcoat.domain.context_references import ContextReference, KnowledgeContext
from smartcoat.domain.evidence_provenance import (
    EvidenceReference,
    KnowledgeObjectV2EvidenceComposition,
    LegacyKnowledgeObjectV2EvidenceAdapterResult,
    ProvenanceV2,
    adapt_legacy_evidence_and_provenance,
)
from smartcoat.domain.knowledge_objects import KnowledgeObjectType
from smartcoat.domain.knowledge_objects_v2 import (
    ConfidentialityLevel,
    DecisionObjectRelationship,
    KnowledgeObjectRelationship,
    KnowledgeObjectV2CoreRecord,
    KnowledgeObjectV2MutableState,
    KnowledgeObjectV2PersistedStateSnapshot,
    LegacyKnowledgeObjectCompatibilityAssessment,
    OwnerReference,
    assess_legacy_knowledge_object,
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
from smartcoat.storage.database.models import KnowledgeObjectRecord
from smartcoat.storage.repositories.mappers import record_to_knowledge


class KnowledgeObjectV2MappingError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class KnowledgeObjectV2PersistenceRecords:
    root: KnowledgeObjectV2Record
    tags: tuple[KnowledgeObjectV2TagRecord, ...]
    evidence: tuple[KnowledgeObjectV2EvidenceRecord, ...]
    provenance: KnowledgeObjectV2ProvenanceRecord
    context: tuple[KnowledgeObjectV2ContextRecord, ...]
    knowledge_relationships: tuple[KnowledgeObjectV2KnowledgeRelationshipRecord, ...]
    decision_relationships: tuple[KnowledgeObjectV2DecisionRelationshipRecord, ...]

    def all_records(self) -> tuple[object, ...]:
        return (
            self.root,
            *self.tags,
            *self.evidence,
            self.provenance,
            *self.context,
            *self.knowledge_relationships,
            *self.decision_relationships,
        )


@dataclass(frozen=True)
class LegacyKnowledgeObjectPersistenceAssessment:
    contract_version: str
    core: LegacyKnowledgeObjectCompatibilityAssessment
    evidence_and_provenance: LegacyKnowledgeObjectV2EvidenceAdapterResult


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def mutable_state_values(state: KnowledgeObjectV2MutableState) -> dict[str, Any]:
    return {
        "title": state.title,
        "description": state.description,
        "knowledge_type": state.knowledge_type.value,
        "owner_id": state.owner.owner_id,
        "owner_role": state.owner.role,
        "confidentiality": state.confidentiality.value,
        "uncertainty_json": (
            _canonical_json(state.uncertainty.model_dump(mode="json"))
            if state.uncertainty is not None
            else None
        ),
        "content_json": _canonical_json(state.content),
    }


def composition_to_persistence_records(
    composition: KnowledgeObjectV2EvidenceComposition,
    *,
    has_ever_left_draft: bool = False,
    last_pre_deprecation_lifecycle: str | None = None,
) -> KnowledgeObjectV2PersistenceRecords:
    core = composition.core
    state = core.mutable_state.to_mutable_state()
    root = KnowledgeObjectV2Record(
        object_id=core.object_id,
        organization_id=core.organization_id,
        contract_version="2",
        revision=core.revision,
        lifecycle_state=core.lifecycle_state.value,
        has_ever_left_draft=has_ever_left_draft,
        last_pre_deprecation_lifecycle=last_pre_deprecation_lifecycle,
        created_at=core.created_at,
        updated_at=core.updated_at,
        **mutable_state_values(state),
    )
    organization_id = core.organization_id
    object_id = core.object_id
    tags = tuple(
        KnowledgeObjectV2TagRecord(
            organization_id=organization_id,
            object_id=object_id,
            position=position,
            tag=tag,
        )
        for position, tag in enumerate(state.tags)
    )
    evidence = tuple(
        KnowledgeObjectV2EvidenceRecord(
            organization_id=organization_id,
            object_id=object_id,
            position=position,
            evidence_id=reference.evidence_id,
            canonical_metadata_json=reference.canonical_metadata_json,
        )
        for position, reference in enumerate(composition.evidence)
    )
    provenance = KnowledgeObjectV2ProvenanceRecord(
        organization_id=organization_id,
        object_id=object_id,
        canonical_provenance_json=_canonical_json(composition.provenance.model_dump(mode="json")),
    )
    context = tuple(
        KnowledgeObjectV2ContextRecord(
            organization_id=organization_id,
            object_id=object_id,
            position=position,
            context_type=reference.context_type.value,
            reference_id=reference.reference_id,
            id_kind=reference.id_kind.value,
            source_system=reference.source_system,
            display_name=reference.display_name,
            version=reference.version,
            relationship_role=reference.relationship_role,
            source_reference=reference.source_reference,
            evidence_reference=reference.evidence_reference,
            attributes_json=_canonical_json(reference.attributes),
        )
        for position, reference in enumerate(state.context.references)
    )
    knowledge_relationships = tuple(
        KnowledgeObjectV2KnowledgeRelationshipRecord(
            organization_id=organization_id,
            source_object_id=object_id,
            position=position,
            target_object_id=relationship.target_object_id,
            relationship_type=relationship.relationship_type,
            target_revision=relationship.target_revision,
        )
        for position, relationship in enumerate(state.knowledge_relationships)
    )
    decision_relationships = tuple(
        KnowledgeObjectV2DecisionRelationshipRecord(
            organization_id=organization_id,
            source_object_id=object_id,
            position=position,
            target_decision_id=relationship.target_decision_id,
            relationship_type=relationship.relationship_type,
            target_revision=relationship.target_revision,
        )
        for position, relationship in enumerate(state.decision_relationships)
    )
    return KnowledgeObjectV2PersistenceRecords(
        root=root,
        tags=tags,
        evidence=evidence,
        provenance=provenance,
        context=context,
        knowledge_relationships=knowledge_relationships,
        decision_relationships=decision_relationships,
    )


def _ordered_rows(
    rows: Sequence[Any],
    *,
    organization_id: str,
    object_id: object,
    object_id_attribute: str,
    collection_name: str,
) -> tuple[Any, ...]:
    ordered = tuple(sorted(rows, key=lambda row: row.position))
    if tuple(row.position for row in ordered) != tuple(range(len(ordered))):
        raise KnowledgeObjectV2MappingError(
            "persistence_position_gap",
            f"{collection_name} positions must be contiguous from zero",
        )
    for row in ordered:
        if row.organization_id != organization_id or getattr(row, object_id_attribute) != object_id:
            raise KnowledgeObjectV2MappingError(
                "persistence_aggregate_mismatch",
                f"{collection_name} contains a row from another aggregate",
            )
    return ordered


def persistence_records_to_composition(
    root: KnowledgeObjectV2Record,
    *,
    tags: Sequence[KnowledgeObjectV2TagRecord],
    evidence: Sequence[KnowledgeObjectV2EvidenceRecord],
    provenance: KnowledgeObjectV2ProvenanceRecord | None,
    context: Sequence[KnowledgeObjectV2ContextRecord],
    knowledge_relationships: Sequence[KnowledgeObjectV2KnowledgeRelationshipRecord],
    decision_relationships: Sequence[KnowledgeObjectV2DecisionRelationshipRecord],
) -> KnowledgeObjectV2EvidenceComposition:
    if root.contract_version != "2":
        raise KnowledgeObjectV2MappingError(
            "persistence_contract_version_mismatch",
            "only explicit contract_version=2 rows can reconstruct canonical v2 objects",
        )
    if provenance is None:
        raise KnowledgeObjectV2MappingError(
            "persistence_provenance_missing",
            "a canonical v2 aggregate requires one provenance record",
        )
    if provenance.organization_id != root.organization_id or provenance.object_id != root.object_id:
        raise KnowledgeObjectV2MappingError(
            "persistence_aggregate_mismatch",
            "the provenance record belongs to another aggregate",
        )

    ordered_tags = _ordered_rows(
        tags,
        organization_id=root.organization_id,
        object_id=root.object_id,
        object_id_attribute="object_id",
        collection_name="tags",
    )
    ordered_evidence = _ordered_rows(
        evidence,
        organization_id=root.organization_id,
        object_id=root.object_id,
        object_id_attribute="object_id",
        collection_name="evidence",
    )
    ordered_context = _ordered_rows(
        context,
        organization_id=root.organization_id,
        object_id=root.object_id,
        object_id_attribute="object_id",
        collection_name="context",
    )
    ordered_knowledge_relationships = _ordered_rows(
        knowledge_relationships,
        organization_id=root.organization_id,
        object_id=root.object_id,
        object_id_attribute="source_object_id",
        collection_name="knowledge_relationships",
    )
    ordered_decision_relationships = _ordered_rows(
        decision_relationships,
        organization_id=root.organization_id,
        object_id=root.object_id,
        object_id_attribute="source_object_id",
        collection_name="decision_relationships",
    )

    evidence_models = tuple(
        EvidenceReference(canonical_metadata_json=row.canonical_metadata_json)
        for row in ordered_evidence
    )
    context_models = [
        ContextReference(
            context_type=row.context_type,
            reference_id=row.reference_id,
            id_kind=row.id_kind,
            source_system=row.source_system,
            display_name=row.display_name,
            version=row.version,
            relationship_role=row.relationship_role,
            source_reference=row.source_reference,
            evidence_reference=row.evidence_reference,
            attributes=json.loads(row.attributes_json),
        )
        for row in ordered_context
    ]
    state = KnowledgeObjectV2MutableState(
        title=root.title,
        description=root.description,
        knowledge_type=KnowledgeObjectType(root.knowledge_type),
        owner=OwnerReference(owner_id=root.owner_id, role=root.owner_role),
        confidentiality=ConfidentialityLevel(root.confidentiality),
        uncertainty=(
            json.loads(root.uncertainty_json) if root.uncertainty_json is not None else None
        ),
        tags=tuple(row.tag for row in ordered_tags),
        content=json.loads(root.content_json),
        context=KnowledgeContext(references=context_models),
        evidence_ids=tuple(row.evidence_id for row in ordered_evidence),
        knowledge_relationships=tuple(
            KnowledgeObjectRelationship(
                target_object_id=row.target_object_id,
                relationship_type=row.relationship_type,
                target_revision=row.target_revision,
            )
            for row in ordered_knowledge_relationships
        ),
        decision_relationships=tuple(
            DecisionObjectRelationship(
                target_decision_id=row.target_decision_id,
                relationship_type=row.relationship_type,
                target_revision=row.target_revision,
            )
            for row in ordered_decision_relationships
        ),
    )
    core = KnowledgeObjectV2CoreRecord(
        object_id=root.object_id,
        organization_id=root.organization_id,
        revision=root.revision,
        lifecycle_state=LifecycleState(root.lifecycle_state),
        created_at=root.created_at,
        updated_at=root.updated_at,
        mutable_state=KnowledgeObjectV2PersistedStateSnapshot.from_mutable_state(state),
    )
    return KnowledgeObjectV2EvidenceComposition(
        core=core,
        evidence=evidence_models,
        provenance=ProvenanceV2.model_validate_json(provenance.canonical_provenance_json),
    )


def assess_legacy_persistence_record(
    record: KnowledgeObjectRecord,
) -> LegacyKnowledgeObjectPersistenceAssessment:
    legacy = record_to_knowledge(record)
    return LegacyKnowledgeObjectPersistenceAssessment(
        contract_version="legacy_v1_table",
        core=assess_legacy_knowledge_object(legacy),
        evidence_and_provenance=adapt_legacy_evidence_and_provenance(
            legacy.evidence,
            legacy.provenance,
        ),
    )
