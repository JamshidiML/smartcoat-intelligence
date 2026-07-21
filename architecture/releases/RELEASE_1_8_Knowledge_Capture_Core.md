# Release 1.8 — Knowledge Capture Core

Status: In progress

Parent issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/38

Release branch: `release/1.8-knowledge-capture-core`

Base release: Release 1.7 at `47df21458038d107bb7c7cb98dc6d23dd3b6d7e9`

## Purpose

Release 1.8 converts the Release 1.7 engineering baseline into a reliable backend product core for governed industrial Knowledge Objects.

The release must provide domain, lifecycle, persistence, evidence, provenance, audit, filtering, pagination, concurrency, and minimum context behavior that can support a human review interface in Release 1.9 and AI-assisted capture in Release 2.0.

## Product Outcome

An application client can create a draft Knowledge Object, attach structured evidence and provenance, update it safely, submit it, move it through a human-controlled lifecycle, persist it in PostgreSQL, retrieve and filter it later, and inspect its immutable audit history.

## Scope

- Knowledge Object v2
- structured evidence references
- expanded provenance
- lifecycle transition enforcement
- controlled mutation, draft deletion, and deprecation policy
- optimistic concurrency
- filtering, sorting, and cursor pagination
- audit history
- minimum project, experiment, material, formulation, substrate, and test-result context references
- explicit API commands and errors
- aligned SQLAlchemy models and Alembic migrations
- PostgreSQL integration evidence

## Exclusions

Release 1.8 does not include UI, LLM extraction, voice capture, follow-up questions, semantic search, file or email ingestion, production IAM, real industrial data, a full ontology, or a live pilot.

## Architecture Rules

- Canonical domain models remain authoritative.
- Routes remain thin.
- Services own lifecycle and mutation behavior.
- Repositories own persistence.
- Lifecycle changes use explicit commands rather than generic field overwrite.
- Trusted records are deprecated rather than silently destroyed.
- Audit events are append-only through the application contract.
- PostgreSQL evidence is required for persistence acceptance.
- Synthetic data only.

## Dependencies

- Issue #35: migration-to-model alignment
- Issue #36: Ruff and formatting debt

These issues remain independently traceable. Their work may be incorporated into bounded Release 1.8 threads, but their acceptance criteria must not be silently weakened.

## Primary Definition

The canonical release definition is:

- `docs/project/RELEASE_1_8_DEFINITION_PACK.md`

## Planned Threads

1. Release contract and ADR guardrails
2. Knowledge Object v2
3. Evidence and provenance
4. Lifecycle and controlled mutation
5. Persistence and migrations
6. Filtering and pagination
7. Audit events
8. Minimum domain context
9. API contracts
10. Engineering and integrated release validation

## Exit Criteria

Release 1.8 closes only after an independently reviewed integrated candidate proves the governed Knowledge Object backend workflow end to end on PostgreSQL, with deterministic failure behavior, migration evidence, no confidential data, and no claims outside the approved scope.
