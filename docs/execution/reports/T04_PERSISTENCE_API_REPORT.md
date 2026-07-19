# T04 Persistence and API Report

Report schema version: `smartcoat-execution-report-v2.0`

Thread ID: T04

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/18

Branch: `thread/04-persistence-api-contracts`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/26

Final status: `READY FOR INDEPENDENT RE-REVIEW`

## Objective

Reproduce, document, and correct confirmed inconsistencies in the FastAPI to
service to repository to PostgreSQL to domain-object path.

## Files Changed

- `src/smartcoat/api/routes/decisions.py`
- `src/smartcoat/api/routes/events.py`
- `src/smartcoat/api/routes/knowledge.py`
- `src/smartcoat/storage/repositories/event_repository.py`
- `src/smartcoat/storage/repositories/mappers.py`
- `tests/test_api_persistent_routes.py`
- `tests/test_event_repository_contract.py`
- `tests/integration/test_persistent_api_postgres.py`
- `docs/implementation/PERSISTENCE_API_CONTRACTS.md`
- `docs/execution/reports/T04_PERSISTENCE_API_REPORT.md`

All paths are owned by issue #18.

## Methods and Commands Executed

- `python -m pip install --constraint ../T03/requirements/constraints-py312.txt -e '.[dev]'`
- `python -m pip install --constraint ../T03/requirements/constraints-py312.txt httpx2`
- `python -m pip check`
- `python -m mypy src`
- `python -m pytest -q`
- `python -m pytest -q tests/test_api_persistent_routes.py tests/test_event_repository_contract.py tests/test_persistence_mappers.py`
- `python -m pytest -q tests/integration/test_persistent_api_postgres.py`
- `python -m ruff check src/smartcoat/api src/smartcoat/services src/smartcoat/storage/repositories tests/test_api_persistent_routes.py tests/test_event_repository_contract.py tests/test_persistence_mappers.py tests/integration/test_persistent_api_postgres.py`
- `python -m ruff format --check src/smartcoat/api src/smartcoat/services src/smartcoat/storage/repositories tests/test_api_persistent_routes.py tests/test_event_repository_contract.py tests/test_persistence_mappers.py tests/integration/test_persistent_api_postgres.py`
- `SMARTCOAT_RUN_LIVE_POSTGRES_TESTS=true SMARTCOAT_TEST_DATABASE_URL=postgresql+psycopg://smartcoat:smartcoat@localhost:5432/smartcoat SMARTCOAT_TEST_SCHEMA=smartcoat_test_t04_cycle3_20260719 python -m pytest -q tests/integration/test_persistent_api_postgres.py`
- `docker exec smartcoat_postgres psql -U smartcoat -d smartcoat -Atc "SELECT COUNT(*) FROM pg_namespace WHERE nspname LIKE 'smartcoat_test_t04_cycle3_20260719%';"`
- `git diff --check`

## Actual Results

| Method or Command | Actual Result | Evidence |
|---|---|---|
| Constrained environment | PASS: Python 3.12.13 and no broken requirements | T03 constraints plus its declared `httpx2` dev dependency. |
| MyPy | PASS: no issues in 41 source files | Cycle 3 output. |
| Full local test suite | PASS: 19 tests; 3 live tests skipped without opt-in | Cycle 3 output. |
| Focused unit/API tests | PASS: 12 tests in 5.83 seconds | Cycle 3 output. |
| Scoped Ruff | PASS: all owned API, service, repository, and test paths | Cycle 3 output. |
| Scoped format check | PASS: 22 files already formatted | Cycle 3 output. |
| PostgreSQL test without URL | PASS: 2 guard tests; 3 live tests skipped | No database connection or mutation attempted. |
| First sandboxed live run | BLOCKED: localhost operation not permitted | Expected sandbox network boundary. |
| First approved live run | BLOCKED: Docker daemon was stopped | Connection refused; no success claimed. |
| Isolated PostgreSQL integration | PASS: 5 tests in 0.95 seconds | Approved localhost run against PostgreSQL 16 container. |
| Partial-failure cleanup | PASS: registered row absent after induced exception | Live integration assertion. |
| HTTP/list round trip | PASS: all three synthetic object types persisted and returned | Live integration assertions. |
| Schema teardown | PASS: fixture and dedicated probe each query `pg_namespace`; external query also returned zero matching schemas | Live and independent PostgreSQL catalog assertions. |
| Migration follow-up | PASS: issue #35 opened with executable acceptance criteria | Separate from ORM/API compatibility evidence. |
| Owned-path check | PASS: ten changed paths, all T04-owned | Branch diff against release baseline. |
| `git diff --check` | PASS: no whitespace errors | Cycle 3 command output. |

## Acceptance-Criteria Evidence

- [x] Distinguish confirmed defects, missing tests, and deferred improvements.
  Evidence: persistence/API contract document and correction history.
- [x] Return canonical domain objects from repositories.
  Evidence: EventRepository mappings and MyPy result.
- [x] Validate the HTTP-to-PostgreSQL path with synthetic data.
  Evidence: live create/get/list tests for knowledge, decisions, and events.
- [x] Make cleanup failure-safe.
  Evidence: immediate registration and induced partial-failure test.
- [x] Add explicit API list limits.
  Evidence: 1-500 validation in all collection routes and route tests.
- [x] Preserve existing architecture and feature scope.
  Evidence: no new entity, route family, migration, or product feature.
- [x] Use no confidential data.
  Evidence: synthetic titles and references only.

## Architecture Impact

The change reinforces the existing contract: services and routes use canonical
domain objects while persistence records remain repository-internal.

## Security and Data Impact

No industrial data, secrets, credentials, customer/supplier facts, prices,
formulations, or production records are included. Live tests use synthetic
payloads and an isolated test target.

## Known Limitations

- Migration-to-model alignment remains deferred to issue #35.
- Live PostgreSQL coverage remains local and is not provisioned in CI.
- Global FastAPI dependency overrides require serial integration execution.
- `create_all()` proves ORM/API compatibility, not migration correctness.
- Pagination and deterministic list ordering remain deferred.

## Lost Points and Correction Items

| Item | Source | Points | Status | Action or Evidence |
|---|---|---:|---|---|
| C01 | PR #26 isolation-mode deduction | 1 | RESOLVED | Cycle 3 reviewer confirmed mandatory isolated-schema behavior and live evidence. |
| C02 | PR #26 teardown-proof deduction | 1 | RESOLVED | Cycle 3 reviewer confirmed catalog teardown assertions and absence evidence. |
| C03 | PR #26 opt-in deduction | 1 | RESOLVED | Cycle 3 reviewer confirmed the exact explicit live-test opt-in guard. |
| C04 | PR #26 evidence/report deduction | 1 | RESOLVED | Cycle 3 reviewer accepted exact commands, failure disclosure, boundaries, and v2 evidence. |
| C05 | PR #26 migration-follow-up deduction | 1 | RESOLVED | Cycle 3 reviewer confirmed migration correctness remains separately tracked in issue #35. |

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 24 | Contract fix plus unit/type/integration evidence. | Independent Cycle 3 review pending. |
| Scope and acceptance criteria | 20 | 20 | Owned paths only and no new features. | None. |
| Architecture and North-Star alignment | 15 | 15 | Canonical domain contracts preserved. | None. |
| Verification, tests, or validation | 15 | 14 | Unit, MyPy, Ruff, guards, teardown, list, and five live PostgreSQL checks. | Migration history is deferred to issue #35. |
| Security, privacy, and data governance | 10 | 10 | Synthetic data and guarded isolated target. | None. |
| Documentation and traceability | 10 | 10 | Contract document, commands, and report. | None. |
| Maintainability and clarity | 5 | 3 | Typed fixture and cleanup helpers. | Global app override requires serial execution. |
| Total | 100 | 96 | Cycle 2 corrections are locally evidenced. | Four self-score points remain. |

## ChatGPT Reviewer Score

Reviewer total: 100

Reviewer evidence: GitHub PR #26 Cycle 3 independent review submitted 2026-07-19.

## Final Score

Provisional weighted score: 98.4

Gate-adjusted score: 98.4

## Critical-Gate Declaration

| Gate | Status | Evidence |
|---|---|---|
| G1 Verified claims | PASS | ORM/API and migration evidence boundaries are distinguished. |
| G2 Confidential data | PASS | Synthetic integration payloads only. |
| G3 Approved scope and architecture | PASS | Existing contracts corrected within owned paths. |
| G4 Required validation | PASS | Unit, type, lint, guard, teardown, list, and five live PostgreSQL checks ran. |
| G5 File ownership | PASS | All ten changed paths are T04-owned. |
| G6 Acceptance completeness | PASS | Every issue criterion is checked with evidence. |

Critical-gate result: PASS

## Correction-Cycle History

| Cycle | Starting Score | Findings | Corrections | Ending Score | Validation Evidence | Status |
|---:|---:|---|---|---:|---|---|
| 1 | 87 | Event contract mismatch, missing limits, override leak, and pending live validation. | Fixed mapping, validation, tests, docs, and ran PostgreSQL integration. | 85 | PR #26 Cycle 1 review after initial live evidence. | CLOSED |
| 2 | 85 | Reviewer found unsafe target, cleanup timing, shallow lists, and overstated migration evidence. | Added schema guard, immediate registration, failure cleanup, list assertions, and evidence boundaries. | 96 | Twelve unit tests, MyPy, Ruff, and three live integration tests. | CLOSED |
| 3 | 95 | Reviewer required mandatory schema, teardown test, explicit opt-in, exact command, migration follow-up, and v2 report. | Implemented both safety signals, strict guards, catalog teardown assertions, exact evidence, issue #35, and v2 normalization. | 96 | Twelve focused tests, MyPy, scoped Ruff/format, two guard tests, and five live PostgreSQL tests passed before independent re-review. | CLOSED |
| 4 | 100 | Cycle 3 independent review closed every T04 branch finding; controlled integration remained pending. | Recorded reviewer authority and resolved all confirmed correction items without claiming release integration. | 100 | PR #26 Cycle 3 review and preserved PostgreSQL, unit, type, lint, and teardown evidence. | OPEN |

## Recommended Follow-up Issues

- Complete migration-to-model alignment in issue #35.
- Add deterministic ordering and pagination to repository lists.
- Provision isolated PostgreSQL integration in CI after explicit security review.

## Blockers

None.
