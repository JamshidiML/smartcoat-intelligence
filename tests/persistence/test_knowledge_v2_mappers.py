from datetime import UTC, datetime
from uuid import uuid4

import pytest

from smartcoat.domain.base import LifecycleState
from smartcoat.domain.context_references import (
    ContextIdKind,
    ContextReference,
    ContextType,
    KnowledgeContext,
)
from smartcoat.domain.evidence_provenance import (
    CreationMethod,
    EvidenceCompleteness,
    EvidenceReference,
    EvidenceType,
    KnowledgeObjectV2EvidenceComposition,
    ProvenanceCompleteness,
    ProvenanceTransformation,
    ProvenanceV2,
)
from smartcoat.domain.knowledge_objects import KnowledgeObjectType
from smartcoat.domain.knowledge_objects_v2 import (
    ConfidentialityLevel,
    DecisionObjectRelationship,
    KnowledgeObjectRelationship,
    KnowledgeObjectV2CoreRecord,
    KnowledgeObjectV2MutableState,
    KnowledgeObjectV2PersistedStateSnapshot,
    OwnerReference,
    UncertaintyDeclaration,
    UncertaintyKind,
)
from smartcoat.storage.database.models import KnowledgeObjectRecord
from smartcoat.storage.repositories.knowledge_v2_mappers import (
    KnowledgeObjectV2MappingError,
    assess_legacy_persistence_record,
    composition_to_persistence_records,
    persistence_records_to_composition,
)

NOW = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)


def complete_composition() -> KnowledgeObjectV2EvidenceComposition:
    context = [
        ContextReference(
            context_type=context_type,
            reference_id=f"synthetic-{position}",
            id_kind=ContextIdKind.EXTERNAL,
            source_system="synthetic-test-catalog",
            display_name=f"Synthetic {context_type.value}",
            version=None if position % 2 else "v1",
            relationship_role=f"role-{position}",
            source_reference=f"catalog://synthetic/{position}",
            evidence_reference="evidence-synthetic-1",
            attributes={
                "boolean_true": True,
                "boolean_false": False,
                "integer_one": 1,
                "float_one": 1.0,
                "nullable": None,
                "ordered": [True, 1, 1.0, False],
            },
        )
        for position, context_type in enumerate(ContextType)
    ]
    state = KnowledgeObjectV2MutableState(
        title="Synthetic complete coating observation",
        description=None,
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        owner=OwnerReference(owner_id="synthetic-owner", role="knowledge_steward"),
        confidentiality=ConfidentialityLevel.INTERNAL,
        uncertainty=UncertaintyDeclaration(
            kind=UncertaintyKind.ESTIMATE,
            confidence=0.75,
            note="Synthetic bounded uncertainty.",
        ),
        tags=("synthetic", "coating"),
        content={
            "boolean_true": True,
            "boolean_false": False,
            "integer_one": 1,
            "float_one": 1.0,
            "ordered": [True, 1, 1.0, False, None],
            "nested": {"alpha": "synthetic", "count": 2},
        },
        context=KnowledgeContext(references=context),
        evidence_ids=("evidence-synthetic-1",),
        knowledge_relationships=(
            KnowledgeObjectRelationship(
                target_object_id=uuid4(),
                relationship_type="supports",
                target_revision=2,
            ),
        ),
        decision_relationships=(
            DecisionObjectRelationship(
                target_decision_id=uuid4(),
                relationship_type="informs",
                target_revision=None,
            ),
        ),
    )
    core = KnowledgeObjectV2CoreRecord(
        object_id=uuid4(),
        organization_id="synthetic-org",
        revision=3,
        lifecycle_state=LifecycleState.REVIEWED,
        created_at=NOW,
        updated_at=NOW,
        mutable_state=KnowledgeObjectV2PersistedStateSnapshot.from_mutable_state(state),
    )
    evidence = EvidenceReference(
        evidence_id="evidence-synthetic-1",
        evidence_type=EvidenceType.MEASUREMENT,
        completeness=EvidenceCompleteness.COMPLETE,
        title="Synthetic measurement reference",
        source_reference="synthetic://measurement/1",
        source_system="synthetic-test-catalog",
        captured_by="synthetic-operator",
        captured_at=NOW,
        source_created_at=None,
        integrity=None,
        media_type="application/json",
        confidentiality=ConfidentialityLevel.INTERNAL,
        context_reference=context[0],
    )
    provenance = ProvenanceV2(
        source_system="synthetic-test-catalog",
        source_reference="synthetic://knowledge/1",
        created_by="synthetic-operator",
        creation_method=CreationMethod.MANUAL,
        captured_at=NOW,
        source_created_at=None,
        transformation_history=(
            ProvenanceTransformation(
                transformation_type="synthetic_normalization",
                performed_by="synthetic-pipeline",
                performed_at=NOW,
                note=None,
                source_reference="synthetic://measurement/1",
            ),
        ),
        derived_from_object_id=uuid4(),
        derived_from_revision=1,
        completeness=ProvenanceCompleteness.COMPLETE,
    )
    return KnowledgeObjectV2EvidenceComposition(
        core=core,
        evidence=(evidence,),
        provenance=provenance,
    )


def test_complete_composition_round_trips_without_semantic_loss() -> None:
    composition = complete_composition()
    records = composition_to_persistence_records(
        composition,
        has_ever_left_draft=True,
    )

    reconstructed = persistence_records_to_composition(
        records.root,
        tags=records.tags,
        evidence=records.evidence,
        provenance=records.provenance,
        context=records.context,
        knowledge_relationships=records.knowledge_relationships,
        decision_relationships=records.decision_relationships,
    )

    assert reconstructed.model_dump(mode="json") == composition.model_dump(mode="json")
    content = reconstructed.core.mutable_state.content
    assert content["boolean_true"] is True
    assert content["boolean_false"] is False
    assert type(content["integer_one"]) is int
    assert type(content["float_one"]) is float
    assert content["ordered"] == [True, 1, 1.0, False, None]
    assert [
        reference.context_type for reference in reconstructed.core.mutable_state.context.references
    ] == list(ContextType)


def test_corrupt_position_sequence_fails_closed() -> None:
    records = composition_to_persistence_records(complete_composition())
    records.context[1].position = 99

    with pytest.raises(KnowledgeObjectV2MappingError) as error:
        persistence_records_to_composition(
            records.root,
            tags=records.tags,
            evidence=records.evidence,
            provenance=records.provenance,
            context=records.context,
            knowledge_relationships=records.knowledge_relationships,
            decision_relationships=records.decision_relationships,
        )

    assert error.value.code == "persistence_position_gap"


def test_legacy_assessment_is_explicitly_incomplete_without_fabricated_governance() -> None:
    object_id = uuid4()
    record = KnowledgeObjectRecord(
        object_id=str(object_id),
        knowledge_type=KnowledgeObjectType.OBSERVATION.value,
        title="Synthetic legacy observation",
        description=None,
        domain=None,
        owner=None,
        lifecycle_state=LifecycleState.DRAFT.value,
        evidence=["synthetic://legacy/evidence/1"],
        related_entities=[],
        related_decisions=[],
        confidence=None,
        tags=[],
        content={"synthetic": True},
        provenance={},
        metadata_={},
        created_at=NOW,
        updated_at=NOW,
    )

    assessment = assess_legacy_persistence_record(record)

    assert assessment.contract_version == "legacy_v1_table"
    assert assessment.core.is_v2_complete is False
    assert assessment.evidence_and_provenance.is_canonical_complete is False
    assert assessment.evidence_and_provenance.provenance.provenance.created_by is None
    assert assessment.evidence_and_provenance.provenance.provenance.captured_at is None
    assert "organization_id" not in assessment.core.safe_copy_fields
