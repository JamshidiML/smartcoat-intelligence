from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from smartcoat.domain.lab_project_capture import (
    ApproachOutcome,
    AssessmentStatus,
    CandidateIssueSeverity,
    CandidateNotReadyError,
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
    SetpointOrActual,
    apply_candidate_completeness,
    evaluate_candidate_completeness,
    evaluate_candidate_readiness,
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


def test_reviewable_process_parameter_semantics_are_preserved_and_reported() -> None:
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

    candidate = _candidate(
        process_parameters=[
            {
                "approach_id": "C-A-001",
                "process_stage": "curing",
                "parameter_name": "temperature",
                "numeric_value": 210,
                "measurement_state": "known",
            },
            {
                "approach_id": "C-A-001",
                "process_stage": "coating",
                "parameter_name": "pressure",
                "numeric_value": 3,
                "unit": "bar",
                "measurement_state": "not_measured",
            },
        ]
    )
    report = evaluate_candidate_readiness(candidate)

    assert candidate.process_parameters[0].numeric_value == 210
    assert candidate.process_parameters[0].unit is None
    assert candidate.process_parameters[1].numeric_value == 3
    assert report.confirmation_ready is False
    assert [issue.code for issue in report.issues] == [
        "process_parameter_numeric_missing_unit",
        "process_parameter_state_value_conflict",
    ]
    assert all(issue.severity is CandidateIssueSeverity.BLOCKING for issue in report.issues)


def test_process_parameter_structural_validation_remains_strict() -> None:
    with pytest.raises(ValidationError):
        ProcessParameter(
            approach_id="C-A-001",
            process_stage="curing",
            parameter_name="temperature",
            numeric_value=float("inf"),
            measurement_state="not-a-state",  # type: ignore[arg-type]
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


def test_physical_archive_issues_are_reviewable() -> None:
    candidate = _candidate(
        samples=[
            {
                "sample_id": "C-S-001",
                "approach_id": "C-A-001",
                "physical_archive_status": "archived",
            },
            {
                "sample_id": "C-S-002",
                "approach_id": "C-A-001",
                "physical_archive_status": "lost",
            },
        ]
    )

    report = evaluate_candidate_readiness(candidate)

    assert candidate.samples[0].archive_location is None
    assert candidate.samples[1].archive_reason_if_missing is None
    assert [issue.code for issue in report.issues] == [
        "sample_archive_location_missing",
        "sample_archive_reason_missing",
    ]


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


def test_qwen_material_shape_is_reviewable_then_ready_after_human_unit_edit() -> None:
    candidate = _candidate(
        materials=[
            {
                "material_id": "C-M-001",
                "material_name": "Synthetic magnesium hydroxide",
                "amount": 5,
            }
        ]
    )

    report = evaluate_candidate_readiness(candidate)

    assert candidate.materials[0].amount == 5
    assert candidate.materials[0].unit is None
    assert report.confirmation_ready is False
    assert report.issues[0].code == "material_amount_missing_unit"
    assert "unit" in report.issues[0].question.casefold()
    with pytest.raises(CandidateNotReadyError) as error:
        to_knowledge_object_content(candidate)
    assert error.value.report == report

    corrected_material = candidate.materials[0].model_copy(update={"unit": "g"})
    corrected = candidate.model_copy(update={"materials": (corrected_material,)})

    assert evaluate_candidate_readiness(corrected).confirmation_ready is True
    assert to_knowledge_object_content(corrected)["materials"][0]["unit"] == "g"  # type: ignore[index]


def test_orphan_relationships_are_preserved_in_stable_readiness_order() -> None:
    candidate = _candidate(
        project={
            "opened_at": "2026-08-10T00:00:00Z",
            "target_due_at": "2026-08-09T00:00:00Z",
        },
        approaches=[],
        process_parameters=[
            {
                "approach_id": "C-A-004",
                "process_stage": "curing",
                "parameter_name": "curing temperature",
                "measurement_state": "unknown",
            }
        ],
        tests=[
            {
                "approach_id": "C-A-003",
                "sample_id": "C-S-003",
                "test_name": "Synthetic test",
                "outcome": "not_measured",
            }
        ],
        samples=[
            {
                "sample_id": "C-S-001",
                "approach_id": "C-A-002",
            }
        ],
        customer_feedback=[
            {
                "sample_id": "C-S-004",
                "received_at": NOW,
                "received_from": "Synthetic reviewer",
                "feedback_summary": "Synthetic feedback.",
            }
        ],
        evidence=[
            {
                "evidence_id": "EV-ORPHAN",
                "evidence_type": "other",
                "source_reference": "synthetic://orphan",
                "sha256": "b" * 64,
                "captured_at": NOW,
                "approach_id": "C-A-005",
                "sample_id": "C-S-005",
            }
        ],
    )

    first = evaluate_candidate_readiness(candidate)
    second = evaluate_candidate_readiness(candidate)

    assert first == second
    assert [issue.code for issue in first.issues] == [
        "project_date_order_invalid",
        "process_parameter_unknown_approach",
        "test_unknown_approach",
        "test_unknown_sample",
        "sample_unknown_approach",
        "feedback_unknown_sample",
        "evidence_unknown_approach",
        "evidence_unknown_sample",
    ]
    assert first.blocking_issue_count == 8
    assert first.warning_issue_count == 0
    with pytest.raises(ValidationError, match="frozen"):
        first.issues[0].message = "Changed"  # type: ignore[misc]


def test_all_reviewable_pairing_and_result_rules_have_machine_codes() -> None:
    candidate = _candidate(
        materials=[
            {
                "material_id": "C-M-001",
                "unit": "g",
                "price_value": 2,
            },
            {
                "material_id": "C-M-002",
                "amount": 5,
                "price_currency": "EUR",
            },
        ],
        process_parameters=[
            {
                "approach_id": "C-A-001",
                "process_stage": "mixing",
                "parameter_name": "viscosity",
                "measurement_state": "known",
            },
            {
                "approach_id": "C-A-001",
                "process_stage": "mixing",
                "parameter_name": "appearance",
                "numeric_value": 1,
                "text_value": "high",
                "unit": "score",
                "measurement_state": "known",
            },
            {
                "approach_id": "C-A-001",
                "process_stage": "mixing",
                "parameter_name": "operator note",
                "measurement_state": "conflicting",
            },
        ],
        tests=[
            {
                "approach_id": "C-A-001",
                "test_name": "Numeric synthetic test",
                "numeric_result": 8,
                "outcome": "passed",
            },
            {
                "approach_id": "C-A-001",
                "test_name": "Unmeasured synthetic test",
                "text_result": "Unexpected result",
                "outcome": "not_measured",
            },
        ],
    )

    codes = {issue.code for issue in evaluate_candidate_readiness(candidate).issues}

    assert codes == {
        "material_unit_missing_amount",
        "material_price_missing_currency",
        "material_amount_missing_unit",
        "material_currency_missing_price",
        "process_parameter_known_without_value",
        "process_parameter_known_with_multiple_values",
        "process_parameter_empty_conflict",
        "test_numeric_result_missing_unit",
        "test_not_measured_with_result",
    }
