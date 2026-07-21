# T01 Release Contracts Report

Report schema version: `smartcoat-execution-report-v2.0`

Thread ID: T01

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/39

Branch: `thread/18-01-release-contracts`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/50

Final status: `READY FOR INDEPENDENT RE-REVIEW`

## Objective

Validate and correct the six Release 1.8 T01 ADR proposals against the current
domain, platform-envelope, governance, Enterprise Event, persistence, API, and
accepted ADR contracts. Apply the eight architecture directions from
independent PR review `4749452113`, preserve implementation boundaries, and
record correction evidence without changing product code, schemas,
persistence, migrations, API routes, dependencies, tests, CI, or the Proposed
status of any ADR.

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

The initial validation cycle added only the report. Correction Cycle 1 modifies
the six proposed ADRs and the authorized active-release/status sections of:

- `AGENTS.md`
- `docs/project/PROJECT_STATE.md`

No implementation path is modified. Relative to the release branch, the T01
diff is exactly these nine paths.

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
- PR #50 and review `4749452113` retrieval through the GitHub connector
- `/Users/mohsenjamshidi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -c '<Correction Cycle 1 contract assertion harness>'`
- `/Users/mohsenjamshidi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -c '<Markdown local-link validator>'`
- `/Users/mohsenjamshidi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -c '<owned-path and untracked-file validator>'`
- `/Users/mohsenjamshidi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -c '<secret, environment, binary, and confidential-data validator>'`

Long inline Python scanner bodies are retained in the execution transcript. The
commands used Python 3.12.13 from the bundled workspace runtime and wrote no
repository files.

## Actual Results

| Method or Command | Actual Result | Evidence |
|---|---|---|
| PR #50 and review preflight | PASS | PR is open, draft, unmerged, based on `release/1.8-knowledge-capture-core`, and reviewed head and remote both equal `960050e494571b024ec0193077a779bb30b0c8b3`; review `4749452113` records 89/100 and D01-D08. |
| First correction assertion invocation | FAIL: Python did not execute | Shell interpreted Markdown backticks in a double-quoted `python -c` argument. The failed invocation is retained and no contract result is claimed from it. |
| Corrected ADR naming and status scan | PASS | Exactly ADR-0020 through ADR-0025 exist in scope, all six state `Status: Proposed`, and none appears in the Accepted ADR index. |
| Lifecycle and review invariant scan | PASS | Sole lifecycle authority, all eight projection rows, history-based draft distinction, generic-write prohibition, and contradiction fail-closed rules are present. |
| Evidence and provenance field-name scan | PASS | Application canonicality, proposal/adapter boundary, ID-only envelope projection, all nine canonical provenance names, honest legacy nulls, versioning, and collision behavior are present. |
| Organization and confidentiality scan | PASS | UUID identity, derived envelope ID, required organization, structured owner, creator distinction, five confidentiality values, organization inheritance/isolation, and fail-closed legacy behavior are present. |
| Cursor contract scan | PASS | Fixed sort, non-null UTC microsecond position, exact filter fingerprint, keyset predicate, page-size rule, six deterministic errors, security disclaimer, and mutation limitation are present. |
| Context identity and duplicate scan | PASS | Required field contract, UUID normalization, external-source rule, unique key, duplicate/version rejection, organization inheritance/isolation, and no-silent-merge rule are present. |
| Active-release authority scan | PASS | Both authorized files mark Release 1.7 completed, Release 1.8 active, and point to the Definition Pack and issue #38. |
| Legacy conflicting-term scan | PASS | No A0-A5, retired confidentiality, legacy review-state, deletion-state, or tenant/company synonym appears in the six ADRs. |
| Markdown-link validation | PASS | 400 Markdown files, 112 local links, and 0 broken local targets. |
| Owned-path and unexpected-file check | PASS | Exactly nine authorized branch/worktree diff paths; zero unexpected paths, missing expected paths, or untracked files. |
| Tests, MyPy, PostgreSQL, Ruff, and format | SKIP | No implementation, schema, persistence, migration, API, dependency, test, or CI change is authorized. |
| Secret, `.env`, binary, and confidential-data scans | PASS | Final changed-path, diff-content, binary-numstat, secret-marker, credential, email, and industrial-detail checks found no prohibited artifact. |
| `git diff --check` | PASS | Final release-branch diff exits zero with no whitespace errors. |
| Report-v2 validation | PASS | Final report validation exits zero; G7 and G8 are recorded in the Release 1.8 gate table. |

## Original Validation Results at Reviewed Head

The following table preserves the initial validation evidence for reviewed head
`960050e494571b024ec0193077a779bb30b0c8b3`. Its FAIL and BLOCKED results are
historical inputs to Correction Cycle 1, not claims about the corrected files.

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

- [x] Every shared contract has one explicit source of truth.
  Evidence: ADR-0020 owns lifecycle/review/audit invariants; ADR-0021 owns
  revision, identity, governance, and transaction requirements; ADR-0022 owns
  deletion/deprecation; ADR-0023 owns pagination; ADR-0024 owns context; and
  ADR-0025 owns application evidence/provenance and the envelope adapter.
- [x] Existing lifecycle names are preserved.
  Evidence: the exact seven-value scan passed across definition, ADR, domain,
  and platform envelope.
- [x] Allowed and invalid transitions are unambiguous.
  Evidence: ADR-0020 retains the closed matrix and now defines every
  lifecycle-to-review projection, history-dependent draft behavior, and
  fail-closed contradiction rule.
- [x] Lifecycle state cannot be changed through generic update behavior.
  Evidence: ADR-0020 prohibits generic create/update payloads from writing
  lifecycle or review status and assigns lifecycle changes to explicit commands.
- [x] Revision and conflict semantics are deterministic.
  Evidence: ADR-0021 defines positive revisions, revision-predicate updates,
  stale conflict behavior, and validate-first no-op handling.
- [x] Delete and deprecate policy is explicit.
  Evidence: ADR-0022 defines draft eligibility, inbound-reference blockers,
  retained safe audit, confidential-content exclusion, atomic deletion, and the
  distinction from legal erasure or backup deletion.
- [x] Pagination stability and cursor semantics are explicit.
  Evidence: ADR-0023 defines the non-null fixed sort, normalized cursor fields,
  exact filter fingerprint, keyset predicate, deterministic errors, security
  boundary, and mutation-between-pages limitation.
- [x] Minimum context avoids implementing the full ontology.
  Evidence: ADR-0024 retains seven bounded context categories, defines embedded
  identity and duplicate behavior, and requires issue-level necessity approval
  before standalone entities or CRUD endpoints.
- [x] Evidence and provenance migration compatibility is explicit.
  Evidence: ADR-0025 defines exact provenance names, structured canonical
  evidence, deterministic legacy IDs and collisions, null/incomplete legacy
  facts, ID-only envelope projection, and a separately versioned future envelope.
- [x] Security and real-data exclusions are preserved.
  Evidence: every ADR retains bounded application claims; scans found no secret,
  environment file, binary, confidential industrial detail, or real dataset.
- [x] ADR and release indexes remain valid.
  Evidence: local links pass, numbering is sequential, and Proposed ADRs are
  correctly absent from the Accepted ADR index.
- [x] Report-v2 evidence and the independent-review correction loop are used.
  Evidence: this report preserves the original findings, records review
  `4749452113` and 89/100, records all eight correction groups and executed
  evidence, and leaves corrected-head acceptance to independent re-review.

## Cross-Contract Matrix

| Proposed ADR | Current domain models | Platform envelope and governance | Enterprise Event | Persistence and API | Review result |
|---|---|---|---|---|---|
| ADR-0020 lifecycle commands | Existing seven-value `LifecycleState` is preserved; current caller-writable model is identified as an implementation gap | Envelope review status is a read-only projection with every valid lifecycle/history mapping defined | `EnterpriseEvent` remains canonical; T07 owns typed Knowledge audit profile and fields | Explicit commands, generic-write rejection, T05 Unit of Work, single commit, rollback, audit read-only, and forgery rejection are normative | READY: contract is internally consistent; implementation remains in owner threads |
| ADR-0021 revision and mutation | UUID identity stays canonical; positive revision and deterministic no-op/stale semantics are defined | Derived envelope ID, organization, structured owner, confidentiality, and fail-closed legacy boundaries are defined | Previous/resulting revision belongs to the T07 typed profile | T05 owns migration mechanics and one transaction boundary; repositories may flush but not commit | READY: identity, mutation, migration ownership, and transaction authority are explicit |
| ADR-0022 deletion and deprecation | Existing lifecycle is preserved; only never-left-draft objects are deletable | Organization and governed-object inbound references fail closed; production legal/retention behavior remains excluded | Safe append-only events and a content-free deletion tombstone remain | Revision predicate, inbound-reference check, row/content delete, audit append, and one commit are atomic under T05 | READY: required audit no longer makes draft deletion unreachable |
| ADR-0023 cursor pagination | Future page model receives fixed non-null UTC/UUID position semantics | Every request reapplies organization, confidentiality, and permission checks; digest is not a security boundary | Not applicable to event representation | Exact keyset predicate, canonical filter fingerprint, page-size rule, six error codes, and mutation limitation are normative | READY: independent T06 and T09 implementations have deterministic inputs and errors |
| ADR-0024 minimum context | Replaces untyped UUIDs with a bounded embedded `ContextReference` contract | Identity kind, source boundary, organization inheritance, and cross-organization prohibition are explicit | Context audit effects remain within the T07 profile | Unique key, UUID normalization, duplicate/version rejection, and no-silent-merge behavior are explicit | READY: full ontology and standalone CRUD remain separately gated |
| ADR-0025 evidence and provenance | Structured EvidenceReference and nine exact provenance fields are canonical for the application | Current envelope remains a proposal/adapter target and receives evidence IDs only; legacy gaps are null, incomplete, and never falsely conformant | Evidence IDs and provenance can be referenced by the T07 profile without creating another event family | T03 owns required-field implementation; T05 owns exact migration; collisions reject deterministically | READY: schema authority, adapter, compatibility, and downstream ownership are explicit |

## Original Contract Findings and Cycle 1 Resolutions

The finding text below is preserved from the initial report and describes the
reviewed head. Each resolution records the independently issued decision now
encoded by Correction Cycle 1.

### F01 Lifecycle and review are two uncoordinated state machines

ADR-0020 correctly closes the lifecycle transition matrix, but the platform
envelope independently requires review statuses `not_reviewed`, `in_review`,
`accepted`, `validated`, `rejected`, and `needs_correction`. Neither the release
definition nor ADR-0020 says whether review status is derived, orthogonal, or
retired for the application contract. T02 and T04 could otherwise implement
contradictory combinations such as lifecycle `draft` with review `accepted`.

Resolution: C01/D01 makes lifecycle the sole authority and defines a read-only,
history-aware review projection plus fail-closed invalid combinations.

### F02 ADR-0025 overstates platform-envelope authority and compatibility

The platform schema README labels the envelope a controlled-pilot proposal, not
an Accepted architecture record. The envelope's evidence references remain
strings, while ADR-0025 says the accepted envelope already requires richer
evidence references and then proposes structured EvidenceReference objects.
Provenance names also diverge: current domain uses `created_by` and `method`, the
envelope uses `created_by`, `creation_method`, and `captured_at`, while ADR-0025
uses prose labels such as actor or creator, capture method, and recorded
timestamp. Silent implementation would create incompatible serializers.

Resolution: C02/D02 makes the Release 1.8 application domain canonical, keeps
the envelope a proposal and ID-only adapter target, and defines exact provenance,
legacy-null, schema-versioning, and collision rules.

### F03 Atomic audit behavior has no canonical representation or transaction owner

ADR-0020 requires object and immutable audit changes to be atomic. The release
definition allows Enterprise Event or a dedicated audit representation. Current
Knowledge and Event repositories each call `session.commit()` independently;
the public event route accepts caller-authored events; and Enterprise Event lacks
revision, reason, correlation, and most lifecycle-mutation event types. T04,
T05, and T07 cannot safely implement atomic audit until one representation and
unit-of-work boundary are selected.

Resolution: C03/D03 keeps `EnterpriseEvent` canonical, assigns the typed
Knowledge profile to T07 and the shared Unit of Work to T05, requires one commit
and rollback, prohibits public audit forgery, and makes normal audit access
read-only.

### F04 Draft deletion conflicts with mandatory create auditing

The release definition requires an immutable audit record for `create`.
ADR-0022 permits hard deletion only when the draft has no retained audit
relationship, then requires a retained deletion tombstone. If the ordinary
create event counts as a retained audit relationship, no created draft is ever
eligible for the advertised delete use case.

Resolution: C04/D04 states that required audit events are not inbound-reference
blockers, retains safe append-only events and a content-free tombstone, and
deletes object row/content atomically under the shared Unit of Work.

### F05 Identity, organization, owner, and confidentiality mappings are missing

Current domain identity is UUID, owner is an optional string, and organization
and confidentiality are absent. The platform envelope requires a namespaced
string object ID, `organization_id`, structured owner, confidentiality, purpose
decisions, and review metadata. The release definition requires organization
boundary metadata but does not decide how v2 maps the existing UUID primary key
or which governance proposal is authoritative. This can cause incompatible
domain, API, and migration designs.

Resolution: C05/D05 retains application UUID identity, derives the envelope ID,
requires organization, structured owner, and five-value confidentiality for new
v2 records, and assigns fail-closed legacy migration mechanics to T05.

### F06 Pagination and context semantics are not deterministic enough

ADR-0023 does not require a cursor fingerprint or signature bound to the exact
normalized filters and sort, and it does not define timestamp precision or null
ordering. ADR-0024 allows either UUID or governed external identifier and says
duplicate/version behavior is deterministic without selecting reject, merge,
or replace semantics. Separate threads could produce mutually incompatible
cursor codecs and context identity rules.

Resolution: C06 and C07/D06-D07 define the exact cursor position, canonical
filter fingerprint, keyset predicate, deterministic errors, context identity,
unique key, duplicate/version rejection, and organization isolation.

### F07 Active release authority is stale outside the T01 branch diff

`AGENTS.md` and `docs/project/PROJECT_STATE.md` still name Release 1.7 as active,
while the Release 1.8 master prompt says T01 must synchronize stale active-release
documentation before implementation contracts are accepted. This run was
explicitly validation and report only, so those files were not changed. Their
stale status must be corrected in an authorized T01 correction cycle.

Resolution: C08/D08 updates only the authorized active-release/status sections;
both files now mark Release 1.7 completed and Release 1.8 active and link the
Definition Pack and issue #38.

## Architecture Impact

Correction Cycle 1 modifies the six Proposed ADRs but does not accept them. It
encodes the independent D01-D07 directions as one v2 contract package: lifecycle
is authoritative; review is projected; UUID application identity is preserved;
evidence/provenance is canonical behind an explicit envelope adapter; mutations
and typed Enterprise Event audit append commit atomically under T05; pagination
and context behavior are deterministic; and legacy gaps fail closed.

Accepted ADR-0005, ADR-0015, ADR-0016, ADR-0017, and ADR-0019 remain unchanged:
domain models remain canonical, services own behavior, repositories own
persistence, mappers remain bidirectional, and routes remain thin. No dependent
thread may treat ADR-0020 through ADR-0025 as Accepted until independent
re-review authorizes that status change and Wave 1.

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
- Reviewer score 89/100 applies to reviewed head `960050e494571b024ec0193077a779bb30b0c8b3`,
  not to the corrected final SHA. Independent re-review is still required.
- The provisional weighted score uses the retained 89 only because the scoring
  contract requires the recorded reviewer score; it is not corrected-head
  acceptance. The prior 79 cap remains authoritative until independent re-review.
- No T02 through T10 implementation was started.

## Lost Points and Correction Items

| Item | Source | Points | Status | Action or Evidence |
|---|---|---:|---|---|
| C01 | Lifecycle and review projection | 4 | RESOLVED | ADR-0020 defines sole lifecycle authority, eight projection rows, audit-history draft distinction, generic-write prohibition, and contradiction invariants. |
| C02 | Structured evidence and envelope boundary | 4 | RESOLVED | ADR-0025 defines application canonicality, proposed-envelope adapter, ID-only projection, exact provenance names, legacy nulls, versioning, and collisions. |
| C03 | Audit representation and transaction owner | 4 | RESOLVED | ADR-0020 through ADR-0022 keep Enterprise Event canonical, assign T07 profile ownership and T05 Unit of Work, one commit, rollback, read-only audit, and forgery prevention. |
| C04 | Draft-delete eligibility | 3 | RESOLVED | ADR-0022 excludes required audit from inbound blockers and defines atomic object/content deletion, retained safe events, and content-free tombstone fields. |
| C05 | Identity and minimum governance mapping | 3 | RESOLVED | ADR-0021, ADR-0024, and ADR-0025 define UUID identity, derived envelope ID, organization, owner, creator, confidentiality, isolation, and fail-closed legacy rules. |
| C06 | Cursor determinism | 1 | RESOLVED | ADR-0023 defines fixed ordering, normalized position, canonical fingerprint, exact keyset predicate, named errors, digest limits, and mutation behavior. |
| C07 | Context identity and duplicates | 1 | RESOLVED | ADR-0024 defines fields, identity kinds, normalization, unique key, duplicate/version rejection, organization inheritance, and standalone-entity gate. |
| C08 | Active-release documents | 1 | RESOLVED | Authorized status sections mark Release 1.7 completed and Release 1.8 active and link the Definition Pack and issue #38. |
| C09 | Independent corrected-head re-review | 11 | OPEN | The reviewed head's authoritative 89/100 leaves eleven reviewer points open until independent ChatGPT reviews the final SHA, assigns a new score, and accepts or returns further corrections. Codex cannot self-resolve this item. |

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 24 | D01-D08 are encoded and every requested contract assertion passes. | One point remains C09 because the corrected head has not received independent re-review. |
| Scope and acceptance criteria | 20 | 20 | All issue #39 documentation criteria are evidenced; only nine authorized paths changed and no dependent implementation began. | None. |
| Architecture and North-Star alignment | 15 | 15 | Canonical domain, human trust, explicit adapter, atomic audit, governance, and bounded-context rules align. | None. |
| Verification, tests, or validation | 15 | 15 | Links, ADR status, eight contract scans, ownership, diff, report-v2, and safety checks pass; failed invocation is retained. | None. |
| Security, privacy, and data governance | 10 | 10 | Synthetic/generalized boundary held and prohibited-artifact scans passed. | None. |
| Documentation and traceability | 10 | 10 | Original findings, review ID/score, eight corrections, matrix, checks, gates, and history are preserved and updated. | None. |
| Maintainability and clarity | 5 | 5 | Exact machine vocabulary, downstream ownership, deterministic errors, and scope boundaries are explicit. | None. |
| Total | 100 | 99 | All Codex-executable correction work is complete. | One point is assigned to open item C09; Codex does not self-approve the proposed ADRs. |

## ChatGPT Reviewer Score

Reviewer score: 89/100

Reviewer total: 89

Reviewer evidence: Review `4749452113` scored head `960050e494571b024ec0193077a779bb30b0c8b3`; the score is retained pending corrected-head re-review.

Review ID: `4749452113`

Reviewed head: `960050e494571b024ec0193077a779bb30b0c8b3`

Reviewer status at that head: `CORRECTION REQUIRED`

The 89/100 score is retained as required but does not review or accept the
corrected final SHA. Independent re-review remains required before any ADR may
be accepted or Wave 1 authorized.

## Final Score

Provisional weighted score: 93.0

Gate-adjusted score: 79

Calculation: `0.40 x 99 + 0.60 x 89 = 93.0`; G3 failure caps the
provisional score at 79 pending independent corrected-head re-review.

## Critical-Gate Declaration

| Gate | Status | Evidence |
|---|---|---|
| G1 Verified claims | PASS | Every claim is tied to executed output or a named repository contract; failed scanner attempts are retained. |
| G2 Confidential data | PASS | Secret, environment, binary, identifier, and confidential-data checks found no prohibited artifact. |
| G3 Approved scope and architecture | FAIL | Review `4749452113` authorized D01-D08 and the edits remain in scope, but the corrected architecture has not yet passed independent re-review and all six ADRs remain Proposed. |
| G4 Required validation | PASS | All T01-requested validation categories ran; non-applicable code and database tests are marked SKIP. |
| G5 File ownership | PASS | Branch/worktree diff is exactly six T01 ADRs, the report, `AGENTS.md`, and `docs/project/PROJECT_STATE.md`; no unexpected file exists. |
| G6 Acceptance completeness | PASS | All issue #39 documentation acceptance criteria and C01-C08 are evidenced complete; C09 is independent review, not missing Codex correction work. |

Critical-gate result: FAIL

## Release 1.8 Additional Gates

| Gate | Status | Evidence |
|---|---|---|
| G7 Persistence alignment and PostgreSQL evidence | PASS | T01 changes no persistence. ADR-0020 through ADR-0022 assign one T05 Unit of Work, fail-closed migration mechanics, revision predicates, and rollback; live PostgreSQL proof remains a required T05 gate. |
| G8 Lifecycle, trust, and audit bypass prevention | PASS | ADR-0020 prohibits generic lifecycle/review writes, defines all projection invariants, requires explicit commands and atomic audit, blocks public audit forgery, and exposes audit read-only. |

## Correction-Cycle History

| Cycle | Starting Score | Findings | Corrections | Ending Score | Validation Evidence | Status |
|---:|---:|---|---|---:|---|---|
| 1 | 100 | Seven contract groups were incomplete or contradictory; three first-pass scanner invocations, one methodology, and one report EOF check also failed. | Re-ran corrected scanners, fixed the report-only EOF defect, built the cross-contract matrix, converted all 21 lost points into C01-C07, and made no unauthorized ADR decision. | 79 | PR/worktree preflight, 112 local links, ADR sequence/status, vocabulary scans, matrix, corrected diff, ownership, security, and report-v2 validation. | BLOCKED |
| 2 | 79 | Independent Correction Cycle 1 review `4749452113` scored the reviewed head 89/100, issued D01-D08, split pagination/context into C06/C07, and authorized C08 status synchronization. | Encoded D01-D07 in all six Proposed ADRs; updated only authorized release-status sections; resolved C01-C08; rebuilt matrix, scores, gates, and evidence. | 99 | 400 Markdown files, 112 local links, six Proposed ADRs, eight passing contract scan groups, exact nine-path ownership, report-v2, diff, and safety validation. | OPEN |

## Recommended Follow-up Issues

- Keep C01 through C09 and their evidence in issue #39 and PR #50 so T01 remains
  the single owner of shared Release 1.8 contracts and review history.
- Keep issue #35 independently traceable and incorporate its migration-to-model
  acceptance criteria only after T01 chooses the migration authority.
- Keep issue #36 independently traceable; do not mix repository-wide Ruff debt
  into this ADR correction cycle.
- Do not start T02 through T10 until independent review confirms the corrected
  T01 head, accepts or otherwise disposes of the six Proposed ADRs, and
  explicitly authorizes Wave 1.

## Original Blockers and Issued Decisions

The five blocker analyses below are preserved from the initial report. Review
`4749452113` supplied the decisions now encoded in the ADRs, so none remains a
human-decision blocker for independent re-review.

### B01 Lifecycle and review authority - RESOLVED

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

Issued decision: D01/C01 adopts this direction with lifecycle as sole authority
and a history-aware read-only projection.

### B02 Evidence, provenance, and envelope version - RESOLVED

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

Issued decision: D02/C02 keeps the current envelope unchanged as a proposal and
ID-only adapter target; a future structured envelope requires a separate version.

### B03 Audit representation and transaction ownership - RESOLVED

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

Issued decision: D03/C03 preserves Enterprise Event, assigns the typed profile
to T07 and the shared database Unit of Work to T05, and requires one commit or
full rollback.

### B04 Draft deletion eligibility - RESOLVED

Question: Does an ordinary create audit event count as the retained audit
relationship that blocks hard deletion?

Options: Treat only downstream trust-bearing references as blockers; let every
audit event block deletion; or remove draft hard deletion from Release 1.8.

Consequences: Treating create audit as a blocker makes the promised draft-delete
use case unreachable; ignoring all audit relationships risks historical loss.

Recommended decision: Preserve create and deletion tombstones, but define only
downstream trust-bearing object, decision, or legal-retention relationships as
deletion blockers.

Issued decision: D04/C04 makes required audit non-disqualifying, limits blockers
to governed inbound object references, and retains a safe content-free tombstone.

### B05 Identity and governance boundary - RESOLVED

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

Issued decision: D05/C05 retains UUID, derives `knowledge_object:<uuid>`,
requires organization, structured owner, and confidentiality for new v2 records,
and assigns exact fail-closed migration mechanics to T05. Production purpose
enforcement remains explicitly outside scope.

## Blockers

No human-decision blocker remains in T01 Correction Cycle 1. C09 remains open
because independent ChatGPT must review the corrected final SHA. Wave 1 remains
unauthorized, all six ADRs remain Proposed, and PR #50 remains draft.

Recommendation: `READY FOR INDEPENDENT RE-REVIEW`.
