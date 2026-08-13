"""Evidence-grounded claim verification and deterministic Candidate assembly."""

from __future__ import annotations

import re
from collections import OrderedDict
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from smartcoat.domain.lab_project_capture import (
    ApproachOutcome,
    AssessmentStatus,
    BaseSubstrate,
    CaptureSourceKind,
    ExperimentalApproach,
    FollowUpStatus,
    LabProjectCaptureCandidate,
    MaterialRecord,
    MeasurementState,
    PhysicalArchiveStatus,
    ProcessParameter,
    ProjectIdentity,
    RootCauseStatus,
    SampleRecord,
    TestOutcome,
    TestRecord,
)

ClaimText = Annotated[str, StringConstraints(min_length=1, max_length=512)]
SourceQuote = Annotated[str, StringConstraints(min_length=1, max_length=300)]


class GroundedClaimType(StrEnum):
    PROJECT_REQUEST = "project_request"
    TARGET_APPLICATION = "target_application"
    INDUSTRIAL_FUNCTION = "industrial_function"
    CUSTOMER_REQUIREMENT = "customer_requirement"
    SUCCESS_CRITERION = "success_criterion"
    SUBSTRATE_NAME = "substrate_name"
    SUBSTRATE_TYPE = "substrate_type"
    SUBSTRATE_REASON = "substrate_reason"
    MATERIAL = "material"
    MATERIAL_AMOUNT = "material_amount"
    MATERIAL_FUNCTION = "material_function"
    APPROACH = "approach"
    APPROACH_OUTCOME = "approach_outcome"
    APPROACH_FAILURE_REASON = "approach_failure_reason"
    APPROACH_LESSON = "approach_lesson"
    PROCESS_PARAMETER = "process_parameter"
    TEST = "test"
    TEST_RESULT = "test_result"
    SAMPLE = "sample"
    SHIPMENT = "shipment"
    ARCHIVE = "archive"
    CUSTOMER_FEEDBACK = "customer_feedback"
    NEXT_ACTION = "next_action"
    PRODUCTION_FEASIBILITY = "production_feasibility"
    PRICE_OPTIMIZATION = "price_optimization"
    REUSE_POTENTIAL = "reuse_potential"


class ProjectMaterialClaimType(StrEnum):
    PROJECT_REQUEST = "project_request"
    TARGET_APPLICATION = "target_application"
    INDUSTRIAL_FUNCTION = "industrial_function"
    CUSTOMER_REQUIREMENT = "customer_requirement"
    SUCCESS_CRITERION = "success_criterion"
    SUBSTRATE_NAME = "substrate_name"
    SUBSTRATE_TYPE = "substrate_type"
    SUBSTRATE_REASON = "substrate_reason"
    MATERIAL = "material"
    MATERIAL_AMOUNT = "material_amount"
    MATERIAL_FUNCTION = "material_function"


class ExperimentalClaimType(StrEnum):
    APPROACH = "approach"
    APPROACH_OUTCOME = "approach_outcome"
    APPROACH_FAILURE_REASON = "approach_failure_reason"
    APPROACH_LESSON = "approach_lesson"
    PROCESS_PARAMETER = "process_parameter"
    TEST = "test"
    TEST_RESULT = "test_result"
    SAMPLE = "sample"
    SHIPMENT = "shipment"
    ARCHIVE = "archive"
    CUSTOMER_FEEDBACK = "customer_feedback"
    NEXT_ACTION = "next_action"
    PRODUCTION_FEASIBILITY = "production_feasibility"
    PRICE_OPTIMIZATION = "price_optimization"
    REUSE_POTENTIAL = "reuse_potential"


class GroundedClaimState(StrEnum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    NOT_MEASURED = "not_measured"
    NOT_ASSESSED = "not_assessed"
    NOT_APPLICABLE = "not_applicable"
    CONFLICTING = "conflicting"


class GroundedClaimStatus(StrEnum):
    VERIFIED = "verified"
    UNSUPPORTED = "unsupported"
    AMBIGUOUS = "ambiguous"


class GroundedClaimReasonCode(StrEnum):
    VERIFIED = "verified"
    INVALID_SOURCE_RANGE = "invalid_source_range"
    SOURCE_QUOTE_MISMATCH = "source_quote_mismatch"
    UNSUPPORTED_CLAIM_TYPE = "unsupported_claim_type"
    UNSUPPORTED_SUBJECT_LABEL = "unsupported_subject_label"
    UNSUPPORTED_TEXT_VALUE = "unsupported_text_value"
    UNSUPPORTED_NUMERIC_VALUE = "unsupported_numeric_value"
    UNSUPPORTED_UNIT = "unsupported_unit"
    UNSUPPORTED_STATE = "unsupported_state"
    UNSUPPORTED_TIMESTAMP = "unsupported_timestamp"
    UNSUPPORTED_CUSTOMER_FEEDBACK = "unsupported_customer_feedback"
    UNSUPPORTED_PRODUCTION_FEASIBILITY = "unsupported_production_feasibility"
    CONFLICTING_CLAIM = "conflicting_claim"
    CONFLICTING_SUPPORTED_CLAIMS = "conflicting_supported_claims"


class GroundedClaim(BaseModel):
    """One atomic model suggestion whose evidence can be checked without an LLM."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: ClaimText
    claim_type: GroundedClaimType
    subject_label: ClaimText
    field_name: ClaimText
    text_value: ClaimText | None = None
    numeric_value: float | None = Field(default=None, allow_inf_nan=False)
    unit: ClaimText | None = None
    state: GroundedClaimState
    source_quote: SourceQuote
    source_start: int
    source_end: int
    model_confidence: float = Field(ge=0, le=1)

    @field_validator("claim_id", "subject_label", "field_name")
    @classmethod
    def reject_candidate_correlation_ids(cls, value: str) -> str:
        normalized = value.strip()
        if re.search(r"\bC-[AMS]-\d{3}\b", normalized, flags=re.IGNORECASE):
            raise ValueError("grounded claims must not contain Candidate correlation IDs")
        return normalized

    @field_validator("text_value", "unit")
    @classmethod
    def reject_blank_optional_values(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("optional claim values must not be blank")
        return value.strip()


class ProjectMaterialGroundedClaim(GroundedClaim):
    claim_type: ProjectMaterialClaimType  # type: ignore[assignment]


class ExperimentalGroundedClaim(GroundedClaim):
    claim_type: ExperimentalClaimType  # type: ignore[assignment]


class GroundedClaimBatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claims: tuple[GroundedClaim, ...] = Field(default_factory=tuple, max_length=8)


class ProjectMaterialGroundedClaimBatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claims: tuple[ProjectMaterialGroundedClaim, ...] = Field(
        default_factory=tuple,
        max_length=8,
    )


class ExperimentalGroundedClaimBatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claims: tuple[ExperimentalGroundedClaim, ...] = Field(
        default_factory=tuple,
        max_length=8,
    )


ProjectMaterialClaimProposal = Annotated[
    str,
    StringConstraints(
        pattern=(
            r"^(?:project_request|target_application|substrate_name|material|"
            r"industrial_function|customer_requirement|success_criterion|substrate_type|"
            r"substrate_reason|material_amount|material_function)\|"
            r"[^|\n]{1,512}\|[0-9]+$"
        )
    ),
]

ExperimentalClaimProposal = Annotated[
    str,
    StringConstraints(
        pattern=(
            r"^(?:approach_outcome|process_parameter|shipment|customer_feedback|"
            r"production_feasibility|approach_failure_reason|approach_lesson|test_result|"
            r"archive|next_action|price_optimization|reuse_potential)\|"
            r"[^|\n]{1,512}\|[0-9]+$"
        )
    ),
]


class ProjectMaterialClaimProposalBatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claims: tuple[ProjectMaterialClaimProposal, ...] = Field(default_factory=tuple, max_length=5)


class ExperimentalClaimProposalBatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claims: tuple[ExperimentalClaimProposal, ...] = Field(default_factory=tuple, max_length=8)


class GroundedClaimVerification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claim: GroundedClaim
    status: GroundedClaimStatus
    reason_code: GroundedClaimReasonCode


class GroundedExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate: LabProjectCaptureCandidate
    claim_verifications: tuple[GroundedClaimVerification, ...] = ()
    pass_a_runtime_seconds: float = Field(default=0, ge=0)
    pass_b_runtime_seconds: float = Field(default=0, ge=0)
    total_runtime_seconds: float = Field(default=0, ge=0)

    @property
    def verified_claim_count(self) -> int:
        return sum(item.status is GroundedClaimStatus.VERIFIED for item in self.claim_verifications)

    @property
    def unsupported_claim_count(self) -> int:
        return sum(
            item.status is GroundedClaimStatus.UNSUPPORTED for item in self.claim_verifications
        )

    @property
    def ambiguous_claim_count(self) -> int:
        return sum(
            item.status is GroundedClaimStatus.AMBIGUOUS for item in self.claim_verifications
        )

    @property
    def unsupported_claims(self) -> tuple[GroundedClaimVerification, ...]:
        return tuple(
            item
            for item in self.claim_verifications
            if item.status is not GroundedClaimStatus.VERIFIED
        )


def normalize_transcript_line_endings(transcript: str) -> str:
    """Normalize CRLF and bare CR to LF; no other source transformation is allowed."""

    return transcript.replace("\r\n", "\n").replace("\r", "\n")


def _semantic_text(value: str) -> str:
    return " ".join(value.casefold().replace("_", " ").replace("-", " ").split())


def _quote_has_negation(quote: str) -> bool:
    normalized = _semantic_text(quote)
    return bool(
        re.search(
            r"\b(?:no|not|never|without|did not|has not|have not|was not|were not)\b",
            normalized,
        )
    )


def _numeric_supported(value: float, quote: str) -> bool:
    numbers = re.findall(r"(?<![\w.])[-+]?\d+(?:[.,]\d+)?(?![\w.])", quote)
    for raw_number in numbers:
        try:
            if abs(float(raw_number.replace(",", ".")) - value) <= 1e-9:
                return True
        except ValueError:
            continue
    return False


def _text_value_supported(claim: GroundedClaim) -> bool:
    if claim.text_value is None:
        return True
    value = _semantic_text(claim.text_value)
    quote = _semantic_text(claim.source_quote)
    if value in quote:
        return True
    if claim.claim_type in {
        GroundedClaimType.APPROACH_OUTCOME,
        GroundedClaimType.TEST_RESULT,
    }:
        outcome_terms = {
            "failed": ("failed", "did not pass", "unsuccessful"),
            "successful": ("successful", "passed"),
            "passed": ("passed", "successful"),
            "partially successful": ("partially successful", "partially passed"),
            "partially passed": ("partially passed", "partially successful"),
            "inconclusive": ("inconclusive",),
        }
        return any(term in quote for term in outcome_terms.get(value, ()))
    return False


def _claim_type_supported(claim: GroundedClaim) -> bool:
    quote = _semantic_text(claim.source_quote)
    required_terms = {
        GroundedClaimType.PROJECT_REQUEST: ("request",),
        GroundedClaimType.TARGET_APPLICATION: ("application", " for "),
        GroundedClaimType.INDUSTRIAL_FUNCTION: ("function", "protection", "resistance"),
        GroundedClaimType.SUBSTRATE_NAME: ("fabric", "substrate", "textile"),
        GroundedClaimType.SUBSTRATE_TYPE: ("fabric", "substrate", "textile"),
        GroundedClaimType.MATERIAL: ("used", "material", "formulation"),
        GroundedClaimType.APPROACH: ("approach", "formulation", "trial"),
        GroundedClaimType.APPROACH_OUTCOME: (
            "failed",
            "passed",
            "successful",
            "inconclusive",
        ),
        GroundedClaimType.APPROACH_FAILURE_REASON: ("failed", "failure"),
        GroundedClaimType.APPROACH_LESSON: ("lesson", "learned"),
        GroundedClaimType.PROCESS_PARAMETER: (
            "temperature",
            "cured",
            "weight",
            "pressure",
            "speed",
            "time",
            "viscosity",
        ),
        GroundedClaimType.TEST: ("test", "tested"),
        GroundedClaimType.TEST_RESULT: ("test", "passed", "failed"),
        GroundedClaimType.SAMPLE: ("sample",),
        GroundedClaimType.SHIPMENT: ("sent", "shipped", "delivered"),
        GroundedClaimType.ARCHIVE: ("archive", "stored", "retained"),
        GroundedClaimType.CUSTOMER_FEEDBACK: ("feedback",),
        GroundedClaimType.NEXT_ACTION: ("next", "follow up", "plan"),
        GroundedClaimType.PRODUCTION_FEASIBILITY: ("production", "feasibility", "scale up"),
        GroundedClaimType.PRICE_OPTIMIZATION: ("price", "cost", "optimization"),
        GroundedClaimType.REUSE_POTENTIAL: ("reuse", "other customer", "potential"),
    }
    terms = required_terms.get(claim.claim_type)
    return terms is None or any(term in quote for term in terms)


def verify_grounded_claim(
    claim: GroundedClaim,
    transcript: str,
) -> GroundedClaimVerification:
    """Verify a claim against the line-ending-normalized immutable transcript."""

    normalized_transcript = normalize_transcript_line_endings(transcript)
    if (
        claim.source_start < 0
        or claim.source_end <= claim.source_start
        or claim.source_end > len(normalized_transcript)
    ):
        return GroundedClaimVerification(
            claim=claim,
            status=GroundedClaimStatus.UNSUPPORTED,
            reason_code=GroundedClaimReasonCode.INVALID_SOURCE_RANGE,
        )
    if normalized_transcript[claim.source_start : claim.source_end] != claim.source_quote:
        return GroundedClaimVerification(
            claim=claim,
            status=GroundedClaimStatus.UNSUPPORTED,
            reason_code=GroundedClaimReasonCode.SOURCE_QUOTE_MISMATCH,
        )
    if not _claim_type_supported(claim):
        return GroundedClaimVerification(
            claim=claim,
            status=GroundedClaimStatus.UNSUPPORTED,
            reason_code=GroundedClaimReasonCode.UNSUPPORTED_CLAIM_TYPE,
        )
    subject = _semantic_text(claim.subject_label)
    if subject not in {"project", "global", "unresolved", "source"} and subject not in (
        _semantic_text(claim.source_quote)
    ):
        return GroundedClaimVerification(
            claim=claim,
            status=GroundedClaimStatus.UNSUPPORTED,
            reason_code=GroundedClaimReasonCode.UNSUPPORTED_SUBJECT_LABEL,
        )
    if claim.state is GroundedClaimState.CONFLICTING:
        return GroundedClaimVerification(
            claim=claim,
            status=GroundedClaimStatus.AMBIGUOUS,
            reason_code=GroundedClaimReasonCode.CONFLICTING_CLAIM,
        )
    if claim.numeric_value is not None and not _numeric_supported(
        claim.numeric_value,
        claim.source_quote,
    ):
        return GroundedClaimVerification(
            claim=claim,
            status=GroundedClaimStatus.UNSUPPORTED,
            reason_code=GroundedClaimReasonCode.UNSUPPORTED_NUMERIC_VALUE,
        )
    if claim.unit is not None and _semantic_text(claim.unit) not in _semantic_text(
        claim.source_quote
    ):
        return GroundedClaimVerification(
            claim=claim,
            status=GroundedClaimStatus.UNSUPPORTED,
            reason_code=GroundedClaimReasonCode.UNSUPPORTED_UNIT,
        )
    if not _text_value_supported(claim):
        return GroundedClaimVerification(
            claim=claim,
            status=GroundedClaimStatus.UNSUPPORTED,
            reason_code=GroundedClaimReasonCode.UNSUPPORTED_TEXT_VALUE,
        )

    quote_is_negative = _quote_has_negation(claim.source_quote)
    negative_known_types = {
        GroundedClaimType.CUSTOMER_FEEDBACK,
        GroundedClaimType.PRODUCTION_FEASIBILITY,
        GroundedClaimType.PRICE_OPTIMIZATION,
    }
    if (
        claim.state is GroundedClaimState.KNOWN
        and quote_is_negative
        and (
            claim.claim_type in negative_known_types
            or (
                claim.claim_type is GroundedClaimType.PROCESS_PARAMETER
                and _semantic_text(claim.field_name) in _semantic_text(claim.source_quote)
            )
        )
    ):
        reason = GroundedClaimReasonCode.UNSUPPORTED_STATE
        if claim.claim_type is GroundedClaimType.CUSTOMER_FEEDBACK:
            reason = GroundedClaimReasonCode.UNSUPPORTED_CUSTOMER_FEEDBACK
        elif claim.claim_type is GroundedClaimType.PRODUCTION_FEASIBILITY:
            reason = GroundedClaimReasonCode.UNSUPPORTED_PRODUCTION_FEASIBILITY
        return GroundedClaimVerification(
            claim=claim,
            status=GroundedClaimStatus.UNSUPPORTED,
            reason_code=reason,
        )
    if (
        claim.state
        in {
            GroundedClaimState.NOT_MEASURED,
            GroundedClaimState.NOT_ASSESSED,
            GroundedClaimState.UNKNOWN,
        }
        and not quote_is_negative
        and not any(
            term in _semantic_text(claim.source_quote)
            for term in ("unknown", "unavailable", "pending", "not assessed", "not measured")
        )
    ):
        return GroundedClaimVerification(
            claim=claim,
            status=GroundedClaimStatus.UNSUPPORTED,
            reason_code=GroundedClaimReasonCode.UNSUPPORTED_STATE,
        )

    field_tokens = set(_semantic_text(claim.field_name).split())
    if field_tokens.intersection({"date", "timestamp", "received", "sent", "due"}) and (
        claim.text_value is None or re.search(r"\b\d{4}-\d{2}-\d{2}\b", claim.source_quote) is None
    ):
        return GroundedClaimVerification(
            claim=claim,
            status=GroundedClaimStatus.UNSUPPORTED,
            reason_code=GroundedClaimReasonCode.UNSUPPORTED_TIMESTAMP,
        )
    if claim.claim_type is GroundedClaimType.CUSTOMER_FEEDBACK:
        quote = _semantic_text(claim.source_quote)
        if claim.state is GroundedClaimState.KNOWN and "feedback" not in quote:
            return GroundedClaimVerification(
                claim=claim,
                status=GroundedClaimStatus.UNSUPPORTED,
                reason_code=GroundedClaimReasonCode.UNSUPPORTED_CUSTOMER_FEEDBACK,
            )
    if claim.claim_type is GroundedClaimType.PRODUCTION_FEASIBILITY:
        quote = _semantic_text(claim.source_quote)
        if not any(term in quote for term in ("production", "feasibility", "scale up")):
            return GroundedClaimVerification(
                claim=claim,
                status=GroundedClaimStatus.UNSUPPORTED,
                reason_code=GroundedClaimReasonCode.UNSUPPORTED_PRODUCTION_FEASIBILITY,
            )

    return GroundedClaimVerification(
        claim=claim,
        status=GroundedClaimStatus.VERIFIED,
        reason_code=GroundedClaimReasonCode.VERIFIED,
    )


_REPEATABLE_CLAIM_TYPES = {
    GroundedClaimType.CUSTOMER_REQUIREMENT,
    GroundedClaimType.SUCCESS_CRITERION,
    GroundedClaimType.MATERIAL,
    GroundedClaimType.APPROACH,
    GroundedClaimType.PROCESS_PARAMETER,
    GroundedClaimType.TEST,
    GroundedClaimType.TEST_RESULT,
    GroundedClaimType.SAMPLE,
    GroundedClaimType.SHIPMENT,
    GroundedClaimType.ARCHIVE,
}


def verify_grounded_claims(
    claims: tuple[GroundedClaim, ...],
    transcript: str,
) -> tuple[GroundedClaimVerification, ...]:
    """Verify claims and mark contradictory singleton assertions as ambiguous."""

    results = [verify_grounded_claim(claim, transcript) for claim in claims]
    supported_by_key: dict[tuple[str, str, str], list[int]] = {}
    for index, result in enumerate(results):
        if (
            result.status is not GroundedClaimStatus.VERIFIED
            or result.claim.claim_type in _REPEATABLE_CLAIM_TYPES
        ):
            continue
        key = (
            result.claim.claim_type.value,
            _semantic_text(result.claim.subject_label),
            _semantic_text(result.claim.field_name),
        )
        supported_by_key.setdefault(key, []).append(index)

    for indexes in supported_by_key.values():
        signatures = {
            (
                result.claim.text_value,
                result.claim.numeric_value,
                result.claim.unit,
                result.claim.state,
            )
            for result in (results[index] for index in indexes)
        }
        if len(signatures) <= 1:
            continue
        for index in indexes:
            results[index] = GroundedClaimVerification(
                claim=results[index].claim,
                status=GroundedClaimStatus.AMBIGUOUS,
                reason_code=GroundedClaimReasonCode.CONFLICTING_SUPPORTED_CLAIMS,
            )
    return tuple(results)


def _claim_text(claim: GroundedClaim) -> str | None:
    return claim.text_value.strip() if claim.text_value is not None else None


def _outcome(value: str | None) -> ApproachOutcome | None:
    if value is None:
        return None
    normalized = _semantic_text(value)
    if normalized in {"failed", "unsuccessful", "did not pass"}:
        return ApproachOutcome.FAILED
    if normalized in {"passed", "successful"}:
        return ApproachOutcome.SUCCESSFUL
    if normalized in {"partially passed", "partially successful"}:
        return ApproachOutcome.PARTIALLY_SUCCESSFUL
    if normalized in {item.value.replace("_", " ") for item in ApproachOutcome}:
        return ApproachOutcome(normalized.replace(" ", "_"))
    return None


def _test_outcome(value: str | None) -> TestOutcome | None:
    if value is None:
        return None
    normalized = _semantic_text(value)
    mapping = {
        "passed": TestOutcome.PASSED,
        "successful": TestOutcome.PASSED,
        "failed": TestOutcome.FAILED,
        "partially passed": TestOutcome.PARTIALLY_PASSED,
        "partially successful": TestOutcome.PARTIALLY_PASSED,
        "not measured": TestOutcome.NOT_MEASURED,
        "inconclusive": TestOutcome.INCONCLUSIVE,
    }
    return mapping.get(normalized)


def _measurement_state(state: GroundedClaimState) -> MeasurementState:
    mapping = {
        GroundedClaimState.KNOWN: MeasurementState.KNOWN,
        GroundedClaimState.UNKNOWN: MeasurementState.UNKNOWN,
        GroundedClaimState.NOT_MEASURED: MeasurementState.NOT_MEASURED,
        GroundedClaimState.NOT_ASSESSED: MeasurementState.UNKNOWN,
        GroundedClaimState.NOT_APPLICABLE: MeasurementState.NOT_APPLICABLE,
        GroundedClaimState.CONFLICTING: MeasurementState.CONFLICTING,
    }
    return mapping[state]


def _process_stage(parameter_name: str) -> str:
    normalized = _semantic_text(parameter_name)
    for stage in ("curing", "coating", "mixing", "drying", "testing"):
        if stage in normalized:
            return stage
    return "source unspecified"


def _quote_mentions_label(claim: GroundedClaim) -> bool:
    label = _semantic_text(claim.subject_label)
    return label in {"project", "global", "unresolved", "source"} or label in _semantic_text(
        claim.source_quote
    )


def assemble_candidate_from_grounded_claims(
    claims: tuple[GroundedClaim, ...],
    *,
    capture_session_id: UUID,
    source_kind: CaptureSourceKind,
    source_language: str | None,
    transcript: str,
    extraction_model: str,
    extraction_started_at: Any,
    extraction_completed_at: Any,
    initial_warnings: tuple[str, ...] = (),
) -> LabProjectCaptureCandidate:
    """Build the existing Candidate from verified claims without model involvement."""

    warnings = list(initial_warnings)

    def warn(value: str) -> None:
        if value not in warnings and len(warnings) < 128:
            warnings.append(value)

    def first(claim_type: GroundedClaimType) -> GroundedClaim | None:
        return next((claim for claim in claims if claim.claim_type is claim_type), None)

    project_request = first(GroundedClaimType.PROJECT_REQUEST)
    target_application = first(GroundedClaimType.TARGET_APPLICATION)
    industrial_function = first(GroundedClaimType.INDUSTRIAL_FUNCTION)
    project = ProjectIdentity(
        request_summary=_claim_text(project_request) if project_request else None,
        target_application=_claim_text(target_application) if target_application else None,
        intended_industrial_function=(
            _claim_text(industrial_function) if industrial_function else None
        ),
        customer_requirements=tuple(
            value
            for claim in claims
            if claim.claim_type is GroundedClaimType.CUSTOMER_REQUIREMENT
            and (value := _claim_text(claim)) is not None
        ),
        success_criteria=tuple(
            value
            for claim in claims
            if claim.claim_type is GroundedClaimType.SUCCESS_CRITERION
            and (value := _claim_text(claim)) is not None
        ),
    )

    substrate_name = first(GroundedClaimType.SUBSTRATE_NAME)
    substrate_type = first(GroundedClaimType.SUBSTRATE_TYPE)
    substrate_reason = first(GroundedClaimType.SUBSTRATE_REASON)
    substrate = (
        BaseSubstrate(
            substrate_name=_claim_text(substrate_name) if substrate_name else None,
            substrate_type=_claim_text(substrate_type) if substrate_type else None,
            reason_selected=_claim_text(substrate_reason) if substrate_reason else None,
        )
        if any((substrate_name, substrate_type, substrate_reason))
        else None
    )

    material_values: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for claim in claims:
        if claim.claim_type is GroundedClaimType.MATERIAL:
            label = _claim_text(claim) or claim.subject_label
            material_values.setdefault(_semantic_text(label), {"material_name": label})
    for claim in claims:
        if claim.claim_type not in {
            GroundedClaimType.MATERIAL_AMOUNT,
            GroundedClaimType.MATERIAL_FUNCTION,
        }:
            continue
        material_key = _semantic_text(claim.subject_label)
        if material_key not in material_values or not _quote_mentions_label(claim):
            warn(f"unresolved_material_relationship:{claim.claim_id}")
            continue
        if claim.claim_type is GroundedClaimType.MATERIAL_AMOUNT:
            material_values[material_key]["amount"] = claim.numeric_value
            material_values[material_key]["unit"] = claim.unit
        else:
            material_values[material_key]["function_in_formulation"] = _claim_text(claim)
    materials = tuple(
        MaterialRecord(material_id=f"C-M-{index:03d}", **values)
        for index, values in enumerate(material_values.values(), start=1)
    )

    approach_values: OrderedDict[str, dict[str, Any]] = OrderedDict()
    relationship_claim_types = {
        GroundedClaimType.APPROACH,
        GroundedClaimType.APPROACH_OUTCOME,
        GroundedClaimType.APPROACH_FAILURE_REASON,
        GroundedClaimType.APPROACH_LESSON,
        GroundedClaimType.PRODUCTION_FEASIBILITY,
        GroundedClaimType.PRICE_OPTIMIZATION,
        GroundedClaimType.REUSE_POTENTIAL,
    }
    for claim in claims:
        if claim.claim_type not in relationship_claim_types:
            continue
        if claim.claim_type in {
            GroundedClaimType.PRODUCTION_FEASIBILITY,
            GroundedClaimType.PRICE_OPTIMIZATION,
            GroundedClaimType.REUSE_POTENTIAL,
        } and _semantic_text(claim.subject_label) in {
            "project",
            "global",
            "unresolved",
            "source",
        }:
            warn(f"unresolved_approach_relationship:{claim.claim_id}")
            continue
        relationship_key = _semantic_text(claim.subject_label)
        values = approach_values.setdefault(relationship_key, {"title": claim.subject_label})
        if claim.claim_type is GroundedClaimType.APPROACH and _claim_text(claim):
            values["title"] = _claim_text(claim)
        elif claim.claim_type is GroundedClaimType.APPROACH_OUTCOME:
            values["outcome"] = _outcome(_claim_text(claim))
            values["outcome_summary"] = claim.source_quote
        elif claim.claim_type is GroundedClaimType.APPROACH_FAILURE_REASON:
            values["failure_reason"] = _claim_text(claim)
            values["root_cause_status"] = RootCauseStatus.HYPOTHESIS
        elif claim.claim_type is GroundedClaimType.APPROACH_LESSON:
            values["lesson_learned"] = _claim_text(claim)
        elif claim.claim_type is GroundedClaimType.PRODUCTION_FEASIBILITY:
            values["production_feasibility_status"] = (
                AssessmentStatus.NOT_ASSESSED
                if claim.state is GroundedClaimState.NOT_ASSESSED
                else AssessmentStatus.ASSESSED
            )
        elif claim.claim_type is GroundedClaimType.PRICE_OPTIMIZATION:
            values["price_optimization_status"] = (
                AssessmentStatus.NOT_ASSESSED
                if claim.state is GroundedClaimState.NOT_ASSESSED
                else AssessmentStatus.ASSESSED
            )
        elif claim.claim_type is GroundedClaimType.REUSE_POTENTIAL:
            values["reuse_potential"] = _claim_text(claim)

    approaches_list: list[ExperimentalApproach] = []
    approach_ids: dict[str, str] = {}
    for key, values in approach_values.items():
        if not isinstance(values.get("outcome"), ApproachOutcome):
            warn(f"approach_missing_supported_outcome:{values['title']}")
            continue
        approach_id = f"C-A-{len(approaches_list) + 1:03d}"
        approach_ids[key] = approach_id
        approaches_list.append(ExperimentalApproach(approach_id=approach_id, **values))
    approaches = tuple(approaches_list)

    process_parameters: list[ProcessParameter] = []
    for claim in claims:
        if claim.claim_type is not GroundedClaimType.PROCESS_PARAMETER:
            continue
        parameter_approach_id = approach_ids.get(_semantic_text(claim.subject_label))
        if parameter_approach_id is None or not _quote_mentions_label(claim):
            parameter_approach_id = "C-A-000"
            warn(f"unresolved_approach_relationship:{claim.claim_id}")
        process_parameters.append(
            ProcessParameter(
                approach_id=parameter_approach_id,
                process_stage=_process_stage(claim.field_name),
                parameter_name=claim.field_name,
                numeric_value=claim.numeric_value,
                text_value=(
                    claim.text_value
                    if claim.numeric_value is None
                    and claim.state in {GroundedClaimState.KNOWN, GroundedClaimState.CONFLICTING}
                    else None
                ),
                unit=claim.unit,
                measurement_state=_measurement_state(claim.state),
                source_note=claim.source_quote,
            )
        )

    test_claims: OrderedDict[tuple[str, str], dict[str, Any]] = OrderedDict()
    for claim in claims:
        if claim.claim_type not in {GroundedClaimType.TEST, GroundedClaimType.TEST_RESULT}:
            continue
        test_key = (_semantic_text(claim.subject_label), _semantic_text(claim.field_name))
        values = test_claims.setdefault(
            test_key,
            {"test_name": claim.field_name, "source_note": claim.source_quote},
        )
        if claim.claim_type is GroundedClaimType.TEST and _claim_text(claim):
            values["test_name"] = _claim_text(claim)
        if claim.claim_type is GroundedClaimType.TEST_RESULT:
            values["outcome"] = _test_outcome(_claim_text(claim))
            values["text_result"] = _claim_text(claim)
    tests: list[TestRecord] = []
    for (approach_key, _), values in test_claims.items():
        outcome = values.pop("outcome", None)
        values.pop("source_note", None)
        if not isinstance(outcome, TestOutcome):
            warn(f"test_missing_supported_outcome:{values['test_name']}")
            continue
        approach_id = approach_ids.get(approach_key, "C-A-000")
        if approach_id == "C-A-000":
            warn(f"unresolved_test_approach:{values['test_name']}")
        tests.append(TestRecord(approach_id=approach_id, outcome=outcome, **values))

    sample_values: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for claim in claims:
        if claim.claim_type not in {
            GroundedClaimType.SAMPLE,
            GroundedClaimType.SHIPMENT,
            GroundedClaimType.ARCHIVE,
            GroundedClaimType.CUSTOMER_FEEDBACK,
        }:
            continue
        if claim.claim_type is GroundedClaimType.CUSTOMER_FEEDBACK and _semantic_text(
            claim.subject_label
        ) in {"project", "global", "unresolved", "source"}:
            warn(f"unresolved_feedback_sample:{claim.claim_id}")
            continue
        key = _semantic_text(claim.subject_label)
        values = sample_values.setdefault(
            key,
            {
                "source_sample_id": claim.subject_label,
                "approach_id": "C-A-000",
                "physical_archive_status": PhysicalArchiveStatus.UNKNOWN,
            },
        )
        if claim.claim_type is GroundedClaimType.SAMPLE:
            values["sample_description"] = _claim_text(claim)
        elif claim.claim_type is GroundedClaimType.SHIPMENT:
            values["recipient"] = _claim_text(claim)
            values["follow_up_status"] = FollowUpStatus.PENDING
        elif claim.claim_type is GroundedClaimType.ARCHIVE:
            archive_mapping = {
                GroundedClaimState.KNOWN: PhysicalArchiveStatus.ARCHIVED,
                GroundedClaimState.UNKNOWN: PhysicalArchiveStatus.UNKNOWN,
                GroundedClaimState.NOT_APPLICABLE: PhysicalArchiveStatus.NOT_ARCHIVED,
            }
            values["physical_archive_status"] = archive_mapping.get(
                claim.state,
                PhysicalArchiveStatus.UNKNOWN,
            )
        elif claim.claim_type is GroundedClaimType.CUSTOMER_FEEDBACK:
            if claim.state in {
                GroundedClaimState.UNKNOWN,
                GroundedClaimState.NOT_ASSESSED,
            }:
                values["follow_up_status"] = FollowUpStatus.PENDING
            else:
                warn(f"customer_feedback_requires_manual_completion:{claim.claim_id}")
    samples = tuple(
        SampleRecord(sample_id=f"C-S-{index:03d}", **values)
        for index, values in enumerate(sample_values.values(), start=1)
    )
    for sample in samples:
        if sample.approach_id == "C-A-000":
            warn(f"unresolved_sample_approach:{sample.source_sample_id or sample.sample_id}")

    next_action_claim = first(GroundedClaimType.NEXT_ACTION)
    return LabProjectCaptureCandidate(
        capture_session_id=capture_session_id,
        source_kind=source_kind,
        source_language=source_language,
        transcript=transcript,
        extraction_model=extraction_model,
        extraction_started_at=extraction_started_at,
        extraction_completed_at=extraction_completed_at,
        project=project,
        substrate=substrate,
        materials=materials,
        approaches=approaches,
        process_parameters=tuple(process_parameters),
        tests=tuple(tests),
        samples=samples,
        current_next_action=_claim_text(next_action_claim) if next_action_claim else None,
        extraction_warnings=tuple(warnings),
        human_confirmed=False,
    )


__all__ = [
    "ExperimentalGroundedClaim",
    "ExperimentalGroundedClaimBatch",
    "ExperimentalClaimProposal",
    "ExperimentalClaimProposalBatch",
    "GroundedClaim",
    "GroundedClaimBatch",
    "GroundedClaimReasonCode",
    "GroundedClaimState",
    "GroundedClaimStatus",
    "GroundedClaimType",
    "GroundedClaimVerification",
    "GroundedExtractionResult",
    "ProjectMaterialGroundedClaim",
    "ProjectMaterialGroundedClaimBatch",
    "ProjectMaterialClaimProposal",
    "ProjectMaterialClaimProposalBatch",
    "assemble_candidate_from_grounded_claims",
    "normalize_transcript_line_endings",
    "verify_grounded_claim",
    "verify_grounded_claims",
]
