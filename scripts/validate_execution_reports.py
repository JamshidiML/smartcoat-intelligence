#!/usr/bin/env python3
"""Validate SmartCoat execution-thread reports against the Cycle 1 contract."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

RUBRIC = {
    "Correctness and evidence": 25.0,
    "Scope and acceptance criteria": 20.0,
    "Architecture and North-Star alignment": 15.0,
    "Verification, tests, or validation": 15.0,
    "Security, privacy, and data governance": 10.0,
    "Documentation and traceability": 10.0,
    "Maintainability and clarity": 5.0,
}

REQUIRED_METADATA = ("Thread ID", "Issue", "Branch", "Draft PR", "Final status")
REQUIRED_SECTIONS = (
    "Objective",
    "Files Changed",
    "Methods and Commands Executed",
    "Actual Results",
    "Acceptance-Criteria Evidence",
    "Architecture Impact",
    "Security and Data Impact",
    "Known Limitations",
    "Lost Points and Correction Items",
    "Codex Self-Score",
    "ChatGPT Reviewer Score",
    "Final Score",
    "Critical-Gate Declaration",
    "Correction-Cycle History",
    "Recommended Follow-up Issues",
    "Blockers",
)
FINAL_STATUSES = {
    "READY FOR CHATGPT REVIEW",
    "CORRECTION IN PROGRESS",
    "100/100 — READY FOR APPROVAL",
    "BLOCKED — HUMAN DECISION REQUIRED",
}
GATE_NAMES = {
    "G1 Verified claims",
    "G2 Confidential data",
    "G3 Approved scope and architecture",
    "G4 Required validation",
    "G5 File ownership",
    "G6 Acceptance completeness",
}
PLACEHOLDERS = {"", "-", "tbd", "todo", "none provided", "pending evidence"}


@dataclass(frozen=True)
class ParsedReport:
    metadata: dict[str, str]
    sections: dict[str, str]


def _parse_report(text: str, errors: list[str]) -> ParsedReport:
    metadata: dict[str, str] = {}
    sections: dict[str, str] = {}
    current: str | None = None
    section_lines: list[str] = []

    def finish_section() -> None:
        if current is not None:
            if current in sections:
                errors.append(f"duplicate section: {current}")
            else:
                sections[current] = "\n".join(section_lines).strip()

    for line in text.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            finish_section()
            current = heading.group(1)
            section_lines = []
            continue
        if current is None:
            for key in REQUIRED_METADATA:
                match = re.match(rf"^{re.escape(key)}:\s*(.+?)\s*$", line)
                if match:
                    if key in metadata:
                        errors.append(f"duplicate metadata field: {key}")
                    metadata[key] = match.group(1).strip(" `")
                    break
        else:
            section_lines.append(line)
    finish_section()
    return ParsedReport(metadata=metadata, sections=sections)


def _table(section: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped[1:-1].split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def _is_evidence(value: str) -> bool:
    return value.strip().lower() not in PLACEHOLDERS and len(value.strip()) >= 3


def _number(value: str, label: str, errors: list[str]) -> float | None:
    try:
        result = float(value.strip())
    except ValueError:
        errors.append(f"{label} must be numeric, got {value!r}")
        return None
    if not 0 <= result <= 100:
        errors.append(f"{label} must be between 0 and 100, got {result:g}")
        return None
    return result


def _score(section: str, label: str, allow_pending: bool, errors: list[str]) -> float | None:
    if allow_pending and re.search(r"Reviewer status:\s*Pending\b", section, re.IGNORECASE):
        return None

    rows = _table(section)
    expected_header = ["Category", "Maximum", "Awarded", "Evidence", "Deduction Reason"]
    if not rows or rows[0] != expected_header:
        errors.append(f"{label} must contain the standard scorecard header")
        return None

    data = rows[1:]
    if len(data) != len(RUBRIC) + 1:
        errors.append(f"{label} must contain seven category rows and one Total row")
        return None

    total_awarded = 0.0
    for row, (category, maximum) in zip(data[:-1], RUBRIC.items(), strict=True):
        if len(row) != 5:
            errors.append(f"{label} row {category!r} must contain five columns")
            continue
        if row[0] != category:
            errors.append(f"{label} expected category {category!r}, got {row[0]!r}")
        stated_max = _number(row[1], f"{label} maximum for {category}", errors)
        awarded = _number(row[2], f"{label} awarded for {category}", errors)
        if stated_max is not None and stated_max != maximum:
            errors.append(f"{label} maximum for {category} must be {maximum:g}")
        if awarded is not None:
            if awarded > maximum:
                errors.append(f"{label} awarded for {category} exceeds {maximum:g}")
            total_awarded += awarded
        if not _is_evidence(row[3]):
            errors.append(f"{label} needs evidence for {category}")
        if awarded is not None and awarded < maximum and not _is_evidence(row[4]):
            errors.append(f"{label} needs a deduction reason for {category}")

    total = data[-1]
    if len(total) != 5 or total[0] != "Total":
        errors.append(f"{label} must end with the standard Total row")
        return None
    stated_max = _number(total[1], f"{label} total maximum", errors)
    stated_awarded = _number(total[2], f"{label} total awarded", errors)
    if stated_max != 100:
        errors.append(f"{label} total maximum must be 100")
    if stated_awarded is not None and abs(stated_awarded - total_awarded) > 0.05:
        errors.append(
            f"{label} total {stated_awarded:g} does not match category sum {total_awarded:g}"
        )
    return stated_awarded


def _final_scores(section: str, errors: list[str]) -> tuple[float | None, float | None]:
    provisional_match = re.search(
        r"^Provisional weighted score:\s*(.+?)\s*$", section, re.MULTILINE
    )
    adjusted_match = re.search(r"^Gate-adjusted score:\s*(.+?)\s*$", section, re.MULTILINE)
    if not provisional_match or not adjusted_match:
        errors.append("Final Score must declare provisional weighted and gate-adjusted scores")
        return None, None

    if provisional_match.group(1).strip().lower() == "pending":
        provisional = None
    else:
        provisional = _number(provisional_match.group(1), "provisional weighted score", errors)
    if adjusted_match.group(1).strip().lower() == "pending":
        adjusted = None
    else:
        adjusted = _number(adjusted_match.group(1), "gate-adjusted score", errors)
    return provisional, adjusted


def _critical_gates(section: str, errors: list[str]) -> bool | None:
    rows = _table(section)
    if not rows or rows[0] != ["Gate", "Status", "Evidence"]:
        errors.append("Critical-Gate Declaration must contain the standard gate table")
        return None
    if len(rows[1:]) != len(GATE_NAMES):
        errors.append("Critical-Gate Declaration must contain all six gates")
        return None

    seen: set[str] = set()
    failed = False
    for row in rows[1:]:
        if len(row) != 3:
            errors.append("each critical-gate row must contain three columns")
            continue
        name, status, evidence = row
        seen.add(name)
        normalized = status.upper()
        if normalized not in {"PASS", "FAIL"}:
            errors.append(f"critical gate {name!r} status must be PASS or FAIL")
        failed = failed or normalized == "FAIL"
        if not _is_evidence(evidence):
            errors.append(f"critical gate {name!r} needs evidence")
    if seen != GATE_NAMES:
        errors.append(f"critical gate names differ from the standard: {sorted(seen ^ GATE_NAMES)}")

    result_match = re.search(r"^Critical-gate result:\s*(PASS|FAIL)\s*$", section, re.MULTILINE)
    if not result_match:
        errors.append("Critical-Gate Declaration must include Critical-gate result")
    elif (result_match.group(1) == "FAIL") != failed:
        errors.append("Critical-gate result does not match the gate rows")
    return failed


def _corrections(section: str, current_loss: float | None, errors: list[str]) -> list[str]:
    rows = _table(section)
    expected = ["Item", "Source", "Points", "Status", "Action or Evidence"]
    if not rows or rows[0] != expected:
        errors.append("Lost Points and Correction Items must contain the standard correction table")
        return []

    statuses: list[str] = []
    unresolved_points = 0.0
    for row in rows[1:]:
        if len(row) != 5:
            errors.append("each correction item must contain five columns")
            continue
        item, source, points_text, status, action = row
        if not re.fullmatch(r"C\d{2,}", item):
            errors.append(f"invalid correction item ID: {item!r}")
        if not _is_evidence(source) or not _is_evidence(action):
            errors.append(f"correction item {item!r} needs source and action/evidence")
        points = _number(points_text, f"correction item {item} points", errors)
        normalized = status.upper()
        if normalized not in {"OPEN", "IN PROGRESS", "BLOCKED", "RESOLVED"}:
            errors.append(f"invalid correction status for {item}: {status!r}")
        if normalized != "RESOLVED" and points is not None:
            unresolved_points += points
        statuses.append(normalized)

    if current_loss is not None and abs(unresolved_points - current_loss) > 0.05:
        errors.append(
            "unresolved correction points "
            f"{unresolved_points:g} must equal current lost points {current_loss:g}"
        )
    return statuses


def _cycle_history(section: str, errors: list[str]) -> None:
    rows = _table(section)
    expected = [
        "Cycle",
        "Starting Score",
        "Findings",
        "Corrections",
        "Ending Score",
        "Validation Evidence",
        "Status",
    ]
    if not rows or rows[0] != expected or len(rows) < 2:
        errors.append("Correction-Cycle History must contain the standard table and one cycle")
        return
    for row in rows[1:]:
        if len(row) != 7:
            errors.append("each correction-cycle row must contain seven columns")
            continue
        if not re.fullmatch(r"\d+", row[0]):
            errors.append(f"invalid correction cycle number: {row[0]!r}")
        for index, name in ((1, "starting"), (4, "ending")):
            if row[index].lower() != "pending":
                _number(row[index], f"cycle {row[0]} {name} score", errors)
        if not all(_is_evidence(row[index]) for index in (2, 3, 5)):
            errors.append(f"cycle {row[0]} needs findings, corrections, and validation evidence")
        if row[6].upper() not in {"OPEN", "CLOSED", "BLOCKED"}:
            errors.append(f"invalid correction-cycle status: {row[6]!r}")


def validate_text(text: str) -> list[str]:
    """Return validation errors for one report string."""

    errors: list[str] = []
    report = _parse_report(text, errors)

    for key in REQUIRED_METADATA:
        if key not in report.metadata or not report.metadata[key]:
            errors.append(f"missing metadata: {key}")
    for section in REQUIRED_SECTIONS:
        if section not in report.sections:
            errors.append(f"missing section: {section}")
        elif not report.sections[section]:
            errors.append(f"empty section: {section}")

    if errors:
        return errors

    status = report.metadata["Final status"]
    if status not in FINAL_STATUSES:
        errors.append(f"invalid Final status: {status!r}")
    if not re.fullmatch(r"T\d{2}", report.metadata["Thread ID"]):
        errors.append("Thread ID must use TNN format")
    if not re.match(r"https://github\.com/.+?/issues/\d+$", report.metadata["Issue"]):
        errors.append("Issue must be a GitHub issue URL")
    if not report.metadata["Branch"].startswith("thread/"):
        errors.append("Branch must start with thread/")
    draft_pr = report.metadata["Draft PR"]
    pre_pr = draft_pr == "Pending (pre-PR)"
    if pre_pr and status != "CORRECTION IN PROGRESS":
        errors.append("Pending (pre-PR) is allowed only while correction is in progress")
    elif not pre_pr and not re.match(r"https://github\.com/.+?/pull/\d+$", draft_pr):
        errors.append("Draft PR must be a GitHub pull-request URL")

    self_score = _score(report.sections["Codex Self-Score"], "Codex Self-Score", False, errors)
    reviewer_score = _score(
        report.sections["ChatGPT Reviewer Score"], "ChatGPT Reviewer Score", True, errors
    )
    provisional, adjusted = _final_scores(report.sections["Final Score"], errors)
    gate_failed = _critical_gates(report.sections["Critical-Gate Declaration"], errors)

    if reviewer_score is None:
        if provisional is not None or adjusted is not None:
            errors.append("final scores must remain Pending until independent review is recorded")
    elif self_score is not None:
        expected_provisional = round(0.4 * self_score + 0.6 * reviewer_score, 1)
        if provisional is None or abs(provisional - expected_provisional) > 0.05:
            errors.append(
                f"provisional weighted score must be {expected_provisional:.1f} "
                "(0.40 self + 0.60 reviewer)"
            )
        expected_adjusted = min(expected_provisional, 79.0) if gate_failed else expected_provisional
        if adjusted is None or abs(adjusted - expected_adjusted) > 0.05:
            errors.append(f"gate-adjusted score must be {expected_adjusted:.1f}")

    scores = [score for score in (self_score, reviewer_score) if score is not None]
    current_loss = 100.0 - min(scores) if scores else None
    correction_statuses = _corrections(
        report.sections["Lost Points and Correction Items"], current_loss, errors
    )
    _cycle_history(report.sections["Correction-Cycle History"], errors)

    criteria = re.findall(
        r"^- \[([ xX])\]\s+(.+)$",
        report.sections["Acceptance-Criteria Evidence"],
        re.MULTILINE,
    )
    if not criteria:
        errors.append("Acceptance-Criteria Evidence must contain checklist items")
    if "evidence" not in report.sections["Acceptance-Criteria Evidence"].lower():
        errors.append("Acceptance-Criteria Evidence must reference evidence")

    complete_status = status == "100/100 — READY FOR APPROVAL"
    if complete_status:
        if self_score != 100 or reviewer_score != 100 or adjusted != 100:
            errors.append("100/100 status requires self, reviewer, and gate-adjusted scores of 100")
        if any(mark.strip().lower() != "x" for mark, _ in criteria):
            errors.append("100/100 status cannot contain unchecked acceptance criteria")
        if gate_failed is not False:
            errors.append("100/100 status requires every critical gate to pass")
        if any(item != "RESOLVED" for item in correction_statuses):
            errors.append("100/100 status requires all correction items resolved")
        if report.sections["Blockers"].strip().lower() not in {"none.", "none"}:
            errors.append("100/100 status cannot contain blockers")

    blocked_status = status == "BLOCKED — HUMAN DECISION REQUIRED"
    if blocked_status:
        blockers = report.sections["Blockers"].lower()
        for field in ("question:", "options:", "consequences:", "recommended decision:"):
            if field not in blockers:
                errors.append(f"blocked status requires {field[:-1]} details")
    elif any(item == "BLOCKED" for item in correction_statuses):
        errors.append("a blocked correction item requires BLOCKED — HUMAN DECISION REQUIRED status")

    return errors


def validate_path(path: Path) -> list[str]:
    """Read and validate one report path."""

    if not path.is_file():
        return ["file does not exist or is not a regular file"]
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ["file is not valid UTF-8"]
    return validate_text(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path, help="thread report Markdown files")
    args = parser.parse_args(argv)

    failed = False
    for path in args.reports:
        errors = validate_path(path)
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
