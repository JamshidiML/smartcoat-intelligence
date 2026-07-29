# Release 1.8 Codex Master Prompt

Use this prompt only after confirming the repository and GitHub state described below.

---

You are implementing SmartCoat Release 1.8 — Knowledge Capture Core.

Repository:
`JamshidiML/smartcoat-intelligence`

Main baseline:
`47df21458038d107bb7c7cb98dc6d23dd3b6d7e9`

Release branch:
`release/1.8-knowledge-capture-core`

Parent issue:
#38

Draft release PR:
#49

Execution issues:

- T01 #39 — release contracts and ADRs
- T02 #40 — Knowledge Object v2
- T03 #41 — structured evidence and provenance
- T04 #42 — lifecycle and controlled mutation
- T05 #43 — persistence, migrations, repository CRUD, and #35
- T06 #44 — filtering, sorting, and cursor pagination
- T07 #45 — immutable audit events and history
- T08 #46 — minimum domain context references
- T09 #47 — API contracts
- T10 #48 — engineering debt, #36, integration, and release evidence

## Read First

Read completely before changing files:

1. `AGENTS.md`
2. `SECURITY.md`
3. `CONTRIBUTING.md`
4. `docs/project/PROJECT_STATE.md`
5. `docs/project/MVP_STRATEGY.md`
6. `docs/project/RELEASE_1_8_DEFINITION_PACK.md`
7. `architecture/releases/RELEASE_1_8_Knowledge_Capture_Core.md`
8. `docs/execution/RELEASE_1_8_EXECUTION_CONTROL_CENTER.md`
9. parent issue #38
10. the assigned thread issue
11. issues #35 and #36 when relevant
12. current domain, service, repository, API, migration, and test code touched by the thread

Where older current-release wording still says Release 1.7, treat Release 1.8 issue #38 and its definition pack as the active release scope. T01 must synchronize stale active-release documentation before implementation contracts are accepted.

## Non-Negotiable Boundaries

Do not:

- commit directly to `main`;
- target implementation PRs at `main`;
- merge or mark PRs ready without authorization;
- force-push, rewrite, squash, or delete history;
- ingest real or confidential industrial data;
- add `.env`, credentials, secrets, proprietary formulations, prices, customer or supplier data, internal emails, production records, private reports, or raw company datasets;
- implement UI, AI extraction, voice capture, adaptive questions, semantic search, ERP, email ingestion, unrestricted file ingestion, production IAM, tenant-isolation claims, the complete ontology, or a live pilot;
- bypass lifecycle, revision, evidence, provenance, or audit contracts through generic updates;
- represent unexecuted validation as passing;
- redefine shared contracts outside T01 without a documented blocker and human decision.

Use synthetic, generalized fixtures only.

## Persistent Worktree Root

Use:

`/Users/mohsenjamshidi/Documents/Smartcoat/worktrees/release-1.8`

Recommended mapping:

| Thread | Path | Branch |
|---|---|---|
| T01 | `.../T01` | `thread/18-01-release-contracts` |
| T02 | `.../T02` | `thread/18-02-knowledge-object-v2` |
| T03 | `.../T03` | `thread/18-03-evidence-provenance` |
| T04 | `.../T04` | `thread/18-04-lifecycle-mutation` |
| T05 | `.../T05` | `thread/18-05-persistence-migrations` |
| T06 | `.../T06` | `thread/18-06-filtering-pagination` |
| T07 | `.../T07` | `thread/18-07-audit-history` |
| T08 | `.../T08` | `thread/18-08-domain-context` |
| T09 | `.../T09` | `thread/18-09-api-contracts` |
| T10 | `.../T10` | `thread/18-10-release-validation` |

Never use `/private/tmp` for persistent worktrees.

## Stage 0 — Preflight and Setup

Before editing:

1. Fetch origin.
2. Verify `main` contains the completed Release 1.7 merge.
3. Verify the release branch exists and PR #49 is open, draft, and targets `main`.
4. Record exact remote heads.
5. Inspect existing worktrees and prune only stale registrations whose directories no longer exist.
6. Create or recover each persistent worktree from the exact intended remote branch head.
7. Create missing thread branches from the exact current release-branch head.
8. Create one draft PR per thread targeting `release/1.8-knowledge-capture-core`.
9. Add issue, branch, PR, owned paths, dependencies, and report path to the control center.
10. Do not begin dependent implementation before the required wave is authorized.

Return a setup table before editing:

- thread
- issue
- worktree
- branch
- base SHA
- PR
- clean status
- ownership boundary
- dependency readiness

Stop on any branch, SHA, worktree, or PR mismatch.

## Execution Waves

The threads are not ten independent parallel implementations. Use dependency-safe waves.

### Wave 0 — Contract Lock

Execute only T01.

T01 must:

- reconcile the Release 1.8 definition with current code and accepted architecture;
- update stale active-release references in `AGENTS.md`, `PROJECT_STATE.md`, roadmap/release indexes when owned and justified;
- write accepted ADR proposals for lifecycle, revision/concurrency, deletion/deprecation, pagination, minimum context, and evidence/provenance compatibility;
- define exact shared contracts and file ownership;
- identify any human decisions required before implementation;
- make no product-code or migration changes.

After T01, stop for independent ChatGPT review. Do not start Wave 1 until T01 shared contracts are accepted.

### Wave 1 — Canonical Domain Foundation

After T01 acceptance:

- T02 Knowledge Object v2
- T08 minimum domain context
- T10 engineering baseline portion for issue #36 only, without claiming final integration

T02 and T08 may proceed in parallel only if T01 assigns non-overlapping ownership and a single integration contract.

Stop for independent review before Wave 2.

### Wave 2 — Evidence and Lifecycle

After Wave 1 acceptance:

- T03 structured evidence and provenance
- T04 lifecycle and controlled mutation

These may proceed in parallel only against the accepted T02/T08 contracts. T04 may define audit commands but must not own T07 persistence or semantics.

Stop for independent review before Wave 3.

### Wave 3 — Persistence and Audit

After Wave 2 acceptance:

- T05 persistence, migrations, repository CRUD, and issue #35
- T07 audit events and history

Coordinate transaction boundaries explicitly. Do not duplicate storage models or migrations. If atomic object-plus-audit behavior requires shared files, assign one owner and make the other thread consume the contract.

Stop for independent review before Wave 4.

### Wave 4 — Query Behavior

Execute T06 filtering, sorting, and cursor pagination after T05 persistence is accepted.

Stop for independent review before Wave 5.

### Wave 5 — API Completion

Execute T09 after T03–T08 contracts are accepted.

Routes remain thin. Real HTTP-to-PostgreSQL evidence is required.

Stop for independent review before integration.

### Wave 6 — Integrated Release Candidate

T10 creates a controlled integration candidate only after T01–T09 are accepted within scope.

Apply accepted heads in the approved integration order. Preserve source histories. Report every conflict. Never resolve a semantic contract conflict silently.

Run the complete integrated validation from issue #48 and the Release 1.8 definition pack.

## Thread Report Contract

Each thread creates one report under:

`docs/execution/reports/release_1_8/`

Suggested names:

- `T01_RELEASE_CONTRACTS_REPORT.md`
- `T02_KNOWLEDGE_OBJECT_V2_REPORT.md`
- `T03_EVIDENCE_PROVENANCE_REPORT.md`
- `T04_LIFECYCLE_MUTATION_REPORT.md`
- `T05_PERSISTENCE_MIGRATIONS_REPORT.md`
- `T06_FILTERING_PAGINATION_REPORT.md`
- `T07_AUDIT_HISTORY_REPORT.md`
- `T08_DOMAIN_CONTEXT_REPORT.md`
- `T09_API_CONTRACTS_REPORT.md`
- `T10_RELEASE_VALIDATION_REPORT.md`

Use the current validated report-v2 contract and scoring rules unless T01/T10 proposes a reviewed additive version.

Report:

- exact objective and acceptance criteria;
- files changed;
- exact commands executed;
- actual pass, fail, skip, blocked, and not-run results;
- architecture impact;
- security and data impact;
- known limitations;
- correction items and point burden;
- self-score;
- independent-review placeholder or recorded score;
- critical gates including G7 and G8;
- correction-cycle history;
- blockers with question, options, consequences, and recommendation.

## Scoring

Rubric:

- correctness and evidence: 25
- scope and acceptance criteria: 20
- architecture and release alignment: 15
- verification and tests: 15
- security, privacy, and governance: 10
- documentation and traceability: 10
- maintainability and clarity: 5

Provisional score:

`0.40 × Codex self-score + 0.60 × ChatGPT reviewer score`

Any critical-gate failure caps the thread at 79 until corrected and independently re-reviewed.

Never claim 100/100 before independent review records 100 and all corrections are resolved.

## Minimum Validation Per Thread

Every thread runs, where applicable:

- focused tests;
- negative and failure tests;
- MyPy for affected source;
- scoped Ruff and format checks;
- full existing tests when practical;
- `git diff --check`;
- owned-path check;
- secret, `.env`, binary, and confidential-data scan;
- report validation.

Persistence and API threads also require live PostgreSQL evidence with exact opt-in, mandatory isolated schema, synthetic data, and proven teardown.

## Final Response Per Wave

Return:

- thread and issue
- branch and PR
- starting and final SHA
- files changed
- acceptance criteria status
- actual validation results
- self-score
- critical gates
- open corrections
- blockers
- recommended next wave

Do not merge. Do not mark ready. Wait for independent ChatGPT review and explicit authorization after every wave.
