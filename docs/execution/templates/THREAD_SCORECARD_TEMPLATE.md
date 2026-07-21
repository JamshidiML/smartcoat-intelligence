# Thread Scorecard Template

Use this component twice: once for `Codex Self-Score` and once after independent
review for `ChatGPT Reviewer Score`. Do not copy the self-score into the reviewer
table. Until review, write `Reviewer status: Pending independent review.`

When the authoritative reviewer published only a total, do not invent category
awards. Use `Reviewer total: NN` and `Reviewer evidence: <dated PR review>`.

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | | | |
| Scope and acceptance criteria | 20 | | | |
| Architecture and North-Star alignment | 15 | | | |
| Verification, tests, or validation | 15 | | | |
| Security, privacy, and data governance | 10 | | | |
| Documentation and traceability | 10 | | | |
| Maintainability and clarity | 5 | | | |
| Total | 100 | | | |

## Final Score Component

```text
Provisional weighted score: Pending

Gate-adjusted score: Pending
```

After independent review, replace `Pending` with one-decimal values:

```text
Provisional weighted score = round(0.40 * self + 0.60 * reviewer, 1)
Gate-adjusted score = provisional, or min(provisional, 79.0) when a gate failed
```

The weighted score is a provisional performance measure only. Correction points
equal self-deductions before review and reviewer deductions after review.

## Critical-Gate Component

| Gate | Status | Evidence |
|---|---|---|
| G1 Verified claims | PASS / FAIL | |
| G2 Confidential data | PASS / FAIL | |
| G3 Approved scope and architecture | PASS / FAIL | |
| G4 Required validation | PASS / FAIL | |
| G5 File ownership | PASS / FAIL | |
| G6 Acceptance completeness | PASS / FAIL | |

Critical-gate result: PASS / FAIL
