# Release 1.8 Definition Pack — Knowledge Capture Core

Version: 1.0

Status: Active Release Definition

Parent issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/38

Base: `main` at `47df21458038d107bb7c7cb98dc6d23dd3b6d7e9`

Release branch: `release/1.8-knowledge-capture-core`

---

## 1. Release Decision

Release 1.8 builds the trustworthy backend core for SmartCoat's first product vertical slice.

The release does not implement the end-user interface or AI-assisted extraction. It creates the domain, lifecycle, persistence, API, evidence, provenance, audit, filtering, pagination, and minimum context behavior that Releases 1.9 and 2.0 require.

The release is successful only when one integrated backend workflow is reliable end to end:

> Create a draft Knowledge Object, attach evidence and provenance, update it safely, move it through a governed human-controlled lifecycle, persist it, retrieve it, filter it, page through results, and inspect its audit history.

---

## 2. Product Boundary

### In Scope

- Knowledge Object contract v2
- structured evidence references
- expanded provenance
- lifecycle transition state machine
- controlled create, read, update, submit, review, validate, approve, reject, deprecate, and draft-delete behavior
- optimistic concurrency and object revision
- deterministic filtering, sorting, and cursor pagination
- immutable audit-event history
- minimum project, experiment, material, formulation, substrate, and test-result context references
- explicit API request and response models
- deterministic domain and HTTP errors
- SQLAlchemy persistence and Alembic migrations
- real API-to-service-to-repository-to-PostgreSQL integration evidence
- synthetic fixtures, documentation, ADRs, and release reports

### Out of Scope

- web or mobile user interface
- free-text or voice extraction
- adaptive follow-up questions
- LLM, agent, or autonomous behavior
- embeddings, vector stores, or semantic retrieval
- unrestricted file, email, ERP, or bulk-document ingestion
- production authentication, IAM, or tenant-isolation implementation
- real customer, supplier, formulation, price, email, production, or confidential company data
- complete enterprise ontology or complete technical-textile ontology
- live industrial pilot

---

## 3. Primary Actors

### Capture Author

Creates and edits draft knowledge, attaches evidence, submits captured knowledge, and responds to correction requests.

### Reviewer

Inspects submitted content, records review notes, requests correction, rejects it, or moves it forward.

### Validator

Confirms that evidence, method, and domain context are adequate for the intended reuse level.

### Approver

Accepts validated knowledge as trusted reusable organizational knowledge.

### System

Enforces contracts, timestamps, versions, transitions, persistence, pagination, filtering, and immutable audit history. The system does not silently grant trust.

Release 1.8 models actors as explicit identifiers and roles. It does not implement production IAM.

---

## 4. Canonical Knowledge Lifecycle

Existing canonical lifecycle names remain authoritative:

- `draft`
- `captured`
- `reviewed`
- `validated`
- `approved`
- `rejected`
- `deprecated`

### State Meaning

| State | Meaning |
|---|---|
| `draft` | Editable work in progress; not ready for organizational reuse. |
| `captured` | Author has submitted a sufficiently complete record for review. |
| `reviewed` | A human reviewer has inspected the record and recorded an outcome. |
| `validated` | Evidence and context have been checked for the declared reuse purpose. |
| `approved` | Authorized human approval permits trusted organizational reuse. |
| `rejected` | The submitted revision is not accepted. Reason and actor are mandatory. |
| `deprecated` | Previously approved knowledge remains auditable but should not guide new work without explicit context. |

### Minimum Transition Contract

| From | Allowed To | Required Evidence |
|---|---|---|
| `draft` | `captured` | actor, reason or submission note, complete minimum fields |
| `captured` | `draft` | reviewer correction reason |
| `captured` | `reviewed` | reviewer actor and review note |
| `captured` | `rejected` | reviewer actor and rejection reason |
| `reviewed` | `draft` | correction reason |
| `reviewed` | `validated` | validator actor and validation note |
| `reviewed` | `rejected` | actor and rejection reason |
| `validated` | `draft` | correction reason |
| `validated` | `approved` | approver actor and approval note |
| `validated` | `rejected` | actor and rejection reason |
| `approved` | `deprecated` | actor, reason, and replacement reference when known |
| `rejected` | `draft` | explicit reopen reason and new revision |

All other transitions are invalid unless an accepted ADR changes the matrix.

Lifecycle changes must be service-controlled and must create audit events. Clients may not overwrite lifecycle state through a generic update payload.

---

## 5. Controlled Mutation and Deletion Policy

- Draft content may be edited.
- Submitted or trusted content must use controlled transition and revision behavior.
- Optimistic concurrency is required for material updates.
- Every material mutation increments a revision or equivalent concurrency token.
- Stale writes return a deterministic conflict error.
- A draft with no downstream trust or audit dependency may be hard-deleted under an explicit draft-delete use case.
- Captured, reviewed, validated, approved, rejected, or deprecated records are not silently hard-deleted.
- Approved records are deprecated, not overwritten or destroyed.
- Administrative erasure and legal deletion are future governed capabilities, not an informal repository operation.

---

## 6. Knowledge Object v2 Minimum Contract

A Knowledge Object must preserve:

- stable object ID
- organization boundary identifier as metadata contract, without claiming production tenant isolation
- title
- optional description
- canonical knowledge type
- lifecycle state
- revision or concurrency token
- author or owner identifier
- created and updated timestamps
- structured evidence references
- expanded provenance
- confidence when applicable
- explicit uncertainty or unknown-state representation when applicable
- tags
- minimum context references
- related Knowledge Objects and Decision Objects
- audit-event relationship
- flexible content only where deliberately governed

The release must not move all future domain semantics into unstructured JSON merely to avoid model decisions.

---

## 7. Evidence Contract

Release 1.8 replaces bare evidence strings with structured evidence references while providing an explicit migration or compatibility decision.

Minimum evidence fields:

- evidence ID
- evidence type
- title or description
- source reference
- source system when known
- captured by
- captured at
- optional event or test timestamp
- optional checksum or fingerprint declaration
- optional media type
- optional confidentiality declaration
- optional relationship to a context entity

Evidence references are metadata and links. Release 1.8 does not ingest or store unrestricted raw files.

---

## 8. Provenance Contract

Minimum provenance fields:

- source system
- source reference
- actor or creator
- capture method
- recorded timestamp
- source timestamp when known
- transformation or import method when applicable
- prior object or revision reference when derived

Unknown values remain explicit. Provenance is not inferred into certainty.

---

## 9. Minimum Context Model

Release 1.8 supports bounded references to:

- Project
- Experiment or Trial
- Material
- Fabric or Substrate
- Formulation Reference
- Process Conditions
- Test Result

The implementation may use minimal canonical reference objects rather than full independent bounded contexts when that satisfies the release workflow. Any new standalone entity requires an issue-level justification and an accepted architecture decision.

The release does not implement the complete technical-textile schema package as application-domain tables.

---

## 10. API Capability Contract

Minimum API capabilities:

- create draft Knowledge Object
- retrieve by ID
- update editable content with concurrency token
- delete eligible draft
- transition lifecycle through dedicated action endpoint or explicit command model
- list with deterministic cursor pagination
- filter by knowledge type, lifecycle state, owner or author, tags, project/context reference, and time range
- deterministic sort order with stable tie-breaker
- retrieve audit history

API rules:

- thin routes
- explicit request and response models
- no direct persistence logic in routes
- deterministic 400, 404, 409, and 422 behavior
- no internal exception leakage
- no generic update path that bypasses lifecycle or immutable fields
- no manual JSON claim as the future user experience

---

## 11. Pagination and Filtering Contract

Release 1.8 uses cursor-based pagination for the canonical list endpoint unless an accepted ADR selects another method.

Requirements:

- deterministic stable ordering
- opaque cursor
- bounded page size
- explicit next cursor
- no duplicates or omissions under unchanged data
- documented behavior when data changes between requests
- combined filters use explicit AND semantics unless documented otherwise
- invalid filter values fail deterministically

Offset pagination may remain only as a documented compatibility endpoint if required; it must not become the canonical scalable contract by accident.

---

## 12. Audit Contract

Every material action creates an immutable Enterprise Event or dedicated audit representation with:

- event ID
- target object ID
- event type
- actor
- timestamp
- previous lifecycle state when applicable
- resulting lifecycle state when applicable
- previous revision
- resulting revision
- reason or note when required
- correlation or request identifier when available
- safe summary of changed fields without leaking sensitive content

Minimum audited actions:

- create
- update
- draft delete
- lifecycle transition
- reject
- reopen
- approve
- deprecate

Audit events are append-only through the application contract.

---

## 13. Persistence and Migration Contract

- SQLAlchemy models, domain mappers, and Alembic migrations must remain aligned.
- Issue #35 must be resolved or explicitly incorporated before new persistence structures are accepted.
- Historical migrations are not casually edited.
- Migration upgrade and downgrade behavior must be tested on synthetic data.
- PostgreSQL is the release database source of truth.
- SQLite-only proof is insufficient for release acceptance.
- JSONB is used deliberately, not as a substitute for domain design.
- The API-to-service-to-repository-to-PostgreSQL round trip must be demonstrated on the integrated candidate.

---

## 14. Security and Governance Boundary

- Synthetic data only.
- No `.env`, secrets, credentials, internal emails, real formulations, prices, customer or supplier data, raw production records, or private reports.
- Actor identifiers in fixtures are synthetic.
- Organization identifiers are boundary metadata, not proof of production tenant isolation.
- Lifecycle roles are contract roles, not proof of production authorization.
- Real-data use remains blocked until later governance, IAM, isolation, retention, and legal decisions are implemented and approved.

---

## 15. Non-Functional Requirements

- Python 3.12 constrained environment remains reproducible.
- Existing passing behavior remains backward compatible unless an accepted migration decision says otherwise.
- Full type-check impact is reviewed.
- Known Ruff and formatting debt from issue #36 is resolved in bounded scope before enabling mandatory gates.
- Tests cover success, invalid transition, conflict, missing object, invalid filter, pagination boundary, mapper, repository, API, migration, audit, and live PostgreSQL paths.
- No test result is claimed without execution evidence.

---

## 16. Release Acceptance Matrix

Release 1.8 cannot close unless the integrated candidate proves:

- [ ] Knowledge Object v2 contract is explicit and migration-compatible.
- [ ] Structured evidence and provenance round-trip through PostgreSQL.
- [ ] Lifecycle matrix is enforced in the service layer.
- [ ] Invalid transitions fail deterministically.
- [ ] Material updates use optimistic concurrency.
- [ ] Draft deletion and trusted-record deprecation policies are enforced.
- [ ] Filtering and cursor pagination are deterministic.
- [ ] Audit history exists for every material action.
- [ ] Minimum context references are sufficient for the first vertical slice.
- [ ] API requests, responses, and errors are documented and tested.
- [ ] Migration/model alignment passes.
- [ ] Live PostgreSQL integration and teardown pass.
- [ ] Security and confidential-data scans pass.
- [ ] No UI, AI, semantic retrieval, real-data, or production-readiness claim is made.

---

## 17. Planned Execution Threads

| Thread | Scope |
|---|---|
| T01 | Release contract, ADRs, lifecycle semantics, and cross-thread architecture guardrails |
| T02 | Knowledge Object v2 domain and compatibility contract |
| T03 | Structured evidence and expanded provenance |
| T04 | Lifecycle transition service and controlled mutation policy |
| T05 | Persistence, migrations, repository CRUD, and issue #35 alignment |
| T06 | Filtering, sorting, and cursor pagination |
| T07 | Immutable audit events and history retrieval |
| T08 | Minimum domain context references and relationship integrity |
| T09 | API request/response/error contracts and end-to-end route behavior |
| T10 | Engineering gates, issue #36, integrated PostgreSQL validation, scoring, and release evidence |

Thread ownership must avoid overlapping files where practical. Cross-thread contract changes require documented coordination.

---

## 18. Recommended Integration Order

1. T01 release contracts and ADRs
2. T02 Knowledge Object v2
3. T03 evidence and provenance
4. T08 minimum context references
5. T04 lifecycle behavior
6. T07 audit behavior
7. T05 persistence and migrations
8. T06 filtering and pagination
9. T09 API contracts
10. T10 integrated validation and release evidence

The final order may be adjusted only with an explicit dependency explanation.

---

## 19. Release Stop Conditions

Stop and request a human decision if work would:

- redefine SmartCoat's product identity;
- replace canonical Knowledge Object, Decision Object, or Enterprise Event concepts;
- introduce a new database or infrastructure platform;
- implement production IAM or claim tenant isolation;
- use confidential industrial data;
- add AI-generated trust without human approval;
- expand into UI, semantic search, agent behavior, ERP, or bulk ingestion;
- require destructive migration or silent data loss;
- turn minimum context references into the complete enterprise ontology.

---

## 20. Definition of Release Completion

Release 1.8 is complete within scope when the integrated candidate is independently reviewed and demonstrates a governed, persistent, auditable, filterable, paginated Knowledge Object backend on PostgreSQL with structured evidence, provenance, lifecycle, concurrency, and minimum context.

Completion does not mean production readiness, real-data authorization, end-user usability, AI capability, or pilot success.
