# ADR-0022 Draft Deletion and Trusted Record Deprecation

Status: Accepted

Parent issue: #39

## Context

Release 1.8 needs controlled CRUD behavior, but industrial knowledge must remain explainable after review or trusted reuse. Treating all records as freely deletable would destroy evidence, audit history, and decision context. Treating every accidental draft as permanently retained would create unnecessary clutter and conflict with future retention policies.

## Decision

SmartCoat shall distinguish disposable drafts from trusted or historically meaningful records.

### Draft hard deletion

A Knowledge Object may be hard-deleted through the normal application contract only when all conditions are true:

- lifecycle state is `draft`;
- the caller supplies the current `expected_revision`;
- the object has never entered `captured`, `reviewed`, `validated`, `approved`, `rejected`, or `deprecated` state;
- no inbound reference exists from another Knowledge Object, Decision Object,
  or governed domain object;
- the delete command records actor and reason;
- an audit tombstone or equivalent retained deletion event is created without preserving confidential content.

Required create and update audit events do not disqualify a draft from this
deletion path. The object row and its content are deleted atomically while safe,
append-only audit events remain. The deletion tombstone records only the actor,
reason, object ID, object revision, server timestamp, and safe metadata needed
to identify the deletion. It shall not copy title, description, evidence,
context attributes, or other confidential content.

T05's shared Unit of Work owns the transaction: load the object, validate
lifecycle and revision, verify inbound-reference eligibility, delete with the
revision predicate, append the typed Knowledge deletion event from the
canonical `EnterpriseEvent` family, and commit once. Participating repositories
may flush but shall not independently commit. Failure rolls back both deletion
and audit append.

### Non-draft records

Captured, reviewed, validated, approved, rejected, and deprecated records shall not be hard-deleted through standard Release 1.8 use cases.

Approved knowledge that should no longer guide new work shall transition to `deprecated`. Deprecation requires actor and reason and may include a replacement object reference.

Rejected knowledge remains auditable and may reopen only through the explicit lifecycle command.

### Future governed erasure

This is application-object deletion. It is not legal erasure, backup deletion,
production retention compliance, retention expiration, administrative purge,
or cryptographic deletion. Those are future governed capabilities and shall not
be simulated through repository delete calls.

## Rationale

This balances practical draft cleanup with the need to preserve organizational learning, trust history, and auditability.

## Consequences

- DELETE behavior is a controlled application use case, not generic repository exposure.
- Repositories must enforce eligibility and reference constraints.
- API responses must distinguish deletion from deprecation.
- Audit history must retain a safe deletion/deprecation record.
- Tests must prove that trusted records cannot be hard-deleted.

## Rejected Alternatives

### Hard delete any object

Rejected because it can erase evidence and trusted history.

### Never delete anything

Rejected because incomplete accidental drafts need bounded cleanup and future retention rules should remain possible.

### Use `deprecated` for accidental drafts

Rejected because deprecation implies prior organizational relevance and would pollute retrieval and audit semantics.

## Scope Boundary

This ADR is not a legal-retention policy and does not authorize real-data deletion behavior. Production retention, legal hold, privacy rights, backups, and deletion verification require later governance and security decisions.
