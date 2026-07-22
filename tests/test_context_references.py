from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from smartcoat.domain.context_references import (
    ContextIdKind,
    ContextReference,
    ContextReferenceCollectionError,
    ContextReferenceOrganizationError,
    ContextType,
    validate_context_organization_boundary,
    validate_context_references,
)
from smartcoat.domain.knowledge_objects import KnowledgeObject, KnowledgeObjectType


def external_reference(**overrides: object) -> ContextReference:
    payload: dict[str, object] = {
        "context_type": ContextType.PROJECT,
        "reference_id": "SYN-PROJECT-001",
        "id_kind": ContextIdKind.EXTERNAL,
        "source_system": "synthetic_registry",
        "display_name": "Synthetic project context",
        "relationship_role": "project",
    }
    payload.update(overrides)
    return ContextReference(**payload)


@pytest.mark.parametrize("context_type", list(ContextType))
def test_every_context_type_is_supported(context_type: ContextType) -> None:
    reference = external_reference(
        context_type=context_type,
        reference_id=f"SYN-{context_type.value}",
    )

    assert reference.context_type is context_type


def test_uuid_reference_is_normalized() -> None:
    raw = "A8098C1A-F86E-11DA-BD1A-00112444BE1E"

    reference = ContextReference(
        context_type=ContextType.EXPERIMENT_OR_TRIAL,
        reference_id=raw,
        id_kind=ContextIdKind.UUID,
        display_name="Synthetic trial",
    )

    assert reference.reference_id == "a8098c1a-f86e-11da-bd1a-00112444be1e"


def test_invalid_uuid_is_rejected_with_stable_code() -> None:
    with pytest.raises(ValidationError) as error:
        ContextReference(
            context_type=ContextType.MATERIAL,
            reference_id="not-a-uuid",
            id_kind=ContextIdKind.UUID,
            display_name="Synthetic material",
        )

    assert error.value.errors()[0]["type"] == "context_reference_invalid_uuid"


def test_external_reference_requires_source_system() -> None:
    with pytest.raises(ValidationError) as error:
        external_reference(source_system=None)

    assert error.value.errors()[0]["type"] == "context_reference_source_system_required"


def test_external_reference_rejects_blank_source_system() -> None:
    with pytest.raises(ValidationError) as error:
        external_reference(source_system="  ")

    assert error.value.errors()[0]["type"] == "context_reference_blank_optional_text"


def test_display_name_must_not_be_blank() -> None:
    with pytest.raises(ValidationError) as error:
        external_reference(display_name=" \t ")

    assert error.value.errors()[0]["type"] == "context_reference_blank_text"


@pytest.mark.parametrize(
    "field",
    ["version", "relationship_role", "source_reference", "evidence_reference"],
)
def test_optional_text_fields_reject_blank_values(field: str) -> None:
    with pytest.raises(ValidationError) as error:
        external_reference(**{field: "   "})

    assert error.value.errors()[0]["type"] == "context_reference_blank_optional_text"


def test_serialization_round_trip_preserves_canonical_data() -> None:
    reference = external_reference(
        version="v1",
        source_reference="synthetic://project/001",
        evidence_reference="evidence:synthetic-001",
        attributes={"temperature_c": 120, "conditions": {"duration_h": 2}},
    )

    restored = ContextReference.model_validate_json(reference.model_dump_json())

    assert restored == reference


def test_exact_duplicate_is_rejected() -> None:
    reference = external_reference()

    with pytest.raises(ContextReferenceCollectionError) as error:
        validate_context_references([reference, reference.model_copy(deep=True)])

    assert error.value.code == "context_reference_exact_duplicate"
    assert error.value.first_index == 0
    assert error.value.second_index == 1


def test_same_key_with_different_version_is_conflict() -> None:
    first = external_reference(version="v1")
    second = external_reference(version="v2")

    with pytest.raises(ContextReferenceCollectionError) as error:
        validate_context_references([first, second])

    assert error.value.code == "context_reference_identity_conflict"


def test_same_key_with_different_id_kind_is_conflict() -> None:
    reference_id = str(uuid4())
    first = external_reference(reference_id=reference_id)
    second = ContextReference(
        context_type=ContextType.PROJECT,
        reference_id=reference_id,
        id_kind=ContextIdKind.UUID,
        display_name="Synthetic project context",
        relationship_role="project",
    )

    with pytest.raises(ContextReferenceCollectionError) as error:
        validate_context_references([first, second])

    assert error.value.code == "context_reference_identity_conflict"


def test_same_key_with_different_source_system_is_conflict() -> None:
    first = external_reference(source_system="synthetic_registry_a")
    second = external_reference(source_system="synthetic_registry_b")

    with pytest.raises(ContextReferenceCollectionError) as error:
        validate_context_references([first, second])

    assert error.value.code == "context_reference_identity_conflict"


def test_same_key_with_different_metadata_is_link_key_conflict() -> None:
    first = external_reference(display_name="Synthetic project A")
    second = external_reference(display_name="Synthetic project B")

    with pytest.raises(ContextReferenceCollectionError) as error:
        validate_context_references([first, second])

    assert error.value.code == "context_reference_link_key_conflict"


def test_relationship_role_is_trimmed_and_casefolded() -> None:
    reference = external_reference(relationship_role="  Primary Material  ")

    assert reference.relationship_role == "primary material"


def test_multiple_valid_references_preserve_input_order() -> None:
    first = external_reference(reference_id="SYN-PROJECT-001")
    second = external_reference(
        context_type=ContextType.TEST_RESULT,
        reference_id="SYN-RESULT-001",
        display_name="Synthetic result",
        relationship_role="result",
    )

    assert validate_context_references([first, second]) == [first, second]


def test_knowledge_object_validates_typed_context() -> None:
    reference = external_reference()

    knowledge = KnowledgeObject(
        title="Synthetic observation",
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        context_references=[reference.model_dump()],
    )

    assert knowledge.context_references == [reference]
    assert isinstance(knowledge.context_references[0], ContextReference)


def test_knowledge_object_rejects_duplicate_context() -> None:
    reference = external_reference()

    with pytest.raises(ValidationError, match="context_reference_exact_duplicate"):
        KnowledgeObject(
            title="Synthetic observation",
            knowledge_type=KnowledgeObjectType.OBSERVATION,
            context_references=[reference, reference.model_copy(deep=True)],
        )


def test_legacy_related_entities_remain_separate_and_opaque() -> None:
    legacy_id = uuid4()
    reference = external_reference()

    knowledge = KnowledgeObject(
        title="Synthetic compatibility example",
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        context_references=[reference],
        related_entities=[legacy_id],
    )

    assert knowledge.context_references == [reference]
    assert knowledge.related_entities == [legacy_id]
    assert reference.reference_id != str(legacy_id)


def test_vertical_slice_fixture_represents_all_minimum_context() -> None:
    references = [
        external_reference(
            context_type=context_type,
            reference_id=f"SYN-{index:02d}",
            display_name=f"Synthetic {context_type.value} context",
            relationship_role=context_type.value,
        )
        for index, context_type in enumerate(ContextType, start=1)
    ]

    knowledge = KnowledgeObject(
        title="Synthetic first vertical slice",
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        context_references=references,
    )

    assert [item.context_type for item in knowledge.context_references] == list(ContextType)


def test_attributes_are_bounded_and_normalized() -> None:
    reference = external_reference(
        attributes={
            " temperature_c ": 120,
            "conditions": {"duration_h": 2, "verified": True},
            "labels": ["synthetic", "generalized"],
        }
    )

    assert reference.attributes["temperature_c"] == 120
    assert reference.attributes["conditions"] == {"duration_h": 2, "verified": True}


@pytest.mark.parametrize(
    ("attributes", "error_code"),
    [
        ({"payload": b"raw-bytes"}, "context_attribute_invalid_type"),
        ({"nested": {"deeper": {"not": "allowed"}}}, "context_attribute_invalid_type"),
        ({"api_key": "synthetic-placeholder"}, "context_attribute_credential_key"),
        (
            {"note": "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456"},
            "context_attribute_secret_value",
        ),
    ],
)
def test_attributes_reject_unbounded_or_secret_content(
    attributes: dict[str, object],
    error_code: str,
) -> None:
    with pytest.raises(ValidationError) as error:
        external_reference(attributes=attributes)

    assert error.value.errors()[0]["type"] == error_code


def test_same_organization_boundary_passes() -> None:
    validate_context_organization_boundary(
        containing_organization_id="org_synthetic",
        referenced_organization_id="org_synthetic",
    )


def test_cross_organization_boundary_fails() -> None:
    with pytest.raises(ContextReferenceOrganizationError) as error:
        validate_context_organization_boundary(
            containing_organization_id="org_synthetic_a",
            referenced_organization_id="org_synthetic_b",
        )

    assert error.value.code == "context_reference_cross_organization"


def test_unverifiable_organization_boundary_fails_when_required() -> None:
    with pytest.raises(ContextReferenceOrganizationError) as error:
        validate_context_organization_boundary(
            containing_organization_id="org_synthetic",
            referenced_organization_id=None,
        )

    assert error.value.code == "context_reference_organization_unverifiable"


def test_unverified_boundary_can_remain_deferred_when_not_required() -> None:
    validate_context_organization_boundary(
        containing_organization_id="org_synthetic",
        referenced_organization_id=None,
        verification_required=False,
    )


def test_uuid_model_dump_is_canonical_string() -> None:
    reference_id = uuid4()
    reference = ContextReference(
        context_type=ContextType.MATERIAL,
        reference_id=str(reference_id).upper(),
        id_kind=ContextIdKind.UUID,
        display_name="Synthetic material",
    )

    assert reference.model_dump(mode="json")["reference_id"] == str(UUID(str(reference_id)))
