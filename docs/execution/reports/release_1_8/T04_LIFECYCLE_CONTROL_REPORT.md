# T04 Lifecycle Control Report

Report schema version: `smartcoat-execution-report-v2.0`

Thread ID: T04

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/42

Branch: `thread/18-04-lifecycle-controlled-mutation`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/56

Final status: `READY FOR INDEPENDENT RE-REVIEW`

## Objective

Implement the complete Accepted ADR-0020 and ADR-0022 lifecycle, controlled
mutation, review-projection, draft-deletion, and safe audit-request contract as
pure application planning. T04 consumes the accepted T02
`KnowledgeObjectV2CoreRecord`, verifies target and revision preconditions,
enforces the exact closed transition matrix, and returns immutable desired-work
plans without changing the current record, persisting data, committing a
transaction, or constructing a final `EnterpriseEvent`.

Correction Cycle 1 closes the strict pre-deprecation history finding from
independent review `4765339529`. A deprecated object now projects a legacy
review status only when trusted history says it has left draft and its exact
last pre-deprecation lifecycle is `approved`; that one valid case projects
`validated`. Missing history and every non-approved predecessor fail closed as
`lifecycle_history_inconsistent`.

Exact starting release SHA:
`f62f4bbc5554f6d19eb1bd2f60b2f7f74bbf8776`.

Implementation SHA:
`edf859d5bd4262ccd474ee152767bd6d47946785`.

Initial publication and independently reviewed SHA:
`8ee81c8411a9659da36b7699200af434156f7dfe`.

Correction implementation SHA:
`91fd13ac762c0a73cff3f51acca1dd4bcfed2e2f`.

The final correction publication head and its exact-head CI are recorded by PR
#56 and the issue evidence comments because a Git commit cannot embed its own
resulting SHA. The correction publication commit changes only this report.

## Files Changed

- `src/smartcoat/domain/knowledge_lifecycle.py`
- `src/smartcoat/services/knowledge_lifecycle_service.py`
- `tests/test_knowledge_lifecycle_service.py`
- `docs/execution/reports/release_1_8/T04_LIFECYCLE_CONTROL_REPORT.md`

These are exactly the four T04-owned paths. T02 and T08 domain modules, shared
package exports, current Knowledge Object, API routes, services, repositories,
mappers, database records, migrations, dependencies, CI, schemas, Accepted
ADRs, and every other thread report remain unchanged.

## Methods and Commands Executed

- `git fetch origin`
- `git status --short --branch`
- `git rev-parse HEAD origin/release/1.8-knowledge-capture-core origin/main`
- `python --version`
- `python3 --version`
- `/Users/mohsenjamshidi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m ruff check .`
- `/Users/mohsenjamshidi/Documents/Smartcoat/worktrees/release-1.8/.venv/bin/python -m pip check`
- `/Users/mohsenjamshidi/Documents/Smartcoat/worktrees/release-1.8/.venv/bin/python -m ruff check .`
- `/Users/mohsenjamshidi/Documents/Smartcoat/worktrees/release-1.8/.venv/bin/python -m ruff format --check .`
- `/Users/mohsenjamshidi/Documents/Smartcoat/worktrees/release-1.8/.venv/bin/python -m mypy src`
- `/Users/mohsenjamshidi/Documents/Smartcoat/worktrees/release-1.8/.venv/bin/python -m pytest`
- `/Users/mohsenjamshidi/Documents/Smartcoat/worktrees/release-1.8/.venv/bin/python -m pytest tests/test_knowledge_lifecycle_service.py -q`
- `/Users/mohsenjamshidi/Documents/Smartcoat/worktrees/release-1.8/.venv/bin/python -m pytest tests/test_knowledge_lifecycle_service.py tests/test_knowledge_objects_v2.py tests/test_context_references.py tests/test_domain_models.py tests/test_imports.py -q`
- `/Users/mohsenjamshidi/Documents/Smartcoat/worktrees/release-1.8/.venv/bin/python -m pytest tests/test_api_persistent_routes.py -q`
- `/Users/mohsenjamshidi/Documents/Smartcoat/worktrees/release-1.8/.venv/bin/python -m ruff format src/smartcoat/domain/knowledge_lifecycle.py src/smartcoat/services/knowledge_lifecycle_service.py tests/test_knowledge_lifecycle_service.py`
- `git diff --cached --check`
- `git commit -m "Implement governed knowledge lifecycle planning"`
- `git push -u origin thread/18-04-lifecycle-controlled-mutation`
- `python -m pytest tests/test_validate_execution_reports.py -q`
- `python scripts/validate_execution_reports.py <all committed execution reports>`
- `python scripts/validate_execution_reports.py docs/execution/reports/release_1_8/T04_LIFECYCLE_CONTROL_REPORT.md`
- `python -c '<standard-library Markdown local-link validator>'`
- `python -c '<exact owned-path and cross-thread zero-overlap validator>'`
- `python -c '<secret, environment, binary, credential, personal-data, and confidential-data validator>'`
- `git diff --check f62f4bbc5554f6d19eb1bd2f60b2f7f74bbf8776 HEAD`
- `git diff --check f62f4bbc5554f6d19eb1bd2f60b2f7f74bbf8776`
- `.venv/bin/python -m pytest tests/test_knowledge_lifecycle_service.py -q`
- `.venv/bin/python -m pytest tests/test_knowledge_lifecycle_service.py -q -k 'deprecated_projection'`
- `../.venv/bin/python -m pytest tests/test_knowledge_lifecycle_service.py -q -k 'deprecated_projection'`
- `../.venv/bin/python -m pytest tests/test_knowledge_lifecycle_service.py -q`
- `../.venv/bin/python -m pytest tests/test_knowledge_lifecycle_service.py tests/test_knowledge_objects_v2.py tests/test_context_references.py tests/test_domain_models.py tests/test_imports.py -q`
- `../.venv/bin/python -m pytest tests/test_api_persistent_routes.py -q`
- `../.venv/bin/python -m pytest -q`
- `../.venv/bin/python -m mypy src`
- `../.venv/bin/python -m ruff check .`
- `../.venv/bin/python -m ruff format --check .`
- `../.venv/bin/python -m pip check`
- `git commit -m "Enforce approved pre-deprecation history"`

GitHub connector operations verified issues #38, #40, #41, #42, #46, and #48,
PRs #49 and #55, created draft PR #56, corrected its initial SHA text, and
inspected workflow run 61 and every job step. Correction Cycle 1 additionally
verified review `4765339529`, the exact reviewed head, PR #56, and issues #42
and #38 before editing. No PostgreSQL, Docker, migration, repository, mapper,
route, or final event command was run.

## Actual Results

| Method or Command | Actual Result | Evidence |
|---|---|---|
| Worktree and release preflight | PASS | Worktree was clean on the required branch; local HEAD and release remote both equaled `f62f4bbc5554f6d19eb1bd2f60b2f7f74bbf8776`; main equaled `47df21458038d107bb7c7cb98dc6d23dd3b6d7e9`. |
| GitHub dependency preflight | PASS | PR #55 was merged; issue #40 was closed completed; issues #38, #41, #42, #46, and #48 were open; PR #49 was open, draft, unmerged, and headed by the exact release SHA. |
| Bare `python` discovery | FAIL: corrected environment selection | The shell had no `python` executable. No validation result was claimed; the existing shared Python 3.12 virtual environment was located and used. |
| System `python3` discovery | PASS: version measured only | System Python reported 3.9.6 and supplied no Release 1.8 validation evidence. |
| Bundled runtime Ruff discovery | FAIL: corrected environment selection | The separate bundled Python 3.12 runtime did not contain Ruff. No quality result was claimed; the repository's existing shared Python 3.12 environment was used. |
| Starting pip check | PASS | No broken requirements found; the disabled user pip cache warning was non-behavioral. |
| Starting Ruff | PASS | Repository-wide Ruff reported zero findings. |
| Starting Ruff format | PASS | All 59 baseline files were formatted. |
| Starting MyPy | PASS | No issues in 46 baseline source files. |
| Starting full pytest | PASS | 258 tests passed and 4 PostgreSQL-opt-in tests skipped. |
| Initial focused T04 tests | PASS | 143 lifecycle tests passed before output-contract hardening. |
| First scoped format check | FAIL: corrected mechanical formatting | Ruff identified all three new source/test paths for formatting; the formatter was applied and rechecked. |
| Internal output-contract review | PASS | Immutable plans now reject manually assembled action/transition, revision, timestamp, audit-request, and deletion-tombstone inconsistencies. |
| Final focused T04 tests | PASS | 148 tests passed, including all 12 allowed transitions and all 37 unsupported lifecycle pairs. |
| Affected T02, T08, domain, and import tests | PASS | 328 tests passed. |
| Current API regression tests | PASS | 8 tests passed; no route or OpenAPI behavior changed. |
| Final full pytest | PASS | 406 tests passed and 4 PostgreSQL-opt-in tests skipped. |
| Final MyPy | PASS | No issues in 48 source files. |
| Final Ruff | PASS | Repository-wide Ruff reported zero findings. |
| Final Ruff format | PASS | All 62 files were formatted. |
| Final pip check | PASS | No broken requirements found. |
| Implementation commit and push | PASS | Commit `edf859d5bd4262ccd474ee152767bd6d47946785` was pushed normally with upstream tracking and no history rewrite. |
| Draft PR creation | PASS | PR #56 is open, draft, unmerged, and targets `release/1.8-knowledge-capture-core`. |
| Initial PR body SHA | FAIL: corrected publication metadata | The first body incorrectly expanded short SHA `edf859d`; GitHub's exact head was immediately used to replace it with `edf859d5bd4262ccd474ee152767bd6d47946785`. Repository content was unaffected. |
| Implementation-head CI run 61 | PASS | Run `30015948231` passed checkout, Python 3.12 setup, dependency installation, pip compatibility, Ruff, format, MyPy, pytest, post-setup, and completion on the exact implementation SHA. |
| Independent review `4765339529` | FAIL: CORRECTION REQUIRED on prior head | Review of exact head `8ee81c8411a9659da36b7699200af434156f7dfe` scored 91/100, provisional weighted 94.2/100, and gate-adjusted 79/100 because deprecated projection accepted impossible non-approved predecessor histories. |
| Correction preflight | PASS | Before edits, local HEAD, upstream, and PR #56 head all exactly equaled reviewed SHA `8ee81c8411a9659da36b7699200af434156f7dfe`; the worktree was clean and the PR remained draft, open, unmerged, and based on the Release 1.8 branch. |
| Worktree-local `.venv` correction invocations | FAIL: corrected environment selection | Both requested test commands failed before collection because this worktree has no `.venv/bin/python`; no test result was claimed, and the established shared environment at `../.venv` was used. |
| Correction-specific deprecated projection tests | PASS | 9 tests passed: approved plus true history projects `validated`; missing, draft, captured, reviewed, validated, rejected, and deprecated predecessors fail closed; approved plus false history also fails closed. |
| Corrected focused T04 tests | PASS | 153 lifecycle tests passed, retaining the exact 12 allowed transitions, all 37 unsupported-pair failures, precedence, revision, delete, reopen, deprecation, and audit regressions. |
| Corrected affected T02, T08, domain, and import tests | PASS | 333 tests passed. |
| Corrected current API regression tests | PASS | 8 tests passed; no route or OpenAPI behavior changed. |
| Corrected full pytest | PASS | 411 tests passed and 4 PostgreSQL-opt-in tests skipped. |
| Corrected MyPy | PASS | No issues in 48 source files. |
| Corrected Ruff | PASS | Repository-wide Ruff reported zero findings. |
| Corrected Ruff format | PASS | All 62 files were formatted. |
| Corrected pip check | PASS | No broken requirements found; the disabled user pip cache warning was non-behavioral. |
| Correction implementation commit | PASS | Commit `91fd13ac762c0a73cff3f51acca1dd4bcfed2e2f` changes only the lifecycle domain and focused test paths. |
| Complete report-validator tests | PASS | 40 tests passed and 1 environment-configured test skipped. |
| All committed and T04 reports | PASS | All 17 execution reports passed the unchanged report-v2 validator. |
| T04 report-v2 | PASS | This report passed the unchanged report-v2 validator. |
| Markdown local links | PASS | 407 Markdown files and 118 repository-local targets were checked with zero broken targets. |
| Owned-path and cross-thread checks | PASS | Complete branch plus untracked publication state contained exactly four T04 paths and zero T03 or other-thread overlap. |
| First safety scanner | FAIL: scanner did not execute | A misplaced inline case-insensitive regex flag raised `re.error` before any path or content was scanned; no safety result was claimed from it. |
| Corrected safety scanner | PASS | Four owned paths contained no `.env`, binary, secret, credential, personal-data, or confidential-industrial-data artifact. |
| Final diff check | PASS | The release-base-to-index/worktree diff, including all four owned paths, had no whitespace error. |
| Correction report-validator tests | PASS | 40 tests passed and 1 environment-configured test skipped. |
| Correction all-report validation | PASS | All 17 committed execution reports, including the corrected T04 report, passed the unchanged report-v2 validator. |
| Corrected T04 report-v2 | PASS | The current corrected report passed the unchanged report-v2 validator with self-score 99, current reviewer/final scores Pending, C01 resolved, and C02 open for one point. |
| Corrected Markdown local links | PASS | 407 Markdown files and 118 repository-local targets were checked with zero broken targets. |
| Corrected exact ownership | PASS | The release-base diff contains exactly the four authorized T04 paths; no unexpected untracked file exists. |
| Corrected T03/T04 zero overlap | PASS | Comparing both complete release-base branch diffs found zero shared paths. |
| Corrected diff checks | PASS | Both release-base and uncommitted report diffs have no whitespace error. |
| Corrected safety scan | PASS | All four owned paths are UTF-8 text and contain no secret, `.env`, binary, credential, email/personal-data, or raw industrial-data artifact indicator. |
| PostgreSQL validation | SKIP | T04 owns no persistence behavior and makes no PostgreSQL evidence claim. |

## Model and Service Inventory

| Contract | Purpose | Boundary |
|---|---|---|
| `LifecycleActor` | Required trimmed actor ID and declared role. | Metadata declaration only; no IAM proof. |
| Twelve explicit transition commands | One bounded input shape per accepted lifecycle action. | No generic lifecycle, review, revision-result, timestamp, event, database, organization, or mutation field. |
| `DeleteDraftCommand` | Explicit target, revision, actor, and reason for deletion planning. | Does not delete a row. |
| `LifecycleHistoryFacts` | Trusted history facts used for draft and deprecated projection. | Internal input from future T05/T07 integration, never a public command field. |
| `DraftDeletionFacts` | Trusted aggregate inbound-governed-reference fact. | T05 supplies the persistence-backed result later. |
| `LifecycleReviewProjection` | Exact read-only compatibility vocabulary. | Never a second writable workflow state. |
| `KnowledgeAuditAppendRequest` | Safe typed request for future audit append. | Not a final `EnterpriseEvent`; T07 owns that profile. |
| `LifecycleMutationPlan` | Immutable desired transition work. | Not a persisted or falsely updated Knowledge Object. |
| `DraftDeletionAuditTombstoneRequest` | Minimal content-free deletion audit request. | Not legal erasure or a final event. |
| `DraftDeletionPlan` | Immutable desired eligible draft deletion work. | T05 owns atomic delete, append, and one commit. |
| `KnowledgeLifecyclePlanner` | Pure transition and deletion planner with injected clock. | No repository, database, API, commit, or final event dependency. |

## Complete Transition Matrix

| From | To | Command | Required role | Required note or reason | Result |
|---|---|---|---|---|---|
| `draft` | `captured` | `SubmitDraftCommand` | Any non-empty declared role | Submission note | PASS |
| `captured` | `draft` | `RequestCapturedCorrectionCommand` | `reviewer` | Correction reason | PASS |
| `captured` | `reviewed` | `CompleteReviewCommand` | `reviewer` | Review note | PASS |
| `captured` | `rejected` | `RejectCapturedCommand` | `reviewer` | Rejection reason | PASS |
| `reviewed` | `draft` | `RequestReviewedCorrectionCommand` | Any non-empty declared role | Correction reason | PASS |
| `reviewed` | `validated` | `ValidateReviewedCommand` | `validator` | Validation note | PASS |
| `reviewed` | `rejected` | `RejectReviewedCommand` | Any non-empty declared role | Rejection reason | PASS |
| `validated` | `draft` | `RequestValidatedCorrectionCommand` | Any non-empty declared role | Correction reason | PASS |
| `validated` | `approved` | `ApproveValidatedCommand` | `approver` | Approval note | PASS |
| `validated` | `rejected` | `RejectValidatedCommand` | Any non-empty declared role | Rejection reason | PASS |
| `approved` | `deprecated` | `DeprecateApprovedCommand` | Any non-empty declared role | Deprecation reason | PASS |
| `rejected` | `draft` | `ReopenRejectedCommand` | Any non-empty declared role | Reopen reason | PASS |

The allowed set contains exactly these 12 rows. A Cartesian test over all 49
From/To pairs confirms every one of the remaining 37 pairs returns
`invalid_lifecycle_transition`. A separate 12-command test proves that each
explicit command is bound to its exact source state even where another command
could legitimately target the same destination.

## Role and Note Matrix

Reviewer is enforced only for captured correction, review completion, and
captured rejection. Validator is enforced only for reviewed validation.
Approver is enforced only for validated approval. The other seven transition
rows accept any trimmed non-empty declared role and do not invent a stricter
authorization policy.

Every transition and draft deletion requires its named non-blank note or
reason. Actor ID, role, note, and reason values are trimmed and bounded.
Missing required command fields fail Pydantic validation; blank roles return
`lifecycle_role_required`; role mismatch returns `lifecycle_role_mismatch`;
blank transition or deletion text returns `lifecycle_note_required`.

These checks validate contract declarations only. They do not authenticate an
identity, assign an employment role, or prove legal or production authority.

## Capture Completeness

Draft submission requires a valid T02 core, at least one bounded content key,
and at least one ordered evidence ID. T02 construction already guarantees
required organization, owner, confidentiality, and bounded JSON. Empty content
or zero evidence IDs returns `knowledge_capture_incomplete`.

T04 deliberately does not require T03 `EvidenceReference` objects while T03
runs in parallel. T05/T09 integration must later prove that each ordered
identity resolves to accepted structured evidence. No textile-specific product
rule is introduced.

All explicit commands forbid extra client fields. Tests reject resulting
revision, transition timestamp, lifecycle, review status, created/updated
timestamps, audit event ID, database ID, organization change, and arbitrary
mutation payload.

## Review Projection and History Facts

| Authoritative lifecycle and facts | Read-only projection | Result |
|---|---|---|
| New `draft`, never left draft | `not_reviewed` | PASS |
| Correction `draft`, previously left draft | `needs_correction` | PASS |
| `captured` | `in_review` | PASS |
| `reviewed` | `accepted` | PASS |
| `validated` | `validated` | PASS |
| `approved` | `validated` | PASS |
| `rejected` | `rejected` | PASS |
| `deprecated`, valid pre-deprecation `approved` | `validated` | PASS |
| `deprecated`, missing or any non-approved predecessor | No projection; fail closed | PASS |
| `deprecated`, pre-deprecation `approved`, never left draft | No projection; fail closed | PASS |

For `deprecated`, the only valid predecessor is `approved` and
`has_ever_left_draft` must be true. Missing, `draft`, `captured`, `reviewed`,
`validated`, `rejected`, and `deprecated` predecessors all return
`lifecycle_history_inconsistent`; false `has_ever_left_draft` also fails even
with `approved`. A non-draft active state that claims never to have left draft,
or pre-deprecation facts on an active record, likewise fails closed.
`approved` is intentionally absent from the review-projection vocabulary, so
projection `validated` never proves authoritative lifecycle `approved`.

## Revision and Error Precedence

The planner verifies command target first and expected revision second before
transition, history, role, note, or capture checks. Tests combine a wrong
target, stale revision, invalid lifecycle, wrong role, blank note, incomplete
capture, and inbound-reference fact and confirm:

1. wrong target returns `knowledge_object_target_mismatch`;
2. matching target with stale revision returns `stale_revision`;
3. the current record revision never increments in memory;
4. the command and alias-free T02 core remain byte-stable.

Every successful transition plan has `resulting_revision = current.revision +
1`. The desired-work output and its audit request independently reject any
other revision relationship.

## Draft Delete Eligibility and Safe Tombstone

Deletion planning succeeds only for a current `draft` whose expected revision
matches, whose trusted history says it has never left draft, and whose trusted
aggregate fact reports no inbound governed reference. Create and update audit
history is intentionally not part of the blocker fact.

A correction draft returns `draft_delete_ineligible`. An inbound Knowledge,
Decision, or other governed reference represented by the aggregate fact returns
`inbound_reference_blocks_deletion`. Captured, reviewed, validated, approved,
rejected, and deprecated records each return
`trusted_record_hard_delete_forbidden`.

The immutable tombstone request contains exactly:

- action `delete_draft`;
- object ID;
- object revision;
- acting actor ID and role;
- reason;
- trusted server timestamp.

It contains no title, description, evidence, content, context, owner,
confidentiality, organization, formulation, or other business payload.

## Reopen, Deprecation, and Audit Boundary

Rejected records reopen only through `ReopenRejectedCommand`; the plan creates
a new revision and projects the resulting draft as `needs_correction`.
Approved records leave active use only through `DeprecateApprovedCommand`;
optional replacement identity is carried safely in the audit append request,
the prior approved review projection remains `validated`, and the source
record remains approved and unchanged. Deprecated records cannot transition
further.

Each transition returns exactly one `KnowledgeAuditAppendRequest` containing
object identity, typed action, previous/resulting lifecycle, declared actor,
reason or note, expected/resulting revision, trusted UTC timestamp, and only a
safe optional replacement identity. Plan validators require exact agreement
between the plan and request.

No event ID or arbitrary event type is accepted. No title, content, evidence
body, context attribute, formulation, database detail, or confidential
business payload is included. T07 owns the final canonical typed
`EnterpriseEvent` profile. T05 owns object mutation plus event append and one
atomic commit.

## Acceptance-Criteria Evidence

- [x] Every one of the 12 allowed transitions succeeds with the exact lifecycle, revision increment, trusted time, projection, actor/note, and one audit request. Evidence: 12-row parameterized test passes.
- [x] Every unsupported lifecycle pair fails deterministically. Evidence: all 37 remaining Cartesian pairs return `invalid_lifecycle_transition`.
- [x] Role and note rules match ADR-0020 without invented production authorization. Evidence: required-role, generic-role, blank actor/role, blank note, and missing-field matrices pass.
- [x] Draft capture readiness requires valid T02 governance, non-empty bounded content, and ordered evidence identity. Evidence: positive and both negative readiness cases pass.
- [x] Review projection is read-only, history-aware, and fail-closed. Evidence: new/correction draft, five active states, approved-only deprecated projection, seven invalid predecessors, false-history, and active-state contradiction tests pass.
- [x] Target and stale revision precedence is deterministic and no source revision changes. Evidence: combined precedence and source-stability tests pass.
- [x] Draft deletion follows ADR-0022 and all non-draft records reject hard deletion. Evidence: eligible, correction, inbound, stale, target, and six non-draft cases pass.
- [x] Reopen and deprecation remain explicit, revisioned, and non-destructive. Evidence: rejected reopen, approved deprecation, replacement, and deprecated-terminal tests pass.
- [x] Audit and tombstone requests are immutable, minimal, internally consistent, and not final events. Evidence: exact-field, extra-field, timestamp, revision, transition, plan/request, and tombstone tests pass.
- [x] T02, T08, current API, persistence, and cross-thread ownership remain isolated. Evidence: 328 affected tests, 8 API tests, source-dependency scans, and exact path checks pass.
- [x] Required static, repository, report, link, safety, and CI checks are recorded. Evidence: implementation-head CI and local quality results pass; publication checks are recorded in Actual Results.
- [x] No real or confidential industrial data was used. Evidence: generalized synthetic fixtures and prohibited-artifact scans pass.

## Architecture Impact

T04 adds a direct-import application contract without modifying shared package
exports. `LifecycleState` remains the sole workflow authority. The new review
enum is explicitly a computed compatibility projection, not another state
machine.

Commands cannot supply server-managed result fields. The planner consumes the
accepted alias-free T02 core and retains no mutable core or command alias in
its result. It returns only immutable desired work and never a falsely
persisted `KnowledgeObjectV2CoreRecord`.

The implementation preserves accepted ownership:

- T03 owns structured evidence and provenance;
- T05 owns persistence, inbound-reference lookup, compare-and-swap, atomic
  object mutation or delete, audit append, and one commit;
- T07 owns final typed Knowledge `EnterpriseEvent` semantics and history;
- T09 owns explicit request, response, error, route, and OpenAPI behavior.

## Security and Data Impact

Fixtures use generalized synthetic actor, owner, organization, evidence, note,
and UUID values. No customer, supplier, formulation, price, production, email,
personal, credential, or confidential industrial data was used.

Commands forbid arbitrary payloads and server-managed fields. Audit requests
contain no Knowledge Object content. Actor and organization values remain
metadata declarations only; there is no production IAM, tenant isolation,
authorization, retention, external-existence, or real-data permission claim.

## Known Limitations

- T03 structured evidence is intentionally not required inside T04's parallel
  capture-readiness check; T05/T09 must integrate accepted evidence later.
- Trusted lifecycle history and inbound-reference facts are supplied by
  downstream application/persistence work; T04 does not query or prove them.
- `KnowledgeAuditAppendRequest` is not a final canonical `EnterpriseEvent`;
  T07 owns that contract.
- Plans do not persist, update, delete, flush, commit, roll back, or prove
  atomic transactions; T05 owns those behaviors.
- No route, mapper, migration, repository, PostgreSQL, production IAM,
  tenancy, legal-erasure, API-completion, real-data, or production-readiness
  result is claimed.
- Independent re-review of the corrected publication head is pending, so the
  self-score remains below 100 and current reviewer, weighted, and
  gate-adjusted scores remain Pending.

## Lost Points and Correction Items

| Item | Source | Points | Status | Action or Evidence |
|---|---|---:|---|---|
| C90 | Initial static-quality pass | 0 | RESOLVED | Historical internal item: applied Ruff formatting to three new files and reran focused and repository-wide checks. |
| C91 | Internal second pass and publication metadata | 0 | RESOLVED | Historical internal item: added immutable output consistency validators and four negative tests; corrected the PR-body SHA and safety-scanner regex, then reran both checks. |
| C92 | Initial exact-head independent review | 0 | RESOLVED | Historical open-review item: independent review `4765339529` evaluated exact head `8ee81c8411a9659da36b7699200af434156f7dfe`, supplied the previous 91/94.2/79 scores, and created C01. |
| C01 | Independent review `4765339529` on previous head | 9 | RESOLVED | Deprecated projection now requires true `has_ever_left_draft` and exact predecessor `approved`; exhaustive tests reject missing, draft, captured, reviewed, validated, rejected, deprecated, and false-history inputs while preserving the valid `validated` projection. |
| C02 | Independent corrected-head re-review | 1 | OPEN | Independent ChatGPT re-review must evaluate the exact corrected publication head before approval, ready transition, or merge. |

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 25 | Complete transition, invalid-pair, precedence, strict approved-only history, deletion, audit, and invariant tests pass. | None. |
| Scope and acceptance criteria | 20 | 20 | Exactly four T04 paths; all issue #42 and Wave 2 criteria are implemented without downstream work. | None. |
| Architecture and North-Star alignment | 15 | 15 | Lifecycle remains authoritative; human trust, explicit commands, deprecation, and bounded desired-work boundaries align. | None. |
| Verification, tests, or validation | 15 | 15 | 9 correction-specific, 153 focused, 333 affected, 8 API, 411/4 full, type, lint, format, pip, report, link, ownership, safety, and CI evidence is recorded. | None. |
| Security, privacy, and data governance | 10 | 10 | Synthetic fixtures, minimal audit requests, no arbitrary payloads, and prohibited-artifact scans preserve the boundary. | None. |
| Documentation and traceability | 10 | 9 | Initial and correction commands, failures, review ID/head/scores, C01, matrices, ownership, limits, gates, and CI publication boundary are recorded. | Exact corrected-head independent re-review remains pending. |
| Maintainability and clarity | 5 | 5 | Explicit commands, one closed matrix, typed errors, immutable outputs, and pure planner separate concerns clearly. | None. |
| Total | 100 | 99 | All in-scope correction implementation and local validation is complete for independent re-review. | One point remains open for independent corrected-head re-review. |

## ChatGPT Reviewer Score

Previous-head reviewer outcome: CORRECTION REQUIRED.

Independent review ID: `4765339529`.

Reviewed head: `8ee81c8411a9659da36b7699200af434156f7dfe`.

Previous-head reviewer score: 91/100.

Previous-head provisional weighted score: 94.2/100.

Previous-head gate-adjusted score: 79/100.

Previous-head gate result: G1 PASS, G2 PASS, G3 FAIL, G4 FAIL, G5 PASS, G6
FAIL, G7 PASS, and G8 FAIL.

Current corrected-head reviewer status: Pending.

Reviewer status: Pending

The current reviewer, weighted, and gate-adjusted scores must be supplied by an
independent re-review of the exact corrected publication head. The historical
scores above apply only to the reviewed previous head.

## Final Score

Provisional weighted score: Pending

Gate-adjusted score: Pending

The weighted and gate-adjusted scores remain pending until independent review.

## Critical-Gate Declaration

| Gate | Status | Evidence |
|---|---|---|
| G1 Verified claims | PASS | Every current claim maps to source, executed commands, exact test counts, GitHub state, CI run 61, or review `4765339529`; prior failures and prior-head scores remain recorded. |
| G2 Confidential data | PASS | Synthetic fixtures and secret, environment, binary, credential, personal-data, and confidential-data checks found no prohibited artifact. |
| G3 Approved scope and architecture | PASS | ADR-0020/0022 authority, T02 consumption, explicit commands, approved-only deprecated projection, and downstream ownership are preserved. |
| G4 Required validation | PASS | Correction-specific, focused, affected, API, full pytest, MyPy, Ruff, format, pip, report, link, ownership, safety, and implementation-head CI checks ran; exact correction-publication CI is reported outside this self-referential commit. |
| G5 File ownership | PASS | The complete branch diff contains exactly the four authorized T04 paths and zero T03 or other-thread overlap. |
| G6 Acceptance completeness | PASS | C01 and every issue #42 and Wave 2 T04 criterion have code, test, report, or explicit downstream-boundary evidence. |

Critical-gate result: PASS

## Release 1.8 Additional Gates

| Gate | Status | Applicability Evidence |
|---|---|---|
| G7 Persistence alignment and PostgreSQL evidence | PASS | T04 changes no persistence, migration, mapper, repository, route, or transaction path and makes no PostgreSQL claim; T05 ownership is explicit. |
| G8 Lifecycle, trust, and audit bypass prevention | PASS | Generic lifecycle/review writes are absent; deprecated history fails closed unless its exact predecessor is approved; exact commands, target/stale checks, closed transitions, immutable plans, and one safe audit request remain mandatory. |

## Correction-Cycle History

| Cycle | Starting Score | Findings | Corrections | Ending Score | Validation Evidence | Status |
|---:|---:|---|---|---:|---|---|
| 1 | 96 | First format check identified three files; internal review found output models should reject manual semantic contradictions; initial PR text contained an incorrect expanded SHA; the first safety regex did not compile. | Applied formatting, added output/action/revision/time/tombstone consistency checks and four tests, corrected PR metadata and scanner syntax, and reran local plus CI validation. | 99 | Historical evidence: 148 focused, 328 affected, 8 API, 406/4 full pytest, MyPy 48, Ruff, format 62, pip, reports, links, safety, and CI run 61 passed. | CLOSED |
| 2 | 79 | Independent review `4765339529` scored the exact previous head 91/100, provisional weighted 94.2/100, and gate-adjusted 79/100 because deprecated projection accepted impossible non-approved lifecycle histories. | Required true left-draft history plus exact `approved` predecessor, returned only `validated`, removed reviewed acceptance, and added exhaustive predecessor and false-history regressions without changing transition, persistence, API, or event ownership. | 99 | 9 correction-specific, 153 focused, 333 affected, 8 API, 411/4 full pytest, MyPy 48, Ruff, format 62, and pip checks passed; report, safety, publication, and exact-head CI evidence follows. | OPEN |

## Recommended Follow-up Issues

- Independent ChatGPT should re-review exact corrected PR #56 head, verify C01,
  and assign the authoritative current reviewer, weighted, and gate-adjusted
  scores.
- T07 should consume only the safe append request when defining the canonical
  typed Knowledge `EnterpriseEvent` profile.
- T05 should supply trusted history/reference facts and execute compare-and-swap
  mutation or eligible deletion plus audit append in one transaction and commit.
- T09 should expose explicit command-specific API contracts only after T03,
  T04, T05, and T07 are accepted and integrated.

## Blockers

None.

## Recommendation

READY FOR INDEPENDENT RE-REVIEW
