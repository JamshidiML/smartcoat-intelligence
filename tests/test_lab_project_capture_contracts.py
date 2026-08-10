from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from smartcoat.domain.lab_project_capture import (
    ApproachOutcome,
    AssessmentStatus,
    CaptureSourceKind,
    EvidenceDescriptor,
    EvidenceType,
    ExperimentalApproach,
    FieldState,
    FollowUpStatus,
    LabProjectCaptureCandidate,
    MaterialRecord,
    MeasurementState,
    PhysicalArchiveStatus,
    ProcessParameter,
    ProjectIdentity,
    ProjectStatus,
    RootCauseStatus,
    SampleRecord,
    SetpointOrActual,
    apply_candidate_completeness,
    evaluate_candidate_completeness,
    to_knowledge_object_content,
)
from smartcoat.domain.lab_project_capture import (
    TestOutcome as LabTestOutcome,
)

NOW = datetime(2026, 8, 6, 8, 30, tzinfo=UTC)
SESSION_ID = UUID("72d399c6-5fdf-4897-a4ab-126739220028")


def _candidate(**overrides: object) -> LabProjectCaptureCandidate:
    payload: dict[str, object] = {
        "capture_session_id": SESSION_ID,
        "source_kind": CaptureSourceKind.TEXT,
        "source_language": "en",
        "transcript": "Synthetic project intake for contract validation.",
        "extraction_model": "deterministic-test-provider",
        "extraction_started_at": NOW,
        "extraction_completed_at": NOW,
        "project": {
            "project_id": "P-SYN-001",
            "project_name": "Synthetic flame barrier",
            "customer_company": "Example Customer",
            "request_summary": "Create a one-sided coated fabric for a synthetic trial.",
            "target_application": "High-temperature flame protection",
            "success_criteria": ["Pass the declared synthetic flame test."],
            "project_status": "open",
        },
        "substrate": {
            "substrate_id": "SUB-01",
            "substrate_name": "Synthetic glass fabric",
            "substrate_type": "woven glass",
            "reason_selected": "Selected for a generalized high-temperature trial.",
        },
        "approaches": [
            {
                "approach_id": "C-A-001",
                "title": "Synthetic baseline",
                "outcome": "successful",
                "production_feasibility_status": "assessed",
                "price_optimization_status": "assessed",
                "reuse_potential": "May support another generalized test case.",
            }
        ],
        "tests": [
            {
                "approach_id": "C-A-001",
                "test_name": "Synthetic flame test",
                "method": "Generalized internal method",
                "acceptance_criteria": "No sustained flame in the synthetic fixture.",
                "text_result": "Passed",
                "outcome": "passed",
            }
        ],
    }
    payload.update(overrides)
    return LabProjectCaptureCandidate.model_validate(payload)


def test_valid_candidate_and_flattened_content() -> None:
    candidate = apply_candidate_completeness(_candidate())

    assert candidate.capture_session_id == SESSION_ID
    assert candidate.human_confirmed is False
    assert candidate.completeness_score == 100

    content = to_knowledge_object_content(candidate)
    assert list(content) == [
        "project",
        "substrates",
        "materials",
        "approaches",
        "process_parameters",
        "tests",
        "samples",
        "customer_feedback",
        "evidence_links",
        "follow_ups",
        "quality_summary",
    ]
    assert content["project"][0]["project_id"] == "P-SYN-001"  # type: ignore[index]


@pytest.mark.parametrize(
    ("enum_type", "expected"),
    [
        (CaptureSourceKind, {"voice", "text", "excel", "manual"}),
        (
            FieldState,
            {"known", "unknown", "not_measured", "not_applicable", "conflicting", "missing"},
        ),
        (
            ApproachOutcome,
            {
                "planned",
                "in_progress",
                "successful",
                "partially_successful",
                "failed",
                "inconclusive",
            },
        ),
        (RootCauseStatus, {"not_assessed", "hypothesis", "confirmed", "not_applicable", "unknown"}),
        (AssessmentStatus, {"assessed", "not_assessed", "not_applicable", "unknown"}),
        (MeasurementState, {"known", "unknown", "not_measured", "not_applicable", "conflicting"}),
        (SetpointOrActual, {"setpoint", "actual", "both", "not_applicable"}),
        (
            LabTestOutcome,
            {"passed", "failed", "partially_passed", "not_measured", "inconclusive"},
        ),
        (PhysicalArchiveStatus, {"archived", "not_archived", "lost", "consumed", "unknown"}),
        (
            FollowUpStatus,
            {"not_required", "pending", "contacted", "feedback_received", "closed", "overdue"},
        ),
        (
            EvidenceType,
            {"audio", "transcript", "image", "pdf", "excel", "test_result", "erp_record", "other"},
        ),
        (
            ProjectStatus,
            {"proposed", "open", "in_progress", "on_hold", "completed", "cancelled", "unknown"},
        ),
    ],
)
def test_canonical_enum_values(enum_type: type, expected: set[str]) -> None:
    assert {item.value for item in enum_type} == expected


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (ProjectIdentity, {"project_name": "   "}),
        (MaterialRecord, {"material_id": " "}),
        (
            ExperimentalApproach,
            {"approach_id": "C-A-001", "title": "\t", "outcome": "planned"},
        ),
    ],
)
def test_blank_strings_are_rejected(model: type, payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_numeric_process_parameter_validation() -> None:
    parameter = ProcessParameter(
        approach_id="C-A-001",
        process_stage="curing",
        parameter_name="temperature",
        numeric_value=210,
        unit="degC",
        setpoint_or_actual=SetpointOrActual.ACTUAL,
        measurement_state=MeasurementState.KNOWN,
    )
    assert parameter.numeric_value == 210

    with pytest.raises(ValidationError, match="require a unit"):
        ProcessParameter(
            approach_id="C-A-001",
            process_stage="curing",
            parameter_name="temperature",
            numeric_value=210,
            measurement_state=MeasurementState.KNOWN,
        )
    with pytest.raises(ValidationError, match="must not carry a value"):
        ProcessParameter(
            approach_id="C-A-001",
            process_stage="curing",
            parameter_name="temperature",
            numeric_value=210,
            unit="degC",
            measurement_state=MeasurementState.NOT_MEASURED,
        )


def test_timezone_aware_dates_are_required() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        _candidate(extraction_started_at=datetime(2026, 8, 6, 8, 30))


@pytest.mark.parametrize(
    "state",
    [
        FieldState.UNKNOWN,
        FieldState.NOT_MEASURED,
        FieldState.NOT_APPLICABLE,
        FieldState.CONFLICTING,
        FieldState.MISSING,
    ],
)
def test_explicit_field_states_are_preserved(state: FieldState) -> None:
    candidate = _candidate(field_states={"project.customer_contact": state})
    assert candidate.state_for("project.customer_contact") is state


def test_failed_approach_completeness_rules_and_question_order_are_deterministic() -> None:
    candidate = _candidate(
        approaches=[
            {
                "approach_id": "C-A-003",
                "outcome": "failed",
                "production_feasibility_status": "not_assessed",
                "price_optimization_status": "not_assessed",
            }
        ],
        tests=[],
    )

    first = evaluate_candidate_completeness(candidate)
    second = evaluate_candidate_completeness(candidate)

    assert first == second
    assert "approaches.C-A-003.failure_reason" in first.critical_missing_fields
    assert "approaches.C-A-003.lesson_learned" in first.critical_missing_fields
    assert "approaches.C-A-003.photograph" in first.critical_missing_fields
    assert first.recommended_questions[:3] == (
        "Why did approach C-A-003 fail?",
        "What lesson was learned from approach C-A-003?",
        "Attach a photograph for approach C-A-003, or explain why none exists.",
    )


def test_sent_sample_follow_up_and_archive_rules() -> None:
    candidate = _candidate(
        samples=[
            {
                "sample_id": "C-S-004",
                "source_sample_id": "S-04",
                "approach_id": "C-A-001",
                "recipient": "Example Customer",
            }
        ]
    )
    result = evaluate_candidate_completeness(candidate)

    assert "samples.C-S-004.physical_archive_status" in result.critical_missing_fields
    assert "samples.C-S-004.sent_at" in result.critical_missing_fields
    assert "samples.C-S-004.follow_up_status" in result.critical_missing_fields
    assert "samples.C-S-004.follow_up_due_at" in result.critical_missing_fields
    assert "customer_feedback" in result.critical_missing_fields


def test_physical_archive_contract_requires_location_or_reason() -> None:
    with pytest.raises(ValidationError, match="archive_location"):
        SampleRecord(
            sample_id="C-S-001",
            approach_id="C-A-001",
            physical_archive_status=PhysicalArchiveStatus.ARCHIVED,
        )
    with pytest.raises(ValidationError, match="archive_reason_if_missing"):
        SampleRecord(
            sample_id="C-S-001",
            approach_id="C-A-001",
            physical_archive_status=PhysicalArchiveStatus.LOST,
        )


def test_demo_missing_information_questions() -> None:
    candidate = _candidate(
        transcript=(
            "Synthetic voice scenario with two explicit approaches and one ambiguous approach."
        ),
        approaches=[
            {
                "approach_id": "C-A-001",
                "outcome": "failed",
                "production_feasibility_status": "not_assessed",
                "price_optimization_status": "not_assessed",
            },
            {
                "approach_id": "C-A-002",
                "outcome": "successful",
                "production_feasibility_status": "not_assessed",
                "price_optimization_status": "not_assessed",
            },
        ],
        process_parameters=[
            {
                "approach_id": "C-A-001",
                "process_stage": "coating",
                "parameter_name": "coating weight",
                "measurement_state": "not_measured",
            },
            {
                "approach_id": "C-A-002",
                "process_stage": "curing",
                "parameter_name": "curing temperature",
                "numeric_value": 210,
                "unit": "degC",
                "measurement_state": "known",
            },
        ],
        tests=[
            {
                "approach_id": "C-A-002",
                "sample_id": "C-S-001",
                "test_name": "Laboratory flame test",
                "text_result": "Passed",
                "outcome": "passed",
            }
        ],
        samples=[
            {
                "sample_id": "C-S-001",
                "source_sample_id": "S-02",
                "approach_id": "C-A-002",
                "recipient": "Example Customer",
                "follow_up_status": "pending",
            }
        ],
    )
    result = evaluate_candidate_completeness(candidate)

    expected = {
        "What was the exact coating weight?",
        "Why did approach C-A-001 fail?",
        "Which test method and acceptance criteria were used?",
        "When was sample S-02 sent?",
        "Where is sample S-02 physically archived?",
        "Has the customer provided feedback?",
        "Was production feasibility evaluated?",
        "Was price optimization evaluated?",
    }
    assert expected.issubset(set(result.recommended_questions))


def test_bounded_knowledge_object_content_rejects_oversized_candidate() -> None:
    valid = _candidate(
        evidence=[
            EvidenceDescriptor(
                evidence_id="EV-01",
                evidence_type=EvidenceType.TRANSCRIPT,
                filename="synthetic.txt",
                media_type="text/plain",
                source_reference="capture://synthetic/EV-01",
                sha256="a" * 64,
                captured_at=NOW,
                description="Synthetic evidence only.",
            )
        ]
    )
    assert to_knowledge_object_content(valid)["evidence_links"]

    oversized = _candidate(
        materials=[
            {
                "material_id": f"C-M-{index + 1:03d}",
                "material_name": f"Synthetic material {index}",
                "safety_notes": "x" * 2000,
            }
            for index in range(32)
        ]
    )
    with pytest.raises(ValidationError, match="payload_too_large"):
        to_knowledge_object_content(oversized)


def test_no_hallucinated_defaults_and_extra_fields_forbidden() -> None:
    candidate = LabProjectCaptureCandidate(
        capture_session_id=SESSION_ID,
        source_kind=CaptureSourceKind.MANUAL,
        project=ProjectIdentity(),
    )
    assert candidate.project.customer_company is None
    assert candidate.project.target_application is None
    assert candidate.materials == ()
    assert candidate.human_confirmed is False

    with pytest.raises(ValidationError, match="extra_forbidden"):
        LabProjectCaptureCandidate.model_validate(
            {
                "capture_session_id": str(SESSION_ID),
                "source_kind": "manual",
                "project": {},
                "invented_field": "not allowed",
            }
        )


def test_candidate_correlation_ids_are_structural_and_source_ids_are_optional() -> None:
    candidate = _candidate(
        materials=[{"material_id": "C-M-001", "material_name": "Synthetic material"}],
        approaches=[
            {
                "approach_id": "C-A-001",
                "outcome": "planned",
                "production_feasibility_status": "assessed",
                "price_optimization_status": "assessed",
                "reuse_potential": "Synthetic reuse context.",
            }
        ],
        tests=[],
    )

    assert candidate.materials[0].material_id == "C-M-001"
    assert candidate.materials[0].source_material_id is None
    assert candidate.approaches[0].source_approach_id is None
    with pytest.raises(ValidationError, match="C-M"):
        MaterialRecord(material_id="SOURCE-MATERIAL-7")


def test_human_confirmation_metadata_is_consistent() -> None:
    with pytest.raises(ValidationError, match="requires actor and timestamp"):
        _candidate(human_confirmed=True)
    with pytest.raises(ValidationError, match="must not carry confirmation metadata"):
        _candidate(human_confirmed_by="pilot-reviewer")
