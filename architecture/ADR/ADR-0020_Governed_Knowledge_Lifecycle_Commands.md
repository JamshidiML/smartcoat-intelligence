# ADR-0020 Governed Knowledge Lifecycle Commands

Status: Proposed

Parent issue: #39

## Context

SmartCoat already defines the canonical lifecycle values `draft`, `captured`, `reviewed`, `validated`, `approved`, `rejected`, and `deprecated`. The current API accepts complete Knowledge Objects and has no service-controlled transition matrix, actor requirements, correction loop, or invalid-transition contract.

Allowing clients to overwrite lifecycle state through a generic update would bypass human review, validation, approval, rejection, and audit requirements.

## Decision

Knowledge Object lifecycle changes shall use explicit application commands. Generic create or update payloads shall not directly assign a trusted lifecycle state.

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

Each successful transition shall:

- verify the expected current revision;
- preserve actor and required note or reason;
- set the transition timestamp server-side;
- increment the object revision;
- create an immutable audit event atomically with the object change;
- return the resulting canonical Knowledge Object.

Lifecycle roles are domain contract roles. Release 1.8 does not claim production IAM or authorization enforcement.

## Rationale

This preserves human control, makes trust changes explicit, prevents accidental privilege through payload shape, and gives Release 1.9 a reliable backend review workflow.

## Consequences

- Services own transition behavior.
- Routes call explicit transition use cases.
- Repositories persist atomic object and audit changes.
- Invalid transitions and stale revisions produce deterministic domain errors.
- Tests must cover the complete allowed and invalid transition matrix.

## Rejected Alternatives

### Generic lifecycle field update

Rejected because it bypasses review rules and makes audit evidence optional.

### Separate lifecycle names for each domain

Rejected because it fragments the canonical platform language.

### Automatic approval after validation

Rejected because trusted organizational reuse requires an explicit human approval command.

## Scope Boundary

This ADR defines application contracts, not production identity, role assignment, legal authority, or real-data permission.
