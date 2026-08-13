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


class CandidateIssueSeverity(StrEnum):
    WARNING = "warning"
    BLOCKING = "blocking"


class CandidateReadinessIssue(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    code: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=128,
            pattern=r"^[a-z][a-z0-9_]*$",
        ),
    ]
    path: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1024)]
    severity: CandidateIssueSeverity
    message: LongText
    question: LongText


class CandidateReadinessReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    confirmation_ready: bool
    blocking_issue_count: int = Field(ge=0)
    warning_issue_count: int = Field(ge=0)
    issues: tuple[CandidateReadinessIssue, ...]


class CandidateNotReadyError(ValueError):
    """Raised when canonical mapping is attempted for an unsafe Candidate."""

    def __init__(self, report: CandidateReadinessReport) -> None:
        self.report = report
        super().__init__("candidate_has_blocking_readiness_issues")


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

        return self

    @staticmethod
    def _validate_unique_ids(section: str, values: list[str]) -> None:
        if len(values) != len(set(values)):
            raise ValueError(f"{section} IDs must be unique")

    def state_for(self, field_path: str) -> FieldState:
        return self.field_states.get(field_path, FieldState.MISSING)


def evaluate_candidate_readiness(
    candidate: LabProjectCaptureCandidate,
) -> CandidateReadinessReport:
    """Report reviewable semantic issues without changing the Candidate."""

    issues: list[CandidateReadinessIssue] = []

    def add(code: str, path: str, message: str, question: str) -> None:
        issues.append(
            CandidateReadinessIssue(
                code=code,
                path=path,
                severity=CandidateIssueSeverity.BLOCKING,
                message=message,
                question=question,
            )
        )

    if (
        candidate.project.opened_at is not None
        and candidate.project.target_due_at is not None
        and candidate.project.target_due_at < candidate.project.opened_at
    ):
        add(
            "project_date_order_invalid",
            "project.target_due_at",
            "The target due date precedes the project opened date.",
            "What are the correct project opened and target due dates?",
        )

    for index, material in enumerate(candidate.materials):
        prefix = f"materials.{index}"
        label = material.material_name or material.source_material_id or material.material_id
        if material.amount is not None and material.unit is None:
            add(
                "material_amount_missing_unit",
                f"{prefix}.unit",
                f"Material {label} has an amount but no unit.",
                f"What unit belongs to the {label} amount?",
            )
        if material.amount is None and material.unit is not None:
            add(
                "material_unit_missing_amount",
                f"{prefix}.amount",
                f"Material {label} has a unit but no amount.",
                f"What amount belongs to the {label} unit?",
            )
        if material.price_value is not None and material.price_currency is None:
            add(
                "material_price_missing_currency",
                f"{prefix}.price_currency",
                f"Material {label} has a price but no currency.",
                f"What currency belongs to the {label} price?",
            )
        if material.price_value is None and material.price_currency is not None:
            add(
                "material_currency_missing_price",
                f"{prefix}.price_value",
                f"Material {label} has a currency but no price value.",
                f"What price value belongs to the {label} currency?",
            )

    approach_ids = {item.approach_id for item in candidate.approaches}
    sample_ids = {item.sample_id for item in candidate.samples}
    for index, parameter in enumerate(candidate.process_parameters):
        prefix = f"process_parameters.{index}"
        label = parameter.parameter_name
        has_numeric = parameter.numeric_value is not None
        has_text = parameter.text_value is not None
        if parameter.approach_id not in approach_ids:
            add(
                "process_parameter_unknown_approach",
                f"{prefix}.approach_id",
                f"Process parameter {label} references an unknown approach.",
                f"Which approach does the {label} belong to?",
            )
        if parameter.measurement_state is MeasurementState.KNOWN and not (has_numeric or has_text):
            add(
                "process_parameter_known_without_value",
                prefix,
                f"Known process parameter {label} has no value.",
                f"What value was recorded for {label}?",
            )
        if parameter.measurement_state is MeasurementState.KNOWN and has_numeric and has_text:
            add(
                "process_parameter_known_with_multiple_values",
                prefix,
                f"Known process parameter {label} has both numeric and text values.",
                f"Which recorded value should be used for {label}?",
            )
        if has_numeric and parameter.unit is None:
            add(
                "process_parameter_numeric_missing_unit",
                f"{prefix}.unit",
                f"Numeric process parameter {label} has no unit.",
                f"What was the unit for the {parameter.numeric_value:g} process value?",
            )
        if parameter.measurement_state in {
            MeasurementState.UNKNOWN,
            MeasurementState.NOT_MEASURED,
            MeasurementState.NOT_APPLICABLE,
        } and (has_numeric or has_text):
            add(
                "process_parameter_state_value_conflict",
                prefix,
                f"Process parameter {label} has a value that conflicts with its state.",
                f"What is the correct measurement state for {label}?",
            )
        if parameter.measurement_state is MeasurementState.CONFLICTING and not (
            has_numeric or has_text or parameter.source_note
        ):
            add(
                "process_parameter_empty_conflict",
                prefix,
                f"Conflicting process parameter {label} has no supporting detail.",
                f"What conflicting information was recorded for {label}?",
            )

    for index, test in enumerate(candidate.tests):
        prefix = f"tests.{index}"
        if test.approach_id not in approach_ids:
            add(
                "test_unknown_approach",
                f"{prefix}.approach_id",
                f"Test {test.test_name} references an unknown approach.",
                f"Which approach does the {test.test_name} test belong to?",
            )
        if test.sample_id is not None and test.sample_id not in sample_ids:
            add(
                "test_unknown_sample",
                f"{prefix}.sample_id",
                f"Test {test.test_name} references an unknown sample.",
                f"Which sample does the {test.test_name} test belong to?",
            )
        if test.numeric_result is not None and test.unit is None:
            add(
                "test_numeric_result_missing_unit",
                f"{prefix}.unit",
                f"Test {test.test_name} has a numeric result but no unit.",
                f"What unit belongs to the {test.test_name} result?",
            )
        if test.outcome is TestOutcome.NOT_MEASURED and (
            test.numeric_result is not None or test.text_result is not None
        ):
            add(
                "test_not_measured_with_result",
                prefix,
                f"Test {test.test_name} is not measured but contains a result.",
                f"Was {test.test_name} measured, and should its result be retained?",
            )

    for index, sample in enumerate(candidate.samples):
        prefix = f"samples.{index}"
        label = sample.source_sample_id or sample.sample_id
        if sample.approach_id not in approach_ids:
            add(
                "sample_unknown_approach",
                f"{prefix}.approach_id",
                f"Sample {label} references an unknown approach.",
                f"Which approach produced sample {label}?",
            )
        if (
            sample.physical_archive_status is PhysicalArchiveStatus.ARCHIVED
            and sample.archive_location is None
        ):
            add(
                "sample_archive_location_missing",
                f"{prefix}.archive_location",
                f"Archived sample {label} has no archive location.",
                f"Where is sample {label} physically archived?",
            )
        if (
            sample.physical_archive_status
            in {PhysicalArchiveStatus.NOT_ARCHIVED, PhysicalArchiveStatus.LOST}
            and sample.archive_reason_if_missing is None
        ):
            add(
                "sample_archive_reason_missing",
                f"{prefix}.archive_reason_if_missing",
                f"Sample {label} has no explanation for its missing archive.",
                f"Why is sample {label} not physically archived?",
            )

    for index, feedback in enumerate(candidate.customer_feedback):
        if feedback.sample_id not in sample_ids:
            add(
                "feedback_unknown_sample",
                f"customer_feedback.{index}.sample_id",
                "Customer feedback references an unknown sample.",
                "Which sample does this customer feedback describe?",
            )

    for index, evidence in enumerate(candidate.evidence):
        prefix = f"evidence.{index}"
        if evidence.approach_id is not None and evidence.approach_id not in approach_ids:
            add(
                "evidence_unknown_approach",
                f"{prefix}.approach_id",
                f"Evidence {evidence.evidence_id} references an unknown approach.",
                f"Which approach does evidence {evidence.evidence_id} support?",
            )
        if evidence.sample_id is not None and evidence.sample_id not in sample_ids:
            add(
                "evidence_unknown_sample",
                f"{prefix}.sample_id",
                f"Evidence {evidence.evidence_id} references an unknown sample.",
                f"Which sample does evidence {evidence.evidence_id} support?",
            )

    blocking_count = sum(issue.severity is CandidateIssueSeverity.BLOCKING for issue in issues)
    warning_count = sum(issue.severity is CandidateIssueSeverity.WARNING for issue in issues)
    return CandidateReadinessReport(
        confirmation_ready=blocking_count == 0,
        blocking_issue_count=blocking_count,
        warning_issue_count=warning_count,
        issues=tuple(issues),
    )


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
    readiness = evaluate_candidate_readiness(candidate)
    questions = list(evaluation.recommended_questions)
    for issue in readiness.issues:
        if issue.question not in questions and len(questions) < MAX_QUESTIONS:
            questions.append(issue.question)
    return candidate.model_copy(
        update={
            "completeness_score": evaluation.completeness_score,
            "critical_missing_fields": evaluation.critical_missing_fields,
            "recommended_questions": tuple(questions),
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
    readiness = evaluate_candidate_readiness(evaluated)
    if not readiness.confirmation_ready:
        raise CandidateNotReadyError(readiness)
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
    "CandidateIssueSeverity",
    "CandidateNotReadyError",
    "CandidateReadinessIssue",
    "CandidateReadinessReport",
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
    "evaluate_candidate_readiness",
    "to_knowledge_object_content",
]
