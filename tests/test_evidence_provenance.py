from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid5

import pytest
from pydantic import BaseModel, ValidationError

import smartcoat.domain.evidence_provenance as evidence_module
from smartcoat.domain.base import LifecycleState, Provenance
from smartcoat.domain.context_references import (
    ContextIdKind,
    ContextReference,
    ContextType,
)
from smartcoat.domain.evidence_provenance import (
    BLAKE2B_SUPPORTED_HEX_LENGTH,
    LEGACY_EVIDENCE_NAMESPACE,
    MAX_DESCRIPTION_LENGTH,
    MAX_EVIDENCE_ID_LENGTH,
    MAX_EVIDENCE_REFERENCES,
    MAX_SOURCE_REFERENCE_LENGTH,
    MAX_TITLE_LENGTH,
    MAX_TRANSFORMATIONS,
    CreationMethod,
    EvidenceCompleteness,
    EvidenceCompositionError,
    EvidenceIntegrity,
    EvidenceReference,
    EvidenceReferenceCollectionError,
    EvidenceType,
    IntegrityAlgorithm,
    KnowledgeObjectV2EvidenceComposition,
    LegacyEvidenceAdapterResult,
    LegacyEvidenceCollectionAdapterResult,
    LegacyKnowledgeObjectV2EvidenceAdapterResult,
    LegacyProvenanceAdapterResult,
    ProvenanceCompleteness,
    ProvenanceTransformation,
    ProvenanceV2,
    adapt_legacy_evidence_and_provenance,
    adapt_legacy_evidence_collection,
    adapt_legacy_evidence_reference,
    adapt_legacy_provenance,
    project_platform_evidence_references,
    validate_evidence_references,
)
from smartcoat.domain.knowledge_objects import KnowledgeObject, KnowledgeObjectType
from smartcoat.domain.knowledge_objects_v2 import (
    ConfidentialityLevel,
    KnowledgeObjectV2CoreRecord,
    KnowledgeObjectV2MutableState,
)

ROOT = Path(__file__).resolve().parents[1]
CAPTURED_AT = datetime(2026, 2, 3, 10, 30, tzinfo=UTC)
OBJECT_ID = UUID("30000000-0000-4000-8000-000000000001")


def context_reference(**overrides: object) -> ContextReference:
    payload: dict[str, object] = {
        "context_type": ContextType.TEST_RESULT,
        "reference_id": "SYN-TEST-001",
        "id_kind": ContextIdKind.EXTERNAL,
        "source_system": "synthetic_register",
        "display_name": "Synthetic test result",
        "relationship_role": "supporting_result",
        "attributes": {"method": "generalized"},
    }
    payload.update(overrides)
    return ContextReference(**payload)


def complete_evidence(**overrides: object) -> EvidenceReference:
    payload: dict[str, object] = {
        "evidence_id": "evidence-synthetic-001",
        "evidence_type": EvidenceType.TEST_RESULT,
        "completeness": EvidenceCompleteness.COMPLETE,
        "title": "Synthetic test result",
        "description": "Generalized evidence metadata only.",
        "source_reference": "synthetic://tests/result-001",
        "source_system": "synthetic_register",
        "captured_by": "actor_synthetic_author",
        "captured_at": CAPTURED_AT,
        "source_created_at": CAPTURED_AT - timedelta(days=1),
        "integrity": {
            "algorithm": IntegrityAlgorithm.SHA256,
            "value": "A" * 64,
        },
        "media_type": " APPLICATION/JSON ",
        "confidentiality": ConfidentialityLevel.INTERNAL,
        "context_reference": context_reference(),
    }
    payload.update(overrides)
    return EvidenceReference(**payload)


def legacy_evidence(**overrides: object) -> EvidenceReference:
    payload: dict[str, object] = {
        "evidence_id": "legacy-evidence-001",
        "evidence_type": EvidenceType.LEGACY_REFERENCE,
        "completeness": EvidenceCompleteness.LEGACY_INCOMPLETE,
        "description": "Explicitly incomplete legacy evidence reference.",
        "source_reference": "legacy://reference/001",
    }
    payload.update(overrides)
    return EvidenceReference(**payload)


def transformation(**overrides: object) -> ProvenanceTransformation:
    payload: dict[str, object] = {
        "transformation_type": "normalized_metadata",
        "performed_by": "actor_synthetic_importer",
        "performed_at": CAPTURED_AT - timedelta(minutes=10),
        "note": "Generalized metadata normalization.",
        "source_reference": "synthetic://imports/job-001",
    }
    payload.update(overrides)
    return ProvenanceTransformation(**payload)


def complete_provenance(**overrides: object) -> ProvenanceV2:
    payload: dict[str, object] = {
        "source_system": "synthetic_register",
        "source_reference": "synthetic://knowledge/source-001",
        "created_by": "actor_synthetic_author",
        "creation_method": CreationMethod.MANUAL,
        "captured_at": CAPTURED_AT,
        "source_created_at": CAPTURED_AT - timedelta(hours=1),
        "transformation_history": [transformation()],
        "completeness": ProvenanceCompleteness.COMPLETE,
    }
    payload.update(overrides)
    return ProvenanceV2(**payload)


def core_record(evidence_ids: tuple[str, ...] | list[str]) -> KnowledgeObjectV2CoreRecord:
    state = KnowledgeObjectV2MutableState(
        title="Synthetic evidence composition",
        description="Generalized domain composition fixture.",
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        owner={"owner_id": "actor_synthetic_author", "role": "capture_author"},
        confidentiality=ConfidentialityLevel.INTERNAL,
        content={"result": "generalized"},
        evidence_ids=evidence_ids,
    )
    return KnowledgeObjectV2CoreRecord(
        object_id=OBJECT_ID,
        organization_id="org_synthetic",
        revision=2,
        lifecycle_state=LifecycleState.DRAFT,
        created_at=CAPTURED_AT,
        updated_at=CAPTURED_AT,
        mutable_state=state,
    )


def assert_validation_code(error: ValidationError, code: str) -> None:
    assert any(item["type"] == code for item in error.errors()), error.errors()


def assert_composition_code(error: ValidationError, code: str) -> None:
    assert code in str(error)
    assert isinstance(error.errors()[0]["ctx"]["error"], EvidenceCompositionError)


def test_canonical_vocabularies_have_exact_bounded_values() -> None:
    assert {item.value for item in EvidenceType} == {
        "legacy_reference",
        "document",
        "image",
        "measurement",
        "test_result",
        "dataset",
        "observation",
        "external_record",
        "other",
    }
    assert {item.value for item in EvidenceCompleteness} == {
        "complete",
        "legacy_incomplete",
    }
    assert {item.value for item in CreationMethod} == {
        "manual",
        "imported",
        "system_generated",
        "derived",
        "legacy_adapter",
    }
    assert {item.value for item in ProvenanceCompleteness} == {
        "complete",
        "legacy_incomplete",
    }
    assert {item.value for item in IntegrityAlgorithm} == {
        "sha256",
        "sha512",
        "blake2b",
    }


@pytest.mark.parametrize("evidence_type", list(EvidenceType))
def test_every_evidence_type_has_one_valid_mode(evidence_type: EvidenceType) -> None:
    if evidence_type is EvidenceType.LEGACY_REFERENCE:
        reference = legacy_evidence()
    else:
        reference = complete_evidence(evidence_type=evidence_type)
    assert reference.evidence_type is evidence_type


def test_complete_reference_normalizes_metadata() -> None:
    reference = complete_evidence(
        evidence_id="  evidence-synthetic-001  ",
        title="  Synthetic test result  ",
        description="  Generalized evidence metadata only.  ",
        source_reference="  synthetic://tests/result-001  ",
        source_system="  synthetic_register  ",
        captured_by="  actor_synthetic_author  ",
    )

    assert reference.evidence_id == "evidence-synthetic-001"
    assert reference.title == "Synthetic test result"
    assert reference.description == "Generalized evidence metadata only."
    assert reference.source_reference == "synthetic://tests/result-001"
    assert reference.source_system == "synthetic_register"
    assert reference.captured_by == "actor_synthetic_author"
    assert reference.media_type == "application/json"
    assert reference.integrity is not None
    assert reference.integrity.value == "a" * 64


def test_reference_requires_title_or_description() -> None:
    with pytest.raises(ValidationError) as error:
        complete_evidence(title=None, description=None)
    assert_validation_code(error.value, "evidence_title_or_description_required")


@pytest.mark.parametrize("field", ["evidence_id", "source_reference"])
def test_reference_rejects_blank_required_identifiers(field: str) -> None:
    with pytest.raises(ValidationError) as error:
        complete_evidence(**{field: " \t "})
    assert_validation_code(error.value, "evidence_provenance_blank_text")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("evidence_id", "e" * (MAX_EVIDENCE_ID_LENGTH + 1)),
        ("source_reference", "s" * (MAX_SOURCE_REFERENCE_LENGTH + 1)),
        ("title", "t" * (MAX_TITLE_LENGTH + 1)),
        ("description", "d" * (MAX_DESCRIPTION_LENGTH + 1)),
    ],
)
def test_reference_rejects_oversized_text(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        complete_evidence(**{field: value})


@pytest.mark.parametrize(
    ("field", "code"),
    [
        ("captured_by", "evidence_complete_actor_required"),
        ("captured_at", "evidence_complete_captured_at_required"),
    ],
)
def test_complete_reference_requires_actor_and_capture_time(field: str, code: str) -> None:
    with pytest.raises(ValidationError) as error:
        complete_evidence(**{field: None})
    assert_validation_code(error.value, code)


def test_legacy_incomplete_reference_preserves_only_available_facts() -> None:
    reference = legacy_evidence()

    assert reference.completeness is EvidenceCompleteness.LEGACY_INCOMPLETE
    assert reference.evidence_type is EvidenceType.LEGACY_REFERENCE
    assert reference.source_reference == "legacy://reference/001"
    assert reference.captured_by is None
    assert reference.captured_at is None
    assert reference.confidentiality is None


def test_legacy_type_cannot_claim_complete_status() -> None:
    with pytest.raises(ValidationError) as error:
        complete_evidence(evidence_type=EvidenceType.LEGACY_REFERENCE)
    assert_validation_code(error.value, "evidence_complete_legacy_type_forbidden")


def test_incomplete_status_requires_legacy_type() -> None:
    with pytest.raises(ValidationError) as error:
        complete_evidence(
            evidence_type=EvidenceType.DOCUMENT,
            completeness=EvidenceCompleteness.LEGACY_INCOMPLETE,
        )
    assert_validation_code(error.value, "evidence_legacy_incomplete_type_required")


@pytest.mark.parametrize("field", ["captured_at", "source_created_at"])
def test_reference_normalizes_aware_timestamps_to_utc(field: str) -> None:
    supplied = datetime(2026, 2, 3, 12, 30, tzinfo=timezone(timedelta(hours=2)))
    reference = complete_evidence(**{field: supplied})

    assert getattr(reference, field) == CAPTURED_AT
    assert getattr(reference, field).tzinfo is UTC


@pytest.mark.parametrize("field", ["captured_at", "source_created_at"])
def test_reference_rejects_naive_timestamps(field: str) -> None:
    with pytest.raises(ValidationError) as error:
        complete_evidence(**{field: datetime(2026, 2, 3, 10, 30)})
    assert_validation_code(error.value, "evidence_provenance_naive_timestamp")


@pytest.mark.parametrize(
    "media_type",
    ["application/json; charset=utf-8", "application", "/json", "application/", "a b/c"],
)
def test_reference_rejects_invalid_media_types(media_type: str) -> None:
    with pytest.raises(ValidationError) as error:
        complete_evidence(media_type=media_type)
    assert_validation_code(error.value, "evidence_invalid_media_type")


def test_reference_reuses_t02_confidentiality_and_t08_context() -> None:
    reference = complete_evidence()

    assert reference.confidentiality is ConfidentialityLevel.INTERNAL
    assert isinstance(reference.context_reference, ContextReference)
    assert reference.context_reference.context_type is ContextType.TEST_RESULT


@pytest.mark.parametrize(
    "extra_field",
    ["raw_bytes", "base64_payload", "body", "ocr_output", "file_metadata"],
)
def test_reference_forbids_raw_or_unrestricted_payload_fields(extra_field: str) -> None:
    payload = complete_evidence().model_dump()
    payload[extra_field] = b"synthetic" if extra_field == "raw_bytes" else "synthetic"
    with pytest.raises(ValidationError):
        EvidenceReference.model_validate(payload)


@pytest.mark.parametrize(
    "source_reference",
    [
        "data:application/pdf;base64,QUJD",
        "synthetic;base64,QUJD",
        "A" * 256,
    ],
)
def test_reference_rejects_embedded_payload_source_reference(source_reference: str) -> None:
    with pytest.raises(ValidationError) as error:
        complete_evidence(source_reference=source_reference)
    assert_validation_code(error.value, "evidence_embedded_payload_forbidden")


def test_reference_forbids_unknown_fields() -> None:
    payload = complete_evidence().model_dump()
    payload["verified"] = True
    with pytest.raises(ValidationError):
        EvidenceReference.model_validate(payload)


def test_reference_serialization_round_trip_is_equivalent() -> None:
    reference = complete_evidence()
    restored = EvidenceReference.model_validate_json(reference.model_dump_json())

    assert restored == reference
    assert restored.context_reference is not reference.context_reference


@pytest.mark.parametrize(
    ("algorithm", "value"),
    [
        (IntegrityAlgorithm.SHA256, "A" * 64),
        (IntegrityAlgorithm.SHA512, "b" * 128),
        (IntegrityAlgorithm.BLAKE2B, "C" * BLAKE2B_SUPPORTED_HEX_LENGTH),
    ],
)
def test_integrity_accepts_supported_digests(
    algorithm: IntegrityAlgorithm,
    value: str,
) -> None:
    integrity = EvidenceIntegrity(algorithm=algorithm, value=value)
    assert integrity.value == value.lower()


@pytest.mark.parametrize(
    ("algorithm", "value"),
    [
        (IntegrityAlgorithm.SHA256, "a" * 63),
        (IntegrityAlgorithm.SHA512, "b" * 127),
        (IntegrityAlgorithm.BLAKE2B, "c" * 64),
    ],
)
def test_integrity_rejects_invalid_lengths(
    algorithm: IntegrityAlgorithm,
    value: str,
) -> None:
    with pytest.raises(ValidationError) as error:
        EvidenceIntegrity(algorithm=algorithm, value=value)
    assert_validation_code(error.value, "evidence_integrity_invalid_length")


def test_integrity_rejects_non_hexadecimal_value() -> None:
    with pytest.raises(ValidationError) as error:
        EvidenceIntegrity(algorithm=IntegrityAlgorithm.SHA256, value="g" * 64)
    assert_validation_code(error.value, "evidence_integrity_invalid_hex")


def test_integrity_rejects_blank_value() -> None:
    with pytest.raises(ValidationError) as error:
        EvidenceIntegrity(algorithm=IntegrityAlgorithm.SHA256, value=" ")
    assert_validation_code(error.value, "evidence_provenance_blank_text")


def test_integrity_rejects_unsupported_algorithm() -> None:
    with pytest.raises(ValidationError):
        EvidenceIntegrity.model_validate({"algorithm": "md5", "value": "a" * 32})


def test_integrity_declaration_has_no_verification_or_trust_claim() -> None:
    assert set(EvidenceIntegrity.model_fields) == {"algorithm", "value"}
    assert "verified" not in EvidenceIntegrity.model_fields
    assert "authentic" not in EvidenceIntegrity.model_fields


def test_valid_evidence_collection_preserves_order() -> None:
    first = complete_evidence(evidence_id="evidence-001")
    second = complete_evidence(evidence_id="evidence-002")

    assert validate_evidence_references([first, second]) == (first, second)


def test_evidence_collection_rejects_exact_duplicate() -> None:
    reference = complete_evidence()
    with pytest.raises(EvidenceReferenceCollectionError) as error:
        validate_evidence_references([reference, reference.model_copy(deep=True)])

    assert error.value.code == "evidence_exact_duplicate"
    assert error.value.first_index == 0
    assert error.value.second_index == 1


def test_evidence_collection_rejects_identity_conflict() -> None:
    first = complete_evidence()
    second = complete_evidence(title="Different normalized metadata")
    with pytest.raises(EvidenceReferenceCollectionError) as error:
        validate_evidence_references([first, second])

    assert error.value.code == "evidence_id_conflict"
    assert error.value.evidence_id == first.evidence_id


def test_evidence_collection_rejects_excessive_size_without_reordering() -> None:
    references = [
        complete_evidence(evidence_id=f"evidence-{index:03d}")
        for index in range(MAX_EVIDENCE_REFERENCES + 1)
    ]
    with pytest.raises(ValueError, match="evidence_collection_too_large"):
        validate_evidence_references(references)


def test_transformation_normalizes_text_and_timestamp() -> None:
    record = transformation(
        transformation_type="  normalized_metadata  ",
        performed_by="  actor_synthetic_importer  ",
        performed_at=datetime(
            2026,
            2,
            3,
            12,
            20,
            tzinfo=timezone(timedelta(hours=2)),
        ),
        note="  Generalized metadata normalization.  ",
    )

    assert record.transformation_type == "normalized_metadata"
    assert record.performed_by == "actor_synthetic_importer"
    assert record.performed_at == CAPTURED_AT - timedelta(minutes=10)
    assert record.note == "Generalized metadata normalization."


@pytest.mark.parametrize("field", ["transformation_type", "performed_by"])
def test_transformation_rejects_blank_required_text(field: str) -> None:
    with pytest.raises(ValidationError):
        transformation(**{field: " "})


@pytest.mark.parametrize("field", ["note", "source_reference"])
def test_transformation_rejects_blank_optional_text(field: str) -> None:
    with pytest.raises(ValidationError):
        transformation(**{field: " "})


def test_transformation_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError) as error:
        transformation(performed_at=datetime(2026, 2, 3, 10, 20))
    assert_validation_code(error.value, "evidence_provenance_naive_timestamp")


def test_transformation_forbids_executable_or_arbitrary_payload() -> None:
    payload = transformation().model_dump()
    payload["script"] = "print('synthetic')"
    with pytest.raises(ValidationError):
        ProvenanceTransformation.model_validate(payload)


def test_complete_provenance_preserves_canonical_fields() -> None:
    provenance = complete_provenance()

    assert set(ProvenanceV2.model_fields) == {
        "source_system",
        "source_reference",
        "created_by",
        "creation_method",
        "captured_at",
        "source_created_at",
        "transformation_history",
        "derived_from_object_id",
        "derived_from_revision",
        "completeness",
    }
    assert provenance.completeness is ProvenanceCompleteness.COMPLETE


def test_complete_provenance_allows_absent_source_system() -> None:
    provenance = complete_provenance(source_system=None)
    assert provenance.source_system is None


@pytest.mark.parametrize(
    "field",
    ["source_reference", "created_by", "creation_method", "captured_at"],
)
def test_complete_provenance_requires_complete_facts(field: str) -> None:
    with pytest.raises(ValidationError) as error:
        complete_provenance(**{field: None})
    assert_validation_code(error.value, "provenance_complete_fields_required")


def test_legacy_incomplete_provenance_preserves_unknowns_as_none() -> None:
    provenance = ProvenanceV2(
        source_reference="legacy://knowledge/001",
        completeness=ProvenanceCompleteness.LEGACY_INCOMPLETE,
    )

    assert provenance.created_by is None
    assert provenance.creation_method is None
    assert provenance.captured_at is None
    assert provenance.source_created_at is None
    assert "unknown" not in provenance.model_dump_json()


@pytest.mark.parametrize(
    ("object_id", "revision"),
    [
        (OBJECT_ID, None),
        (None, 2),
    ],
)
def test_provenance_requires_derivation_pair(
    object_id: UUID | None,
    revision: int | None,
) -> None:
    with pytest.raises(ValidationError) as error:
        complete_provenance(
            derived_from_object_id=object_id,
            derived_from_revision=revision,
        )
    assert_validation_code(error.value, "provenance_derivation_pair_required")


def test_provenance_requires_positive_derived_revision() -> None:
    with pytest.raises(ValidationError):
        complete_provenance(
            derived_from_object_id=OBJECT_ID,
            derived_from_revision=0,
        )


def test_provenance_preserves_transformation_history_order() -> None:
    first = transformation(transformation_type="first")
    second = transformation(transformation_type="second")
    provenance = complete_provenance(transformation_history=[first, second])

    assert tuple(item.transformation_type for item in provenance.transformation_history) == (
        "first",
        "second",
    )


def test_provenance_rejects_excessive_transformation_history() -> None:
    history = [
        transformation(transformation_type=f"step-{index}")
        for index in range(MAX_TRANSFORMATIONS + 1)
    ]
    with pytest.raises(ValidationError):
        complete_provenance(transformation_history=history)


@pytest.mark.parametrize("field", ["captured_at", "source_created_at"])
def test_provenance_rejects_naive_timestamps(field: str) -> None:
    with pytest.raises(ValidationError) as error:
        complete_provenance(**{field: datetime(2026, 2, 3, 10, 30)})
    assert_validation_code(error.value, "evidence_provenance_naive_timestamp")


def test_provenance_serialization_round_trip_is_equivalent() -> None:
    provenance = complete_provenance(
        derived_from_object_id=OBJECT_ID,
        derived_from_revision=2,
    )
    restored = ProvenanceV2.model_validate_json(provenance.model_dump_json())
    assert restored == provenance


def test_provenance_forbids_lifecycle_review_approval_and_authorization_fields() -> None:
    for field in ("lifecycle_state", "review_status", "approved", "authorized"):
        payload = complete_provenance().model_dump()
        payload[field] = "synthetic"
        with pytest.raises(ValidationError):
            ProvenanceV2.model_validate(payload)


def test_canonical_composition_requires_exact_evidence_identity_alignment() -> None:
    evidence = complete_evidence(evidence_id="evidence-001")
    composition = KnowledgeObjectV2EvidenceComposition(
        core=core_record(("evidence-001",)),
        evidence=(evidence,),
        provenance=complete_provenance(),
    )

    assert composition.core.mutable_state.evidence_ids == ("evidence-001",)
    assert tuple(item.evidence_id for item in composition.evidence) == ("evidence-001",)


def test_composition_rejects_missing_evidence_object() -> None:
    with pytest.raises(ValidationError) as error:
        KnowledgeObjectV2EvidenceComposition(
            core=core_record(("evidence-001", "evidence-002")),
            evidence=(complete_evidence(evidence_id="evidence-001"),),
            provenance=complete_provenance(),
        )
    assert_composition_code(error.value, "evidence_objects_missing")


def test_composition_rejects_extra_evidence_object() -> None:
    with pytest.raises(ValidationError) as error:
        KnowledgeObjectV2EvidenceComposition(
            core=core_record(("evidence-001",)),
            evidence=(
                complete_evidence(evidence_id="evidence-001"),
                complete_evidence(evidence_id="evidence-002"),
            ),
            provenance=complete_provenance(),
        )
    assert_composition_code(error.value, "evidence_objects_extra")


def test_composition_rejects_reordered_evidence() -> None:
    with pytest.raises(ValidationError) as error:
        KnowledgeObjectV2EvidenceComposition(
            core=core_record(("evidence-001", "evidence-002")),
            evidence=(
                complete_evidence(evidence_id="evidence-002"),
                complete_evidence(evidence_id="evidence-001"),
            ),
            provenance=complete_provenance(),
        )
    assert_composition_code(error.value, "evidence_order_mismatch")


def test_composition_rejects_exact_duplicate_evidence() -> None:
    reference = complete_evidence(evidence_id="evidence-001")
    with pytest.raises(ValidationError) as error:
        KnowledgeObjectV2EvidenceComposition(
            core=core_record(("evidence-001",)),
            evidence=(reference, reference.model_copy(deep=True)),
            provenance=complete_provenance(),
        )
    assert_composition_code(error.value, "evidence_exact_duplicate")


def test_composition_rejects_conflicting_evidence_identity() -> None:
    with pytest.raises(ValidationError) as error:
        KnowledgeObjectV2EvidenceComposition(
            core=core_record(("evidence-001",)),
            evidence=(
                complete_evidence(evidence_id="evidence-001"),
                complete_evidence(
                    evidence_id="evidence-001",
                    title="Different metadata",
                ),
            ),
            provenance=complete_provenance(),
        )
    assert_composition_code(error.value, "evidence_id_conflict")


def test_composition_rejects_incomplete_evidence_for_new_record() -> None:
    reference = legacy_evidence(evidence_id="legacy-evidence-001")
    with pytest.raises(ValidationError) as error:
        KnowledgeObjectV2EvidenceComposition(
            core=core_record((reference.evidence_id,)),
            evidence=(reference,),
            provenance=complete_provenance(),
        )
    assert_composition_code(error.value, "canonical_evidence_incomplete")


def test_composition_rejects_incomplete_provenance_for_new_record() -> None:
    reference = complete_evidence(evidence_id="evidence-001")
    with pytest.raises(ValidationError) as error:
        KnowledgeObjectV2EvidenceComposition(
            core=core_record((reference.evidence_id,)),
            evidence=(reference,),
            provenance=ProvenanceV2(
                source_reference="legacy://knowledge/001",
                completeness=ProvenanceCompleteness.LEGACY_INCOMPLETE,
            ),
        )
    assert_composition_code(error.value, "canonical_provenance_incomplete")


def test_composition_detaches_core_evidence_and_provenance_aliases() -> None:
    core = core_record(("evidence-001",))
    reference = complete_evidence(evidence_id="evidence-001")
    provenance = complete_provenance()
    core_before = core.model_dump_json()

    composition = KnowledgeObjectV2EvidenceComposition(
        core=core,
        evidence=(reference,),
        provenance=provenance,
    )

    assert composition.core is not core
    assert composition.evidence[0] is not reference
    assert composition.provenance is not provenance
    assert composition.core.model_dump_json() == core_before
    assert core.model_dump_json() == core_before


def test_platform_projection_emits_ordered_unique_ids_only() -> None:
    evidence = (
        complete_evidence(evidence_id="evidence-001"),
        complete_evidence(evidence_id="evidence-002"),
    )
    composition = KnowledgeObjectV2EvidenceComposition(
        core=core_record(("evidence-001", "evidence-002")),
        evidence=evidence,
        provenance=complete_provenance(),
    )

    assert project_platform_evidence_references(composition) == (
        "evidence-001",
        "evidence-002",
    )


def test_composition_has_no_api_or_persistence_fields() -> None:
    assert set(KnowledgeObjectV2EvidenceComposition.model_fields) == {
        "core",
        "evidence",
        "provenance",
    }
    assert not {
        "database_id",
        "stored_at",
        "api_version",
        "response_status",
    }.intersection(KnowledgeObjectV2EvidenceComposition.model_fields)


def test_legacy_evidence_id_is_deterministic_and_standard_uuid5() -> None:
    reference = "Legacy://Synthetic/Result-A"
    first = adapt_legacy_evidence_reference(reference)
    second = adapt_legacy_evidence_reference(reference)
    expected = str(uuid5(LEGACY_EVIDENCE_NAMESPACE, reference))

    assert first.reference.evidence_id == expected
    assert second.reference.evidence_id == expected


def test_legacy_evidence_id_is_stable_in_a_fresh_process() -> None:
    source_reference = "Legacy://Synthetic/Result-A"
    script = (
        "from smartcoat.domain.evidence_provenance import "
        "adapt_legacy_evidence_reference; "
        f"print(adapt_legacy_evidence_reference({source_reference!r}).reference.evidence_id)"
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == str(uuid5(LEGACY_EVIDENCE_NAMESPACE, source_reference))


def test_legacy_evidence_trims_outer_whitespace_without_rewriting_semantics() -> None:
    upper = adapt_legacy_evidence_reference("  Legacy://Synthetic/Result-A  ")
    lower = adapt_legacy_evidence_reference("legacy://synthetic/result-a")

    assert upper.reference.source_reference == "Legacy://Synthetic/Result-A"
    assert upper.reference.evidence_id != lower.reference.evidence_id


def test_legacy_evidence_fabricates_no_actor_time_owner_or_confidentiality() -> None:
    result = adapt_legacy_evidence_reference("legacy://synthetic/result-a")
    reference = result.reference

    assert isinstance(result, LegacyEvidenceAdapterResult)
    assert result.is_canonical_complete is False
    assert reference.captured_by is None
    assert reference.captured_at is None
    assert reference.source_created_at is None
    assert reference.confidentiality is None
    assert reference.context_reference is None


def test_legacy_collection_preserves_order_and_returns_required_ids() -> None:
    result = adapt_legacy_evidence_collection(["legacy://synthetic/a", "legacy://synthetic/b"])

    assert isinstance(result, LegacyEvidenceCollectionAdapterResult)
    assert tuple(item.source_reference for item in result.references) == (
        "legacy://synthetic/a",
        "legacy://synthetic/b",
    )
    assert result.evidence_ids == tuple(item.evidence_id for item in result.references)


def test_legacy_collection_rejects_duplicate_trimmed_reference() -> None:
    with pytest.raises(EvidenceReferenceCollectionError) as error:
        adapt_legacy_evidence_collection(["legacy://synthetic/a", "  legacy://synthetic/a  "])
    assert error.value.code == "evidence_exact_duplicate"


def test_legacy_collection_rejects_deterministic_id_collision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(evidence_module, "_legacy_evidence_id", lambda _: "collision-id")

    with pytest.raises(EvidenceReferenceCollectionError) as error:
        adapt_legacy_evidence_collection(["legacy://synthetic/a", "legacy://synthetic/b"])
    assert error.value.code == "evidence_id_conflict"


def test_legacy_provenance_maps_only_explicit_supported_fields() -> None:
    legacy = Provenance(
        source_system="  legacy_register  ",
        source_reference="  legacy://knowledge/001  ",
        created_by="  actor_legacy_author  ",
        method="manual_capture",
    )
    result = adapt_legacy_provenance(legacy)

    assert isinstance(result, LegacyProvenanceAdapterResult)
    assert result.provenance.source_system == "legacy_register"
    assert result.provenance.source_reference == "legacy://knowledge/001"
    assert result.provenance.created_by == "actor_legacy_author"
    assert result.provenance.creation_method is CreationMethod.MANUAL
    assert result.provenance.completeness is ProvenanceCompleteness.LEGACY_INCOMPLETE
    assert result.provenance.captured_at is None
    assert result.provenance.source_created_at is None


def test_legacy_provenance_preserves_unmapped_method_as_adapter_evidence() -> None:
    result = adapt_legacy_provenance(Provenance(method="custom_legacy_method"))

    assert result.provenance.creation_method is None
    assert result.unmapped_legacy_method == "custom_legacy_method"
    assert "creation_method" in result.unavailable_fields


def test_legacy_provenance_does_not_mutate_source_object() -> None:
    legacy = Provenance(
        source_system=" legacy_register ",
        source_reference=" legacy://knowledge/001 ",
        created_by=" actor_legacy_author ",
        method="manual",
    )
    before = legacy.model_dump_json()

    adapt_legacy_provenance(legacy)

    assert legacy.model_dump_json() == before


def test_combined_legacy_adapter_is_explicitly_not_canonical_composition() -> None:
    result = adapt_legacy_evidence_and_provenance(
        ["legacy://synthetic/a"],
        Provenance(source_reference="legacy://knowledge/001", method="manual"),
    )

    assert isinstance(result, LegacyKnowledgeObjectV2EvidenceAdapterResult)
    assert result.is_canonical_complete is False
    assert result.evidence.is_canonical_complete is False
    assert result.provenance.is_canonical_complete is False
    assert not isinstance(result, KnowledgeObjectV2EvidenceComposition)


@pytest.mark.parametrize(
    "model_type",
    [
        EvidenceIntegrity,
        EvidenceReference,
        ProvenanceTransformation,
        ProvenanceV2,
        KnowledgeObjectV2EvidenceComposition,
        LegacyEvidenceAdapterResult,
        LegacyEvidenceCollectionAdapterResult,
        LegacyProvenanceAdapterResult,
        LegacyKnowledgeObjectV2EvidenceAdapterResult,
    ],
)
def test_all_t03_models_forbid_extra_fields(model_type: type[BaseModel]) -> None:
    assert model_type.model_config["extra"] == "forbid"


def test_release_1_7_model_and_provenance_contracts_remain_unchanged() -> None:
    assert KnowledgeObject.model_fields["evidence"].annotation == list[str]
    assert set(Provenance.model_fields) == {
        "source_system",
        "source_reference",
        "created_by",
        "method",
    }


def test_t02_identity_only_evidence_contract_remains_unchanged() -> None:
    assert "evidence_ids" in KnowledgeObjectV2MutableState.model_fields
    assert "evidence" not in KnowledgeObjectV2MutableState.model_fields
    assert "provenance" not in KnowledgeObjectV2MutableState.model_fields


def test_t08_context_contract_remains_the_reused_type() -> None:
    reference = complete_evidence().context_reference
    assert type(reference) is ContextReference
    assert {item.value for item in ContextType} == {
        "project",
        "experiment_or_trial",
        "material",
        "fabric_or_substrate",
        "formulation_reference",
        "process_conditions",
        "test_result",
    }


def test_t03_module_imports_no_api_persistence_or_file_ingestion_framework() -> None:
    source = (ROOT / "src/smartcoat/domain/evidence_provenance.py").read_text()
    forbidden_imports = (
        "fastapi",
        "sqlalchemy",
        "smartcoat.api",
        "smartcoat.services",
        "smartcoat.storage",
        "alembic",
    )
    assert not any(import_name in source for import_name in forbidden_imports)
    assert not {
        "raw_bytes",
        "base64_payload",
        "document_body",
        "ocr_output",
        "file_metadata",
        "storage_location",
    }.intersection(EvidenceReference.model_fields)


def test_t03_contracts_do_not_modify_api_or_persistence_behavior() -> None:
    assert "response_model" not in KnowledgeObjectV2EvidenceComposition.model_fields
    assert "persisted" not in KnowledgeObjectV2EvidenceComposition.model_fields
    assert "repository" not in KnowledgeObjectV2EvidenceComposition.model_fields
