# Release 1.8 Execution Control Center

Release: Knowledge Capture Core

Parent issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/38

Branch: `release/1.8-knowledge-capture-core`

Status: Definition and issue setup

## Release Objective

Deliver a governed, persistent, auditable, filterable, paginated Knowledge Object backend on PostgreSQL with structured evidence, provenance, lifecycle, concurrency, and minimum context.

## Operating Rules

- Every non-trivial change begins from an issue.
- Every thread uses a dedicated branch and draft PR targeting the Release 1.8 branch.
- No direct commits to `main`.
- No real or confidential industrial data.
- No UI, AI extraction, semantic search, ERP, email, or bulk-ingestion expansion.
- No self-approval of architecture, governance, security, or release completion.
- Codex reports actual commands and results; unexecuted checks are `NOT RUN`.
- ChatGPT performs independent review and assigns the authoritative reviewer score.
- Threads remain open until accepted within scope or blocked by a documented human decision.

## Scoring Contract

| Category | Points |
|---|---:|
| Correctness and evidence | 25 |
| Scope and acceptance criteria | 20 |
| Architecture and release alignment | 15 |
| Verification and tests | 15 |
| Security, privacy, and governance | 10 |
| Documentation and traceability | 10 |
| Maintainability and clarity | 5 |
| Total | 100 |

Provisional score:

`0.40 × Codex self-score + 0.60 × independent reviewer score`

Critical-gate failure caps the thread at 79 until correction and independent re-review.

## Critical Gates

- G1: Claims are supported by executed evidence.
- G2: No secrets or confidential industrial data are included.
- G3: Scope and architecture remain approved.
- G4: Required validation is executed and honestly reported.
- G5: File ownership and cross-thread boundaries are respected.
- G6: Acceptance criteria are complete.
- G7: Persistence changes include migration/model alignment and PostgreSQL evidence.
- G8: Lifecycle, trust, and audit controls cannot be bypassed by generic updates.

## Thread Register

| Thread | Issue | Scope | Primary Dependency | Status |
|---|---|---|---|---|
| T01 | Pending | Release contracts, ADRs, lifecycle semantics | Release definition | Not started |
| T02 | Pending | Knowledge Object v2 | T01 | Not started |
| T03 | Pending | Evidence and provenance | T01, T02 | Not started |
| T04 | Pending | Lifecycle and controlled mutation | T01, T02 | Not started |
| T05 | Pending | Persistence, migrations, repository CRUD | T02, T03, T04, #35 | Not started |
| T06 | Pending | Filtering, sorting, cursor pagination | T02, T05 | Not started |
| T07 | Pending | Audit events and history | T04, T05 | Not started |
| T08 | Pending | Minimum domain context references | T01, T02 | Not started |
| T09 | Pending | API contracts and end-to-end route behavior | T03–T08 | Not started |
| T10 | Pending | Engineering gates, #36, integration and release evidence | All threads | Not started |

## Planned Integration Order

1. T01
2. T02
3. T03
4. T08
5. T04
6. T07
7. T05
8. T06
9. T09
10. T10

The order may change only with a documented dependency reason and independent review.

## Shared Contract Decisions

The following are shared contracts and must not be independently redefined by implementation threads:

- lifecycle names and meanings
- transition matrix
- Knowledge Object identity and revision semantics
- evidence and provenance boundaries
- audit-event requirements
- pagination contract
- deletion/deprecation policy
- minimum context boundary
- production-security and real-data exclusions

## Integration Acceptance

The integrated candidate must run:

- constrained Python 3.12 installation
- `python -m pip check`
- full pytest
- MyPy for `src`
- bounded Ruff and format checks, with issue #36 handled explicitly
- migration upgrade and downgrade validation
- exact PostgreSQL API round trip
- transition and concurrency conflict matrix
- evidence/provenance round trip
- cursor pagination invariants
- audit-history invariants
- report validation
- Markdown and index checks
- secret, `.env`, binary, and confidential-data scans
- `git diff --check`

## Stop Conditions

Stop and request a human decision when work would introduce confidential data, destructive migration, production IAM claims, a new database, UI or AI scope, semantic retrieval, full ontology expansion, or automatic trust without human approval.
