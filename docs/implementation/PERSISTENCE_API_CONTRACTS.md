# Persistence and API Contracts

Status: Release 1.7 stabilization note

Issue: #18

## Purpose

This document records the verified contract for the current FastAPI -> service
-> repository -> persistence path.

## Current Canonical Types

| Endpoint family | Domain object | Repository return contract |
|---|---|---|
| `/knowledge` | `KnowledgeObject` | `KnowledgeObject` or list of `KnowledgeObject` |
| `/decisions` | `DecisionObject` | `DecisionObject` or list of `DecisionObject` |
| `/events` | `EnterpriseEvent` | `EnterpriseEvent` or list of `EnterpriseEvent` |

Repositories may use SQLAlchemy records internally, but services and routes
must receive canonical domain objects. Database records must not silently become
the API or service contract.

## Confirmed Defect Corrected

`EventRepository` previously returned mixed types:

- `create()` returned the input `EnterpriseEvent`.
- `get()` returned `EnterpriseEventRecord`.
- `list()` returned `list[EnterpriseEventRecord]`.

This broke the service type contract and was confirmed by `mypy src`. The
repository now maps all persisted event records back through `record_to_event`.

## Collection Limits

Current list endpoints accept:

```text
1 <= limit <= 500
```

Invalid limits return FastAPI validation errors instead of passing unsafe or
ambiguous values into services and repositories.

## PostgreSQL Integration Test Boundary

The integration test at `tests/integration/test_persistent_api_postgres.py`
uses `SMARTCOAT_TEST_DATABASE_URL` and requires both safety signals:

- `SMARTCOAT_RUN_LIVE_POSTGRES_TESTS=true` as an exact explicit opt-in; and
- an isolated schema named with the guarded `smartcoat_test_...` prefix via
  mandatory `SMARTCOAT_TEST_SCHEMA`.

The test refuses a URL-only invocation, missing/invalid schema, non-PostgreSQL
URL, or any opt-in spelling except lowercase `true` before table creation.
Schema-isolated runs create the named schema, route all test sessions through
its `search_path`, delete registered object IDs, drop the schema with `CASCADE`,
and query `pg_namespace` to assert that zero matching schemas remain. A dedicated
test exercises the same drop-and-assert helper. Each successful POST is
registered immediately, so cleanup remains effective after an intermediate
assertion or request failure.

Exact local live command:

```bash
SMARTCOAT_RUN_LIVE_POSTGRES_TESTS=true \
SMARTCOAT_TEST_DATABASE_URL=postgresql+psycopg://smartcoat:smartcoat@localhost:5432/smartcoat \
SMARTCOAT_TEST_SCHEMA=smartcoat_test_t04_cycle3_20260719 \
python -m pytest -q tests/integration/test_persistent_api_postgres.py
```

This is local live validation, not CI coverage. No current workflow provisions a
PostgreSQL service or sets the two safety signals.

`Base.metadata.create_all()` validates compatibility among the current ORM
models, repositories, and API behavior. It does **not** execute or validate the
Alembic migration history and must not be cited as migration-correctness
evidence.

The fixture temporarily mutates the process-global FastAPI dependency override
map. It snapshots and restores the complete prior map, but integration tests
using this app must still run serially until the application exposes a factory
that can provide a per-test app instance.

## Deferred Design Questions

1. Whether repository list methods should add deterministic ordering.
2. Whether collection endpoints should add pagination tokens for Release 1.8.
3. Whether integration tests should provision PostgreSQL automatically in CI
   after the CI baseline is expanded.
4. Migration-to-model alignment is tracked separately in
   [issue #35](https://github.com/JamshidiML/smartcoat-intelligence/issues/35),
   owned by persistence engineering. Acceptance requires creating a clean
   database by the repository migration mechanism, comparing migrated tables and
   constraints to current SQLAlchemy metadata, running the persistence contract
   suite, and proving upgrade/rollback behavior without
   `Base.metadata.create_all()`.
