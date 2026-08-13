from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from smartcoat.domain.lab_project_capture import CaptureSourceKind
from smartcoat.services.lab_project_grounding import (
    GroundedClaim,
    GroundedClaimReasonCode,
    GroundedClaimState,
    GroundedClaimStatus,
    GroundedClaimType,
    assemble_candidate_from_grounded_claims,
    normalize_transcript_line_endings,
    verify_grounded_claim,
    verify_grounded_claims,
)

NOW = datetime(2026, 8, 13, 8, 0, tzinfo=UTC)
SESSION_ID = UUID("dfe846e0-0421-4da8-bfe6-d8d436af91a8")


def _claim(
    transcript: str,
    quote: str,
    *,
    claim_id: str = "claim-001",
    claim_type: GroundedClaimType = GroundedClaimType.PROJECT_REQUEST,
    subject_label: str = "project",
    field_name: str = "request_summary",
    text_value: str | None = None,
    numeric_value: float | None = None,
    unit: str | None = None,
    state: GroundedClaimState = GroundedClaimState.KNOWN,
    source_start: int | None = None,
) -> GroundedClaim:
    start = transcript.index(quote) if source_start is None else source_start
    return GroundedClaim(
        claim_id=claim_id,
        claim_type=claim_type,
        subject_label=subject_label,
        field_name=field_name,
        text_value=text_value,
        numeric_value=numeric_value,
        unit=unit,
        state=state,
        source_quote=quote,
        source_start=start,
        source_end=start + len(quote),
        model_confidence=0.8,
    )


def _assemble(claims: tuple[GroundedClaim, ...], transcript: str):
    verifications = verify_grounded_claims(claims, transcript)
    verified = tuple(
        item.claim for item in verifications if item.status is GroundedClaimStatus.VERIFIED
    )
    candidate = assemble_candidate_from_grounded_claims(
        verified,
        capture_session_id=SESSION_ID,
        source_kind=CaptureSourceKind.TEXT,
        source_language="en",
        transcript=transcript,
        extraction_model="deterministic-grounding-test",
        extraction_started_at=NOW,
        extraction_completed_at=NOW,
    )
    return candidate, verifications


def test_claim_contract_rejects_candidate_correlation_ids() -> None:
    with pytest.raises(ValidationError, match="must not contain Candidate correlation IDs"):
        _claim(
            "First approach failed.",
            "First approach failed.",
            subject_label="C-A-001",
            text_value="failed",
        )


def test_line_endings_are_the_only_documented_source_normalization() -> None:
    transcript = "First line.\r\nSecond line.\rThird line."
    normalized = normalize_transcript_line_endings(transcript)
    quote = "Second line."
    claim = _claim(
        normalized,
        quote,
        claim_type=GroundedClaimType.CUSTOMER_REQUIREMENT,
        text_value=quote,
    )

    verification = verify_grounded_claim(claim, transcript)

    assert normalized == "First line.\nSecond line.\nThird line."
    assert verification.status is GroundedClaimStatus.VERIFIED


def test_fabricated_customer_feedback_timestamp_is_unsupported_and_not_assembled() -> None:
    transcript = "The sample was sent to the customer. Customer feedback has not yet been received."
    fabricated_quote = "Customer feedback received 2026-08-01."
    claim = GroundedClaim(
        claim_id="feedback-001",
        claim_type=GroundedClaimType.CUSTOMER_FEEDBACK,
        subject_label="sample",
        field_name="received_at",
        text_value="2026-08-01",
        state=GroundedClaimState.KNOWN,
        source_quote=fabricated_quote,
        source_start=transcript.index("Customer feedback"),
        source_end=transcript.index("Customer feedback") + len(fabricated_quote),
        model_confidence=0.9,
    )

    candidate, verifications = _assemble((claim,), transcript)

    assert verifications[0].status is GroundedClaimStatus.UNSUPPORTED
    assert verifications[0].reason_code is GroundedClaimReasonCode.SOURCE_QUOTE_MISMATCH
    assert candidate.customer_feedback == ()
    assert "2026-08-01" not in candidate.model_dump_json()


def test_negative_production_feasibility_cannot_become_assessed() -> None:
    transcript = "Production feasibility has not yet been evaluated."
    claim = _claim(
        transcript,
        transcript,
        claim_type=GroundedClaimType.PRODUCTION_FEASIBILITY,
        subject_label="project",
        field_name="production_feasibility_status",
        text_value="assessed",
        state=GroundedClaimState.KNOWN,
    )

    candidate, verifications = _assemble((claim,), transcript)

    assert verifications[0].status is GroundedClaimStatus.UNSUPPORTED
    assert candidate.approaches == ()
    assert "assessed" not in candidate.model_dump_json()


def test_claim_type_must_match_the_selected_source_evidence() -> None:
    transcript = "Customer feedback has not yet been received."
    claim = _claim(
        transcript,
        transcript,
        claim_type=GroundedClaimType.SHIPMENT,
        subject_label="unresolved",
        field_name="shipment",
        state=GroundedClaimState.UNKNOWN,
    )

    verification = verify_grounded_claim(claim, transcript)

    assert verification.status is GroundedClaimStatus.UNSUPPORTED
    assert verification.reason_code is GroundedClaimReasonCode.UNSUPPORTED_CLAIM_TYPE


def test_positive_outcome_is_supported_in_a_mixed_negative_sentence() -> None:
    transcript = (
        "The first approach failed after the Bunsen test, but we did not record "
        "the exact coating weight."
    )
    claim = _claim(
        transcript,
        transcript,
        claim_type=GroundedClaimType.APPROACH_OUTCOME,
        subject_label="first approach",
        field_name="outcome",
        text_value="failed",
        state=GroundedClaimState.KNOWN,
    )

    verification = verify_grounded_claim(claim, transcript)

    assert verification.status is GroundedClaimStatus.VERIFIED


def test_exact_curing_temperature_is_verified_and_populates_candidate() -> None:
    transcript = "The curing temperature was 210 degrees Celsius."
    claim = _claim(
        transcript,
        transcript,
        claim_type=GroundedClaimType.PROCESS_PARAMETER,
        subject_label="unresolved",
        field_name="curing temperature",
        numeric_value=210,
        unit="degrees Celsius",
    )

    candidate, verifications = _assemble((claim,), transcript)

    assert verifications[0].status is GroundedClaimStatus.VERIFIED
    assert candidate.process_parameters[0].numeric_value == 210
    assert candidate.process_parameters[0].unit == "degrees Celsius"
    assert candidate.process_parameters[0].approach_id == "C-A-000"
    assert "unresolved_approach_relationship:claim-001" in candidate.extraction_warnings


def test_omitted_material_is_not_fabricated_by_deterministic_assembly() -> None:
    transcript = (
        "We used magnesium hydroxide and calcium carbonate, cured at 210 degrees Celsius, "
        "and sent sample S-02 to the customer."
    )
    material = _claim(
        transcript,
        transcript,
        claim_type=GroundedClaimType.MATERIAL,
        subject_label="magnesium hydroxide",
        field_name="material_name",
        text_value="magnesium hydroxide",
    )
    temperature = _claim(
        transcript,
        transcript,
        claim_id="process-001",
        claim_type=GroundedClaimType.PROCESS_PARAMETER,
        subject_label="unresolved",
        field_name="curing temperature",
        numeric_value=210,
        unit="degrees Celsius",
    )
    shipment = _claim(
        transcript,
        transcript,
        claim_id="shipment-001",
        claim_type=GroundedClaimType.SHIPMENT,
        subject_label="S-02",
        field_name="shipment",
        text_value="customer",
    )

    candidate, verifications = _assemble((material, temperature, shipment), transcript)

    assert all(item.status is GroundedClaimStatus.VERIFIED for item in verifications)
    assert [item.material_name for item in candidate.materials] == ["magnesium hydroxide"]
    assert all(item.material_name != "calcium carbonate" for item in candidate.materials)
    assert candidate.process_parameters[0].numeric_value == 210
    assert candidate.samples[0].source_sample_id == "S-02"
    assert candidate.samples[0].recipient == "customer"
    assert candidate.human_confirmed is False
