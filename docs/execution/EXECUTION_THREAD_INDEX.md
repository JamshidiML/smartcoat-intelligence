# SmartCoat Multi-Thread Execution Dashboard

Version: 1.0

Status: Ready for Codex Execution

Last updated: 2026-07-15

---

## Purpose

This is the central navigation and evaluation page for SmartCoat's first multi-thread execution cycle.

Each Execution Thread is a separate GitHub Issue with bounded scope, acceptance criteria, a 100-point rubric, and an iterative improvement loop.

The ten threads are designed to proceed in parallel with minimal file overlap.

---

## Operating Model

```text
Mohsen — Product Owner and Domain Authority
        ↓
ChatGPT — Orchestrator, Product Architect, Technical Reviewer
        ↓
Codex — Parallel Implementation and Audit Threads
        ↓
Thread-specific Branches and Pull Requests
        ↓
Self-score by Codex
        ↓
Independent Review Score by ChatGPT
        ↓
Gap Analysis
        ↓
Revision Loop
        ↓
Final Approval or Further Iteration
```

---

## Thread Dashboard

| Thread | Scope | Issue | Codex Score | Review Score | Final Score | Loop Count | Status |
|---:|---|---|---:|---:|---:|---:|---|
| 01 | North Star and mother-platform alignment | [Open Thread 01](https://github.com/JamshidiML/smartcoat-intelligence/issues/4) | — | — | — | 0 | Ready |
| 02 | Repository documentation synchronization | [Open Thread 02](https://github.com/JamshidiML/smartcoat-intelligence/issues/5) | — | — | — | 0 | Ready |
| 03 | CI and quality-gate baseline | [Open Thread 03](https://github.com/JamshidiML/smartcoat-intelligence/issues/6) | — | — | — | 0 | Ready |
| 04 | Docker and PostgreSQL connectivity | [Open Thread 04](https://github.com/JamshidiML/smartcoat-intelligence/issues/7) | — | — | — | 0 | Ready |
| 05 | Persistence contract and repository consistency | [Open Thread 05](https://github.com/JamshidiML/smartcoat-intelligence/issues/8) | — | — | — | 0 | Ready |
| 06 | Persistent API integration tests | [Open Thread 06](https://github.com/JamshidiML/smartcoat-intelligence/issues/9) | — | — | — | 0 | Ready |
| 07 | API contract, validation, and collection behavior | [Open Thread 07](https://github.com/JamshidiML/smartcoat-intelligence/issues/10) | — | — | — | 0 | Ready |
| 08 | Security, confidentiality, and data boundary | [Open Thread 08](https://github.com/JamshidiML/smartcoat-intelligence/issues/11) | — | — | — | 0 | Ready |
| 09 | Technical-textile pilot data inventory and mapping | [Open Thread 09](https://github.com/JamshidiML/smartcoat-intelligence/issues/12) | — | — | — | 0 | Ready |
| 10 | Living Factory reference architecture and roadmap | [Open Thread 10](https://github.com/JamshidiML/smartcoat-intelligence/issues/13) | — | — | — | 0 | Ready |

---

## File-Ownership Boundaries

These boundaries reduce merge conflicts.

| Thread | Primary Ownership |
|---:|---|
| 01 | `docs/strategy/`, selected top-level project identity documents, thread report |
| 02 | `README.md`, `ROADMAP.md`, `CHANGELOG.md`, architecture indexes and navigation, thread report |
| 03 | `.github/workflows/`, quality configuration when required, thread report |
| 04 | `docker-compose.yml`, Docker-specific environment/setup documentation, connectivity tests, thread report |
| 05 | `src/smartcoat/storage/repositories/`, focused persistence tests, thread report |
| 06 | PostgreSQL-backed integration-test infrastructure and files, thread report |
| 07 | `src/smartcoat/api/`, API-focused tests, thread report |
| 08 | Security and data-governance documents, `.gitignore` review, safe-fixture guidance, thread report |
| 09 | Pilot inventory, source mapping, synthetic examples, thread report; no raw industrial data |
| 10 | Living Factory reference architecture and execution-roadmap documents, thread report |

A thread must not modify another thread's primary files without posting a coordination comment first.

---

## Required Branch Model

Each thread uses a dedicated branch created from:

```text
release/1.7-project-reset
```

Recommended branches:

```text
thread/01-north-star
thread/02-doc-sync
thread/03-ci-quality
thread/04-docker-postgres
thread/05-persistence-contract
thread/06-persistent-api-tests
thread/07-api-contract
thread/08-security-boundary
thread/09-pilot-data-inventory
thread/10-living-factory-architecture
```

Each thread opens a separate draft Pull Request targeting:

```text
release/1.7-project-reset
```

No thread merges automatically.

---

## Scoring Model

Every task is evaluated out of 100 using its issue-specific rubric.

### Score Sources

1. **Codex Self-Score**
   - Codex evaluates its work against every rubric category.
   - Each deduction must include a reason and evidence.

2. **ChatGPT Review Score**
   - Independent architecture, product, security, test, and quality review.
   - A score may be lower than Codex's self-score.

3. **Final Score**

```text
Final Score = min(Codex Self-Score, ChatGPT Review Score)
```

The minimum is used to prevent optimistic self-evaluation from hiding unresolved weaknesses.

### Score Meaning

| Score | Meaning | Action |
|---:|---|---|
| 98–100 | Excellent and release-ready | Eligible for approval |
| 95–97 | Strong with only minor documented limitations | Eligible for approval after review |
| 90–94 | Useful but needs another correction loop | Revise |
| 80–89 | Significant gaps | Major revision |
| <80 | Not acceptable | Rework from findings |

### Completion Gate

A thread is not complete merely because its code or document exists.

Minimum completion conditions:

- Final Score >=95
- no unresolved critical security issue
- no false claim of completed functionality
- required tests or evidence are present
- documentation is linked
- PR has been reviewed

A score of 100 is aspirational, not cosmetic. It may only be assigned when every rubric category is fully supported by evidence and there are no known unresolved deductions within scope.

---

## Iterative Correction Loop

Each thread must follow this cycle:

```text
1. Inspect and reproduce
2. Plan bounded work
3. Implement or document
4. Run tests/checks
5. Codex self-score
6. List deductions and unresolved risks
7. Correct every feasible deduction
8. Re-run tests/checks
9. Re-score
10. Open/update draft PR
11. ChatGPT independent review
12. Convert review findings into a correction checklist
13. Codex revises
14. Repeat until Final Score >=95 or a human decision blocks further improvement
```

Maximum automation does not mean bypassing judgment. Stop and request a decision when a change affects product identity, confidential data, destructive migration, safety, legal exposure, or core architecture.

---

## Required Thread Report Template

Every `docs/execution/thread-XX-...-report.md` must contain:

```markdown
# Thread XX Report

## Objective
## Scope
## Inputs Reviewed
## Work Completed
## Files Changed
## Commands and Tests Executed
## Actual Results
## Confirmed Findings
## Rejected or Unconfirmed Suspicions
## Architecture Impact
## Security and Data Impact
## Known Limitations
## Deferred Work

## Codex Self-Score
| Criterion | Maximum | Awarded | Evidence | Deduction Reason |

## Correction Loops
| Loop | Starting Score | Changes Made | Ending Score |

## Final Status
## Pull Request
```

---

## Final Cycle Summary

After all threads reach a reviewable state, create:

```text
docs/execution/CYCLE_01_SUMMARY.md
```

It must include:

- one-paragraph result for each thread
- links to every issue, report, branch, and PR
- Codex score, ChatGPT score, final score, and loop count
- changes merged
- changes deferred
- conflicts between threads
- unresolved architectural decisions
- readiness assessment for controlled industrial-data ingestion
- recommended next ten threads

---

## Industrial Data Ingestion Gate

Real technical-textile data ingestion must not begin until, at minimum:

- Thread 08 defines and passes the security/data boundary
- Thread 09 defines approved source inventory and canonical mapping
- persistent storage and integration tests are stable
- an explicit data owner approves the selected pilot data
- raw source files remain outside the source-code repository
- ingestion uses a controlled, reversible, provenance-preserving process

---

## Current Cycle Goal

Cycle 01 does not build the full Living Factory.

It establishes the strategic, documentary, technical, security, and pilot-data foundation required to move safely and quickly toward the first controlled technical-textile ingestion and later Living Factory capabilities.
