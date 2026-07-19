# TXX Thread Report

Report schema version: `smartcoat-execution-report-v2.0`

Thread ID: TXX

Issue: https://github.com/OWNER/REPOSITORY/issues/NN

Branch: `thread/NN-name`

Draft PR: Pending (pre-PR)

Final status: `CORRECTION IN PROGRESS`

## Objective

State the approved issue objective and bounded outcome.

## Files Changed

- List every created/modified path and confirm ownership.

## Methods and Commands Executed

- `exact command`
- Describe non-command review/validation methods precisely.

## Actual Results

| Method or Command | Actual Result | Evidence |
|---|---|---|
| | PASS / FAIL / SKIP / BLOCKED / NOT RUN: count or outcome | output, log, file, or explicit observation |

Every result starts with one allowed status. Never write a planned result as
actual.

## Acceptance-Criteria Evidence

- [ ] Criterion copied or faithfully summarized.
  Evidence: file, line, command/result, PR artifact, or explicit blocker.

## Architecture Impact

Name aligned decisions and any conflict, migration, or follow-up. Write `None`
only with a reason.

## Security and Data Impact

State data type, confidentiality, secrets check, permission/security effects, and
whether examples are synthetic/generalized.

## Known Limitations

- Include unresolved technical, evidence, environment, and scope limitations.

## Lost Points and Correction Items

| Item | Source | Points | Status | Action or Evidence |
|---|---|---:|---|---|
| C01 | | | OPEN | |

Before independent review, unresolved points equal `100 - self-score`. After
review, they equal `100 - reviewer-score`; the weighted score is not the
correction burden. Keep locally implemented reviewer items `IN PROGRESS` until
independent re-review verifies closure.

## Codex Self-Score

Insert the complete standard scorecard from `THREAD_SCORECARD_TEMPLATE.md`.

## ChatGPT Reviewer Score

Reviewer status: Pending independent review.

After review, use the full scorecard when category awards were published. If the
authoritative review contains only a total, replace the pending line with:

```text
Reviewer total: NN

Reviewer evidence: GitHub PR #NN review, cycle and date.
```

## Final Score

Provisional weighted score: Pending

Gate-adjusted score: Pending

## Critical-Gate Declaration

Insert all six standard gate rows and `Critical-gate result: PASS` or `FAIL`.

## Correction-Cycle History

| Cycle | Starting Score | Findings | Corrections | Ending Score | Validation Evidence | Status |
|---:|---:|---|---|---:|---|---|
| 1 | | | | | | OPEN |

## Recommended Follow-up Issues

- Record out-of-scope work with owner, rationale, and acceptance direction.

## Blockers

None.

For a human blocker, replace `None` with the four required fields in
`CORRECTION_CYCLE_TEMPLATE.md`.

Standard table cells must not contain escaped Markdown pipes. Use words, commas,
or prose outside the table. Every backticked path in `Files Changed` must exist
in the report's branch.

## PR Summary Template

```markdown
## Summary
- Approved scope and user/system outcome

## Files
- Owned paths only

## Validation
- Exact command: actual result

## Scores and gates
- Codex self-score: NN/100
- ChatGPT reviewer score: Pending or NN/100
- Provisional/gate-adjusted: Pending or NN.N/100
- Critical gates: PASS/FAIL with named failures

## Corrections and limitations
- Open/resolved items and human blockers

Closes #NN
```
