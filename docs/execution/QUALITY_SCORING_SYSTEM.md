# SmartCoat Execution Quality Scoring System

Report schema version: `smartcoat-execution-report-v2.0`

Policy version: 2.0 Draft

Authority: Parent issue #14, `EXECUTION_CONTROL_CENTER.md`, and assigned thread issue

## Purpose

This system makes implementation claims, evidence, independent review, lost
points, and corrections auditable across all ten execution threads. A score is a
structured judgment, not objective truth. Evidence and reviewer rationale remain
more important than the number.

The older `EXECUTION_THREAD_INDEX.md` contains a superseded minimum-score formula.
For this cycle the current parent issue and control center govern: self-score is
40% and independent ChatGPT review is 60% of the provisional weighted score.

## 100-Point Rubric

| Category | Points | Evidence required |
|---|---:|---|
| Correctness and evidence | 25 | Issue requirements mapped to outputs; claims tied to inspected sources, tests, or explicit proposals; defects and uncertainty stated |
| Scope and acceptance criteria | 20 | Owned-path status/diff, criterion-by-criterion checklist, non-goals preserved, no silent cross-thread work |
| Architecture and North-Star alignment | 15 | Named architecture/project decisions, impact statement, conflicts or follow-up issue |
| Verification, tests, or validation | 15 | Exact commands/methods, environment/dependencies, actual pass/fail/skip counts, known unrun checks |
| Security, privacy, and data governance | 10 | Data classification, secret/confidential-data check, threat or permission implications, synthetic-data statement |
| Documentation and traceability | 10 | Issue, branch, PR, files, report, decisions, evidence references, limitations and follow-ups |
| Maintainability and clarity | 5 | Local conventions, readable boundaries, reusable artifacts, focused comments/tests |
| **Total** | **100** | Every awarded point must be defensible |

Scores may use decimals, but each category must stay within its maximum. Each
deduction has a reason. Unsupported evidence earns no point merely because work
looks plausible.

## Score Sources and Calculation

1. **Codex Self-Score:** implementation engineer's evidence-based assessment.
2. **ChatGPT Reviewer Score:** independent assessment recorded separately; it
   must not be pre-filled or inferred by Codex. Use a full category table when
   the reviewer published category awards. When the authoritative review
   published only a total, preserve it without invention as `Reviewer total`
   plus a dated PR-review evidence reference.
3. **Provisional weighted score:**

```text
round(0.40 * Codex Self-Score + 0.60 * ChatGPT Reviewer Score, 1)
```

4. **Gate-adjusted score:** provisional score when all gates pass; otherwise the
   lower of provisional score and `79.0`.
5. **Accepted score:** gate-adjusted score accepted after review/corrections. It
   is not final merely because arithmetic exists.

Until independent review is recorded, both final-score fields are `Pending`.
The weighted score measures provisional performance; it does **not** define the
correction burden. Before independent review, correction points equal Codex
self-deductions. After independent review, correction points equal reviewer
deductions, because reviewer findings are the authoritative work queue until a
later independent review replaces them.

## Critical Gates

| Gate | Failure examples | Effect |
|---|---|---|
| G1 Verified claims | Unrun command claimed passed; proposal stated as implemented | Cap at 79 |
| G2 Confidential data | Secret, personal, proprietary, raw industrial data committed | Stop, contain, cap at 79 |
| G3 Approved scope and architecture | Unapproved identity/core change or unsafe scope expansion | Cap at 79 |
| G4 Required validation | Required test/check missing, fabricated, or materially failing | Cap at 79 |
| G5 File ownership | Unsafe edit outside issue-owned paths | Cap at 79 |
| G6 Acceptance completeness | Incomplete criterion claimed complete | Cap at 79 |

Each gate is explicitly `PASS` or `FAIL` with evidence. A high weighted score
cannot override a failure. A failure remains visible in cycle history after it is
corrected.

## Lost Points and Corrections

Every current lost point maps to a numbered correction item with source, points,
status, and concrete action/evidence. Allowed statuses are `OPEN`, `IN PROGRESS`,
`BLOCKED`, and `RESOLVED`. Before independent review, unresolved correction
points must equal:

```text
100 - Codex Self-Score
```

After independent review they must equal:

```text
100 - ChatGPT Reviewer Score
```

Resolved historical items remain in the table but no longer count toward current
lost points. Review findings override optimistic self-assessment. One item may
cover several points only when its rationale identifies the full deduction.

## Correction Cycle

1. Inspect issue, sources, branch, and owned paths.
2. Plan and implement only approved scope.
3. Run validation and record actual results, including failures.
4. Complete self-score and critical gates.
5. Convert every self-deduction into correction items.
6. Perform internal second-pass review, correct, and rerun checks.
7. Open/update the draft PR and request independent review.
8. Record reviewer score and every reviewer deduction.
9. Resolve feasible corrections on the same branch and rerun validation.
10. Repeat until `100/100` within approved scope or a human-decision blocker.

Cycle history records starting/ending scores, findings, corrections, validation
evidence, and `OPEN`, `CLOSED`, or `BLOCKED` state. Do not erase earlier cycles.

## Status Rules

- `READY FOR INDEPENDENT REVIEW`: first-pass implementation and internal
  validation are ready; a real draft PR URL is required.
- `READY FOR INDEPENDENT RE-REVIEW`: reviewer corrections are implemented and
  locally validated, but the prior reviewer score remains authoritative.
- `CORRECTION IN PROGRESS`: work or a correction is active. `Pending (pre-PR)` is
  allowed only in this state.
- `100/100 — READY FOR APPROVAL`: self, reviewer, weighted and gate-adjusted
  scores are 100; all criteria checked; all gates pass; all items resolved; no blocker.
- `BLOCKED — HUMAN DECISION REQUIRED`: report the exact question, options,
  consequences, and recommended decision. A blocker is not hidden as a low score.

`100/100` means complete against the approved issue and rubric, not universal
perfection. Out-of-scope futures may be follow-up issues; unresolved in-scope
defects, missing required validation, or unchecked criteria prevent 100.

Ready-for-review and ready-for-re-review reports must have every in-scope
acceptance criterion checked. A correction may be implemented locally while its
reviewer-sourced item remains `IN PROGRESS` until independent re-review verifies
closure.

## Schema Version and Migration

Every report declares `Report schema version:
smartcoat-execution-report-v2.0`. The v2 validator does not silently reinterpret
legacy reports. A v1 or unversioned report must be explicitly normalized, retain
its historical scores, gates, and cycles, and then pass v2 validation. Future
breaking changes require a new schema version and documented migration.

The quality system is not considered adopted by the ten-thread wave until the
validator runs against exactly ten actual reports with zero errors. Use
`--require-count 10` for that integration evidence.

## Validator Contract

`scripts/validate_execution_reports.py` checks:

- metadata, exact report schema version, valid status, issue/branch/PR forms
- seven category rows, fixed maxima totaling 100, numeric ranges and evidence
- independent reviewer pending or a complete reviewer scorecard
- weighted calculation and critical-gate cap
- all six gate declarations and evidence
- acceptance checklist and evidence language
- reviewer-based correction burden after review and self-based burden before it
- duplicate correction/cycle IDs and prohibited escaped pipes in table cells
- existing backticked repository paths in `Files Changed`
- exact commands plus structured actual-result declarations
- correction-cycle structure and blocker details
- strict `100/100` completion conditions

Usage:

```bash
python scripts/validate_execution_reports.py --require-count 10 REPORT_1 ... REPORT_10
```

The command exits `0` only when every supplied report validates; otherwise it
prints report-specific errors and exits `1`. It uses only the Python standard
library. Tests use synthetic reports and contain no industrial data.

Escaped Markdown pipes (`\|`) are prohibited inside standard table rows because
the v2 parser uses a strict, auditable table grammar. Use words, commas, or a
non-table paragraph instead.
