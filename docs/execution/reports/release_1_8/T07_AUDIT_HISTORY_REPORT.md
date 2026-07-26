# T07 Immutable Audit Events and History Retrieval Report

Report schema version: `smartcoat-execution-report-v2.0`

Thread ID: T07

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/45

Branch: `thread/18-07-audit-history`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/59

Final status: `READY FOR INDEPENDENT RE-REVIEW`

## Objective

Implement Release 1.8 Wave 3B immutable Knowledge audit events and
organization-scoped history retrieval from exact Release SHA
`bff38e056e2f7dbfe16f2eda8d024e7216024675`.

The implementation defines a frozen canonical Knowledge audit profile in the
Enterprise Event family, persists it independently in
`knowledge_audit_events_v2`, and atomically couples create, complete-composition
update, accepted T04 lifecycle transition, and eligible draft deletion with
exactly one audit append through the existing T05 Unit of Work. No public
arbitrary append API or T07 route is added.

Implementation commit `4ca70d30c5bfc4598f83dcf8b102b45944c7f0af`
was pushed normally and associated with draft PR CI run `30198494465`. Both
jobs passed. The final report-publication SHA and its final exact-head CI are
recorded in PR #59, issue #45, and the orchestrator response because a commit
cannot contain its own SHA.

Independent Review Correction Cycle 1 preserves that implementation history.
Corrected implementation commit
`c241cf54264cb78718b952f21670d95832bf9fdf` enforces draft-only governed
material updates and retains the optional T04 deprecation replacement UUID.
GitHub Actions run `30201484822`, on the PR merge ref associated with that
branch head, passed both required jobs. The correction report-publication SHA
and its exact-head CI are recorded in PR #59, issues #45 and #38, and the
orchestrator response because a commit cannot contain its own SHA.

## Files Changed

- `.github/workflows/ci.yml`
- `alembic/env.py`
- `alembic/versions/0003_release_1_8_knowledge_audit.py`
- `src/smartcoat/domain/knowledge_audit.py`
- `src/smartcoat/services/knowledge_audit_service.py`
- `src/smartcoat/storage/database/knowledge_audit_models.py`
- `src/smartcoat/storage/repositories/knowledge_audit_repository.py`
- `tests/integration/test_knowledge_audit_postgres.py`
- `tests/integration/test_knowledge_v2_postgres.py`
- `tests/persistence/test_knowledge_audit_repository.py`
- `tests/test_knowledge_audit.py`
- `tests/test_knowledge_audit_service.py`
- `docs/execution/reports/release_1_8/T07_AUDIT_HISTORY_REPORT.md`

The original ownership declaration on issue #45 named 12 paths, including this
report. Before editing it, a second ownership comment added
tests/integration/test_knowledge_v2_postgres.py solely to advance the T05
live-test expected Alembic head from `0002` to `0003`. No other T05-owned path
was modified.

## Methods and Commands Executed

- `git fetch --all --prune`
- `git rev-parse origin/release/1.8-knowledge-capture-core origin/main`
- `gh issue view 45 --repo JamshidiML/smartcoat-intelligence`
- `gh issue view 43 --repo JamshidiML/smartcoat-intelligence`
- `gh issue view 35 --repo JamshidiML/smartcoat-intelligence`
- `gh pr view 49 --repo JamshidiML/smartcoat-intelligence`
- `git worktree add -b thread/18-07-audit-history <T07-path> bff38e056e2f7dbfe16f2eda8d024e7216024675`
- `python -m pip check`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python -m mypy src`
- `python -m pytest -ra`
- `python -m pytest -q tests/test_knowledge_audit.py`
- `python -m pytest -q tests/test_knowledge_audit_service.py`
- `python -m pytest -q tests/persistence`
- `python -m pytest -q tests/test_knowledge_audit_service.py tests/integration/test_knowledge_audit_postgres.py -k ir_c01`
- `python -m pytest -q tests/test_knowledge_audit.py tests/test_knowledge_audit_service.py tests/persistence/test_knowledge_audit_repository.py tests/integration/test_knowledge_audit_postgres.py -k ir_c02`
- `python -m pytest -q <affected T02 T03 T04 T05 T08 paths>`
- `python -m pytest -q tests/ingestion/test_manifest_validation.py`
- `SMARTCOAT_RUN_LIVE_POSTGRES_TESTS=true SMARTCOAT_TEST_DATABASE_URL=<local-synthetic-test-dsn> python -m pytest -q tests/integration/test_knowledge_audit_postgres.py`
- `SMARTCOAT_RUN_LIVE_POSTGRES_TESTS=true SMARTCOAT_TEST_DATABASE_URL=<local-synthetic-test-dsn> SMARTCOAT_TEST_SCHEMA=smartcoat_test_t07_legacy_api python -m pytest -ra tests/integration/test_knowledge_audit_postgres.py tests/integration/test_knowledge_v2_postgres.py tests/integration/test_persistent_api_postgres.py`
- `python -m pytest -q tests/test_validate_execution_reports.py`
- `python scripts/validate_execution_reports.py --require-count 19 <all existing reports>`
- `python scripts/validate_execution_reports.py --require-count 20 <all reports including T07>`
- `python scripts/validate_execution_reports.py docs/execution/reports/release_1_8/T07_AUDIT_HISTORY_REPORT.md`
- `python -c '<standard-library Markdown local-link validator>'`
- `git diff --check`
- `git diff --check bff38e056e2f7dbfe16f2eda8d024e7216024675`
- `file <all owned paths>`
- `rg <secret, credential, email, personal-data, and real-data patterns> <all owned paths>`
- `git commit -m "Implement immutable knowledge audit history"`
- `git push -u origin thread/18-07-audit-history`
- `gh pr create --draft --base release/1.8-knowledge-capture-core --head thread/18-07-audit-history`
- `gh pr checks 59 --repo JamshidiML/smartcoat-intelligence --watch --interval 10`
- `git commit -m "Correct T07 audit lifecycle contracts"`
- `git push origin thread/18-07-audit-history`

The live DSN targets a localhost PostgreSQL 16 container and a database whose
name begins with `smartcoat_test`. Credentials are intentionally redacted.
Every T07 fixture uses randomized `smartcoat_test_t07_*` schemas and synthetic,
metadata-only content.

## Actual Results

| Method or Command | Actual Result | Evidence |
|---|---|---|
| Protected-state preflight | PASS | Release remote exactly matched `bff38e056e2f7dbfe16f2eda8d024e7216024675`; main exactly matched `47df21458038d107bb7c7cb98dc6d23dd3b6d7e9`; #45 was open; #43 and #35 were closed completed; PR #49 was open, draft, and unmerged. |
| Branch and worktree creation | PASS | Exact branch `thread/18-07-audit-history` started at the required Release SHA in the persistent T07 path with a clean worktree and release dependency state. |
| Ownership declaration | PASS | Issue #45 comment `5083002977` declared the start SHA, branch, worktree, proposed paths, overlap rationale, and untouched T06/T09/T10 before edits. |
| Ownership amendment | PASS | Issue #45 comment `5083039297` added only the T05 live-test head expectation path before that one-line edit. |
| Initial focused tests | FAIL: corrected test doubles | 53 tests passed and 2 failed because mock-flushed ORM records lacked server-default schema and family values; test doubles were corrected without weakening domain validation. |
| Initial focused Ruff | FAIL: corrected static findings | One unused integration-test import and six format-only differences were corrected; subsequent focused and repository-wide Ruff checks passed. |
| Initial sandboxed PostgreSQL run | FAIL: corrected execution permission | One guardrail test passed, one cleanup test failed, and 18 setup errors reported localhost and Docker access as not permitted; the same suite was rerun with approved local access. |
| Initial T07 live PostgreSQL suite | PASS | 20 tests passed with zero skips before the internal second-pass correction. |
| Internal second-pass clock review | FAIL: corrected implementation defect | PostgreSQL `now()` represents transaction start and could precede the later application occurrence time. Correction Cycle 1 changed the server default to `clock_timestamp()` and added a delayed wall-clock live regression. |
| First correction live suite | PASS | 21 T07 live PostgreSQL tests passed after the server-time correction and metadata comparison remained empty. |
| Acceptance-matrix evidence review | FAIL: corrected test coverage | Mutation-stage failure and failure after an audit row flush were only indirectly covered. Explicit service and live PostgreSQL rollback tests were added. |
| Post-append rollback proof | PASS | The participant flushed a canonical row and then raised; the Unit of Work rolled back both the new Knowledge object and the flushed audit row to zero records. |
| Final T07 live PostgreSQL suite | PASS | 22 tests passed with zero skips in 6.23 seconds. |
| Final focused T07 domain tests | PASS | 29 tests passed. |
| Final focused T07 service tests | PASS | 21 tests passed. |
| Final persistence tests | PASS | All 17 persistence tests passed, including six T07 repository and participant tests. |
| Affected T02 T03 T04 T05 T08 contracts | PASS | 483 domain, evidence, lifecycle, context, mapper, repository, and Unit-of-Work tests passed. |
| T08 ingestion compatibility | PASS | 22 manifest-validation tests passed. |
| Final default-mode pytest | PASS | 671 items were collected; 622 passed, 49 expected opt-in or environment-configured items skipped, zero failed, and zero were deselected. |
| Final combined live PostgreSQL suites | PASS | 52 items were collected and passed with zero skips: 22 T07, 25 T05, and 5 Release 1.7 persistent API regressions. |
| Alembic graph and metadata | PASS | Clean `0002` to `0003`, clean database to head, downgrade to `0002`, re-upgrade to `0003`, and SQLAlchemy `compare_metadata == []` all passed. |
| PostgreSQL append-only behavior | PASS | Direct SQL UPDATE and DELETE each raised the append-only trigger error; the audit table has no restrictive object foreign key and history survived eligible draft deletion. |
| Organization and deterministic history | PASS | Every read predicate includes organization and object; cross-organization history is empty; equal timestamps remain ordered by server-owned `audit_sequence ASC`. |
| Legacy EnterpriseEvent compatibility | PASS | Release 1.7 API live tests passed and a caller-created legacy event remained retrievable through the legacy repository but absent from canonical Knowledge audit history. |
| Final pip compatibility | PASS | No broken requirements were found. |
| Final Ruff | PASS | Repository-wide Ruff returned zero findings. |
| Final Ruff format | PASS | All 84 implementation-head files were formatted. |
| Final MyPy | PASS | No issues were found in 57 source files. |
| Report-validator tests | PASS | 40 tests passed and one environment-configured integration check skipped. |
| Existing report validation | PASS | All 19 pre-T07 execution reports passed the unchanged report-v2 validator. |
| First T07 report-v2 validation | FAIL: corrected duplicate path reference | The Files Changed prose repeated one already listed repository path in backticks; the duplicate token was removed without changing ownership or evidence. |
| T07 report-v2 validation | PASS | This report passes the unchanged report-v2 validator. |
| All-report validation | PASS | All 20 reports, including T07, pass with the exact required count. |
| Markdown local-link validation | PASS | 410 Markdown files and 118 repository-local links were checked with zero broken targets. |
| Exact owned-path validation | PASS | Release-base diff contains exactly the 13 declared and amended paths, with no missing, unexpected, or untracked file. |
| Binary and environment-file scan | PASS | All 13 changed paths are UTF-8 or ASCII text; no changed `.env` file or binary exists. The repository's unchanged `.env.example` remains outside the diff. |
| Secret and credential scan attempt 1 | FAIL: corrected scanner invocation | A shell quoting error produced `bad pattern` before scanning; no result is claimed from that invocation. |
| Secret and credential scan | PASS | Token and private-key patterns returned zero matches. One report-only personal-data phrase was reviewed as a negated boundary statement; no email, credential, secret, or personal record is present. |
| Real or confidential data scan | PASS | Implementation and fixture paths returned no prohibited-data marker; report-only matches are its explicit negated boundary statements. Fixtures identify synthetic data. |
| Diff checks | PASS | Worktree, staged, and complete release-base diff checks returned zero whitespace errors. |
| First commit attempt | FAIL: corrected Git metadata permission | The sandbox denied creation of the linked-worktree index lock before staging or committing; the approved Git operation was rerun normally. |
| Implementation commit and push | PASS | Commit `4ca70d30c5bfc4598f83dcf8b102b45944c7f0af` was pushed normally with upstream tracking; no force push, reset, rebase, or history rewrite occurred. |
| Draft PR publication | PASS | PR #59 is open, draft, unmerged, and targets `release/1.8-knowledge-capture-core`; it closes no issue. |
| Implementation-head PR CI | PASS | Run `30198494465`, associated with branch head `4ca70d30c5bfc4598f83dcf8b102b45944c7f0af`, passed Python 3.12 tests in 36 seconds and PostgreSQL 16 migrations/persistence in 1 minute 13 seconds on the pull-request merge ref. |
| First post-report remote-state verification | FAIL: corrected execution permission | The sandbox denied the linked-worktree FETCH_HEAD write and GitHub API network calls; local read-only SHA checks still completed, but no remote-state result is claimed from the failed parts. |
| Post-report remote-state verification | PASS | The approved rerun confirmed local and remote T07 heads matched, Release and main retained their protected SHAs, PR #49 remained open/draft/unmerged, PR #59 remained open/draft/unmerged at the expected head, and issue #45 remained open. |
| Corrected report-head PR CI | PASS | Run `30198785192`, associated with report head `152a47a805d4d6a44ec3538f669b2a931c18d9d7`, passed Python 3.12 in 35 seconds and PostgreSQL 16 migrations/persistence in 1 minute 5 seconds. |
| First final PR evidence synchronization | FAIL: corrected shell quoting | Unescaped Markdown backticks treated the run number as a shell command and omitted it from one PR sentence; the SHA update still landed and no file or Git history changed. |
| Final PR evidence synchronization | PASS | A plain-quoted correction restored run `30198785192`; PR #59 then reported the exact head, remained open and draft, and retained the final CI evidence. |
| Historical independent review | FAIL: correction required | Independent review `4781619375` evaluated reviewed head `e1cfd181f0737c9212e86d5ffc23a0cd06981e30`, scored it 87/100, calculated provisional weighted score 92.2/100 and gate-adjusted score 79/100, and required IR-C01 plus IR-C02. |
| Correction-cycle protected-state preflight | PASS | Local and remote branch heads exactly matched reviewed head `e1cfd181f0737c9212e86d5ffc23a0cd06981e30`; Release and main retained their required SHAs; PR #59 and PR #49 were open, draft, and unmerged; issues #45 and #38 were open; the worktree was clean. |
| Correction ownership declaration | PASS | Issue #45 comment `5083356895` declared the exact ten-path correction boundary before edits. |
| IR-C01 draft-only update enforcement | PASS | Organization-scoped lookup remains first; target and expected revision checks precede lifecycle editability; only draft reaches T05 complete-composition comparison and CAS. Non-draft material and no-op updates return typed code `knowledge_update_lifecycle_forbidden`. |
| IR-C01 focused evidence | PASS | 31 focused service and live PostgreSQL cases passed, including all seven states, stale-before-lifecycle precedence, no-write behavior, and four correction or reopen paths back to draft. |
| IR-C01 approved protection | PASS | Live PostgreSQL proves a forbidden approved composition update preserves content, evidence, provenance, child collections, revision 5, approved lifecycle, root `xmin`, and audit history. |
| IR-C02 replacement preservation | PASS | The exact nested T04 `replacement_object_id` is copied into the canonical request, event, ORM row, repository mapping, and history. Non-deprecation domain payloads reject it. |
| IR-C02 focused evidence | PASS | 15 focused domain, service, repository, and live PostgreSQL cases passed; replacement and null deprecation paths round-trip exactly. |
| IR-C02 database boundary | PASS | Corrected 0003 and ORM metadata add one nullable PostgreSQL UUID with the required bounded check and no foreign key. Direct non-deprecation insertion is rejected; nonexistent and later-deleted replacement UUIDs remain readable in source history. |
| First correction-focused Ruff and format | FAIL: corrected static findings | Import ordering and format-only differences in new correction tests were fixed with Ruff; repository-wide checks subsequently passed. |
| First correction validation invocation | FAIL: corrected virtual-environment path | The worktree-local `./.venv/bin/ruff` path did not exist. The existing shared Release 1.8 virtual environment was used for all claimed validation. |
| Correction T07 domain tests | PASS | 39 tests passed. |
| Correction T07 service tests | PASS | 41 tests passed. |
| Correction persistence tests | PASS | All 19 persistence tests passed, including 8 T07 repository tests. |
| Correction T07 live PostgreSQL suite | PASS | All 36 T07 items passed with zero skips against migrated 0003. This includes upgrade, clean head, downgrade, re-upgrade, metadata, append-only, rollback, and randomized-schema cleanup checks. |
| Correction affected contracts | PASS | 489 affected T02, T03, T04, T05, and T08 tests plus 22 ingestion compatibility tests passed. |
| Correction default-mode pytest | PASS | 717 items were collected; 654 passed and 63 expected opt-in or environment-configured items skipped, with zero failures and zero deselections. |
| Correction combined live PostgreSQL suites | PASS | All 66 items passed with zero skips: 36 T07, 25 T05, and 5 Release 1.7 persistent API regressions. |
| Correction static and dependency gates | PASS | Pip found no broken requirements; Ruff returned zero findings; all 84 files were formatted; MyPy found no issues in 57 source files. |
| Correction implementation safety | PASS | The implementation commit contains exactly nine authorized implementation and test paths; this report makes the complete correction diff exactly ten authorized paths; the release-base PR diff remains exactly 13 owned paths. All correction files are ASCII text, with no binary, environment file, secret, credential, personal record, or confidential industrial data. |
| Correction report and link validation | PASS | The unchanged report-v2 test suite passed 40 tests with one expected environment-gated skip; this report and all 20 execution reports passed; 410 Markdown files and 118 local links had zero broken targets. |
| First correction commit attempt | FAIL: corrected Git metadata permission | The sandbox denied creation of the linked-worktree index lock after the exact nine paths were staged. The approved normal commit then succeeded without changing staged content or rewriting history. |
| Correction implementation commit and push | PASS | Commit `c241cf54264cb78718b952f21670d95832bf9fdf` was pushed normally to the existing branch; no force push, reset, rebase, or replacement branch was used. |
| Correction implementation-head PR CI | PASS | Run `30201484822`, on the pull-request merge ref associated with corrected branch head `c241cf54264cb78718b952f21670d95832bf9fdf`, passed Python 3.12 tests in 38 seconds and PostgreSQL 16 migrations and persistence in 1 minute 11 seconds. |

## Acceptance-Criteria Evidence

- [x] Canonical frozen, extra-forbid, alias-free audit request and event
  contracts contain every required server-owned field. Evidence: 29 domain
  tests and immutable round-trip repository tests pass.
- [x] Every T04 `LifecycleAction` maps deterministically to the required event
  type and exact lifecycle/revision pair. Evidence: parameterized domain,
  service, and 12-action live PostgreSQL tests pass.
- [x] Create, material update, lifecycle transition, and draft deletion
  invariants fail closed. Evidence: invalid combinations, stale operations,
  invalid lifecycle plans, and deletion safety tests append no success event.
- [x] Safe summaries contain only approved top-level names and never values or
  payload fragments. Evidence: raw payload, nested field, duplicate field, and
  unsafe name rejection tests pass.
- [x] Evidence-only and provenance-only changes are material; dictionary order
  is ignored; governed list order and Boolean, integer, and float identity are
  preserved. Evidence: focused service and live type-identity tests pass.
- [x] Alembic revision `0003_release_1_8_knowledge_audit` creates exact metadata,
  deterministic ordering, constraints, indexes, and an append-only PostgreSQL
  guard. Evidence: migration graph, empty metadata diff, downgrade/re-upgrade,
  and direct DML rejection pass.
- [x] Repository surface is exactly append, scoped get, and scoped history,
  with no commit, save, update, delete, or global listing. Evidence: source
  surface and SQL predicate tests pass.
- [x] History remains stable at equal timestamps, isolated by organization,
  immutable on return, and available after draft deletion. Evidence: live
  PostgreSQL and focused repository tests pass.
- [x] Governed mutation and audit append share one T05 Unit of Work and one
  Session. Evidence: pre-append and post-append participant failures roll back
  object mutation and audit state together.
- [x] Legacy EnterpriseEvent behavior remains unchanged and caller-authored
  legacy rows never enter canonical history. Evidence: five live Release 1.7
  API tests and the explicit legacy separation test pass.
- [x] CI explicitly runs T07, T05, and Release 1.7 PostgreSQL suites. Evidence:
  implementation-head run `30198494465` passed both required jobs.
- [x] Scope, data, report, and safety gates are complete. Evidence: exact
  13-path ownership, 20 report validations, 118 local links, diff checks, and
  safety scans pass.
- [x] Governed complete-composition updates are draft-only, including true
  no-ops. Evidence: the seven-state service matrix and all 36 live T07 tests
  prove typed rejection, stale-before-lifecycle precedence, unchanged approved
  storage, and successful correction or reopen before later draft editing.
- [x] Deprecation preserves the exact optional T04 replacement UUID without
  adding content or target authorization semantics. Evidence: domain,
  translation, service, repository, DDL, direct-insert, history, nonexistent
  target, and later-deleted target tests pass.

## Architecture Impact

Canonical Knowledge audit is a dedicated typed profile in the accepted
Enterprise Event family, not a replacement for the Release 1.7 event feature.
The storage discriminator is structural:

- `enterprise_events` remains caller-authored legacy storage;
- `knowledge_audit_events_v2` is internal canonical Knowledge audit storage;
- no public arbitrary append route or global history listing exists;
- no legacy event module, service, repository, model, or route changed.

The separation is necessary because the legacy event route accepts caller
payloads, its repository commits independently, and its record lacks
organization, lifecycle action, prior/resulting revision, mandatory reason,
correlation, safe changed-field summary, server sequence, and append-only
guarantees. Reusing it would allow audit forgery and risk Release 1.7
compatibility.

Migration graph:

`0001_release_1_7_baseline` to `0002_release_1_8_knowledge_v2` to
`0003_release_1_8_knowledge_audit`.

The audit table deliberately has no restrictive object foreign key, preserving
history after an eligible draft is deleted. `audit_sequence ASC` is the sole
documented stable history order; sequence gaps after rollback are valid.

The governed service does not redefine T04 transitions or T05 persistence. It
consumes `LifecycleMutationPlan` and `DraftDeletionPlan`, stages through the T05
repository, queues one canonical request, flushes the internal participant on
the same Session, and commits once.

The governed material-update use case now performs organization-scoped lookup,
target and expected-revision validation, and draft editability validation
before asking T05 to compare or mutate the complete composition. A stale
non-draft command therefore remains `stale_revision`, an organization mismatch
remains a non-disclosing not-found result, and a valid non-draft no-op is still
forbidden.

The optional deprecation replacement is canonical audit metadata copied from
the accepted nested T04 plan. It is stored as a nullable PostgreSQL UUID. A
bounded check permits a non-null value only for `deprecate` with
`deprecate_approved`; domain validation remains the complete semantic
authority. There is deliberately no replacement-object foreign key.

## Security and Data Impact

Audit summaries expose only normalized field names. They contain no previous
or resulting values, title, description, content keys, content values,
evidence metadata, provenance values, context attributes, or relationship
targets. Draft-deletion events are content-free tombstones.

Every read includes organization and object predicates. A mismatched
organization receives an empty result without object-existence disclosure.
This is an application boundary and defense in depth, not production IAM,
authenticated tenancy, PostgreSQL row-level security, or legal authorization.

PostgreSQL rejects UPDATE and DELETE on canonical audit rows. Normal code has
no generic save, update, delete, commit, public append API, or global history
method. Direct database INSERT authenticity still depends on deployment
credentials and permissions outside T07 scope.

Fixtures are synthetic and metadata-only. No real or confidential industrial
data, personal record, production formula, customer data, binary, secret, or
credential is committed.

The replacement UUID identifies no title, content, evidence, context, or
relationship data. T07 neither resolves nor authorizes that target, and the
event remains scoped to the deprecated source object's organization.

## Known Limitations

- No public API route is added; T09 owns future explicit request, response,
  authorization, error, and OpenAPI contracts.
- Organization predicates are not production IAM, authenticated tenant
  isolation, or PostgreSQL row-level security.
- Append-only database behavior rejects UPDATE and DELETE; trusted database
  roles, direct INSERT policy, backups, replication, and administrator
  controls remain deployment responsibilities.
- This is an audit log, not event sourcing, a distributed transaction system,
  external event-authenticity proof, SIEM integration, or legal retention and
  erasure policy.
- Application and PostgreSQL hosts require ordinary clock synchronization.
  `clock_timestamp()` avoids transaction-start skew and the domain rejects a
  record time before occurrence.
- History intentionally has no T06 filters, cursor pagination, or global
  listing.
- Audit sequence gaps after rollback are expected and do not weaken ordering.
- Low-level T05 primitives remain available for persistence internals. Only
  the governed T07 service may claim complete mutation-plus-audit behavior.
- Replacement-target existence, cross-organization authorization, and later
  API validation remain outside T07. History intentionally retains the supplied
  UUID when the target is absent or later deleted.
- T06, T09, T10, Release 1.8 completion, production deployment, production
  readiness, voice, AI extraction, semantic search, and UI are not claimed.

Downstream invariants:

- Every governed child mutation must increment the aggregate-root revision.
- T06 and T09 must not add child-only writes or bypass the governed audit
  service when claiming complete mutation behavior.
- A future API must not expose `KnowledgeAuditAppendRequest` as caller input.
- Legacy `/events` records must remain excluded from canonical Knowledge
  history.

## Lost Points and Correction Items

| Item | Source | Points | Status | Action or Evidence |
|---|---|---:|---|---|
| C01 | Internal second-pass clock review | 0 | RESOLVED | Replaced PostgreSQL transaction-start `now()` with insert-time `clock_timestamp()` and added a delayed wall-clock live regression; metadata and 22 live T07 tests pass. |
| C02 | Acceptance-matrix rollback evidence | 0 | RESOLVED | Added explicit mutation-failure and post-append participant-failure tests, proving zero success events and atomic rollback of both tables. |
| C03 | Independent review `4781619375` combined deduction | 13 | RESOLVED | Corrected both independent findings at exact reviewed head `e1cfd181f0737c9212e86d5ffc23a0cd06981e30`; the reviewer did not assign the 13 lost points between findings, so this row preserves the combined historical deduction without fabricating an allocation. |
| C04 | IR-C01 draft-only governed material editability | 0 | RESOLVED | Added ordered lifecycle preconditions, a seven-state material and no-op matrix, stale and organization precedence, no-write approved evidence, and correction or reopen then update proofs. |
| C05 | IR-C02 deprecation replacement preservation | 0 | RESOLVED | Added the canonical UUID field, exact T04 translation, nullable PostgreSQL persistence with bounded check and no foreign key, and complete positive, null, rejection, and retention proofs. |
| C90 | Initial focused test-double failures | 0 | RESOLVED | Assigned server-owned defaults in mock flush behavior and reran all focused and complete suites. |
| C91 | Initial Ruff and format findings | 0 | RESOLVED | Removed the unused import, applied Ruff formatting, and reran repository-wide checks successfully. |
| C92 | Initial sandboxed localhost denial | 0 | RESOLVED | Preserved the failed invocation, obtained approved local access, and ran all PostgreSQL suites with zero T07 skips. |
| C93 | First safety-scanner quoting failure | 0 | RESOLVED | Preserved the non-result, simplified the shell-safe patterns, and reran secret, personal-data, and prohibited-data scans successfully. |
| C94 | First Git metadata permission denial | 0 | RESOLVED | No index state changed; the approved normal stage and commit operation then succeeded. |
| C95 | First report-v2 validation | 0 | RESOLVED | Removed one duplicate backticked path reference and reran the unchanged T07, all-report, and validator-test checks successfully. |
| C96 | First post-report remote-state verification | 0 | RESOLVED | Preserved the sandbox and network denials, reran with approved Git and GitHub access, and verified all protected remote states exactly. |
| C97 | First final PR evidence synchronization | 0 | RESOLVED | Replaced the unsafe Markdown-backtick substitution with plain text, restored the run number, and verified the PR body, final head, draft state, and open state. |
| C98 | First correction-focused Ruff and format | 0 | RESOLVED | Corrected import ordering and format-only findings, then reran focused and repository-wide Ruff and format checks successfully. |
| C99 | First correction virtual-environment invocation | 0 | RESOLVED | Preserved the missing worktree-local executable result and reran every claimed check through the existing shared Release 1.8 environment. |
| C100 | First correction commit attempt | 0 | RESOLVED | The approved normal commit created exact implementation SHA `c241cf54264cb78718b952f21670d95832bf9fdf` from unchanged staged content after the sandboxed index-lock denial. |

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 25 | Domain invariants, exact T04 mapping, atomic mutation/audit rollback, safe summaries, stable history, and direct DML rejection pass locally and on PostgreSQL. | None. |
| Scope and acceptance criteria | 20 | 20 | Exact 13-path declared ownership implements every T07 criterion without T06, T09, T10, API, UI, legacy-event, or production-scope changes. | None. |
| Architecture and North-Star alignment | 15 | 15 | Dedicated canonical audit storage, unchanged legacy events, accepted T04 plan authority, T05 Unit of Work reuse, and fail-closed boundaries align with accepted contracts. | None. |
| Verification, tests, or validation | 15 | 15 | Correction evidence includes IR-C01 31, IR-C02 15, T07 39 domain plus 41 service plus 8 repository plus 36 live, 19 persistence, affected 489 plus 22 ingestion, 654/63 full, 66/0 combined live, MyPy 57, Ruff, format, and both implementation-head CI jobs. | None. |
| Security, privacy, and data governance | 10 | 10 | Safe name-only summaries, organization-scoped reads, append-only DML guard, synthetic fixtures, target guardrails, cleanup, and prohibited-data scans pass. | None. |
| Documentation and traceability | 10 | 10 | Start SHA, ownership, architecture rationale, migration graph, commands, failures, corrections, exact evidence, gates, and limitations are recorded. | None. |
| Maintainability and clarity | 5 | 5 | Typed contracts, a narrow repository, explicit participant, bounded service, deterministic mappings, and focused tests keep responsibilities clear. | None. |
| Total | 100 | 100 | All corrected in-scope acceptance, quality, live PostgreSQL, compatibility, safety, normal publication, and implementation-head CI evidence passes. | None. |

## ChatGPT Reviewer Score

Historical independent review:

- Independent review: `4781619375`
- Reviewed head: `e1cfd181f0737c9212e86d5ffc23a0cd06981e30`
- Historical reviewer score: 87/100
- Historical provisional weighted score: 92.2/100
- Historical gate-adjusted score: 79/100
- Historical decision: CORRECTION REQUIRED
- Finding IR-C01: draft-only governed material editability
- Finding IR-C02: deprecation replacement reference preservation

Reviewer status: Pending independent re-review.

Corrected-head reviewer score, weighted score, gate-adjusted score, evidence,
and decision remain pending. No independent-review acceptance is claimed.

## Final Score

Provisional weighted score: Pending

Gate-adjusted score: Pending

Codex contributes 40 percent and the independent reviewer contributes 60
percent. No weighted score exists until independent review.

## Critical-Gate Declaration

| Gate | Status | Evidence |
|---|---|---|
| G1 Verified claims | PASS | Claims map to exact command output, source inspection, PostgreSQL behavior, issue comments, PR state, or Actions runs `30198494465`, `30198785192`, and `30201484822`; failed invocations remain recorded. |
| G2 Confidential data | PASS | Synthetic metadata-only fixtures, localhost target guards, cleanup, and secret, personal, binary, and prohibited-data scans pass. |
| G3 Approved scope and architecture | PASS | The correction changes exactly nine of ten authorized correction paths; the complete 13-path PR diff uses dedicated audit storage, leaves legacy event behavior intact, and does not start T06, T09, or T10. |
| G4 Required validation | PASS | Full, IR-focused, T07, persistence, affected, 66-item live PostgreSQL, migration, static, report, link, diff, safety, and both corrected implementation-head CI jobs pass. |
| G5 File ownership | PASS | Original declaration, one pre-edit implementation amendment, and correction comment `5083356895` account for every changed path with no unexpected path. |
| G6 Acceptance completeness | PASS | Every original T07 criterion plus IR-C01 and IR-C02 has implementation evidence, a passing test, or an explicit non-production boundary. |

Critical-gate result: PASS

## Release 1.8 Additional Gates

| Gate | Status | Applicability Evidence |
|---|---|---|
| G7 Migration, model, and PostgreSQL correctness | PASS | Exact corrected metadata, 0002-to-0003 upgrade, clean head, downgrade/re-upgrade, 66 live tests, replacement check, no foreign key, trigger rejection, transaction rollback, and cleanup pass. |
| G8 Lifecycle, trust, and audit-bypass prevention | PASS | Draft-only updates, stale precedence, exact T04 replacement translation, every lifecycle mapping, zero-event invalid operations, no public append API, legacy separation, and shared-transaction append behavior pass. |

## Correction-Cycle History

| Cycle | Starting Score | Findings | Corrections | Ending Score | Validation Evidence | Status |
|---:|---:|---|---|---:|---|---|
| 1 | 96 | Internal review found transaction-start recording-time risk and two acceptance-matrix evidence gaps; validation also exposed test-double, formatting, sandbox, scanner, Git-permission, report-path, final remote-state, and PR-body quoting failures. | Used insert-time server recording, added wall-clock and post-append rollback proofs, corrected test doubles and formatting, reran with approved access, fixed scanner, report, and PR invocations, verified remote state, and preserved every failed result. | 100 | 29 domain, 21 service, 17 persistence, 22 T07 live, 483 affected, 22 ingestion, 622/49 full, 52/0 combined live, MyPy 57, Ruff, format, reports, links, safety, remote state, and runs `30198494465` plus `30198785192` pass. | CLOSED |
| 2 | 87 | Independent review `4781619375` found non-draft complete-composition updates were permitted and the accepted T04 deprecation replacement UUID was dropped. | Enforced ordered draft editability, preserved exact replacement metadata through domain and PostgreSQL history, added bounded DDL without a foreign key, and expanded all required test matrices while preserving original history. | 100 | IR-C01 31, IR-C02 15, T07 39 domain plus 41 service plus 8 repository plus 36 live, 19 persistence, 489 affected, 22 ingestion, 654/63 full, 66/0 live, MyPy 57, Ruff, format, safety, and run `30201484822` pass. | CLOSED |

## Recommended Follow-up Issues

- Independent ChatGPT review should evaluate PR #59 at the final exact report
  head before any readiness or merge decision.
- T06 must preserve organization scope, deterministic root-revision behavior,
  and the no-child-only-write invariant when adding filters and pagination.
- T09 must route governed mutations through T07 orchestration and must not
  expose arbitrary audit append payloads.
- T10 final integration must wait for independently accepted wave outputs.
- PR #49 must remain draft and unmerged.

## Blockers

None.

## Recommendation

READY FOR INDEPENDENT RE-REVIEW
