# ADR-0021 Optimistic Revision and Controlled Mutation

Status: Proposed

Parent issue: #39

## Context

The current Knowledge Object model has stable identity and timestamps but no revision or concurrency token. A later client can overwrite a newer record without detecting that another actor or process changed it.

Release 1.8 requires safe editing, lifecycle commands, and deterministic conflict behavior without introducing long-lived database locks or production collaboration infrastructure.

## Decision

Every persisted Knowledge Object shall have a positive integer `revision`.

- New objects start at revision `1` after successful persistence.
- Every material update or lifecycle transition increments the revision by exactly one.
- Mutation commands must include `expected_revision`.
- The persistence layer shall update only when the stored revision equals `expected_revision`.
- A zero-row update caused by revision mismatch shall produce a dedicated stale-revision conflict error.
- Clients may not directly set the resulting revision.
- Server-managed identity, lifecycle, creation timestamp, update timestamp, and audit linkage are immutable through generic content-update commands.

A material update means a change to reusable knowledge content, title, description, owner/author, evidence, provenance, tags, context, relationships, confidence, or governed metadata. Read operations do not change revision.

No-op update behavior shall be explicit and deterministic. The preferred Release 1.8 behavior is to return the unchanged object without incrementing revision when the normalized requested state is identical, while still rejecting a stale `expected_revision`.

## Rationale

Optimistic concurrency is simple, testable, compatible with HTTP conflict semantics, and adequate for the bounded Release 1.8 backend. It prevents silent lost updates while avoiding premature real-time collaboration architecture.

## Consequences

- Domain and API update commands require `expected_revision`.
- SQL updates require an atomic revision predicate.
- Lifecycle transitions share the same concurrency rule.
- Audit events preserve previous and resulting revisions.
- HTTP mapping uses `409 Conflict` for stale revisions.
- Existing Release 1.7 records need a migration default and compatibility evidence.

## Rejected Alternatives

### Last-write-wins

Rejected because it silently destroys newer knowledge and weakens traceability.

### Pessimistic row locking as the public contract

Rejected because it adds operational complexity and does not solve disconnected client updates.

### Timestamp-only concurrency

Rejected because timestamp precision and serialization behavior are less deterministic than an explicit integer revision.

## Scope Boundary

This ADR does not implement collaborative editing, field-level merge, conflict resolution UI, event sourcing, or distributed consensus.
