# T04 Persistence and API Report

Thread ID: T04

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/18

Branch: `thread/04-persistence-api-contracts`

Draft PR: Pending

Final status: `READY FOR CHATGPT REVIEW`

## Objective

Reproduce, document, and correct confirmed inconsistencies in the current
FastAPI -> service -> repository -> PostgreSQL -> domain-object path.

## Scope

Changed only owned persistence/API files, persistence/API tests, and the
thread report/documentation.

## Inputs Reviewed

- `AGENTS.md`
- `SECURITY.md`
- `docs/project/PROJECT_STATE.md`
- `docs/project/MVP_STRATEGY.md`
- `docs/project/DECISION_LOG.md`
- Issue #18
- API routes under `src/smartcoat/api/`
- Services under `src/smartcoat/services/`
- Repositories and mappers under `src/smartcoat/storage/repositories/`
- SQLAlchemy models and migration shape
- Existing API and mapper tests

## Execution Plan

1. Reproduce suspected event contract issue.
2. Fix only confirmed repository/service/API contract defects.
3. Add bounded API list-limit validation.
4. Add repository and HTTP-to-PostgreSQL integration coverage.
5. Re-run unit, type, and integration validation.

## Work Completed

- Corrected `EventRepository` to return canonical `EnterpriseEvent` objects for
  create, get, and list.
- Converted route dependencies to `typing.Annotated` to avoid FastAPI `Depends`
  lint findings in owned route files.
- Added `1 <= limit <= 500` validation to all current collection endpoints.
- Added event repository contract coverage.
- Added an opt-in PostgreSQL-backed integration test covering Knowledge Object,
  Decision Object, and Enterprise Event HTTP round trips.
- Updated existing API route tests to isolate dependency overrides.
- Added persistence/API contract documentation.

## Commands and Tests Executed

```bash
/private/tmp/smartcoat-1-7-threads/.venv312/bin/python -m mypy src
/private/tmp/smartcoat-1-7-threads/.venv312/bin/python -m pytest tests/test_api_persistent_routes.py tests/test_event_repository_contract.py tests/test_persistence_mappers.py
/private/tmp/smartcoat-1-7-threads/.venv312/bin/python -m ruff check src/smartcoat/api src/smartcoat/services src/smartcoat/storage/repositories tests/test_api_persistent_routes.py tests/test_event_repository_contract.py tests/integration/test_persistent_api_postgres.py
docker ps -a --filter name=smartcoat_postgres --format '{{.ID}} {{.Names}} {{.Status}} {{.Ports}}'
SMARTCOAT_TEST_DATABASE_URL=postgresql+psycopg://smartcoat:smartcoat@localhost:5432/smartcoat /private/tmp/smartcoat-1-7-threads/.venv312/bin/python -m pytest tests/integration/test_persistent_api_postgres.py
```

## Actual Results

| Command | Result |
|---|---|
| `python -m mypy src` | Passed: no issues found in 41 source files. |
| Focused unit/API tests | Passed: 12 tests passed. |
| Scoped ruff check | Passed for owned API, service, repository, and new test files. |
| PostgreSQL integration test without DB URL | Skipped by design with explicit message. |
| `docker compose up -d postgres` | Did not recreate service because an existing `smartcoat_postgres` container already owned the fixed container name. |
| Existing PostgreSQL container | Found running on `0.0.0.0:5432->5432/tcp`. |
| First sandboxed PostgreSQL test | Blocked by sandbox localhost networking permission. |
| Escalated PostgreSQL integration test | Passed: 1 HTTP-to-PostgreSQL round-trip test passed. |

## Acceptance-Criteria Evidence

| Criterion | Evidence |
|---|---|
| Findings distinguish defect vs missing test vs deferred improvement | Contract document and this report. |
| Repository methods return canonical types | `EventRepository` maps records through `record_to_event`; mypy validation. |
| HTTP-to-PostgreSQL path tested | Live integration test passed against running `smartcoat_postgres`. |
| Synthetic data and cleanup | Integration test uses synthetic payloads and deletes created IDs. |
| Existing tests remain valid | API route tests updated and rerun. |
| API validation explicit and tested | Limit validation tests for knowledge, decisions, and events. |
| No new capability/entity | No new domain model, route family, migration, or product feature. |
| No confidential data | Synthetic titles and evidence references only. |

## Architecture Impact

The change reinforces the existing architecture rule: services and routes use
canonical domain objects; persistence records remain internal to repositories.

## Security and Data Impact

No real industrial data, secrets, credentials, customer data, supplier data,
prices, formulations, or production records are included. Tests use synthetic
payloads only.

## Known Limitations

- PostgreSQL integration tests require an external test database URL and are not
  automatically provisioned by this thread.
- List endpoints still use simple limits, not full pagination.
- Deterministic ordering for repository lists remains deferred.

## Lost Points and Correction Items

Initial deductions:

1. Event repository returned persistence records through service type contracts.
2. Collection limits accepted unsafe values.
3. Existing route tests leaked dependency overrides globally.

All three in-scope code items were corrected in this cycle.

Remaining blocker: none.

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 25 | Contract fix plus unit/type/integration evidence. | None. |
| Scope and acceptance criteria | 20 | 20 | Owned paths only; no new features. | None. |
| Architecture and North-Star alignment | 15 | 15 | Preserves canonical domain contracts. | None. |
| Verification, tests, or validation | 15 | 15 | Unit, mypy, ruff, and live PostgreSQL integration checks passed. | None. |
| Security, privacy, and data governance | 10 | 10 | Synthetic-only data. | None. |
| Documentation and traceability | 10 | 10 | Contract doc and report. | None. |
| Maintainability and clarity | 5 | 5 | Small mapper-based fix and route validation. | None. |
| Total | 100 | 100 | Evidence above. | None. |

## Critical-Gate Declaration

No critical gate failed. The live PostgreSQL integration test passed after
rerunning with localhost database access outside the sandbox.

## Correction-Cycle History

| Cycle | Starting Score | Findings | Changes Made | Ending Score |
|---:|---:|---|---|---:|
| 1 | 87 | Event contract mismatch, missing API limit validation, test override leak, and pending live PostgreSQL validation. | Fixed repository mapping, route validation, tests, docs, and ran the live integration test. | 100 |

## Recommended Follow-up Issues

- Add deterministic ordering and pagination to repository list endpoints.
- Provision PostgreSQL service automatically in CI after T03 CI baseline lands.

## Blockers

None.
