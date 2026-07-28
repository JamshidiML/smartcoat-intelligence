# T09 Knowledge Object v2 API Contracts Report

Report schema version: `smartcoat-execution-report-v2.0`

Thread ID: T09

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/47

Branch: `thread/18-09-api-contracts`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/61

Final status: `READY FOR INDEPENDENT REVIEW`

## Objective

Implement Release 1.8 Wave 5 / T09 as an explicit, governed HTTP boundary for
the accepted Knowledge Object v2 domain, lifecycle, persistence, query, audit,
evidence, provenance, and context contracts.

Work began from exact Release SHA
`03db68fd710f3bdbe67ce4e077313fabb77d64d5`. Main remained protected at
`47df21458038d107bb7c7cb98dc6d23dd3b6d7e9`. Dependencies #41 through #46
were closed completed, including T08 administrative completion in #46. Parent
#38, T09 issue #47, and final integration issue #48 remained open. PR #49
remained open, draft, unmerged, and based on the exact Release SHA.

Implementation commit `2924c8e91bb3a7f5ed9c60830672765a949ab977`
adds seven operations under `/api/v2/knowledge` without changing the Release
1.7 `/knowledge`, `/events`, or `/decisions` route implementations. Draft PR
#61 targets `release/1.8-knowledge-capture-core`.

PR merge-ref Actions run `30350682417` validated implementation head
`2924c8e91bb3a7f5ed9c60830672765a949ab977`. Both required jobs passed. The
PostgreSQL 16 job executed all 82 tests in the five-file live matrix, including
all five strengthened T09 API tests with zero skips. The later report-only head
and its CI are necessarily external publication evidence because a commit
cannot contain its own SHA or subsequent workflow result.

This work uses synthetic test values only. It does not establish production
authentication, authorization, IAM, tenancy, row-level security, secret
management, rate limiting, public-internet readiness, UI completion, AI
extraction, semantic search, real-data authorization, full Release 1.8
completion, or production readiness.

## Files Changed

- `.env.example`
- `.github/workflows/ci.yml`
- `src/smartcoat/api/main.py`
- `src/smartcoat/api/routes/knowledge_v2.py`
- `src/smartcoat/api/knowledge_v2_schemas.py`
- `src/smartcoat/api/knowledge_v2_errors.py`
- `src/smartcoat/api/dependencies/knowledge_v2.py`
- `src/smartcoat/services/knowledge_v2_read_service.py`
- `src/smartcoat/core/config.py`
- `tests/test_knowledge_v2_api_schemas.py`
- `tests/test_knowledge_v2_api_dependencies.py`
- `tests/test_knowledge_v2_api_routes.py`
- `tests/test_knowledge_v2_openapi.py`
- `tests/integration/test_knowledge_v2_api_postgres.py`
- `docs/execution/reports/release_1_8/T09_API_CONTRACTS_REPORT.md`

Issue #47 comment `5085843355` declared these exact fifteen paths before
editing. No ownership amendment was required. No accepted T02-T08 contract,
legacy route implementation, migration, repository, mapper, ORM model, Unit of
Work, ADR, dependency definition, or package export file changed.

## Methods and Commands Executed

- `git fetch origin`
- `git rev-parse origin/release/1.8-knowledge-capture-core`
- `git rev-parse origin/main`
- `gh pr view 60 --repo JamshidiML/smartcoat-intelligence`
- `gh pr view 49 --repo JamshidiML/smartcoat-intelligence`
- `gh issue view 47 --repo JamshidiML/smartcoat-intelligence`
- `git worktree add -b thread/18-09-api-contracts <persistent-T09-path> 03db68fd710f3bdbe67ce4e077313fabb77d64d5`
- `python -m pip check`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python -m mypy src`
- `python -m pytest -q`
- `python -m pytest -q tests/test_knowledge_v2_api_schemas.py tests/test_knowledge_v2_api_dependencies.py tests/test_knowledge_v2_api_routes.py tests/test_knowledge_v2_openapi.py`
- `python -m pytest -q <affected-T02-through-T08-contract-paths>`
- `python -m pytest -q tests/test_knowledge_v2_api_schemas.py tests/test_knowledge_v2_api_dependencies.py tests/test_knowledge_v2_api_routes.py tests/test_knowledge_v2_openapi.py tests/test_api_persistent_routes.py`
- `python -m pytest -q tests/persistence`
- `python -m pytest -q tests/ingestion`
- `SMARTCOAT_RUN_LIVE_POSTGRES_TESTS=true SMARTCOAT_TEST_DATABASE_URL=<redacted-local-synthetic-test-dsn> python -m pytest -q tests/integration/test_knowledge_v2_api_postgres.py`
- `python -m pytest -q tests/test_validate_execution_reports.py`
- `python scripts/validate_execution_reports.py --require-count 21 <existing-reports>`
- `python <standard-library-Markdown-local-link-validator>`
- `git diff --check`
- `file <all-owned-paths>`
- `rg <secret-credential-email-personal-and-prohibited-data-patterns> <all-owned-paths>`
- `git commit -m "Implement governed Knowledge Object v2 API"`
- `git push -u origin thread/18-09-api-contracts`
- `gh pr create --draft --base release/1.8-knowledge-capture-core --head thread/18-09-api-contracts`
- `GitHub App create_pull_request repository=JamshidiML/smartcoat-intelligence base=release/1.8-knowledge-capture-core head=thread/18-09-api-contracts draft=true`
- `GitHub Actions run 30350682417`

The local live DSN used PostgreSQL 16 and an existing synthetic test database
whose name begins with `smartcoat_test`. Credentials are redacted. The T09
fixture used Alembic upgrade to current head, a randomized isolated schema,
guarded localhost and test-database inputs, and finalizer verification that the
schema no longer existed.

## Actual Results

| Method or Command | Actual Result | Evidence |
|---|---|---|
| Protected-state preflight | PASS | Release and main matched the two required SHAs; PR #60 was merged at the Release SHA; #41-#46 were closed completed; #47, #48, and #38 were open; PR #49 was open, draft, unmerged, and based on the Release SHA. |
| T09 absence and final-T10 check | PASS | No T09 branch, worktree, or PR existed before creation; issue #48 remained open and final integration work had not started. |
| Persistent branch and worktree | PASS | The required persistent T09 path was created on the exact requested branch and Release head, with a clean starting tree. |
| Starting pip check | PASS | No broken requirements were found. |
| Starting Ruff | PASS | The exact Release baseline had zero Ruff findings. |
| Starting format check | PASS | All 91 baseline files were formatted. |
| Starting MyPy | PASS | Baseline MyPy passed 60 source files. |
| Starting full pytest | PASS | 743 tests passed and 73 expected opt-in or configured tests skipped. |
| Ownership declaration | PASS | Issue #47 comment `5085843355` declared the exact fifteen-path ceiling before editing; no amendment followed. |
| Initial bundled-runtime Ruff invocation | FAIL: corrected runtime selection | The initially selected bundled interpreter did not contain Ruff. The shared Release 1.8 virtual environment was selected and all required tools ran there. |
| Initial focused static checks | FAIL: corrected implementation findings | Import ordering, format-only differences, and typed dictionary keyword construction were corrected before repository-wide Ruff, format, and MyPy passed. |
| First inherited T02 isolation regression | FAIL: corrected application composition | Eager v2 router loading caused the inherited API-main import-isolation test to fail. Lazy first-v2-request and OpenAPI composition retained the required v2 surface without eagerly loading the domain; all three isolation tests and legacy routes then passed. |
| First application-factory Ruff correction | FAIL: corrected composition form | An intermediate dynamic method assignment triggered a Ruff finding. A typed `SmartCoatAPI` subclass replaced it and both Ruff and MyPy passed. |
| T09 focused API contracts | PASS | 74 schema, dependency, route, and OpenAPI tests passed. |
| Complete API selection | PASS | 82 v2 and legacy API tests passed after correcting one nonexistent test-path invocation. |
| First complete API selection invocation | FAIL: corrected file name | `tests/test_api_routes.py` did not exist and collected no tests. The corrected command used `tests/test_api_persistent_routes.py`; 82 tests passed. |
| Affected T02-T08 regression | PASS | 659 accepted domain, lifecycle, persistence, query, audit, context, evidence, and provenance tests passed. |
| Persistence regression | PASS | All 41 persistence tests passed. |
| Ingestion compatibility | PASS | All 22 ingestion tests passed. |
| Initial local PostgreSQL access | BLOCKED: corrected with approved access | The sandbox denied the first PostgreSQL socket operation before tests ran. The approved execution reached the local PostgreSQL 16 service. |
| First local database selection | FAIL: corrected test database | The first approved DSN named a nonexistent `smartcoat_test` database. Read-only database inventory identified the existing synthetic `smartcoat_test_t05` database. |
| Local T09 PostgreSQL API suite | PASS | Five tests passed with zero skips in 1.86 seconds against PostgreSQL 16; migration, randomized schema, HTTP flow, rollback, isolation, lifecycle, query, legacy, and cleanup assertions all passed at that test head. |
| Strengthened local PostgreSQL rerun | BLOCKED: CI supplied final evidence | After only test assertions were strengthened, host approval usage limits prevented a second privileged local run. No product change followed the successful local run except a composition refactor covered by default tests. PR CI later executed the strengthened suite successfully. |
| PR merge-ref T09 PostgreSQL | PASS | Run `30350682417` executed all five strengthened T09 tests with zero skips. |
| PR merge-ref combined PostgreSQL | PASS | Run `30350682417` collected and passed 82 tests: 5 T09, 11 T06, 36 T07, 25 T05, and 5 Release 1.7 API tests. |
| Create and exact composition | PASS | HTTP create returned 201, draft revision 1, exact organization, complete evidence, provenance, four context classes, tags, content, and one canonical create audit event; detail returned the explicit composition. |
| Update and no-op | PASS | Material PUT incremented revision once and emitted one audit event; a true no-op preserved revision and returned null audit event. |
| Update conflicts | PASS | Stale revision and non-draft update returned safe 409 envelopes; cross-organization lookup returned the same safe 404 form as absence. |
| Complete lifecycle HTTP matrix | PASS | Every one of the twelve accepted T04 actions executed through HTTP and `KnowledgeAuditService.transition`; invalid transitions returned 409. |
| Draft deletion and retained history | PASS | Eligible never-left-draft deletion returned only ID, deleted true, and the canonical event; detail became 404 while organization-scoped history remained 200. |
| Query and cursor behavior | PASS | Explicit filters, bounded page size, pagination, opaque cursor binding, cross-organization mismatch, and legacy-row exclusion matched accepted T06 behavior. |
| Read-only proof | PASS | Detail, list, and history reads did not add audit events or change root or child xmin snapshots. |
| Atomic rollback proof | PASS | An injected audit participant failure left neither a misleading audit event nor a partial root mutation. |
| Legacy compatibility | PASS | Existing Release 1.7 API route tests passed; a live legacy create/detail round trip worked and its row remained absent from v2 results. |
| OpenAPI contract | PASS | Exactly seven v2 operations, unique IDs, explicit models, both headers, safe error responses, twelve-action discriminator, legacy routes, and prohibited-surface absence passed eight tests. |
| Error and correlation contract | PASS | Valid supplied UUIDs were preserved, omitted UUIDs generated once, malformed UUIDs returned 400, safe 422 omitted inputs, and safe 500 omitted exception, DSN, table, and stack details. |
| Cursor-key composition | PASS | SecretStr setting has no valid default; missing or fewer than 32 UTF-8 bytes fails before session creation; synthetic valid keys inject into the query service and never appear in OpenAPI. |
| Final full pytest | PASS | 818 tests passed, 77 expected opt-in or environment-configured tests skipped, and none failed. |
| Final MyPy | PASS | No issues were found in 65 source files. |
| Final Ruff | PASS | Repository-wide Ruff returned zero findings. |
| Final format check | PASS | All 101 files were formatted. |
| Final pip check | PASS | No broken requirements were found. |
| Report-validator tests | PASS | 40 tests passed and one environment-configured integration test skipped. |
| Existing report validation | PASS | All 21 pre-T09 execution reports passed the unchanged report-v2 validator. |
| First Markdown validator invocation | FAIL: corrected expression | The first standard-library command had a comprehension assignment syntax error and scanned nothing. The corrected loop-based invocation completed. |
| Markdown local links before report | PASS | 411 Markdown files and 118 local references had zero broken targets. |
| Scope, diff, and file-type checks | PASS | The implementation commit contains exactly the fourteen declared implementation and test paths, 3,845 insertions and 11 deletions, no whitespace error, and only ASCII text. |
| Secret and credential scan | PASS | Matches were limited to SecretStr contracts, inherited non-production placeholders, CI synthetic values, and tests that prove secret redaction; no real credential or private key was present. |
| Email and prohibited-data scan | PASS | The sole DSN-like email-form string was an explicitly synthetic guardrail example; broad client and formulation terms were code or generalized synthetic context, not personal or confidential industrial data. |
| Implementation commit and push | PASS | Commit `2924c8e91bb3a7f5ed9c60830672765a949ab977` was pushed normally with upstream tracking and no reset, rebase, force push, or history rewrite. |
| First CLI PR creation | BLOCKED: corrected publication path | Sandboxed `gh pr create` lacked GitHub network access; its required escalated retry was blocked by the host approval usage limit. Work stopped safely until renewed user authorization. |
| Local GitHub CLI authentication | FAIL: documented connector use | `gh auth status` reported the local token invalid. The installed publishing workflow's preferred connected GitHub App created the draft PR directly after renewed authorization. |
| Draft PR publication | PASS | PR #61 is open, draft, unmerged, has base `release/1.8-knowledge-capture-core`, head `thread/18-09-api-contracts`, and implementation head `2924c8e91bb3a7f5ed9c60830672765a949ab977`. |
| Implementation-head PR CI | PASS | Actions run `30350682417` validated PR merge ref `a2b6680a9edf4a40ca3c5164c1e44ae3b3655041`; Python 3.12 tests and PostgreSQL 16 migrations and persistence both passed. |

## Acceptance-Criteria Evidence

- [x] Evidence: all seven required v2 operations exist under the versioned
  `/api/v2/knowledge` boundary and all legacy routes remain separate.
- [x] Evidence: mutation routes call only `KnowledgeAuditService`, list calls
  only `KnowledgeObjectV2QueryService`, history uses the accepted audit read,
  and detail uses the bounded read service.
- [x] Evidence: route-source proof finds no direct repository or Unit of Work
  construction.
- [x] Evidence: every route requires trimmed, bounded organization metadata,
  and the models do not accept organization in mutation bodies.
- [x] Evidence: actor ID and role map exactly to `LifecycleActor` and are
  documented as declared, unauthenticated application metadata.
- [x] Evidence: one optional correlation UUID is preserved or generated,
  returned on success and error, and forwarded to audit-producing mutations.
- [x] Evidence: create, get, complete replacement update, no-op, draft delete,
  list, and audit-history contracts pass focused and live tests.
- [x] Evidence: all twelve lifecycle request models map one-to-one to accepted
  T04 commands; delete is excluded and deprecation alone accepts replacement.
- [x] Evidence: response models are explicit, extra-forbid where appropriate,
  aware-time and UUID preserving, alias safe, and free of canonical JSON, ORM,
  xmin, SQL, and internal retry fields.
- [x] Evidence: known failures map through a safe whitelist, while validation,
  database, configuration, and unknown failures use deterministic sanitized
  envelopes.
- [x] Evidence: the signing key is SecretStr, environment composed, absent by
  default, length checked before session creation, synthetic in tests and CI,
  and absent from OpenAPI and errors.
- [x] Evidence: local and CI PostgreSQL tests prove exact composition,
  lifecycle, audit, deletion, cursor, organization, read-only, rollback,
  legacy, migration, and cleanup behavior.
- [x] Evidence: affected contracts, complete API, persistence, ingestion,
  full default, static, report-validator, Markdown, scope, binary, secret,
  personal-data, and confidential-data checks pass.
- [x] Evidence: PR #61 remains draft and unmerged; #47, #48, and #38 remain
  open; PR #49 remains draft and unmerged; final T10 has not started.

## Architecture Impact

### Versioning and Endpoint Matrix

The accepted Release 1.8 boundary is additive. No legacy path redirects to v2,
and no legacy row is silently treated as a v2 aggregate.

| Method | Path | Success | Accepted service boundary |
|---|---|---|---|
| POST | `/api/v2/knowledge` | 201 mutation response | `KnowledgeAuditService.create` |
| GET | `/api/v2/knowledge` | 200 page response | `KnowledgeObjectV2QueryService.query` |
| GET | `/api/v2/knowledge/{object_id}` | 200 complete response | `KnowledgeObjectV2ReadService.get` |
| PUT | `/api/v2/knowledge/{object_id}` | 200 mutation response | `KnowledgeAuditService.update` |
| DELETE | `/api/v2/knowledge/{object_id}` | 200 deletion response | `KnowledgeAuditService.delete_draft` |
| POST | `/api/v2/knowledge/{object_id}/lifecycle-actions` | 200 mutation response | `KnowledgeAuditService.transition` |
| GET | `/api/v2/knowledge/{object_id}/audit-history` | 200 history response | `KnowledgeAuditService.history_for_object` |

There is no public audit append, generic canonical-event creation, raw
repository, semantic search, bulk export, UI, or authentication operation.

### Request Context

`X-SmartCoat-Organization-ID` is required, trimmed, non-blank, and bounded by
the accepted identifier length. It is application-boundary metadata only. It
does not prove authenticated identity, tenant authorization, legal access, or
database row-level security.

`X-Correlation-ID` is optional. A valid supplied UUID is preserved exactly; an
omitted value is generated once; malformed input returns deterministic 400.
The final UUID is stored on request state, returned in the response header,
included in v2 error envelopes, and supplied to each audit-producing mutation.

Mutation bodies declare `actor_id` and `actor_role`. These fields map to
`LifecycleActor`; they are not inferred from organization, correlation, or
client metadata. T09 neither authenticates the actor nor verifies authority.

### Request and Response Models

Requests are `KnowledgeCreateRequest`, `KnowledgeUpdateRequest`,
`KnowledgeDraftDeleteRequest`, and twelve explicit discriminated lifecycle
action models. Create maps exactly to `KnowledgeObjectV2CreateCommand` inside
`GovernedKnowledgeCreateCommand`. PUT maps exactly to
`KnowledgeObjectV2UpdateCommand` inside `GovernedKnowledgeUpdateCommand`. The
path UUID is authoritative.

Responses are `KnowledgeObjectV2Response`, `KnowledgeMutationResponse`,
`KnowledgeDraftDeleteResponse`, `KnowledgeObjectV2CollectionItemResponse`,
`KnowledgeObjectV2PageResponse`, `KnowledgeAuditEventResponse`,
`KnowledgeAuditHistoryResponse`, and `SmartCoatAPIErrorResponse`.

Nested public evidence mapping deliberately exposes bounded metadata values,
not `canonical_metadata_json`. Complete responses preserve mutable state,
structured evidence, provenance, typed context, Knowledge relationships, and
Decision relationships without persistence records.

### Lifecycle Mapping Matrix

| API action | Accepted T04 command | Action-specific field |
|---|---|---|
| submit_draft | `SubmitDraftCommand` | `submission_note` |
| request_captured_correction | `RequestCapturedCorrectionCommand` | `correction_reason` |
| complete_review | `CompleteReviewCommand` | `review_note` |
| reject_captured | `RejectCapturedCommand` | `rejection_reason` |
| request_reviewed_correction | `RequestReviewedCorrectionCommand` | `correction_reason` |
| validate_reviewed | `ValidateReviewedCommand` | `validation_note` |
| reject_reviewed | `RejectReviewedCommand` | `rejection_reason` |
| request_validated_correction | `RequestValidatedCorrectionCommand` | `correction_reason` |
| approve_validated | `ApproveValidatedCommand` | `approval_note` |
| reject_validated | `RejectValidatedCommand` | `rejection_reason` |
| deprecate_approved | `DeprecateApprovedCommand` | `deprecation_reason`, `replacement_object_id` |
| reopen_rejected | `ReopenRejectedCommand` | `reopen_reason` |

Every model also carries expected revision and declared actor. Extra or
irrelevant fields are forbidden. `delete_draft` is a distinct DELETE contract
and is not a lifecycle-union member.

### Error and Status Matrix

| Status | Public category | Representative conditions |
|---|---|---|
| 400 | malformed request context or cursor | correlation UUID, cursor shape, signature, version, position, query binding, incomplete context filter |
| 404 | organization-scoped absence | missing or cross-organization object, unknown empty history |
| 409 | accepted state conflict | stale revision, invalid lifecycle transition, source or role conflict, non-draft update, ineligible delete, relationship or atomic persistence conflict |
| 422 | safe request validation | Pydantic or FastAPI validation without raw input values |
| 500 | sanitized server failure | missing cursor configuration, unexpected database failure, unknown exception |

All v2 failures use one envelope containing code, safe message, and correlation
UUID. Unknown exceptions do not return raw exception text. Legacy handler
behavior remains unchanged outside the v2 prefix.

### Read and Composition Boundaries

`KnowledgeObjectV2ReadService` opens one session, calls only
`KnowledgeObjectV2Repository.get`, and returns the canonical composition or
None. It has no Unit of Work, commit, flush, mutation, or audit dependency.

The application factory retains `app` for Uvicorn and permits test dependency
overrides. V2 router composition is lazy only to preserve the inherited
API-main import-isolation contract; OpenAPI still contains all v2 and legacy
operations and opens no database session.

### Cursor and CI Composition

`Settings.knowledge_cursor_signing_key` is `SecretStr` with no valid default.
The dependency encodes UTF-8 deterministically, requires at least 32 bytes, and
fails closed before creating a query-service session. `.env.example` contains
an instruction and blank value, not a working secret. CI injects a clearly
synthetic value and executes T09 before the unchanged T06, T07, T05, and
Release 1.7 live suites.

## Security and Data Impact

- No real confidential industrial data, personal data, credential, private
  key, production secret, or customer record was ingested or committed.
- Test organizations, actors, context, evidence, provenance, content, UUIDs,
  cursor keys, and database values are synthetic or generalized.
- Organization metadata is explicit but is not advertised as authentication,
  authorization, tenancy, legal access control, or row-level security.
- Actor metadata is declared and forwarded; identity and role authority are not
  verified in T09.
- Request validation errors never echo content, provenance, evidence, cursor,
  or secret values.
- Unexpected exceptions and SQLAlchemy failures return generic safe messages,
  preserving only the request correlation UUID.
- The cursor key is secret-typed, absent by default, never reused from the
  inherited `change-me` setting, and absent from schemas, repr-based evidence,
  logs, and errors.
- Reads use accepted organization predicates. Cross-organization detail
  returns the same 404 as absence, and cursor boundary changes return 400.
- Mutation atomicity remains owned by accepted T07 and T05 services; the API
  does not create a persistence bypass.

## Known Limitations

- T09 has no production identity provider, authentication, authorization,
  role-authority enforcement, tenancy control, row-level security, rate limit,
  abuse control, production secret store, or public deployment hardening.
- The organization header and actor fields are declared metadata supplied by
  the caller. They are not independently trustworthy.
- Cursor contents remain T06's signed opaque contract; the cursor is not an
  authorization token and does not provide snapshot pagination.
- The API exposes no UI, AI extraction, semantic search, unrestricted
  ingestion, bulk export, or real-data authorization.
- The strengthened T09 PostgreSQL suite could not be rerun locally after a
  host approval limit. It did run and pass with zero skips in PR merge-ref CI.
- The report-only final head and its PR CI must be recorded externally after
  this report commit. The implementation-head run already passed both jobs.
- T09 does not complete Release 1.8. Final T10 integration in issue #48 remains
  open, unstarted, and subject to independent review authorization.

## Lost Points and Correction Items

| Item | Source | Points | Status | Action or Evidence |
|---|---|---|---|---|
| C01 | Initial static checks | 0 | RESOLVED | Imports, formatting, and typed construction were corrected; final Ruff, format, and MyPy pass. |
| C02 | Inherited T02 isolation regression | 0 | RESOLVED | Lazy v2 composition preserves import isolation while OpenAPI and runtime tests prove the complete router. |
| C03 | Local PostgreSQL rerun approval limit | 0 | RESOLVED | Final strengthened suite and complete 82-test PostgreSQL matrix passed in run `30350682417`. |
| C04 | Markdown and API command typos | 0 | RESOLVED | Corrected invocations completed with zero broken links and 82 passing API tests. |
| C05 | CLI publication blockers | 0 | RESOLVED | Renewed authorization and the connected GitHub App created draft PR #61 directly. |
| C06 | Independent review | 0 | RESOLVED | No implementation point is deducted before review; reviewer score remains Pending and the PR remains draft. |

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---|---|---|---|
| Correctness and evidence | 25 | 25 | Focused, live PostgreSQL, merge-ref CI, safe-error, rollback, and exact-command evidence pass. | None. |
| Scope and acceptance criteria | 20 | 20 | All seven endpoints, twelve lifecycle actions, explicit models, and owned paths are complete. | None. |
| Architecture and North-Star alignment | 15 | 15 | Thin routes reuse accepted T02-T08 services and add only one bounded read service. | None. |
| Verification, tests, or validation | 15 | 15 | 818 default tests, 82 API tests, 82 live PostgreSQL tests, static checks, and report checks pass. | None. |
| Security, privacy, and data governance | 10 | 10 | Safe envelopes, secret typing, fail-closed configuration, organization boundaries, and synthetic-only data are proven. | None. |
| Documentation and traceability | 10 | 10 | Issue ownership, PR, commands, failures, corrections, matrices, CI, limits, and gates are recorded. | None. |
| Maintainability and clarity | 5 | 5 | Explicit schemas, central errors, dependency injection, factory composition, and focused tests keep responsibilities bounded. | None. |
| Total | 100 | 100 | Every in-scope acceptance criterion and required validation has actual passing evidence. | None. |

## ChatGPT Reviewer Score

Reviewer status: Pending

Reviewer evidence: Independent ChatGPT review has not yet evaluated draft PR #61.

## Final Score

Provisional weighted score: Pending

Gate-adjusted score: Pending

Codex contributes 40 percent and the independent reviewer contributes 60
percent. No final weighted score is claimed before independent review.

## Critical-Gate Declaration

| Gate | Status | Evidence |
|---|---|---|
| G1 Verified claims | PASS | Every material claim is tied to local test output, exact commits, issue state, or Actions run `30350682417`. |
| G2 Confidential data | PASS | File, secret, personal-data, and industrial-data scans found only reviewed synthetic or declarative values. |
| G3 Approved scope and architecture | PASS | Diff is limited to the exact declared paths and preserves accepted T02-T08 and legacy boundaries. |
| G4 Required validation | PASS | Focused, regression, full, static, PostgreSQL, OpenAPI, report, link, diff, and safety checks passed. |
| G5 File ownership | PASS | All fifteen PR paths were declared before editing and no amendment was needed. |
| G6 Acceptance completeness | PASS | Seven endpoints, twelve actions, context headers, explicit models, safe errors, cursor configuration, and compatibility evidence are complete. |

Critical-gate result: PASS

## Release 1.8 Additional Gates

| Gate | Status | Evidence |
|---|---|---|
| G7 HTTP, OpenAPI, PostgreSQL, and error correctness | PASS | 74 focused tests, 8 OpenAPI tests, 5 T09 live tests, safe 422 and 500 tests, and PR merge-ref CI pass. |
| G8 Lifecycle, audit, query, and persistence bypass prevention | PASS | Routes use only accepted services, source proof excludes direct repositories and Unit of Work, reads create no audit, and injected failure rolls back atomically. |

## Correction-Cycle History

| Cycle | Starting Score | Findings | Corrections | Ending Score | Validation Evidence | Status |
|---|---|---|---|---|---|---|
| 1 | 90 | Initial static findings and eager router composition affected inherited isolation. | Corrected imports, formatting, typed construction, and lazy factory composition. | 97 | Focused API, inherited isolation, Ruff, format, and MyPy passed. | CLOSED |
| 2 | 97 | Local database selection and later host approval limits interrupted PostgreSQL evidence. | Selected the guarded synthetic database, completed local live validation, strengthened tests, and required the final suite in PR CI. | 100 | Local 5-test run and PR merge-ref 82-test PostgreSQL run passed with zero T09 skips. | CLOSED |

## Recommended Follow-up Issues

- Issue #48 must perform final T10 integration only after independent T09
  review and explicit authorization.
- Production identity, authorization, tenancy, row-level security, secret
  management, rate limiting, deployment hardening, and real-data governance
  require separate future decisions and are not implied by T09.
- The local GitHub CLI token should be reauthenticated for future
  administrative work; it did not affect the connected App publication or
  repository content.

## Blockers

None.

## Recommendation

READY FOR INDEPENDENT REVIEW
