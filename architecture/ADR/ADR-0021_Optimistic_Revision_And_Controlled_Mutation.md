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

No-op update behavior is deterministic: validate `expected_revision` first,
then return the unchanged object without incrementing revision when the
normalized requested state is identical. A stale `expected_revision` is still
rejected even when the requested state would otherwise be a no-op.

### Identity and minimum governance fields

- `object_id` remains the canonical application and database UUID identity.
- A platform-envelope adapter derives `knowledge_object:<uuid>` from
  `object_id`; no second platform identity is stored.
- New v2 create commands require `organization_id`.
- New v2 records require exactly one confidentiality value: `public`,
  `internal`, `confidential`, `restricted`, or `strategic`.
- Owner is a structured reference with `owner_id` and `role`; the creator
  remains `provenance.created_by`.
- Legacy compatibility is fail-closed and explicitly marked. It shall not infer
  a real organization, owner, or confidentiality value. T05 owns the exact
  migration mechanics.

These fields define application contracts only. They do not claim production
tenancy, IAM, or purpose-decision enforcement.

### Transaction ownership

T05 owns the shared Unit of Work and database transaction boundary for material
mutations. The Unit of Work loads the object, validates lifecycle and revision,
updates with the revision predicate, appends the required typed Knowledge audit
event from the canonical `EnterpriseEvent` family, and commits once.
Participating repositories may flush but shall not independently commit. Any
failure rolls back both the object mutation and audit append.

## Rationale

Optimistic concurrency is simple, testable, compatible with HTTP conflict semantics, and adequate for the bounded Release 1.8 backend. It prevents silent lost updates while avoiding premature real-time collaboration architecture.

## Consequences

- Domain and API update commands require `expected_revision`.
- SQL updates require an atomic revision predicate.
- Lifecycle transitions share the same concurrency rule.
- Audit events preserve previous and resulting revisions.
- HTTP mapping uses `409 Conflict` for stale revisions.
- Existing Release 1.7 records need a fail-closed migration rule and
  compatibility evidence owned by T05.

## Rejected Alternatives

### Last-write-wins

Rejected because it silently destroys newer knowledge and weakens traceability.

### Pessimistic row locking as the public contract

Rejected because it adds operational complexity and does not solve disconnected client updates.

### Timestamp-only concurrency

Rejected because timestamp precision and serialization behavior are less deterministic than an explicit integer revision.

## Scope Boundary

This ADR does not implement collaborative editing, field-level merge, conflict resolution UI, event sourcing, or distributed consensus.
