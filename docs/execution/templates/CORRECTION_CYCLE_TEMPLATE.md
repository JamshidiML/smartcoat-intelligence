# Correction Cycle Template

## Lost Points and Correction Items

Before review, unresolved points equal `100 - self-score`. After review, they
equal `100 - reviewer-score`; do not derive them from the weighted score. Keep
resolved items for history and give each item an evidence-based source and
testable completion action.

| Item | Source | Points | Status | Action or Evidence |
|---|---|---:|---|---|
| C01 | Self-score category or review finding | | OPEN | |

Allowed item statuses: `OPEN`, `IN PROGRESS`, `BLOCKED`, `RESOLVED`.
IDs must be unique. A locally corrected reviewer item remains `IN PROGRESS` until
independent re-review verifies it.

## Correction-Cycle History

| Cycle | Starting Score | Findings | Corrections | Ending Score | Validation Evidence | Status |
|---:|---:|---|---|---:|---|---|
| 1 | | | | | | OPEN |

Allowed cycle statuses: `OPEN`, `CLOSED`, `BLOCKED`.
Cycle numbers must be unique and historical rows must not be overwritten.

## Human-Decision Blocker

Use only with final status `BLOCKED — HUMAN DECISION REQUIRED`:

```text
Question:
Options:
Consequences:
Recommended decision:
```

Do not classify an engineering task as a human blocker merely because it is hard,
slow, or would benefit from clarification.
