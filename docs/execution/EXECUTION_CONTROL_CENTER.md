# SmartCoat Execution Control Center

Version: 1.0

Status: Ready to Launch

Parent orchestration issue: [#14 — Execution Control Center](https://github.com/JamshidiML/smartcoat-intelligence/issues/14)

Baseline branch: `release/1.7-project-reset`

Target integration branch: `release/1.7-project-reset`

---

## Purpose

This document is the navigation and status center for SmartCoat's first ten parallel execution threads.

Each thread runs as an independent Codex task in a dedicated environment and branch. Each thread opens a draft pull request, produces evidence and a scorecard, receives independent ChatGPT review, and enters a correction loop until it reaches 100/100 within the approved scope or records a human-decision blocker.

No thread may merge automatically.

---

## Execution Model

```text
Founder direction and approved North Star
                ↓
Execution Control Center
                ↓
10 independent Codex threads
                ↓
Dedicated branch + owned paths + draft PR
                ↓
Codex evidence and self-score
                ↓
ChatGPT review and score
                ↓
Lost points become correction items
                ↓
Correction cycle and re-validation
                ↓
100/100 within scope or human-decision blocker
                ↓
Reviewed integration into Release 1.7
```

---

## Thread Dashboard

| ID | Thread | GitHub Issue | Branch | Primary Output | Status | Codex Score | ChatGPT Score | Final |
|---|---|---|---|---|---|---:|---:|---:|
| T01 | Living Industry North Star and Mother Platform | [#15](https://github.com/JamshidiML/smartcoat-intelligence/issues/15) | `thread/01-living-industry-north-star` | `docs/strategy/LIVING_INDUSTRY_PLATFORM_MODEL.md` | Ready | — | — | — |
| T02 | Repository documentation synchronization | [#16](https://github.com/JamshidiML/smartcoat-intelligence/issues/16) | `thread/02-documentation-synchronization` | Root docs, roadmap, changelog, indexes | Ready | — | — | — |
| T03 | Reproducible engineering baseline and CI | [#17](https://github.com/JamshidiML/smartcoat-intelligence/issues/17) | `thread/03-engineering-baseline-ci` | CI, PR template, engineering baseline | Ready | — | — | — |
| T04 | Persistence and API contracts | [#18](https://github.com/JamshidiML/smartcoat-intelligence/issues/18) | `thread/04-persistence-api-contracts` | Persistent API fixes and integration tests | Ready | — | — | — |
| T05 | Technical Textiles Canonical Schema v1 | [#19](https://github.com/JamshidiML/smartcoat-intelligence/issues/19) | `thread/05-technical-textile-canonical-schema` | Human- and machine-readable pilot schemas | Ready | — | — | — |
| T06 | Data-source inventory and readiness | [#20](https://github.com/JamshidiML/smartcoat-intelligence/issues/20) | `thread/06-data-source-inventory-readiness` | Source register and readiness matrix | Ready | — | — | — |
| T07 | Data governance and human oversight | [#21](https://github.com/JamshidiML/smartcoat-intelligence/issues/21) | `thread/07-data-governance-human-oversight` | Governance, confidentiality, autonomy levels | Ready | — | — | — |
| T08 | Generic ingestion foundation prototype | [#22](https://github.com/JamshidiML/smartcoat-intelligence/issues/22) | `thread/08-ingestion-foundation-prototype` | Manifest validation and provenance prototype | Ready | — | — | — |
| T09 | Technical-textile living-factory pilot blueprint | [#23](https://github.com/JamshidiML/smartcoat-intelligence/issues/23) | `thread/09-technical-textile-pilot-blueprint` | Pilot, metrics, investor/customer proof plan | Ready | — | — | — |
| T10 | Quality scorecards and correction-loop validation | [#24](https://github.com/JamshidiML/smartcoat-intelligence/issues/24) | `thread/10-execution-scorecards-loop` | Rubric, templates, validator, tests | Ready | — | — | — |

---

## Thread Independence Matrix

The threads are designed to minimize merge conflicts.

| Thread | Primary Ownership | Must Not Modify |
|---|---|---|
| T01 | New strategy model and its report | Root docs, code, schemas |
| T02 | Root docs, roadmap, changelog, indexes | Application code, schemas, governance |
| T03 | CI, PR template, engineering baseline | Application behavior, persistence code |
| T04 | API, services, repositories, persistence tests | CI, schemas, ingestion, root docs |
| T05 | Technical-textile schema docs and machine-readable schemas | App models, migrations, ingestion code |
| T06 | Source inventory, readiness templates | Raw data, schemas, ingestion code |
| T07 | Governance and oversight documents | Existing security policy, code, schemas |
| T08 | New ingestion module, tests, synthetic examples | Existing API, DB, schemas, raw data |
| T09 | Pilot and proof-package documents | Code, schemas, governance policies |
| T10 | Scoring docs, templates, validator, validator tests | Product code, CI, other thread reports |

If a thread discovers a required change outside its ownership, it must document the finding and recommend a separate issue instead of editing the file silently.

---

## Quality Rubric — 100 Points

| Category | Points |
|---|---:|
| Correctness and evidence | 25 |
| Scope and acceptance criteria | 20 |
| Architecture and North-Star alignment | 15 |
| Verification, tests, or validation | 15 |
| Security, privacy, and data governance | 10 |
| Documentation and traceability | 10 |
| Maintainability and clarity | 5 |
| **Total** | **100** |

### Provisional Score

```text
Provisional Score = 0.40 × Codex Self-Score + 0.60 × ChatGPT Review Score
```

The final accepted score is determined after critical-gate checks and correction cycles.

### Critical Gates

Any critical-gate failure caps the score at 79 until corrected:

- unverified claim presented as fact
- secret or confidential data committed
- unapproved change to product identity or core architecture
- missing required verification or tests
- unsafe cross-thread file ownership violation
- acceptance criteria claimed complete when they are not complete

---

## Correction Loop

For every review cycle:

1. Codex implements and validates.
2. Codex records evidence and self-score.
3. Codex opens or updates a draft PR.
4. ChatGPT reviews independently.
5. Every lost point is converted into a numbered correction item.
6. Codex corrects on the same branch.
7. Commands, tests, validation, and documentation are rerun.
8. Scores and evidence are updated.
9. Repeat until 100/100 within approved scope.

If a missing external decision prevents completion, the thread status becomes:

```text
BLOCKED — HUMAN DECISION REQUIRED
```

The report must state the exact question, options, consequences, and recommended decision.

---

## Required Thread Outputs

Every thread must produce:

- the owned deliverable files
- a thread report under `docs/execution/reports/`
- actual commands or validation methods used
- evidence for acceptance criteria
- Codex self-score
- gap list
- correction-cycle history
- known limitations
- recommended follow-up issues
- a draft PR targeting `release/1.7-project-reset`

---

## Industrial Data Safety Boundary

This execution wave prepares SmartCoat for controlled technical-textile data ingestion.

It does **not** authorize ingestion or commitment of:

- proprietary formulations
- customer-identifiable data
- supplier-confidential information
- prices or contracts
- employee personal data
- internal email content
- raw meeting or voice recordings
- unpublished inventions or R&D reports
- production datasets
- credentials or secrets

Use synthetic, generalized, anonymized, or metadata-only examples until the governance and approval gates are accepted.

---

## Launch Instructions

Open ten Codex tasks in parallel.

For each task:

1. Select `JamshidiML/smartcoat-intelligence`.
2. Use `release/1.7-project-reset` as the baseline.
3. Assign exactly one issue from #15–#24.
4. Tell Codex to read `AGENTS.md`, the assigned issue, and required project documents.
5. Require a dedicated branch and draft PR.
6. Do not allow automatic merge.

The master launch prompt is stored in:

`docs/execution/CODEX_10_THREAD_MASTER_PROMPT.md`

---

## Completion Summary

When all threads reach an accepted state, this dashboard will be updated with:

- PR links
- Codex scores
- ChatGPT scores
- final scores
- correction-cycle counts
- accepted outputs
- blocked decisions
- integration order
- Release 1.7 readiness conclusion
