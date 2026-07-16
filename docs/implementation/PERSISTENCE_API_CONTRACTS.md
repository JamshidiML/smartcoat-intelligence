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
uses `SMARTCOAT_TEST_DATABASE_URL`. It creates SQLAlchemy tables if needed,
uses only synthetic objects, and deletes the objects it creates. It does not
ingest real industrial data.

## Deferred Design Questions

1. Whether repository list methods should add deterministic ordering.
2. Whether collection endpoints should add pagination tokens for Release 1.8.
3. Whether integration tests should provision PostgreSQL automatically in CI
   after the CI baseline is expanded.
