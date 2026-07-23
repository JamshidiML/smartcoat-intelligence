from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError

from smartcoat.api.main import app
from smartcoat.api.routes.knowledge import get_knowledge_service
from smartcoat.domain.base import LifecycleState, Provenance
from smartcoat.domain.context_references import (
    ContextIdKind,
    ContextReference,
    ContextType,
    KnowledgeContext,
)
from smartcoat.domain.knowledge_objects import KnowledgeObject, KnowledgeObjectType
from smartcoat.domain.knowledge_objects_v2 import (
    MAX_CONTENT_COLLECTION_ITEMS,
    MAX_CONTENT_JSON_BYTES,
    MAX_CONTENT_NESTING_DEPTH,
    MAX_CONTENT_STRING_LENGTH,
    MAX_CONTENT_TOP_LEVEL_KEYS,
    ConfidentialityLevel,
    DecisionObjectRelationship,
    KnowledgeObjectRelationship,
    KnowledgeObjectUpdateError,
    KnowledgeObjectV2CoreRecord,
    KnowledgeObjectV2CreateCommand,
    KnowledgeObjectV2MutableState,
    KnowledgeObjectV2UpdateCommand,
    LegacyCompatibilityBlocker,
    OwnerReference,
    UncertaintyDeclaration,
    UncertaintyKind,
    UpdateDisposition,
    assess_legacy_knowledge_object,
    evaluate_knowledge_object_update,
)
from smartcoat.services.knowledge_service import KnowledgeService
from smartcoat.storage.database.models import KnowledgeObjectRecord

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_OBJECT_ID = UUID("10000000-0000-4000-8000-000000000001")
SYNTHETIC_RELATED_ID = UUID("10000000-0000-4000-8000-000000000002")
SYNTHETIC_DECISION_ID = UUID("20000000-0000-4000-8000-000000000001")
CREATED_AT = datetime(2026, 1, 2, 9, 30, tzinfo=UTC)


def context_reference(**overrides: object) -> ContextReference:
    payload: dict[str, object] = {
        "context_type": ContextType.PROJECT,
        "reference_id": "SYN-PROJECT-001",
        "id_kind": ContextIdKind.EXTERNAL,
        "source_system": "synthetic_registry",
        "display_name": "Synthetic project",
        "relationship_role": "project",
    }
    payload.update(overrides)
    return ContextReference(**payload)


def mutable_state(**overrides: object) -> KnowledgeObjectV2MutableState:
    payload: dict[str, object] = {
        "title": "Synthetic adhesion observation",
        "description": "Generalized, non-confidential test knowledge.",
        "knowledge_type": KnowledgeObjectType.OBSERVATION,
        "owner": {"owner_id": "actor_synthetic_author", "role": "capture_author"},
        "confidentiality": ConfidentialityLevel.INTERNAL,
        "uncertainty": {
            "kind": UncertaintyKind.ESTIMATE,
            "confidence": 0.75,
            "note": "Synthetic estimate for contract testing.",
        },
        "tags": ["synthetic", "generalized"],
        "content": {"observation": "Generalized synthetic result", "attempt": 1},
        "context": KnowledgeContext(references=[context_reference()]),
        "evidence_ids": ["evidence-synthetic-001"],
        "knowledge_relationships": [
            {
                "target_object_id": SYNTHETIC_RELATED_ID,
                "relationship_type": "supports",
                "target_revision": 2,
            }
        ],
        "decision_relationships": [
            {
                "target_decision_id": SYNTHETIC_DECISION_ID,
                "relationship_type": "informs",
                "target_revision": 1,
            }
        ],
    }
    payload.update(overrides)
    return KnowledgeObjectV2MutableState(**payload)


def core_record(**overrides: object) -> KnowledgeObjectV2CoreRecord:
    payload: dict[str, object] = {
        "object_id": SYNTHETIC_OBJECT_ID,
        "organization_id": "org_synthetic",
        "revision": 3,
        "lifecycle_state": LifecycleState.DRAFT,
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT + timedelta(minutes=10),
        "mutable_state": mutable_state(),
    }
    payload.update(overrides)
    return KnowledgeObjectV2CoreRecord(**payload)


@pytest.mark.parametrize("level", list(ConfidentialityLevel))
def test_every_confidentiality_value_is_supported(level: ConfidentialityLevel) -> None:
    assert mutable_state(confidentiality=level).confidentiality is level


def test_owner_and_organization_identifiers_are_trimmed() -> None:
    owner = OwnerReference(owner_id="  actor_synthetic  ", role="  reviewer  ")
    command = KnowledgeObjectV2CreateCommand(
        organization_id="  org_synthetic  ",
        mutable_state=mutable_state(owner=owner),
    )

    assert command.organization_id == "org_synthetic"
    assert command.mutable_state.owner.owner_id == "actor_synthetic"
    assert command.mutable_state.owner.role == "reviewer"


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"organization_id": "  ", "mutable_state": mutable_state()}, "organization_id"),
        ({"owner_id": " ", "role": "author"}, "owner_id"),
        ({"owner_id": "actor_synthetic", "role": "\t"}, "role"),
    ],
)
def test_blank_governance_identifiers_are_rejected(
    payload: dict[str, object],
    field: str,
) -> None:
    with pytest.raises(ValidationError) as error:
        if "organization_id" in payload:
            KnowledgeObjectV2CreateCommand(**payload)
        else:
            OwnerReference(**payload)

    assert field in str(error.value)


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (OwnerReference, {"owner_id": "actor_synthetic", "role": "author", "trusted": True}),
        (
            UncertaintyDeclaration,
            {"kind": "estimate", "confidence": 0.5, "lifecycle_state": "approved"},
        ),
        (
            KnowledgeObjectRelationship,
            {
                "target_object_id": SYNTHETIC_RELATED_ID,
                "relationship_type": "supports",
                "database_id": 1,
            },
        ),
    ],
)
def test_value_objects_forbid_extra_fields(
    model: type[OwnerReference] | type[UncertaintyDeclaration] | type[KnowledgeObjectRelationship],
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        model.model_validate(payload)


@pytest.mark.parametrize(
    "model",
    [
        OwnerReference,
        UncertaintyDeclaration,
        KnowledgeObjectRelationship,
        DecisionObjectRelationship,
        KnowledgeObjectV2MutableState,
        KnowledgeObjectV2CreateCommand,
        KnowledgeObjectV2UpdateCommand,
        KnowledgeObjectV2CoreRecord,
    ],
)
def test_all_v2_input_models_forbid_extra_fields(model: type[BaseModel]) -> None:
    assert model.model_config["extra"] == "forbid"


@pytest.mark.parametrize(
    "factory",
    [
        lambda: OwnerReference(owner_id="x" * 513, role="author"),
        lambda: OwnerReference(owner_id="actor_synthetic", role="x" * 129),
        lambda: KnowledgeObjectV2CreateCommand(
            organization_id="x" * 513,
            mutable_state=mutable_state(),
        ),
    ],
)
def test_governance_identifiers_are_bounded(factory: Callable[[], object]) -> None:
    with pytest.raises(ValidationError, match="knowledge_v2_text_too_long"):
        factory()


@pytest.mark.parametrize("kind", list(UncertaintyKind))
def test_every_uncertainty_kind_is_supported(kind: UncertaintyKind) -> None:
    payload: dict[str, object] = {"kind": kind}
    if kind is UncertaintyKind.CONFLICT:
        payload["note"] = "Synthetic sources conflict."
    elif kind is not UncertaintyKind.UNKNOWN:
        payload["confidence"] = 0.5

    declaration = UncertaintyDeclaration(**payload)

    assert declaration.kind is kind


@pytest.mark.parametrize("confidence", [0.0, 1.0])
def test_uncertainty_confidence_accepts_bounds(confidence: float) -> None:
    declaration = UncertaintyDeclaration(
        kind=UncertaintyKind.ESTIMATE,
        confidence=confidence,
    )

    assert declaration.confidence == confidence


@pytest.mark.parametrize(
    "confidence",
    [-0.01, 1.01, float("nan"), float("inf"), -float("inf"), True],
)
def test_uncertainty_rejects_invalid_confidence(confidence: float | bool) -> None:
    with pytest.raises(ValidationError):
        UncertaintyDeclaration(kind=UncertaintyKind.ESTIMATE, confidence=confidence)


def test_conflict_uncertainty_requires_non_empty_note() -> None:
    with pytest.raises(ValidationError, match="knowledge_v2_uncertainty_conflict_note_required"):
        UncertaintyDeclaration(kind=UncertaintyKind.CONFLICT)

    with pytest.raises(ValidationError, match="knowledge_v2_blank_text"):
        UncertaintyDeclaration(kind=UncertaintyKind.CONFLICT, note="   ")


def test_unknown_uncertainty_rejects_numeric_confidence() -> None:
    with pytest.raises(
        ValidationError,
        match="knowledge_v2_uncertainty_unknown_confidence_forbidden",
    ):
        UncertaintyDeclaration(kind=UncertaintyKind.UNKNOWN, confidence=0.0)


def test_uncertainty_serialization_round_trip() -> None:
    declaration = UncertaintyDeclaration(
        kind=UncertaintyKind.INFERENCE,
        confidence=0.65,
        note="  Synthetic inference.  ",
    )

    restored = UncertaintyDeclaration.model_validate_json(declaration.model_dump_json())

    assert restored == declaration
    assert restored.note == "Synthetic inference."


def test_bounded_content_accepts_finite_json_and_preserves_order() -> None:
    content = {
        "first": None,
        "second": [True, 2, 3.5, "synthetic"],
        "third": {"nested": "value"},
    }

    state = mutable_state(content=content)

    assert list(state.content) == ["first", "second", "third"]
    assert state.content == content


@pytest.mark.parametrize("invalid", [b"raw", {"set"}, object()])
def test_bounded_content_rejects_non_json_values(invalid: object) -> None:
    with pytest.raises(ValidationError, match="knowledge_v2_content_invalid_type"):
        mutable_state(content={"invalid": invalid})


def test_bounded_content_rejects_non_string_keys() -> None:
    with pytest.raises(ValidationError, match="knowledge_v2_content_non_string_key"):
        mutable_state(content={1: "invalid"})


@pytest.mark.parametrize("number", [float("nan"), float("inf"), -float("inf")])
def test_bounded_content_rejects_non_finite_numbers(number: float) -> None:
    with pytest.raises(ValidationError, match="knowledge_v2_content_non_finite_number"):
        mutable_state(content={"number": number})


def test_bounded_content_rejects_excessive_depth() -> None:
    too_deep = {"a": {"b": {"c": {"d": {"e": "too deep"}}}}}

    with pytest.raises(ValidationError, match="knowledge_v2_content_too_deep"):
        mutable_state(content=too_deep)

    assert MAX_CONTENT_NESTING_DEPTH == 4


def test_bounded_content_rejects_excessive_top_level_keys() -> None:
    content = {f"key_{index}": index for index in range(MAX_CONTENT_TOP_LEVEL_KEYS + 1)}

    with pytest.raises(
        ValidationError,
        match="knowledge_v2_content_too_many_top_level_keys",
    ):
        mutable_state(content=content)


@pytest.mark.parametrize(
    "content",
    [
        {"items": list(range(MAX_CONTENT_COLLECTION_ITEMS + 1))},
        {"items": {str(index): index for index in range(MAX_CONTENT_COLLECTION_ITEMS + 1)}},
    ],
)
def test_bounded_content_rejects_excessive_collection_size(
    content: dict[str, object],
) -> None:
    with pytest.raises(ValidationError, match="knowledge_v2_content_collection_too_large"):
        mutable_state(content=content)


def test_bounded_content_rejects_excessive_string_size() -> None:
    with pytest.raises(ValidationError, match="knowledge_v2_content_string_too_long"):
        mutable_state(content={"value": "x" * (MAX_CONTENT_STRING_LENGTH + 1)})


def test_bounded_content_rejects_excessive_serialized_size() -> None:
    content = {f"key_{index}": "x" * MAX_CONTENT_STRING_LENGTH for index in range(9)}

    with pytest.raises(ValidationError, match="knowledge_v2_content_payload_too_large"):
        mutable_state(content=content)

    assert MAX_CONTENT_JSON_BYTES == 32768


def test_relationships_are_typed_and_relationship_types_are_trimmed() -> None:
    knowledge = KnowledgeObjectRelationship(
        target_object_id=SYNTHETIC_RELATED_ID,
        relationship_type="  supports  ",
        target_revision=2,
    )
    decision = DecisionObjectRelationship(
        target_decision_id=SYNTHETIC_DECISION_ID,
        relationship_type="  informs  ",
        target_revision=1,
    )

    assert knowledge.relationship_type == "supports"
    assert decision.relationship_type == "informs"


@pytest.mark.parametrize("relationship_type", ["", "   ", "\t"])
def test_relationship_type_rejects_blank_values(relationship_type: str) -> None:
    with pytest.raises(ValidationError, match="knowledge_v2_blank_text"):
        KnowledgeObjectRelationship(
            target_object_id=SYNTHETIC_RELATED_ID,
            relationship_type=relationship_type,
        )


def test_relationship_type_is_bounded() -> None:
    with pytest.raises(ValidationError, match="knowledge_v2_text_too_long"):
        KnowledgeObjectRelationship(
            target_object_id=SYNTHETIC_RELATED_ID,
            relationship_type="x" * 129,
        )


@pytest.mark.parametrize("target_revision", [0, -1])
def test_relationship_target_revision_must_be_positive(target_revision: int) -> None:
    with pytest.raises(ValidationError):
        DecisionObjectRelationship(
            target_decision_id=SYNTHETIC_DECISION_ID,
            relationship_type="informs",
            target_revision=target_revision,
        )


@pytest.mark.parametrize("field", ["knowledge_relationships", "decision_relationships"])
def test_exact_relationship_duplicates_are_rejected(field: str) -> None:
    relationship: KnowledgeObjectRelationship | DecisionObjectRelationship
    if field == "knowledge_relationships":
        relationship = KnowledgeObjectRelationship(
            target_object_id=SYNTHETIC_RELATED_ID,
            relationship_type="supports",
            target_revision=2,
        )
    else:
        relationship = DecisionObjectRelationship(
            target_decision_id=SYNTHETIC_DECISION_ID,
            relationship_type="informs",
            target_revision=1,
        )

    with pytest.raises(ValidationError, match="knowledge_v2_relationship_exact_duplicate"):
        mutable_state(**{field: [relationship, relationship.model_copy(deep=True)]})


@pytest.mark.parametrize("field", ["knowledge_relationships", "decision_relationships"])
def test_relationship_revision_conflicts_are_rejected(field: str) -> None:
    if field == "knowledge_relationships":
        first = KnowledgeObjectRelationship(
            target_object_id=SYNTHETIC_RELATED_ID,
            relationship_type="supports",
            target_revision=1,
        )
        second = first.model_copy(update={"target_revision": 2})
    else:
        first = DecisionObjectRelationship(
            target_decision_id=SYNTHETIC_DECISION_ID,
            relationship_type="informs",
            target_revision=1,
        )
        second = first.model_copy(update={"target_revision": 2})

    with pytest.raises(ValidationError, match="knowledge_v2_relationship_revision_conflict"):
        mutable_state(**{field: [first, second]})


def test_valid_relationship_order_is_preserved() -> None:
    first = KnowledgeObjectRelationship(
        target_object_id=SYNTHETIC_RELATED_ID,
        relationship_type="supports",
    )
    second = KnowledgeObjectRelationship(
        target_object_id=uuid4(),
        relationship_type="qualifies",
    )

    state = mutable_state(knowledge_relationships=[first, second])

    assert state.knowledge_relationships == (first, second)


def test_persisted_record_rejects_self_relationship() -> None:
    state = mutable_state(
        knowledge_relationships=[
            KnowledgeObjectRelationship(
                target_object_id=SYNTHETIC_OBJECT_ID,
                relationship_type="duplicates",
            )
        ]
    )

    with pytest.raises(ValidationError, match="knowledge_v2_self_relationship"):
        core_record(mutable_state=state)


def test_tags_and_evidence_ids_are_trimmed_unique_and_ordered() -> None:
    state = mutable_state(
        tags=[" first ", "second"],
        evidence_ids=[" evidence-synthetic-a ", "evidence-synthetic-b"],
    )

    assert state.tags == ("first", "second")
    assert state.evidence_ids == ("evidence-synthetic-a", "evidence-synthetic-b")


@pytest.mark.parametrize("field", ["tags", "evidence_ids"])
def test_duplicate_or_blank_identity_collections_are_rejected(field: str) -> None:
    with pytest.raises(ValidationError, match="knowledge_v2_duplicate_text_item"):
        mutable_state(**{field: [" synthetic ", "synthetic"]})

    with pytest.raises(ValidationError, match="knowledge_v2_blank_text"):
        mutable_state(**{field: [" "]})


def test_evidence_boundary_accepts_identity_only() -> None:
    schema = KnowledgeObjectV2MutableState.model_json_schema()["properties"]

    assert "evidence_ids" in schema
    assert "evidence" not in schema
    assert "evidence_references" not in schema
    with pytest.raises(ValidationError):
        mutable_state(evidence_ids=[{"evidence_id": "evidence-synthetic-001"}])


def test_existing_knowledge_context_is_composed_without_duplication() -> None:
    context = KnowledgeContext(references=[context_reference()])

    state = mutable_state(context=context)

    assert state.context is context
    assert isinstance(state.context.references[0], ContextReference)


def test_mutable_state_contains_only_editable_fields() -> None:
    immutable = {
        "object_id",
        "organization_id",
        "revision",
        "lifecycle_state",
        "created_at",
        "updated_at",
    }

    assert immutable.isdisjoint(KnowledgeObjectV2MutableState.model_fields)
    assert {"author", "creator", "created_by"}.isdisjoint(
        KnowledgeObjectV2MutableState.model_fields
    )
    assert {"lifecycle_state", "review_status"}.isdisjoint(UncertaintyDeclaration.model_fields)


def test_title_and_description_are_normalized_and_bounded() -> None:
    state = mutable_state(title="  Synthetic title  ", description="  Synthetic description  ")

    assert state.title == "Synthetic title"
    assert state.description == "Synthetic description"
    with pytest.raises(ValidationError, match="knowledge_v2_blank_text"):
        mutable_state(title=" ")
    with pytest.raises(ValidationError, match="knowledge_v2_blank_text"):
        mutable_state(description=" ")


def test_valid_create_command_has_no_fake_persisted_fields() -> None:
    command = KnowledgeObjectV2CreateCommand(
        organization_id="org_synthetic",
        mutable_state=mutable_state(),
    )

    dumped = command.model_dump(mode="json")
    assert set(dumped) == {"organization_id", "mutable_state"}
    assert {
        "object_id",
        "revision",
        "lifecycle_state",
        "created_at",
        "updated_at",
    }.isdisjoint(dumped)


@pytest.mark.parametrize(
    "forbidden",
    ["object_id", "revision", "lifecycle_state", "created_at", "updated_at", "audit_events"],
)
def test_create_command_rejects_server_managed_fields(forbidden: str) -> None:
    payload = {
        "organization_id": "org_synthetic",
        "mutable_state": mutable_state(),
        forbidden: "synthetic-forbidden-value",
    }

    with pytest.raises(ValidationError, match="extra_forbidden"):
        KnowledgeObjectV2CreateCommand.model_validate(payload)


def test_valid_update_command_is_full_state_replacement() -> None:
    replacement = mutable_state(title="Replacement synthetic title")
    command = KnowledgeObjectV2UpdateCommand(
        object_id=SYNTHETIC_OBJECT_ID,
        expected_revision=3,
        replacement=replacement,
    )

    assert command.replacement == replacement
    assert set(command.model_dump()) == {"object_id", "expected_revision", "replacement"}


@pytest.mark.parametrize("expected_revision", [0, -1])
def test_update_expected_revision_must_be_positive(expected_revision: int) -> None:
    with pytest.raises(ValidationError):
        KnowledgeObjectV2UpdateCommand(
            object_id=SYNTHETIC_OBJECT_ID,
            expected_revision=expected_revision,
            replacement=mutable_state(),
        )


@pytest.mark.parametrize(
    "forbidden",
    ["organization_id", "lifecycle_state", "revision", "created_at", "updated_at"],
)
def test_update_command_rejects_immutable_or_lifecycle_fields(forbidden: str) -> None:
    payload = {
        "object_id": SYNTHETIC_OBJECT_ID,
        "expected_revision": 3,
        "replacement": mutable_state(),
        forbidden: "synthetic-forbidden-value",
    }

    with pytest.raises(ValidationError, match="extra_forbidden"):
        KnowledgeObjectV2UpdateCommand.model_validate(payload)


def test_update_evaluation_rejects_target_mismatch() -> None:
    command = KnowledgeObjectV2UpdateCommand(
        object_id=uuid4(),
        expected_revision=3,
        replacement=mutable_state(),
    )

    with pytest.raises(KnowledgeObjectUpdateError) as error:
        evaluate_knowledge_object_update(core_record(), command)

    assert error.value.code == "knowledge_object_target_mismatch"


def test_update_evaluation_rejects_stale_revision_before_no_op_comparison() -> None:
    current = core_record()
    command = KnowledgeObjectV2UpdateCommand(
        object_id=current.object_id,
        expected_revision=current.revision - 1,
        replacement=current.mutable_state,
    )

    with pytest.raises(KnowledgeObjectUpdateError) as error:
        evaluate_knowledge_object_update(current, command)

    assert error.value.code == "stale_revision"


def test_update_evaluation_detects_normalized_no_op_without_mutation() -> None:
    current = core_record()
    original = current.model_dump(mode="json")
    replacement = mutable_state(title="  Synthetic adhesion observation  ")
    command = KnowledgeObjectV2UpdateCommand(
        object_id=current.object_id,
        expected_revision=current.revision,
        replacement=replacement,
    )

    disposition = evaluate_knowledge_object_update(current, command)

    assert disposition is UpdateDisposition.NO_OP
    assert current.model_dump(mode="json") == original


def test_update_evaluation_detects_material_change_without_incrementing_revision() -> None:
    current = core_record()
    command = KnowledgeObjectV2UpdateCommand(
        object_id=current.object_id,
        expected_revision=current.revision,
        replacement=current.mutable_state.model_copy(update={"title": "Changed synthetic title"}),
    )

    disposition = evaluate_knowledge_object_update(current, command)

    assert disposition is UpdateDisposition.MATERIAL_CHANGE
    assert current.revision == 3
    assert current.updated_at == CREATED_AT + timedelta(minutes=10)


def test_core_record_requires_positive_persisted_revision() -> None:
    with pytest.raises(ValidationError):
        core_record(revision=0)


def test_core_record_normalizes_aware_timestamps_to_utc() -> None:
    plus_two = timezone(timedelta(hours=2))
    created = datetime(2026, 1, 2, 11, 30, tzinfo=plus_two)
    updated = created + timedelta(minutes=5)

    record = core_record(created_at=created, updated_at=updated)

    assert record.created_at == CREATED_AT
    assert record.created_at.tzinfo is UTC
    assert record.updated_at.tzinfo is UTC


@pytest.mark.parametrize("field", ["created_at", "updated_at"])
def test_core_record_rejects_naive_timestamps(field: str) -> None:
    with pytest.raises(ValidationError, match="knowledge_v2_naive_timestamp"):
        core_record(**{field: datetime(2026, 1, 2, 9, 30)})


def test_core_record_rejects_updated_before_created() -> None:
    with pytest.raises(ValidationError, match="knowledge_v2_updated_before_created"):
        core_record(updated_at=CREATED_AT - timedelta(seconds=1))


def test_core_record_is_frozen() -> None:
    record = core_record()

    with pytest.raises(ValidationError, match="frozen_instance"):
        record.revision = 4


def test_core_record_serialization_round_trip() -> None:
    record = core_record()

    restored = KnowledgeObjectV2CoreRecord.model_validate_json(record.model_dump_json())

    assert restored == record
    assert restored.lifecycle_state is LifecycleState.DRAFT


def legacy_object(**overrides: object) -> KnowledgeObject:
    payload: dict[str, object] = {
        "object_id": SYNTHETIC_OBJECT_ID,
        "title": "Synthetic Release 1.7 object",
        "description": "Generalized compatibility fixture.",
        "knowledge_type": KnowledgeObjectType.OBSERVATION,
        "owner": "legacy_owner_text",
        "evidence": ["synthetic://legacy/evidence/1"],
        "related_entities": [SYNTHETIC_RELATED_ID],
        "related_decisions": [SYNTHETIC_DECISION_ID],
        "confidence": 0.6,
        "tags": ["synthetic"],
        "content": {"observation": "Generalized result"},
        "provenance": Provenance(
            source_system="synthetic_legacy",
            source_reference="synthetic://legacy/object/1",
            created_by="actor_synthetic",
            method="manual",
        ),
    }
    payload.update(overrides)
    return KnowledgeObject(**payload)


def test_legacy_assessment_is_fail_closed_and_deterministic() -> None:
    assessment = assess_legacy_knowledge_object(legacy_object())

    assert assessment.is_v2_complete is False
    assert assessment.blockers == (
        LegacyCompatibilityBlocker.MISSING_ORGANIZATION_ID,
        LegacyCompatibilityBlocker.MISSING_STRUCTURED_OWNER,
        LegacyCompatibilityBlocker.MISSING_CONFIDENTIALITY,
        LegacyCompatibilityBlocker.LEGACY_EVIDENCE_REQUIRES_T03,
        LegacyCompatibilityBlocker.LEGACY_RELATED_ENTITIES_REQUIRE_CLASSIFICATION,
        LegacyCompatibilityBlocker.LEGACY_RELATED_DECISIONS_REQUIRE_TYPING,
        LegacyCompatibilityBlocker.LEGACY_CONFIDENCE_REQUIRES_UNCERTAINTY_KIND,
        LegacyCompatibilityBlocker.MINIMAL_PROVENANCE_REQUIRES_T03,
        LegacyCompatibilityBlocker.REVISION_MIGRATION_REQUIRES_T05,
        LegacyCompatibilityBlocker.LIFECYCLE_MIGRATION_REQUIRES_T05,
    )
    assert assessment.safe_copy_fields == (
        "knowledge_type",
        "title",
        "description",
        "tags",
        "content",
    )


def test_legacy_assessment_does_not_fabricate_governance_or_mutate_source() -> None:
    legacy = legacy_object()
    before = legacy.model_dump(mode="json")

    assessment = assess_legacy_knowledge_object(legacy)

    dumped = assessment.model_dump(mode="json")
    assert "organization_id" not in dumped
    assert "owner" not in dumped
    assert "confidentiality" not in dumped
    assert legacy.model_dump(mode="json") == before


def test_empty_legacy_optional_fields_do_not_create_false_blockers() -> None:
    assessment = assess_legacy_knowledge_object(
        legacy_object(
            evidence=[],
            related_entities=[],
            related_decisions=[],
            confidence=None,
        )
    )

    assert LegacyCompatibilityBlocker.LEGACY_EVIDENCE_REQUIRES_T03 not in assessment.blockers
    assert (
        LegacyCompatibilityBlocker.LEGACY_RELATED_ENTITIES_REQUIRE_CLASSIFICATION
        not in assessment.blockers
    )
    assert (
        LegacyCompatibilityBlocker.LEGACY_RELATED_DECISIONS_REQUIRE_TYPING
        not in assessment.blockers
    )
    assert (
        LegacyCompatibilityBlocker.LEGACY_CONFIDENCE_REQUIRES_UNCERTAINTY_KIND
        not in assessment.blockers
    )
    assert LegacyCompatibilityBlocker.MINIMAL_PROVENANCE_REQUIRES_T03 in assessment.blockers


def test_unbounded_legacy_content_is_not_silently_copied() -> None:
    legacy = legacy_object(content={"payload": b"legacy-bytes"})

    assessment = assess_legacy_knowledge_object(legacy)

    assert assessment.bounded_content is None
    assert LegacyCompatibilityBlocker.CONTENT_REQUIRES_REVIEW in assessment.blockers
    assert "content" not in assessment.safe_copy_fields


def test_malformed_legacy_text_is_not_marked_safe_to_copy() -> None:
    assessment = assess_legacy_knowledge_object(
        legacy_object(title=" ", description=" ", tags=["duplicate", " duplicate "])
    )

    assert LegacyCompatibilityBlocker.MUTABLE_TEXT_REQUIRES_REVIEW in assessment.blockers
    assert "title" not in assessment.safe_copy_fields
    assert "description" not in assessment.safe_copy_fields
    assert "tags" not in assessment.safe_copy_fields


def test_current_knowledge_object_schema_remains_release_1_7_only() -> None:
    v2_fields = {
        "organization_id",
        "revision",
        "confidentiality",
        "context",
        "uncertainty",
    }

    assert v2_fields.isdisjoint(KnowledgeObject.model_fields)
    assert v2_fields.isdisjoint(KnowledgeObject.model_json_schema()["properties"])


def test_current_post_knowledge_openapi_does_not_advertise_v2_fields() -> None:
    openapi = app.openapi()
    request_schema = openapi["paths"]["/knowledge"]["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"]
    schema_name = request_schema["$ref"].rsplit("/", maxsplit=1)[-1]
    properties = openapi["components"]["schemas"][schema_name]["properties"]

    assert {
        "organization_id",
        "revision",
        "confidentiality",
        "context",
        "uncertainty",
    }.isdisjoint(properties)


def test_v2_create_payload_cannot_enter_current_post_knowledge_route() -> None:
    command = KnowledgeObjectV2CreateCommand(
        organization_id="org_synthetic",
        mutable_state=mutable_state(),
    )
    app.dependency_overrides[get_knowledge_service] = lambda: KnowledgeService()
    try:
        response = TestClient(app).post("/knowledge", json=command.model_dump(mode="json"))
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_current_mapper_repository_service_and_route_do_not_import_v2() -> None:
    paths = [
        "src/smartcoat/api/routes/knowledge.py",
        "src/smartcoat/services/knowledge_service.py",
        "src/smartcoat/storage/repositories/knowledge_repository.py",
        "src/smartcoat/storage/repositories/mappers.py",
        "src/smartcoat/storage/database/models.py",
    ]

    for path in paths:
        assert "knowledge_objects_v2" not in (ROOT / path).read_text(encoding="utf-8")


def test_current_api_import_does_not_eagerly_load_v2_module() -> None:
    script = (
        "import sys; "
        "import smartcoat.api.main; "
        "assert 'smartcoat.domain.knowledge_objects_v2' not in sys.modules"
    )
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src")}

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_current_database_record_shape_remains_release_1_7_only() -> None:
    assert list(KnowledgeObjectRecord.__table__.columns.keys()) == [
        "object_id",
        "knowledge_type",
        "title",
        "description",
        "domain",
        "owner",
        "lifecycle_state",
        "evidence",
        "related_entities",
        "related_decisions",
        "confidence",
        "tags",
        "content",
        "provenance",
        "metadata",
        "created_at",
        "updated_at",
    ]


def test_public_domain_exports_resolve_v2_types_lazily() -> None:
    from smartcoat.domain import KnowledgeObjectV2CoreRecord as ExportedCoreRecord

    assert ExportedCoreRecord is KnowledgeObjectV2CoreRecord
