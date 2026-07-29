# ADR-0020 Governed Knowledge Lifecycle Commands

Status: Accepted

Parent issue: #39

## Context

SmartCoat already defines the canonical lifecycle values `draft`, `captured`, `reviewed`, `validated`, `approved`, `rejected`, and `deprecated`. The current API accepts complete Knowledge Objects and has no service-controlled transition matrix, actor requirements, correction loop, or invalid-transition contract.

Allowing clients to overwrite lifecycle state through a generic update would bypass human review, validation, approval, rejection, and audit requirements.

## Decision

`LifecycleState` is the sole authoritative workflow and trust state machine for
Release 1.8. Knowledge Object lifecycle changes shall use explicit application
commands. A create command establishes a new `draft` server-side. Generic
create or update payloads shall not write either `lifecycle_state` or
`review.status`.

The minimum transition matrix is:

| From | To | Required Contract |
|---|---|---|
| `draft` | `captured` | actor, submission note, minimum completeness |
| `captured` | `draft` | reviewer actor and correction reason |
| `captured` | `reviewed` | reviewer actor and review note |
| `captured` | `rejected` | reviewer actor and rejection reason |
| `reviewed` | `draft` | actor and correction reason |
| `reviewed` | `validated` | validator actor and validation note |
| `reviewed` | `rejected` | actor and rejection reason |
| `validated` | `draft` | actor and correction reason |
| `validated` | `approved` | approver actor and approval note |
| `validated` | `rejected` | actor and rejection reason |
| `approved` | `deprecated` | actor, reason, and replacement reference when known |
| `rejected` | `draft` | actor, reopen reason, and new revision |

All other transitions are invalid unless a later accepted ADR changes the matrix.

### Review-status compatibility projection

`review.status` is a read-only compatibility projection. It is not an
independently mutable state machine or a second source of trust. The projection
is:

| Authoritative lifecycle and history | Projected `review.status` |
|---|---|
| new `draft` | `not_reviewed` |
| correction `draft` | `needs_correction` |
| `captured` | `in_review` |
| `reviewed` | `accepted` |
| `validated` | `validated` |
| `approved` | `validated`; authoritative lifecycle remains `approved` |
| `rejected` | `rejected` |
| `deprecated` | preserve the projection of the latest pre-deprecation lifecycle state |

A new draft has no lifecycle/audit history showing a prior non-draft state. A
correction draft has lifecycle/audit history showing an explicit return or
reopen into `draft`. The immutable lifecycle/audit history, not a client flag,
determines this distinction.

The following invariants are mandatory:

- every persisted object has exactly one authoritative lifecycle state;
- a review projection is computed only from that lifecycle and its audit
  history and cannot be written by a generic payload;
- only combinations in the projection table are valid;
- `review.status=validated` never proves approval without authoritative
  lifecycle `approved`;
- deprecation cannot replace or recompute the last pre-deprecation review
  projection; and
- a contradictory lifecycle/review combination is a contract violation and
  fails closed rather than being stored or returned as conformant.

Each successful transition shall:

- verify the expected current revision;
- preserve actor and required note or reason;
- set the transition timestamp server-side;
- increment the object revision;
- create an immutable audit event atomically with the object change;
- return the resulting canonical Knowledge Object.

`EnterpriseEvent` remains the canonical event family. T07 may define a typed
Knowledge audit profile or subtype, additional Knowledge event types, and their
required fields. T05 owns the shared Unit of Work and database transaction
boundary. Every material mutation transaction shall perform this sequence:

1. load the object;
2. validate lifecycle and expected revision;
3. update or delete with the revision predicate;
4. append the required audit event; and
5. commit once.

Participating repositories may flush but shall not independently commit.
Failure at any step rolls back both the object mutation and audit append. A
generic public event-creation route shall not allow callers to forge system
Knowledge audit events. Audit history is read-only through the normal
application API.

Lifecycle roles are domain contract roles. Release 1.8 does not claim production IAM or authorization enforcement.

## Rationale

This preserves human control, makes trust changes explicit, prevents accidental privilege through payload shape, and gives Release 1.9 a reliable backend review workflow.

## Consequences

- Services own transition behavior.
- Routes call explicit transition use cases.
- T05's shared Unit of Work persists atomic object and audit changes.
- Invalid transitions and stale revisions produce deterministic domain errors.
- Tests must cover the complete allowed and invalid transition matrix, the
  review projection invariants, rollback, and audit-forgery rejection.

## Rejected Alternatives

### Generic lifecycle field update

Rejected because it bypasses review rules and makes audit evidence optional.

### Separate lifecycle names for each domain

Rejected because it fragments the canonical platform language.

### Automatic approval after validation

Rejected because trusted organizational reuse requires an explicit human approval command.

## Scope Boundary

This ADR defines application contracts, not production identity, role assignment, legal authority, or real-data permission.
