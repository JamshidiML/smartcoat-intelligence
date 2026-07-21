# T01 Release Contracts Report

Report schema version: `smartcoat-execution-report-v2.0`

Thread ID: T01

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/39

Branch: `thread/18-01-release-contracts`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/50

Final status: `BLOCKED — HUMAN DECISION REQUIRED`

## Objective

Validate the six Release 1.8 T01 ADR proposals against the current domain,
platform-envelope, governance, Enterprise Event, persistence, API, and accepted
ADR contracts. Record implementation guardrails and contradictions without
changing product code, persistence, migrations, API routes, dependencies, CI,
or the Proposed status of any ADR.

Starting branch SHA: `ab7a7a78a4228f9303955e45653b5665571c6b8d`.

Release-base SHA: `fb3c2859922681998dd6b68cba75462bccbc0f5f`.

## Files Changed

The T01 branch contains these issue-owned paths relative to the release branch:

- `architecture/ADR/ADR-0020_Governed_Knowledge_Lifecycle_Commands.md`
- `architecture/ADR/ADR-0021_Optimistic_Revision_And_Controlled_Mutation.md`
- `architecture/ADR/ADR-0022_Draft_Deletion_And_Trusted_Record_Deprecation.md`
- `architecture/ADR/ADR-0023_Cursor_Based_Knowledge_Pagination.md`
- `architecture/ADR/ADR-0024_Minimum_Domain_Context_References.md`
- `architecture/ADR/ADR-0025_Structured_Evidence_And_Provenance_Compatibility.md`
- `docs/execution/reports/release_1_8/T01_RELEASE_CONTRACTS_REPORT.md`

This validation cycle adds only the report. It does not modify the six ADR
proposals or any implementation path.

## Methods and Commands Executed

- `git fetch origin`
- `git status --short --untracked-files=all`
- `git branch --show-current`
- `git rev-parse HEAD`
- `git rev-parse @{upstream}`
- `git diff --name-status origin/release/1.8-knowledge-capture-core...HEAD`
- `git diff --check origin/release/1.8-knowledge-capture-core...HEAD`
- `/Users/mohsenjamshidi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -c '<standard-library Markdown link resolver>'`
- `/Users/mohsenjamshidi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -c '<ADR naming, numbering, and status scanner>'`
- `/Users/mohsenjamshidi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -c '<lifecycle and review vocabulary scanners>'`
- `/Users/mohsenjamshidi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -c '<evidence, provenance, organization, and confidentiality contract scanners>'`
- `rg -n -i '\b(A[0-5]|highly_confidential|pending_review|under_review|published|archived|soft_deleted|tenant_id|company_id)\b' <T01 ADR and current-contract paths>`
- `rg -n 'payload: KnowledgeObject|lifecycle_state|@router\.(post|put|patch|delete)|response_model=list\[KnowledgeObject\]|expected_revision|revision|next_cursor|evidence: list\[str\]|related_entities: list\[UUID\]' src/smartcoat/domain src/smartcoat/services src/smartcoat/storage src/smartcoat/api/routes/knowledge.py`
- `rg -n 'class EventType|KNOWLEDGE_|session\.commit|@router\.post|previous_state|new_state|previous_revision|resulting_revision|correlation|reason|append' <event, service, repository, route, and event-model paths>`
- `python scripts/validate_execution_reports.py docs/execution/reports/release_1_8/T01_RELEASE_CONTRACTS_REPORT.md`

Long inline Python scanner bodies are retained in the execution transcript. The
commands used Python 3.12.13 from the bundled workspace runtime and wrote no
repository files.

## Actual Results

| Method or Command | Actual Result | Evidence |
|---|---|---|
| PR #50 metadata | PASS: open draft, unmerged, correct base and head | Base is `release/1.8-knowledge-capture-core`; head is `thread/18-01-release-contracts`. |
| Worktree and upstream preflight | PASS: clean and exact | Local HEAD, upstream, and remote head all equaled `ab7a7a78a4228f9303955e45653b5665571c6b8d`. |
| Markdown-link validation | PASS: initial and final runs, 399 then 400 Markdown files, 112 local links, 0 broken | Python 3.12 standard-library local-target resolution before and after report creation. |
| First ADR scanner invocation | FAIL: scanner did not execute | An f-string quoting error produced `SyntaxError`; no result was claimed. |
| Corrected ADR naming and status scan | PASS: six files numbered 0020 through 0025, no duplicates, all Proposed | No proposed ADR appears in the Accepted ADR index. |
| Lifecycle vocabulary scan | PASS: exact seven canonical values align | Definition, ADR-0020, domain enum, and platform envelope each contain `draft`, `captured`, `reviewed`, `validated`, `approved`, `rejected`, and `deprecated`. |
| First review-status scan | FAIL: discarded methodology | A prose occurrence of `accepted` caused a false positive; the result was not used. |
| Corrected review-status scan | FAIL: T01 does not reconcile the independent review contract | Platform values are `not_reviewed`, `in_review`, `accepted`, `validated`, `rejected`, and `needs_correction`; ADR-0020 does not define their lifecycle mapping. |
| First evidence and provenance scanner invocation | FAIL: scanner did not execute | Shell and Python quoting caused a syntax error; no alignment result was claimed. |
| Corrected evidence and provenance scan | FAIL: current and proposed contracts do not align | Domain evidence is `list[str]`; envelope evidence items are strings; domain and envelope provenance field names differ; ADR-0025 proposes structured objects without a versioned envelope decision. |
| First organization and confidentiality scanner invocation | FAIL: scanner did not execute | Quoting produced a `NameError`; no alignment result was claimed. |
| Corrected organization and confidentiality scan | FAIL: canonical values exist but application mapping is absent | Envelope and governance agree on five confidentiality values; current domain and the six ADRs do not define object-level `organization_id` and confidentiality compatibility. |
| Legacy conflicting-term scan | PASS: no scoped matches | No A0-A5 values, `highly_confidential`, legacy review-state synonyms, `tenant_id`, or `company_id` were found in the six ADRs, current domain, or platform envelope. |
| Cross-contract matrix | FAIL: seven correction groups remain | Lifecycle/review, evidence/provenance, audit/transaction, deletion, identity/governance, query/context, and active-release authority are unresolved. |
| Code, typing, Ruff, and PostgreSQL tests | SKIP: not applicable to this validation-only documentation cycle | No product code, persistence, migration, API, dependency, or CI file changed. |
| `git diff --check` before report | PASS: no whitespace errors | Six-ADR branch diff exited zero. |
| Final owned-path and unexpected-file check | PASS: exactly seven T01 paths | Six proposed ADRs plus this report; no other branch-diff path. |
| Secret, `.env`, binary, and confidential-data scans | PASS: no prohibited artifact found | Pattern scans, binary numstat inspection, path checks, and manual review of generalized contract prose passed. |
| First final `git diff --check` | FAIL: report had one extra blank line at EOF | The seven-path check identified the exact report line; no pass was claimed. |
| Corrected final `git diff --check` | PASS: no whitespace errors | Seven-path branch diff exited zero after removing the report-only EOF defect. |
| Report-v2 validation | PASS: report satisfies the existing v2 parser | Validator exited zero for this report; G7 and G8 are recorded separately because v2 validates only G1 through G6. |

## Acceptance-Criteria Evidence

- [ ] Every shared contract has one explicit source of truth.
  Evidence: the cross-contract matrix finds competing or incomplete authorities
  for review status, evidence/provenance, audit representation, identity, and
  governance metadata.
- [x] Existing lifecycle names are preserved.
  Evidence: the exact seven-value scan passed across definition, ADR, domain,
  and platform envelope.
- [ ] Allowed and invalid transitions are unambiguous.
  Evidence: ADR-0020 has a closed lifecycle matrix, but it does not define how
  the independent platform `review.status` values change with those commands.
- [x] Lifecycle state cannot be changed through generic update behavior.
  Evidence: ADR-0020 explicitly prohibits create or update payloads from
  assigning trusted lifecycle states; implementation remains future work.
- [ ] Revision and conflict semantics are deterministic.
  Evidence: ADR-0021 defines expected revision and 409 behavior, but no-op
  handling is only preferred, and legacy row initialization and API migration
  remain undecided.
- [ ] Delete and deprecate policy is explicit.
  Evidence: the broad policy is stated, but the required create audit event can
  conflict with the rule that an eligible draft has no retained audit relation.
- [ ] Pagination stability and cursor semantics are explicit.
  Evidence: ordering and tie-breaker are stated, but exact filter binding,
  timestamp normalization, cursor integrity, and changed-query behavior are not
  normative enough for independent implementations.
- [x] Minimum context avoids implementing the full ontology.
  Evidence: ADR-0024 limits Release 1.8 to seven typed reference categories and
  requires separate approval for standalone entities.
- [ ] Evidence and provenance migration compatibility is explicit.
  Evidence: ADR-0025 names an adapter direction, but required legacy actor/time
  values, field names, envelope versioning, duplicate policy, and old-output
  retirement are unresolved.
- [x] Security and real-data exclusions are preserved.
  Evidence: every ADR retains synthetic/generalized boundaries and rejects raw
  file ingestion, production IAM claims, or real-data authorization.
- [x] ADR and release indexes remain valid.
  Evidence: local links pass, numbering is sequential, and Proposed ADRs are
  correctly absent from the Accepted ADR index.
- [x] Report-v2 evidence and the independent-review correction loop are used.
  Evidence: this report passes the current validator and leaves reviewer score
  pending for independent ChatGPT review.

## Cross-Contract Matrix

| Proposed ADR | Current domain models | Platform envelope and governance | Enterprise Event | Persistence and API | Review result |
|---|---|---|---|---|---|
| ADR-0020 lifecycle commands | `LifecycleState` has the same seven values, but the base object permits caller-supplied lifecycle | Envelope has the same lifecycle enum plus a separate six-value `review.status` contract | Event types lack update, review, validation, approval, rejection, reopen, and deprecation events | POST accepts a complete Knowledge Object; no transition command or atomic audit transaction exists | BLOCKED: define lifecycle-to-review invariants and legacy create behavior |
| ADR-0021 revision and mutation | No revision field or command model exists | Envelope has no revision field or compatibility rule | Event has no previous or resulting revision fields | ORM and SQL have no revision column; repository commits internally; API has no update route | BLOCKED: decide migration default, no-op rule, identity ownership, and transaction boundary |
| ADR-0022 deletion and deprecation | Lifecycle includes `draft`, `approved`, and `deprecated`, but no deletion behavior exists | Governance requires explicit human approval for deletion and fail-closed unknowns | Event types have no draft-delete tombstone or deprecation event | No delete route or repository method exists | BLOCKED: resolve whether the mandatory create audit record disqualifies every draft from deletion |
| ADR-0023 cursor pagination | Domain has no page or cursor model | Envelope does not define query pagination | Not applicable to event representation | Service and repository return an unordered limited list; API returns a plain list | CORRECTION REQUIRED: bind cursor to normalized filters and ordering and define integrity and precision rules |
| ADR-0024 minimum context | `related_entities` is an untyped UUID list | Envelope relationships use string target IDs and relationship types; governance requires organization isolation | Event has one optional related UUID only | JSONB stores raw UUID strings; API exposes the current full domain object | BLOCKED: choose canonical reference identity, duplicate, version-conflict, and organization-boundary rules |
| ADR-0025 evidence and provenance | Evidence is `list[str]`; provenance is four optional fields | Envelope evidence references are strings; provenance is richer and required; the envelope and governance files remain proposals | Event evidence is also `list[str]` | JSONB and mappers preserve old shapes; API accepts and returns old shapes | BLOCKED: version the envelope or define a non-conflicting adapter with exact machine field names and unknown-value rules |

## Contract Conflicts

### F01 Lifecycle and review are two uncoordinated state machines

ADR-0020 correctly closes the lifecycle transition matrix, but the platform
envelope independently requires review statuses `not_reviewed`, `in_review`,
`accepted`, `validated`, `rejected`, and `needs_correction`. Neither the release
definition nor ADR-0020 says whether review status is derived, orthogonal, or
retired for the application contract. T02 and T04 could otherwise implement
contradictory combinations such as lifecycle `draft` with review `accepted`.

### F02 ADR-0025 overstates platform-envelope authority and compatibility

The platform schema README labels the envelope a controlled-pilot proposal, not
an Accepted architecture record. The envelope's evidence references remain
strings, while ADR-0025 says the accepted envelope already requires richer
evidence references and then proposes structured EvidenceReference objects.
Provenance names also diverge: current domain uses `created_by` and `method`, the
envelope uses `created_by`, `creation_method`, and `captured_at`, while ADR-0025
uses prose labels such as actor or creator, capture method, and recorded
timestamp. Silent implementation would create incompatible serializers.

### F03 Atomic audit behavior has no canonical representation or transaction owner

ADR-0020 requires object and immutable audit changes to be atomic. The release
definition allows Enterprise Event or a dedicated audit representation. Current
Knowledge and Event repositories each call `session.commit()` independently;
the public event route accepts caller-authored events; and Enterprise Event lacks
revision, reason, correlation, and most lifecycle-mutation event types. T04,
T05, and T07 cannot safely implement atomic audit until one representation and
unit-of-work boundary are selected.

### F04 Draft deletion conflicts with mandatory create auditing

The release definition requires an immutable audit record for `create`.
ADR-0022 permits hard deletion only when the draft has no retained audit
relationship, then requires a retained deletion tombstone. If the ordinary
create event counts as a retained audit relationship, no created draft is ever
eligible for the advertised delete use case.

### F05 Identity, organization, owner, and confidentiality mappings are missing

Current domain identity is UUID, owner is an optional string, and organization
and confidentiality are absent. The platform envelope requires a namespaced
string object ID, `organization_id`, structured owner, confidentiality, purpose
decisions, and review metadata. The release definition requires organization
boundary metadata but does not decide how v2 maps the existing UUID primary key
or which governance proposal is authoritative. This can cause incompatible
domain, API, and migration designs.

### F06 Pagination and context semantics are not deterministic enough

ADR-0023 does not require a cursor fingerprint or signature bound to the exact
normalized filters and sort, and it does not define timestamp precision or null
ordering. ADR-0024 allows either UUID or governed external identifier and says
duplicate/version behavior is deterministic without selecting reject, merge,
or replace semantics. Separate threads could produce mutually incompatible
cursor codecs and context identity rules.

### F07 Active release authority is stale outside the T01 branch diff

`AGENTS.md` and `docs/project/PROJECT_STATE.md` still name Release 1.7 as active,
while the Release 1.8 master prompt says T01 must synchronize stale active-release
documentation before implementation contracts are accepted. This run was
explicitly validation and report only, so those files were not changed. Their
stale status must be corrected in an authorized T01 correction cycle.

## Architecture Impact

No architecture decision is accepted or modified by this report. The review
preserves accepted ADR-0005, ADR-0015, ADR-0016, ADR-0017, and ADR-0019: domain
models remain canonical, services own behavior, repositories own persistence,
mappers remain bidirectional, and routes remain thin. It prevents dependent
threads from treating six unresolved proposals as implementation authority.

The recommended direction is one explicit v2 contract package that maps
lifecycle and review, uses exact machine field names, preserves UUID application
identity while defining the platform-envelope boundary, makes audit mutation
internal and atomic, and version-controls legacy adapters.

## Security and Data Impact

Only repository contracts and generalized examples were read. No raw file,
industrial record, customer or supplier fact, formulation, price, email,
credential, personal data, or confidential dataset was introduced. The six ADRs
remain proposals and do not authorize production IAM, tenant isolation, real
data, file ingestion, legal deletion, or external evidence authenticity claims.

Pattern scans found no secret assignment, private-key marker, `.env` path,
binary diff, email address, currency amount, or composition percentage in the
owned branch diff. Generic words such as confidentiality, formulation, and
supplier occur only in scope and exclusion language and were manually reviewed.

## Known Limitations

- External HTTP links were not fetched; local Markdown targets were validated.
- Product tests, MyPy, Ruff, formatting, migrations, and PostgreSQL were not run
  because this cycle changed no implementation or persistence file.
- Pattern scans reduce risk but are not a substitute for a dedicated secret
  scanner or legal/confidentiality review.
- The current report-v2 validator knows G1 through G6 only. G7 and G8 are
  declared in a separate Release 1.8 table below.
- No independent reviewer score is recorded yet.
- No T02 through T10 implementation was started.

## Lost Points and Correction Items

| Item | Source | Points | Status | Action or Evidence |
|---|---|---:|---|---|
| C01 | Lifecycle and review-status matrix | 4 | BLOCKED | Decide whether review status is derived, orthogonal, or replaced, then define every valid lifecycle and review combination. |
| C02 | Evidence, provenance, and platform-envelope compatibility | 4 | BLOCKED | Select the authoritative schema version and exact machine field names, then define honest legacy unknown-value behavior. |
| C03 | Audit representation and atomic transaction boundary | 4 | BLOCKED | Select Enterprise Event or dedicated audit representation and assign one service or unit-of-work transaction owner. |
| C04 | Draft-delete eligibility contradiction | 3 | BLOCKED | Clarify which retained audit relationships block deletion and preserve create and delete audit evidence without making deletion impossible. |
| C05 | Identity, organization, owner, and confidentiality mapping | 3 | BLOCKED | Approve the UUID-to-envelope identity boundary and required governance metadata contract. |
| C06 | Pagination and context determinism | 2 | OPEN | Add filter-bound cursor integrity, precision rules, and exact context duplicate and version behavior. |
| C07 | Stale active-release documentation | 1 | OPEN | Update active-release wording in T01-owned or explicitly authorized project guidance before Wave 1. |

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 21 | Complete file review, executed scans, and source-backed conflict matrix. | Four points lost because the proposed contract set remains internally incomplete. |
| Scope and acceptance criteria | 20 | 14 | Validation and report stayed inside T01 and no dependent implementation began. | Six points lost for six unchecked issue criteria. |
| Architecture and North-Star alignment | 15 | 8 | Accepted architecture boundaries and human-controlled trust were preserved. | Seven points lost for unresolved lifecycle, schema, audit, identity, and migration authority. |
| Verification, tests, or validation | 15 | 15 | Required T01 links, indexes, vocabularies, diff, ownership, report, and security checks ran with failed attempts retained. | None. |
| Security, privacy, and data governance | 10 | 10 | Synthetic/generalized boundary held and prohibited-artifact scans passed. | None. |
| Documentation and traceability | 10 | 7 | Report links issue, branch, PR, commands, evidence, conflicts, gates, and corrections. | Three points lost because stale active-release guidance remains outside this validation-only edit. |
| Maintainability and clarity | 5 | 4 | Matrix assigns concrete downstream consequences and decisions. | One point lost until one canonical machine vocabulary and compatibility package is chosen. |
| Total | 100 | 79 | Critical architecture and completeness gates remain unresolved. | Twenty-one points are converted into C01 through C07. |

## ChatGPT Reviewer Score

Reviewer status: Pending

Independent ChatGPT review is required before any ADR may be accepted or Wave 1
may be authorized.

## Final Score

Provisional weighted score: Pending

Gate-adjusted score: Pending

## Critical-Gate Declaration

| Gate | Status | Evidence |
|---|---|---|
| G1 Verified claims | PASS | Every claim is tied to executed output or a named repository contract; failed scanner attempts are retained. |
| G2 Confidential data | PASS | Secret, environment, binary, identifier, and confidential-data checks found no prohibited artifact. |
| G3 Approved scope and architecture | FAIL | Proposed contracts conflict with platform, review, audit, identity, and migration authorities and cannot be self-approved. |
| G4 Required validation | PASS | All T01-requested validation categories ran; non-applicable code and database tests are marked SKIP. |
| G5 File ownership | PASS | Branch diff is limited to six T01 ADRs and the required T01 report. |
| G6 Acceptance completeness | FAIL | Six issue criteria remain unchecked and seven correction items remain unresolved. |

Critical-gate result: FAIL

## Release 1.8 Additional Gates

| Gate | Status | Evidence |
|---|---|---|
| G7 Persistence alignment and PostgreSQL evidence | BLOCKED | T01 changes no persistence, but revision, audit atomicity, schema versioning, and issue #35 migration authority must be decided before persistence implementation. |
| G8 Lifecycle, trust, and audit bypass prevention | BLOCKED | ADR-0020 states the prohibition, but lifecycle-review invariants, legacy create behavior, public event creation, and atomic audit ownership remain unresolved. |

## Correction-Cycle History

| Cycle | Starting Score | Findings | Corrections | Ending Score | Validation Evidence | Status |
|---:|---:|---|---|---:|---|---|
| 1 | 100 | Seven contract groups were incomplete or contradictory; three first-pass scanner invocations, one methodology, and one report EOF check also failed. | Re-ran corrected scanners, fixed the report-only EOF defect, built the cross-contract matrix, converted all 21 lost points into C01-C07, and made no unauthorized ADR decision. | 79 | PR/worktree preflight, 112 local links, ADR sequence/status, vocabulary scans, matrix, corrected diff, ownership, security, and report-v2 validation. | BLOCKED |

## Recommended Follow-up Issues

- Keep corrections C01 through C07 in issue #39 and PR #50 so T01 remains the
  single owner of shared Release 1.8 contracts.
- Keep issue #35 independently traceable and incorporate its migration-to-model
  acceptance criteria only after T01 chooses the migration authority.
- Keep issue #36 independently traceable; do not mix repository-wide Ruff debt
  into this ADR correction cycle.
- Do not start T02 through T10 until independent review confirms the corrected
  T01 head and explicitly authorizes Wave 1.

## Blockers

### B01 Lifecycle and review authority

Question: Is platform `review.status` an independent state machine, a derived
view of lifecycle commands, or replaced by lifecycle for Knowledge Object v2?

Options: Keep both with a complete invariant table; derive review status from
lifecycle and command history; or version the envelope and remove duplicate
review state from the application contract.

Consequences: Leaving both uncoordinated permits contradictory trust states and
different T02 and T04 implementations.

Recommended decision: Keep review detail as a command-owned record, derive its
summary status from accepted lifecycle commands, and publish an explicit mapping
table with invalid combinations.

### B02 Evidence, provenance, and envelope version

Question: Does Release 1.8 version the platform envelope to structured evidence,
or keep v1.1 string references and place EvidenceReference objects behind a
separate canonical application schema?

Options: Create an envelope v1.2 with exact structured fields; retain v1.1 and
add a versioned application wrapper; or defer structured evidence, which would
contradict Release 1.8 scope.

Consequences: Silent reinterpretation breaks existing schemas, mappers, API
payloads, and migration honesty.

Recommended decision: Publish a versioned envelope evolution and use one exact
snake_case vocabulary across domain, schema, persistence, and API. Preserve v1.1
strings only through a named legacy adapter.

### B03 Audit representation and transaction ownership

Question: Is the immutable audit record an Enterprise Event subtype or a
separate Audit Event model, and which layer owns the atomic transaction?

Options: Extend Enterprise Event with internal-only audit subtypes and a
service-owned unit of work; create a dedicated immutable Audit Event; or keep
separate repository commits, which cannot meet the atomicity requirement.

Consequences: Without one answer, object mutation can commit without audit or a
public client can fabricate audit history.

Recommended decision: Preserve Enterprise Event as the canonical carrier, add
an internal immutable audit subtype/command path, prohibit generic public audit
creation, and place object-plus-event commit ownership in one service-level unit
of work.

### B04 Draft deletion eligibility

Question: Does an ordinary create audit event count as the retained audit
relationship that blocks hard deletion?

Options: Treat only downstream trust-bearing references as blockers; let every
audit event block deletion; or remove draft hard deletion from Release 1.8.

Consequences: Treating create audit as a blocker makes the promised draft-delete
use case unreachable; ignoring all audit relationships risks historical loss.

Recommended decision: Preserve create and deletion tombstones, but define only
downstream trust-bearing object, decision, or legal-retention relationships as
deletion blockers.

### B05 Identity and governance boundary

Question: How does current UUID Knowledge Object identity map to the envelope's
namespaced string ID, structured owner, organization, confidentiality, purpose,
and review fields?

Options: Replace application UUIDs; retain UUIDs and map at the envelope
boundary; or leave the fields in generic metadata.

Consequences: Replacing IDs raises migration and relationship risk; generic
metadata weakens validation and organization isolation semantics.

Recommended decision: Retain UUID as the application and database primary key,
define a deterministic namespaced envelope ID at the schema boundary, and add
typed organization, owner, confidentiality, purpose, and review contracts rather
than hiding them in ungoverned metadata.

Recommendation: `BLOCKED — HUMAN DECISION REQUIRED`.
