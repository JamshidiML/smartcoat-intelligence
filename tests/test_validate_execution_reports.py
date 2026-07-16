from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from validate_execution_reports import main, validate_text  # noqa: E402

CATEGORIES = (
    ("Correctness and evidence", 25),
    ("Scope and acceptance criteria", 20),
    ("Architecture and North-Star alignment", 15),
    ("Verification, tests, or validation", 15),
    ("Security, privacy, and data governance", 10),
    ("Documentation and traceability", 10),
    ("Maintainability and clarity", 5),
)


def scorecard(total: int) -> str:
    deduction = 100 - total
    rows = ["| Category | Maximum | Awarded | Evidence | Deduction Reason |"]
    rows.append("|---|---:|---:|---|---|")
    for index, (category, maximum) in enumerate(CATEGORIES):
        awarded = maximum - deduction if index == 0 else maximum
        reason = "Independent review item." if awarded < maximum else "None."
        rows.append(f"| {category} | {maximum} | {awarded} | Synthetic evidence. | {reason} |")
    rows.append(f"| Total | 100 | {total} | Synthetic score evidence. | Current deductions. |")
    return "\n".join(rows)


def make_report(
    *,
    self_score: int = 95,
    reviewer_score: int | None = 95,
    gate_failed: bool = False,
    status: str = "READY FOR CHATGPT REVIEW",
    unchecked: bool = False,
    correction_points: int | None = None,
    correction_status: str = "OPEN",
    blockers: str = "None.",
) -> str:
    reviewer = (
        "Reviewer status: Pending independent review."
        if reviewer_score is None
        else scorecard(reviewer_score)
    )
    if reviewer_score is None:
        provisional = "Pending"
        adjusted = "Pending"
        current_loss = 100 - self_score
    else:
        weighted = round(0.4 * self_score + 0.6 * reviewer_score, 1)
        provisional = f"{weighted:.1f}"
        adjusted = f"{min(weighted, 79.0) if gate_failed else weighted:.1f}"
        current_loss = 100 - min(self_score, reviewer_score)
    points = current_loss if correction_points is None else correction_points
    correction_row = ""
    if points or correction_points is not None or correction_status != "OPEN":
        correction_row = (
            f"\n| C01 | Current score | {points} | {correction_status} | "
            "Apply and validate the correction. |"
        )
    mark = " " if unchecked else "x"
    gate_status = "FAIL" if gate_failed else "PASS"
    gate_result = gate_status

    return f"""# Synthetic Thread Report

Thread ID: T99

Issue: https://github.com/example/repository/issues/99

Branch: `thread/99-synthetic`

Draft PR: https://github.com/example/repository/pull/99

Final status: `{status}`

## Objective

Validate a synthetic report.

## Files Changed

- `synthetic.md`

## Methods and Commands Executed

- `pytest tests/test_synthetic.py`

## Actual Results

Passed one synthetic validation.

## Acceptance-Criteria Evidence

- [{mark}] Synthetic acceptance criterion.
  Evidence: `synthetic-result`.

## Architecture Impact

No application architecture change.

## Security and Data Impact

Synthetic content only.

## Known Limitations

Independent evidence is intentionally small.

## Lost Points and Correction Items

| Item | Source | Points | Status | Action or Evidence |
|---|---|---:|---|---|{correction_row}

## Codex Self-Score

{scorecard(self_score)}

## ChatGPT Reviewer Score

{reviewer}

## Final Score

Provisional weighted score: {provisional}

Gate-adjusted score: {adjusted}

## Critical-Gate Declaration

| Gate | Status | Evidence |
|---|---|---|
| G1 Verified claims | {gate_status} | Synthetic command result. |
| G2 Confidential data | PASS | Synthetic-only inspection. |
| G3 Approved scope and architecture | PASS | Synthetic owned path. |
| G4 Required validation | PASS | Synthetic test result. |
| G5 File ownership | PASS | Synthetic status check. |
| G6 Acceptance completeness | PASS | Synthetic checklist. |

Critical-gate result: {gate_result}

## Correction-Cycle History

| Cycle | Starting Score | Findings | Corrections | Ending Score | Validation Evidence | Status |
|---:|---:|---|---|---:|---|---|
| 1 | 90 | Synthetic gap. | Synthetic correction. | {self_score} | Synthetic test passed. | CLOSED |

## Recommended Follow-up Issues

- Independent review.

## Blockers

{blockers}
"""


def assert_has_error(report: str, phrase: str) -> None:
    errors = validate_text(report)
    assert any(phrase in error for error in errors), errors


def test_valid_reviewed_report() -> None:
    assert validate_text(make_report()) == []


def test_valid_pending_reviewer_report() -> None:
    assert validate_text(make_report(reviewer_score=None)) == []


def test_valid_pre_pr_report_is_correction_in_progress() -> None:
    report = make_report(status="CORRECTION IN PROGRESS").replace(
        "https://github.com/example/repository/pull/99", "Pending (pre-PR)"
    )
    assert validate_text(report) == []


def test_ready_report_rejects_pending_pr() -> None:
    report = make_report().replace(
        "https://github.com/example/repository/pull/99", "Pending (pre-PR)"
    )
    assert_has_error(report, "allowed only while correction is in progress")


def test_valid_gate_failed_report_is_capped() -> None:
    assert validate_text(make_report(gate_failed=True)) == []


def test_missing_required_section_is_rejected() -> None:
    report = make_report().replace("## Architecture Impact", "## Removed Architecture Impact")
    assert_has_error(report, "missing section: Architecture Impact")


def test_category_score_above_maximum_is_rejected() -> None:
    report = make_report().replace(
        "| Correctness and evidence | 25 | 20 |",
        "| Correctness and evidence | 25 | 26 |",
        1,
    )
    assert_has_error(report, "exceeds 25")


def test_weighted_formula_mismatch_is_rejected() -> None:
    report = make_report().replace(
        "Provisional weighted score: 95.0", "Provisional weighted score: 96.0"
    )
    assert_has_error(report, "provisional weighted score must be 95.0")


def test_gate_failure_above_cap_is_rejected() -> None:
    report = make_report(gate_failed=True).replace(
        "Gate-adjusted score: 79.0", "Gate-adjusted score: 95.0"
    )
    assert_has_error(report, "gate-adjusted score must be 79.0")


def test_missing_category_evidence_is_rejected() -> None:
    report = make_report().replace("Synthetic evidence.", "-", 1)
    assert_has_error(report, "needs evidence")


def test_lost_points_must_match_unresolved_corrections() -> None:
    report = make_report(correction_points=4)
    assert_has_error(report, "must equal current lost points 5")


def test_100_status_rejects_unchecked_acceptance_criterion() -> None:
    report = make_report(
        self_score=100,
        reviewer_score=100,
        status="100/100 — READY FOR APPROVAL",
        unchecked=True,
    )
    assert_has_error(report, "cannot contain unchecked acceptance criteria")


def test_100_status_rejects_unresolved_correction() -> None:
    report = make_report(
        self_score=100,
        reviewer_score=100,
        status="100/100 — READY FOR APPROVAL",
        correction_points=0,
        correction_status="OPEN",
    )
    assert_has_error(report, "requires all correction items resolved")


def test_blocked_status_requires_decision_details() -> None:
    report = make_report(status="BLOCKED — HUMAN DECISION REQUIRED")
    assert_has_error(report, "blocked status requires question details")


def test_valid_human_decision_blocker() -> None:
    blockers = """Question: Which approved option should be selected?
Options: A or B.
Consequences: A delays scope; B changes cost.
Recommended decision: Select A."""
    report = make_report(
        status="BLOCKED — HUMAN DECISION REQUIRED",
        correction_status="BLOCKED",
        blockers=blockers,
    )
    assert validate_text(report) == []


def test_acceptance_checklist_is_required() -> None:
    report = make_report().replace("- [x] Synthetic acceptance criterion.", "Synthetic criterion.")
    assert_has_error(report, "must contain checklist items")


def test_invalid_final_status_is_rejected() -> None:
    report = make_report(status="DONE")
    assert_has_error(report, "invalid Final status")


def test_cli_returns_nonzero_for_invalid_report(tmp_path: Path) -> None:
    report = tmp_path / "invalid.md"
    report.write_text("# Invalid\n", encoding="utf-8")
    assert main([str(report)]) == 1


def test_cli_accepts_valid_report(tmp_path: Path) -> None:
    report = tmp_path / "valid.md"
    report.write_text(make_report(), encoding="utf-8")
    assert main([str(report)]) == 0
