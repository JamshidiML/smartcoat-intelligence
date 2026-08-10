"""Strict candidate contracts for the local lab-project intake pilot.

Candidates are unapproved interpretations. This module contains no persistence
behavior; only a separate human-confirmed application service may create a
canonical Knowledge Object v2 record.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, cast
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from smartcoat.domain.knowledge_objects import KnowledgeObjectType

if TYPE_CHECKING:
    from smartcoat.domain.knowledge_objects_v2 import JsonValue

Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=256)]
CandidateMaterialId = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^C-M-[0-9]{3}$"),
]
CandidateApproachId = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^C-A-[0-9]{3}$"),
]
CandidateSampleId = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^C-S-[0-9]{3}$"),
]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=512)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4096)]
LanguageCode = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=35)]
FiniteNumber = Annotated[float, Field(allow_inf_nan=False)]
NonNegativeNumber = Annotated[float, Field(ge=0, allow_inf_nan=False)]
PositiveNumber = Annotated[float, Field(gt=0, allow_inf_nan=False)]

MAX_SECTION_ITEMS = 64
MAX_QUESTIONS = 128


class StrictCaptureModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
    )


class CaptureSourceKind(StrEnum):
    VOICE = "voice"
    TEXT = "text"
    EXCEL = "excel"
    MANUAL = "manual"


class FieldState(StrEnum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    NOT_MEASURED = "not_measured"
    NOT_APPLICABLE = "not_applicable"
    CONFLICTING = "conflicting"
    MISSING = "missing"


class ProjectStatus(StrEnum):
    PROPOSED = "proposed"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class ApproachOutcome(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    SUCCESSFUL = "successful"
    PARTIALLY_SUCCESSFUL = "partially_successful"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"


class RootCauseStatus(StrEnum):
    NOT_ASSESSED = "not_assessed"
    HYPOTHESIS = "hypothesis"
    CONFIRMED = "confirmed"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"


class AssessmentStatus(StrEnum):
    ASSESSED = "assessed"
    NOT_ASSESSED = "not_assessed"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"


class MeasurementState(StrEnum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    NOT_MEASURED = "not_measured"
    NOT_APPLICABLE = "not_applicable"
    CONFLICTING = "conflicting"


class SetpointOrActual(StrEnum):
    SETPOINT = "setpoint"
    ACTUAL = "actual"
    BOTH = "both"
    NOT_APPLICABLE = "not_applicable"


class TestOutcome(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    PARTIALLY_PASSED = "partially_passed"
    NOT_MEASURED = "not_measured"
    INCONCLUSIVE = "inconclusive"


class PhysicalArchiveStatus(StrEnum):
    ARCHIVED = "archived"
    NOT_ARCHIVED = "not_archived"
    LOST = "lost"
    CONSUMED = "consumed"
    UNKNOWN = "unknown"


class FollowUpStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    CONTACTED = "contacted"
    FEEDBACK_RECEIVED = "feedback_received"
    CLOSED = "closed"
    OVERDUE = "overdue"


class EvidenceType(StrEnum):
    AUDIO = "audio"
    TRANSCRIPT = "transcript"
    IMAGE = "image"
    PDF = "pdf"
    EXCEL = "excel"
    TEST_RESULT = "test_result"
    ERP_RECORD = "erp_record"
    OTHER = "other"


class ProjectIdentity(StrictCaptureModel):
    project_id: Identifier | None = None
    project_name: ShortText | None = None
    customer_company: ShortText | None = None
    customer_contact: ShortText | None = None
    request_summary: LongText | None = None
    target_application: ShortText | None = None
    intended_industrial_function: ShortText | None = None
    customer_requirements: tuple[LongText, ...] = Field(default_factory=tuple, max_length=64)
    success_criteria: tuple[LongText, ...] = Field(default_factory=tuple, max_length=64)
    opened_at: AwareDatetime | None = None
    target_due_at: AwareDatetime | None = None
    project_status: ProjectStatus | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> ProjectIdentity:
        if self.opened_at and self.target_due_at and self.target_due_at < self.opened_at:
            raise ValueError("target_due_at must not precede opened_at")
        return self


class BaseSubstrate(StrictCaptureModel):
    substrate_id: Identifier | None = None
    substrate_name: ShortText | None = None
    substrate_type: ShortText | None = None
    supplier: ShortText | None = None
    construction: ShortText | None = None
    basis_weight: PositiveNumber | None = None
    relevant_specification: LongText | None = None
    reason_selected: LongText | None = None


class MaterialRecord(StrictCaptureModel):
    # Correlation IDs connect Candidate sections; they are not source-system facts.
    material_id: CandidateMaterialId
    source_material_id: Identifier | None = None
    material_name: ShortText | None = None
    supplier: ShortText | None = None
    commercial_grade: ShortText | None = None
    function_in_formulation: ShortText | None = None
    amount: NonNegativeNumber | None = None
    unit: ShortText | None = None
    batch_or_lot: ShortText | None = None
    price_value: NonNegativeNumber | None = None
    price_currency: str | None = Field(default=None, min_length=3, max_length=3)
    price_basis: ShortText | None = None
    tds_reference: ShortText | None = None
    sds_reference: ShortText | None = None
    safety_notes: LongText | None = None

    @field_validator("price_currency", mode="after")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.isalpha():
            raise ValueError("price_currency must be a three-letter alphabetic code")
        return value.upper()

    @model_validator(mode="after")
    def validate_quantity_and_price(self) -> MaterialRecord:
        if (self.amount is None) != (self.unit is None):
            raise ValueError("amount and unit must be supplied together")
        if (self.price_value is None) != (self.price_currency is None):
            raise ValueError("price_value and price_currency must be supplied together")
        return self


class ExperimentalApproach(StrictCaptureModel):
    # Correlation IDs connect Candidate sections; they are not source-system facts.
    approach_id: CandidateApproachId
    source_approach_id: Identifier | None = None
    title: ShortText | None = None
    description: LongText | None = None
    technical_rationale: LongText | None = None
    hypothesis: LongText | None = None
    outcome: ApproachOutcome
    outcome_summary: LongText | None = None
    failure_reason: LongText | None = None
    root_cause_status: RootCauseStatus | None = None
    lesson_learned: LongText | None = None
    laboratory_challenges: tuple[LongText, ...] = Field(default_factory=tuple, max_length=32)
    improvement_possible: bool | None = None
    improvement_idea: LongText | None = None
    price_optimization_status: AssessmentStatus | None = None
    production_feasibility_status: AssessmentStatus | None = None
    production_feasibility_notes: LongText | None = None
    reuse_potential: LongText | None = None
    innovation_potential: LongText | None = None
    photograph_missing_reason: LongText | None = None


class ProcessParameter(StrictCaptureModel):
    approach_id: CandidateApproachId
    process_stage: ShortText
    equipment_name: ShortText | None = None
    parameter_name: ShortText
    numeric_value: FiniteNumber | None = None
    text_value: ShortText | None = None
    unit: ShortText | None = None
    setpoint_or_actual: SetpointOrActual | None = None
    measurement_state: MeasurementState
    source_note: LongText | None = None

    @model_validator(mode="after")
    def validate_measurement(self) -> ProcessParameter:
        has_numeric = self.numeric_value is not None
        has_text = self.text_value is not None
        if self.measurement_state is MeasurementState.KNOWN:
            if has_numeric == has_text:
                raise ValueError("known parameters require exactly one numeric_value or text_value")
            if has_numeric and self.unit is None:
                raise ValueError("known numeric parameters require a unit")
        elif self.measurement_state in {
            MeasurementState.UNKNOWN,
            MeasurementState.NOT_MEASURED,
            MeasurementState.NOT_APPLICABLE,
        }:
            if has_numeric or has_text:
                raise ValueError("non-known parameters must not carry a value")
        elif not (has_numeric or has_text or self.source_note):
            raise ValueError("conflicting parameters require a value or source_note")
        return self


class TestRecord(StrictCaptureModel):
    approach_id: CandidateApproachId
    sample_id: CandidateSampleId | None = None
    test_name: ShortText
    method: ShortText | None = None
    standard: ShortText | None = None
    evaluation_type: ShortText | None = None
    acceptance_criteria: LongText | None = None
    numeric_result: FiniteNumber | None = None
    text_result: LongText | None = None
    unit: ShortText | None = None
    outcome: TestOutcome
    performed_at: AwareDatetime | None = None
    performed_by: ShortText | None = None
    evidence_references: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)
    notes: LongText | None = None

    @model_validator(mode="after")
    def validate_result(self) -> TestRecord:
        if self.outcome is TestOutcome.NOT_MEASURED:
            if self.numeric_result is not None or self.text_result is not None:
                raise ValueError("not_measured tests must not carry a result")
        elif self.numeric_result is not None and self.unit is None:
            raise ValueError("numeric test results require a unit")
        return self


class SampleRecord(StrictCaptureModel):
    # Correlation IDs connect Candidate sections; they are not source-system facts.
    sample_id: CandidateSampleId
    source_sample_id: Identifier | None = None
    approach_id: CandidateApproachId
    sample_description: LongText | None = None
    physical_archive_status: PhysicalArchiveStatus | None = None
    archive_location: ShortText | None = None
    archive_reason_if_missing: LongText | None = None
    created_at: AwareDatetime | None = None
    sent_at: AwareDatetime | None = None
    recipient: ShortText | None = None
    shipment_reference: ShortText | None = None
    follow_up_status: FollowUpStatus | None = None
    follow_up_due_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_archive(self) -> SampleRecord:
        if self.physical_archive_status is PhysicalArchiveStatus.ARCHIVED:
            if self.archive_location is None:
                raise ValueError("archived samples require archive_location")
        if (
            self.physical_archive_status
            in {
                PhysicalArchiveStatus.NOT_ARCHIVED,
                PhysicalArchiveStatus.LOST,
            }
            and self.archive_reason_if_missing is None
        ):
            raise ValueError("missing physical samples require archive_reason_if_missing")
        return self


class CustomerFeedbackRecord(StrictCaptureModel):
    sample_id: CandidateSampleId
    received_at: AwareDatetime
    received_from: ShortText
    feedback_summary: LongText
    result: ShortText | None = None
    requested_changes: LongText | None = None
    next_action: LongText | None = None


class EvidenceDescriptor(StrictCaptureModel):
    evidence_id: Identifier
    evidence_type: EvidenceType
    filename: ShortText | None = None
    media_type: ShortText | None = None
    source_reference: ShortText
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    captured_at: AwareDatetime
    description: LongText | None = None
    approach_id: CandidateApproachId | None = None
    sample_id: CandidateSampleId | None = None

    @field_validator("sha256", mode="before")
    @classmethod
    def normalize_sha256(cls, value: Any) -> Any:
        return value.lower() if isinstance(value, str) else value


class CompletenessEvaluation(StrictCaptureModel):
    completeness_score: int = Field(ge=0, le=100)
    critical_missing_fields: tuple[str, ...] = Field(max_length=MAX_QUESTIONS)
    recommended_questions: tuple[str, ...] = Field(max_length=MAX_QUESTIONS)
    extraction_warnings: tuple[str, ...] = Field(max_length=MAX_QUESTIONS)


class LabProjectCaptureCandidate(StrictCaptureModel):
    capture_session_id: UUID
    source_kind: CaptureSourceKind
    source_language: LanguageCode | None = None
    transcript: LongText | None = None
    extraction_model: ShortText | None = None
    extraction_started_at: AwareDatetime | None = None
    extraction_completed_at: AwareDatetime | None = None

    project: ProjectIdentity
    substrate: BaseSubstrate | None = None
    materials: tuple[MaterialRecord, ...] = Field(
        default_factory=tuple, max_length=MAX_SECTION_ITEMS
    )
    approaches: tuple[ExperimentalApproach, ...] = Field(
        default_factory=tuple,
        max_length=MAX_SECTION_ITEMS,
    )
    process_parameters: tuple[ProcessParameter, ...] = Field(
        default_factory=tuple,
        max_length=MAX_SECTION_ITEMS,
    )
    tests: tuple[TestRecord, ...] = Field(default_factory=tuple, max_length=MAX_SECTION_ITEMS)
    samples: tuple[SampleRecord, ...] = Field(default_factory=tuple, max_length=MAX_SECTION_ITEMS)
    customer_feedback: tuple[CustomerFeedbackRecord, ...] = Field(
        default_factory=tuple,
        max_length=MAX_SECTION_ITEMS,
    )
    evidence: tuple[EvidenceDescriptor, ...] = Field(
        default_factory=tuple,
        max_length=MAX_SECTION_ITEMS,
    )

    current_next_action: LongText | None = None
    responsible_person: ShortText | None = None
    next_action_due_at: AwareDatetime | None = None
    commercial_potential: LongText | None = None
    potential_other_customers: tuple[ShortText, ...] = Field(default_factory=tuple, max_length=64)
    estimated_cost_status: AssessmentStatus | None = None
    production_trial_required: bool | None = None
    unresolved_questions: tuple[LongText, ...] = Field(
        default_factory=tuple, max_length=MAX_QUESTIONS
    )
    formulation_source_text: LongText | None = None
    source_cell_references: tuple[LongText, ...] = Field(default_factory=tuple, max_length=256)

    field_states: dict[str, FieldState] = Field(default_factory=dict, max_length=256)
    completeness_score: int = Field(default=0, ge=0, le=100)
    critical_missing_fields: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAX_QUESTIONS
    )
    recommended_questions: tuple[str, ...] = Field(default_factory=tuple, max_length=MAX_QUESTIONS)
    extraction_warnings: tuple[str, ...] = Field(default_factory=tuple, max_length=MAX_QUESTIONS)
    human_confirmed: bool = False
    human_confirmed_by: ShortText | None = None
    human_confirmed_at: AwareDatetime | None = None

    @field_validator("field_states", mode="before")
    @classmethod
    def validate_field_state_paths(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        normalized: dict[str, Any] = {}
        for key, state in value.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("field_states keys must be non-blank dotted field paths")
            normalized[key.strip()] = state
        return normalized

    @model_validator(mode="after")
    def validate_candidate(self) -> LabProjectCaptureCandidate:
        if self.source_kind in {CaptureSourceKind.VOICE, CaptureSourceKind.TEXT}:
            if self.transcript is None:
                raise ValueError("voice and text candidates require transcript")
        if bool(self.extraction_started_at) != bool(self.extraction_completed_at):
            raise ValueError("extraction timestamps must be supplied together")
        if (
            self.extraction_started_at
            and self.extraction_completed_at
            and self.extraction_completed_at < self.extraction_started_at
        ):
            raise ValueError("extraction_completed_at must not precede extraction_started_at")
        if self.human_confirmed:
            if self.human_confirmed_by is None or self.human_confirmed_at is None:
                raise ValueError("human confirmation requires actor and timestamp")
        elif self.human_confirmed_by is not None or self.human_confirmed_at is not None:
            raise ValueError("unconfirmed candidates must not carry confirmation metadata")

        self._validate_unique_ids("materials", [item.material_id for item in self.materials])
        self._validate_unique_ids("approaches", [item.approach_id for item in self.approaches])
        self._validate_unique_ids("samples", [item.sample_id for item in self.samples])
        self._validate_unique_ids("evidence", [item.evidence_id for item in self.evidence])

        approach_ids = {item.approach_id for item in self.approaches}
        for section, references in {
            "process_parameters": [item.approach_id for item in self.process_parameters],
            "tests": [item.approach_id for item in self.tests],
            "samples": [item.approach_id for item in self.samples],
        }.items():
            unknown = sorted(set(references) - approach_ids)
            if unknown:
                raise ValueError(f"{section} reference unknown approach IDs: {unknown}")
        return self

    @staticmethod
    def _validate_unique_ids(section: str, values: list[str]) -> None:
        if len(values) != len(set(values)):
            raise ValueError(f"{section} IDs must be unique")

    def state_for(self, field_path: str) -> FieldState:
        return self.field_states.get(field_path, FieldState.MISSING)


_NUMERIC_PARAMETER_TERMS = {
    "temperature",
    "curing temperature",
    "curing time",
    "pressure",
    "line speed",
    "speed",
    "coating weight",
    "viscosity",
    "mixer speed",
    "mixing time",
    "dryer temperature",
    "dryer zone",
    "padder pressure",
    "foulard pressure",
    "knife gap",
    "coating passes",
}


def _normalized_parameter_name(value: str) -> str:
    return " ".join(value.casefold().replace("_", " ").replace("-", " ").split())


def _expects_numeric_value(parameter_name: str) -> bool:
    normalized = _normalized_parameter_name(parameter_name)
    return any(term in normalized for term in _NUMERIC_PARAMETER_TERMS)


def evaluate_candidate_completeness(
    candidate: LabProjectCaptureCandidate,
) -> CompletenessEvaluation:
    """Evaluate deterministic missing-information rules in stable priority order."""

    fields: list[str] = []
    questions: list[str] = []
    warnings: list[str] = list(candidate.extraction_warnings)
    penalty = 0

    def add(field: str, question: str, *, weight: int = 6, warning: str | None = None) -> None:
        nonlocal penalty
        if field not in fields:
            fields.append(field)
            penalty += weight
        if question not in questions:
            questions.append(question)
        if warning and warning not in warnings:
            warnings.append(warning)

    if candidate.project.request_summary is None:
        add("project.request_summary", "What exactly did the customer request?", weight=10)
    if candidate.project.target_application is None:
        add("project.target_application", "What is the target application?", weight=8)
    if not candidate.project.success_criteria:
        add("project.success_criteria", "What are the measurable success criteria?", weight=8)
    if candidate.substrate is None or candidate.substrate.reason_selected is None:
        add("substrate.reason_selected", "Why was this base fabric selected?")
    if not candidate.approaches:
        add("approaches", "Which experimental approaches were attempted or planned?", weight=12)

    image_approach_ids = {
        item.approach_id
        for item in candidate.evidence
        if item.evidence_type is EvidenceType.IMAGE and item.approach_id is not None
    }
    tests_by_approach: dict[str, list[TestRecord]] = {}
    for test in candidate.tests:
        tests_by_approach.setdefault(test.approach_id, []).append(test)

    for approach in candidate.approaches:
        prefix = f"approaches.{approach.approach_id}"
        approach_label = approach.source_approach_id or approach.approach_id
        if approach.outcome is ApproachOutcome.FAILED:
            if approach.failure_reason is None:
                add(f"{prefix}.failure_reason", f"Why did approach {approach_label} fail?")
            if approach.lesson_learned is None:
                add(
                    f"{prefix}.lesson_learned",
                    f"What lesson was learned from approach {approach_label}?",
                )
            if (
                approach.approach_id not in image_approach_ids
                and approach.photograph_missing_reason is None
            ):
                add(
                    f"{prefix}.photograph",
                    "Attach a photograph for approach "
                    f"{approach_label}, or explain why none exists.",
                )

        approach_tests = tests_by_approach.get(approach.approach_id, [])
        tests_state = candidate.state_for(f"{prefix}.tests")
        if not approach_tests and tests_state is not FieldState.NOT_MEASURED:
            add(
                f"{prefix}.tests",
                "Which test method and acceptance criteria were used for approach "
                f"{approach_label}?",
            )

        if approach.production_feasibility_status in {None, AssessmentStatus.NOT_ASSESSED}:
            add(
                f"{prefix}.production_feasibility_status",
                "Was production feasibility evaluated?",
            )
        if approach.price_optimization_status in {None, AssessmentStatus.NOT_ASSESSED}:
            add(
                f"{prefix}.price_optimization_status",
                "Was price optimization evaluated?",
            )

    for parameter in candidate.process_parameters:
        if not _expects_numeric_value(parameter.parameter_name):
            continue
        path = f"process_parameters.{parameter.approach_id}.{parameter.parameter_name}"
        normalized_name = _normalized_parameter_name(parameter.parameter_name)
        if (
            parameter.measurement_state is MeasurementState.KNOWN
            and parameter.numeric_value is None
        ):
            add(
                path,
                f"What was the actual numeric value and unit for {parameter.parameter_name}?",
                warning=f"{parameter.parameter_name} is prose-only but normally requires a number.",
            )
        elif parameter.measurement_state in {
            MeasurementState.UNKNOWN,
            MeasurementState.NOT_MEASURED,
        }:
            question = (
                "What was the exact coating weight?"
                if "coating weight" in normalized_name
                else f"What was the actual {parameter.parameter_name}?"
            )
            add(path, question)

    for test in candidate.tests:
        if test.outcome is TestOutcome.NOT_MEASURED:
            continue
        if test.method is None or test.acceptance_criteria is None:
            add(
                f"tests.{test.approach_id}.{test.test_name}.method_and_criteria",
                "Which test method and acceptance criteria were used?",
            )

    sent_samples: list[SampleRecord] = []
    for sample in candidate.samples:
        prefix = f"samples.{sample.sample_id}"
        sample_label = sample.source_sample_id or sample.sample_id
        if sample.physical_archive_status in {None, PhysicalArchiveStatus.UNKNOWN}:
            add(
                prefix + ".physical_archive_status",
                f"Where is sample {sample_label} physically archived?",
            )
        is_sent = any(
            (
                sample.sent_at is not None,
                sample.recipient is not None,
                sample.shipment_reference is not None,
                sample.follow_up_status is not None,
            )
        )
        if not is_sent:
            continue
        sent_samples.append(sample)
        if sample.sent_at is None:
            add(prefix + ".sent_at", f"When was sample {sample_label} sent?")
        if sample.follow_up_status is None:
            add(
                prefix + ".follow_up_status",
                f"Was the customer contacted after shipment of sample {sample_label}?",
            )
        if sample.follow_up_status not in {FollowUpStatus.NOT_REQUIRED, FollowUpStatus.CLOSED}:
            if sample.follow_up_due_at is None:
                add(
                    prefix + ".follow_up_due_at",
                    f"When is follow-up for sample {sample_label} due?",
                )

    feedback_sample_ids = {item.sample_id for item in candidate.customer_feedback}
    if sent_samples and any(item.sample_id not in feedback_sample_ids for item in sent_samples):
        add("customer_feedback", "Has the customer provided feedback?")

    if candidate.approaches and all(item.reuse_potential is None for item in candidate.approaches):
        if not candidate.potential_other_customers:
            add("follow_ups.reuse_potential", "Was commercial reuse potential considered?")

    return CompletenessEvaluation(
        completeness_score=max(0, 100 - penalty),
        critical_missing_fields=tuple(fields),
        recommended_questions=tuple(questions),
        extraction_warnings=tuple(warnings),
    )


def apply_candidate_completeness(
    candidate: LabProjectCaptureCandidate,
) -> LabProjectCaptureCandidate:
    evaluation = evaluate_candidate_completeness(candidate)
    return candidate.model_copy(
        update={
            "completeness_score": evaluation.completeness_score,
            "critical_missing_fields": evaluation.critical_missing_fields,
            "recommended_questions": evaluation.recommended_questions,
            "extraction_warnings": evaluation.extraction_warnings,
        }
    )


def _dump_records(records: tuple[StrictCaptureModel, ...]) -> JsonValue:
    from smartcoat.domain.knowledge_objects_v2 import JsonValue

    dumped = [record.model_dump(mode="json", exclude_none=True) for record in records]
    return cast(JsonValue, dumped)


def to_knowledge_object_content(
    candidate: LabProjectCaptureCandidate,
) -> dict[str, JsonValue]:
    """Map a candidate to shallow content and validate Knowledge Object v2 bounds."""

    from smartcoat.domain.knowledge_objects_v2 import (
        ConfidentialityLevel,
        JsonValue,
        KnowledgeObjectV2MutableState,
        OwnerReference,
    )

    evaluated = apply_candidate_completeness(candidate)
    project = evaluated.project.model_dump(mode="json", exclude_none=True)
    substrates = (
        [evaluated.substrate.model_dump(mode="json", exclude_none=True)]
        if evaluated.substrate is not None
        else []
    )
    follow_up: dict[str, Any] = {
        "current_next_action": evaluated.current_next_action,
        "responsible_person": evaluated.responsible_person,
        "next_action_due_at": evaluated.next_action_due_at.isoformat()
        if evaluated.next_action_due_at
        else None,
        "commercial_potential": evaluated.commercial_potential,
        "potential_other_customers": list(evaluated.potential_other_customers),
        "estimated_cost_status": evaluated.estimated_cost_status,
        "production_trial_required": evaluated.production_trial_required,
        "unresolved_questions": list(evaluated.unresolved_questions),
    }
    follow_up = {key: value for key, value in follow_up.items() if value is not None}
    quality: dict[str, Any] = {
        "capture_session_id": str(evaluated.capture_session_id),
        "source_kind": evaluated.source_kind,
        "source_language": evaluated.source_language,
        "extraction_model": evaluated.extraction_model,
        "completeness_score": evaluated.completeness_score,
        "critical_missing_fields": list(evaluated.critical_missing_fields),
        "recommended_questions": list(evaluated.recommended_questions),
        "extraction_warnings": list(evaluated.extraction_warnings),
        "formulation_source_text": evaluated.formulation_source_text,
        "source_cell_references": list(evaluated.source_cell_references),
        "field_states": evaluated.field_states,
        "human_confirmed": evaluated.human_confirmed,
        "human_confirmed_by": evaluated.human_confirmed_by,
        "human_confirmed_at": evaluated.human_confirmed_at.isoformat()
        if evaluated.human_confirmed_at
        else None,
    }
    quality = {key: value for key, value in quality.items() if value is not None}

    content: dict[str, JsonValue] = {
        "project": cast(JsonValue, [project]),
        "substrates": cast(JsonValue, substrates),
        "materials": _dump_records(evaluated.materials),
        "approaches": _dump_records(evaluated.approaches),
        "process_parameters": _dump_records(evaluated.process_parameters),
        "tests": _dump_records(evaluated.tests),
        "samples": _dump_records(evaluated.samples),
        "customer_feedback": _dump_records(evaluated.customer_feedback),
        "evidence_links": _dump_records(evaluated.evidence),
        "follow_ups": cast(JsonValue, [follow_up]),
        "quality_summary": cast(JsonValue, [quality]),
    }

    validated = KnowledgeObjectV2MutableState(
        title=evaluated.project.project_name or "Lab project capture",
        description=evaluated.project.request_summary,
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        owner=OwnerReference(owner_id="lab-project-content-mapper", role="system"),
        confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        content=content,
    )
    return validated.content


__all__ = [
    "ApproachOutcome",
    "AssessmentStatus",
    "BaseSubstrate",
    "CaptureSourceKind",
    "CompletenessEvaluation",
    "CustomerFeedbackRecord",
    "EvidenceDescriptor",
    "EvidenceType",
    "ExperimentalApproach",
    "FieldState",
    "FollowUpStatus",
    "LabProjectCaptureCandidate",
    "MaterialRecord",
    "MeasurementState",
    "PhysicalArchiveStatus",
    "ProcessParameter",
    "ProjectIdentity",
    "ProjectStatus",
    "RootCauseStatus",
    "SampleRecord",
    "SetpointOrActual",
    "TestOutcome",
    "TestRecord",
    "apply_candidate_completeness",
    "evaluate_candidate_completeness",
    "to_knowledge_object_content",
]
