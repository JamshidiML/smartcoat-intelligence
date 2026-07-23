# T05 Persistence, Migrations, and Unit of Work Report

Report schema version: `smartcoat-execution-report-v2.0`

Thread ID: T05

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/43

Branch: `thread/18-05-persistence-uow`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/58

Final status: `READY FOR INDEPENDENT RE-REVIEW`

## Objective

Implement Release 1.8 Wave 3A persistence scope from exact release SHA
`6c15727fa6ecb86fbd5f73a6036c974694c654cc`: bounded Alembic support,
PostgreSQL Knowledge Object v2 storage, lossless T02/T03/T08 mapping, a
dedicated flush-only v2 repository, atomic optimistic concurrency, eligible
draft deletion, and one shared Unit of Work that owns commit, rollback, and
session lifecycle.

Original validated implementation SHA:
`92736d38c7047204e84eb1fb31a49497c3daecdc`.

Independent review `4766496385` evaluated publication head
`c27f217513e237bb3e302354cae7c1dea777e694`, scored it 86/100, and required
two corrections: complete-composition material-update semantics and
snapshot-consistent aggregate reads. Correction implementation SHA
`c222c279eceaeaa3b1d082adf8e78bd78889a00a` resolves both findings within
the four authorized correction paths. Independent re-review remains pending.

The final report-publication SHA is the Git commit containing this report. It
will be recorded in PR #58, issues #35, #38, #43, and #45, and the final
orchestrator response after normal push because a Git commit cannot contain
its own SHA.

The repository previously had raw SQL files under `database/migrations/` and a
`Base.metadata.create_all()` initializer, but no usable Alembic configuration,
environment, version table, or revision graph. The introduced Release 1.7
baseline is a bounded compatibility description for clean and unversioned
schemas; it is not represented as historical production-migration evidence.

## Files Changed

- `.github/workflows/ci.yml`
- `alembic.ini`
- `alembic/env.py`
- `alembic/script.py.mako`
- `alembic/versions/0001_release_1_7_baseline.py`
- `alembic/versions/0002_release_1_8_knowledge_v2.py`
- `pyproject.toml`
- `requirements/constraints-py312.txt`
- `src/smartcoat/storage/database/models.py`
- `src/smartcoat/storage/database/knowledge_v2_models.py`
- `src/smartcoat/storage/repositories/knowledge_v2_mappers.py`
- `src/smartcoat/storage/repositories/knowledge_v2_repository.py`
- `src/smartcoat/storage/unit_of_work.py`
- `tests/persistence/test_knowledge_v2_mappers.py`
- `tests/persistence/test_knowledge_v2_repository.py`
- `tests/persistence/test_unit_of_work.py`
- `tests/integration/test_knowledge_v2_postgres.py`
- `docs/execution/reports/release_1_8/T05_PERSISTENCE_MIGRATIONS_UOW_REPORT.md`

The initial 17 implementation paths were published on issue #43 before edits.
The dedicated v2 ORM path was added in a second pre-modification ownership
comment after the full suite exposed T02's requirement that the current
Release 1.7 model module and API import graph remain v2-free.

## Methods and Commands Executed

- `git fetch origin`
- `git rev-parse origin/release/1.8-knowledge-capture-core origin/main`
- `git status --short --branch`
- `python -m pip check`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python -m mypy src`
- `python -m pytest`
- `python -m pytest tests/persistence -q`
- `SMARTCOAT_RUN_LIVE_POSTGRES_TESTS=true SMARTCOAT_TEST_DATABASE_URL=<local-test-dsn> SMARTCOAT_TEST_SCHEMA=smartcoat_test_t05_legacy_api python -m pytest tests/integration/test_knowledge_v2_postgres.py tests/integration/test_persistent_api_postgres.py -q`
- `python -m pytest tests/test_knowledge_objects_v2.py::test_current_mapper_repository_service_and_route_do_not_import_v2 tests/test_knowledge_objects_v2.py::test_current_api_import_does_not_eagerly_load_v2_module tests/test_knowledge_objects_v2.py::test_current_database_record_shape_remains_release_1_7_only -q`
- `python -m pytest tests/test_validate_execution_reports.py -q`
- `python scripts/validate_execution_reports.py <all committed execution reports>`
- `python scripts/validate_execution_reports.py docs/execution/reports/release_1_8/T05_PERSISTENCE_MIGRATIONS_UOW_REPORT.md`
- `git diff --check`
- `git diff --check 6c15727fa6ecb86fbd5f73a6036c974694c654cc`
- `git commit -m "Add Alembic and Knowledge Object v2 schema"`
- `git commit -m "Implement v2 repository and shared unit of work"`
- `git push -u origin thread/18-05-persistence-uow`
- `gh pr create --draft --base release/1.8-knowledge-capture-core --head thread/18-05-persistence-uow`
- `gh pr checks 58 --repo JamshidiML/smartcoat-intelligence`
- `python -m pytest tests/integration/test_knowledge_v2_postgres.py -q -k '<C01 selection>'`
- `python -m pytest tests/integration/test_knowledge_v2_postgres.py -q -k 'revision_verified'`
- `python -m pytest tests/persistence -q`
- `python -m pytest tests/test_knowledge_objects_v2.py tests/test_evidence_provenance.py tests/test_knowledge_lifecycle_service.py tests/test_context_references.py -q`
- `SMARTCOAT_RUN_LIVE_POSTGRES_TESTS=true SMARTCOAT_TEST_DATABASE_URL=<local-test-dsn> SMARTCOAT_TEST_SCHEMA=smartcoat_test_t05_correction_legacy_api python -m pytest tests/integration/test_knowledge_v2_postgres.py tests/integration/test_persistent_api_postgres.py -q`
- `git commit -m "Correct v2 composition updates and coherent reads"`
- `git push origin thread/18-05-persistence-uow`
- `gh pr checks 58 --repo JamshidiML/smartcoat-intelligence --watch --interval 10`
- `gh run view 30030301803 --repo JamshidiML/smartcoat-intelligence`

The live test DSN used a local PostgreSQL 16 container, the dedicated
`smartcoat_test_t05` database, synthetic credentials already defined by the
local Docker development configuration, and randomized
`smartcoat_test_t05_*` schemas. Credentials are not emitted in this report.

## Actual Results

| Method or Command | Actual Result | Evidence |
|---|---|---|
| Protected release preflight | PASS | Release remote exactly equaled `6c15727fa6ecb86fbd5f73a6036c974694c654cc`; main exactly equaled `47df21458038d107bb7c7cb98dc6d23dd3b6d7e9`; PRs #56 and #57 were merged; issues #41 and #42 were closed; required open issues and draft PR #49 matched the execution contract. |
| Starting pip compatibility | PASS | No broken requirements were found. |
| Starting Ruff | PASS | Repository-wide Ruff returned zero findings. |
| Starting Ruff format | PASS | All 64 baseline files were formatted. |
| Starting MyPy | PASS | No issues in 49 baseline source files. |
| Starting full pytest | PASS | 553 tests passed and 4 PostgreSQL opt-in tests skipped. |
| Existing migration mechanism assessment | PASS | No usable Alembic history existed; only raw SQL scripts and a create-all initializer were present. |
| First sandboxed PostgreSQL invocation | FAIL: corrected execution permission | Localhost TCP was denied by the filesystem/network sandbox before any database connection; the same suite was rerun with explicit approved local-network access. |
| First actual live PostgreSQL pass | FAIL: corrected metadata alignment | Nine tests passed; one Alembic comparison found four legacy lifecycle/status server defaults present in migration DDL but absent from ORM metadata. |
| Metadata correction | PASS | The four legacy ORM server-default declarations were aligned; clean Alembic migration comparison returned no differences. |
| First full-suite integration pass | FAIL: corrected T02 isolation | 562 tests passed, 13 opt-in tests skipped, and three T02 tests rejected v2 ORM declarations in the current Release 1.7 model module and eager v2 loading from the repository initializer. |
| T02 isolation correction | PASS | V2 ORM records moved to a dedicated module, the legacy column shape was restored, the eager package export was removed, and all three contract tests passed. |
| Focused mapper, repository, and Unit-of-Work tests | PASS | 10 tests passed. |
| Clean Alembic upgrade | PASS | The isolated empty schema upgraded only through Alembic to `0002_release_1_8_knowledge_v2`. |
| Migration and ORM structural comparison | PASS | Alembic `compare_metadata` returned an empty difference list across tables, columns, types, defaults, nullability, keys, checks, and indexes. |
| Release 1.7 schema upgrade | PASS | A schema created from the historical SQL shape upgraded to head; its synthetic legacy row remained readable and explicitly incomplete. |
| Downgrade and re-upgrade | PASS | Head downgraded to `0001_release_1_7_baseline`, removed only v2 tables, then re-upgraded to head and completed a repository smoke round trip. |
| V2 composition round trip | PASS | Core, structured evidence, provenance, all seven context types, Knowledge and Decision relationships, order, UUIDs, UTC times, nulls, and nested content reconstructed canonically. |
| Scalar identity | PASS | Canonical text round trips preserved `true`, `false`, integer `1`, float `1.0`, null, list order, and dictionary semantics. |
| Create behavior | PASS | Repository-assigned UUID, draft lifecycle, revision 1, database timestamps, organization boundary, complete evidence/provenance checks, and invalid evidence-alignment rejection passed. |
| No-op behavior | PASS | Revision, timestamp, and PostgreSQL `xmin` remained unchanged, proving no row write. |
| Material update and stale behavior | PASS | Material update used atomic identity, organization, and revision predicates, incremented exactly once, stale material and stale no-op failed, and target mismatch was deterministic. |
| Concurrent session behavior | PASS | A real blocked two-session race allowed one revision-1 update to commit and forced the competing update to return `stale_revision`; no last-write-wins result occurred. |
| Lifecycle plan persistence | PASS | A valid T04 plan persisted its exact lifecycle and resulting revision; source domain state stayed immutable and reusing the plan failed stale. |
| Draft deletion | PASS | Eligible never-left-draft deletion succeeded; non-draft, correction draft, revision conflict, inbound Knowledge relation, and inbound Decision relation cases failed closed. |
| Unit-of-Work commit | PASS | Repositories flushed without commit; one observed Unit-of-Work commit made staged data visible. |
| Unit-of-Work rollback | PASS | Participant failure rolled back staged create, and leaving a staged material update uncommitted rolled back revision and content together. |
| Cross-organization access | PASS | Organization-mismatched reads returned no aggregate and did not reveal a cross-boundary record. |
| Combined live PostgreSQL suites | PASS | 15 tests passed and zero tests skipped: 10 T05 migration/persistence tests plus 5 current Release 1.7 PostgreSQL API regressions. |
| Final full pytest | PASS | 564 tests passed and 13 opt-in tests skipped; every T05 PostgreSQL test also ran separately with zero skips. |
| Final MyPy | PASS | No issues in 53 source files. |
| Final Ruff | PASS | Repository-wide Ruff returned zero findings. |
| Final Ruff format | PASS | All 75 files were formatted. |
| Final pip compatibility | PASS | No broken requirements were found. |
| Test-schema cleanup | PASS | Every randomized schema was dropped in fixture teardown and queried from `pg_namespace` with zero residual rows; a dedicated cleanup probe also passed. |
| Complete report-validator tests | PASS | 40 tests passed and one environment-configured test skipped. |
| All-report validation | PASS | All 19 committed/current execution reports passed the unchanged report-v2 validator. |
| T05 report-v2 validation | PASS | This T05 report passed the unchanged report-v2 validator. |
| Markdown local links | PASS | 409 Markdown files and 118 repository-local targets were checked with zero broken targets. |
| Exact owned-path validation | PASS | The release-base branch diff plus untracked report state contained exactly 18 declared T05 paths with no missing or unexpected path. |
| Safety and data scan | PASS | All 18 paths were UTF-8 text with no secret, environment file, binary, credential-token, email, phone, personal-record, or real-data marker finding. |
| Final diff checks | PASS | Both worktree and release-base diffs had zero whitespace error. |
| Implementation commits and push | PASS | Commits `6d8263a` and `92736d3` were pushed normally; no force push, reset, rebase, or history rewrite occurred. |
| Draft PR publication | PASS | PR #58 is draft, open, unmerged, and targets `release/1.8-knowledge-capture-core`. |
| Implementation-head GitHub Actions | PASS | Run `30027268394` passed the Python 3.12 quality job in 42 seconds and PostgreSQL 16 migration/persistence job in 1 minute 25 seconds; checkout used the pull-request merge ref derived from implementation head `92736d38c7047204e84eb1fb31a49497c3daecdc`. |
| Independent review | FAIL: correction required | Review `4766496385` evaluated head `c27f217513e237bb3e302354cae7c1dea777e694`, scored it 86/100, produced a 91.6/100 weighted score and 79/100 gate-adjusted score, and found C01 complete-composition updates plus C02 snapshot-consistent reads incomplete. |
| First correction live PostgreSQL invocation | FAIL: corrected test helper | Three tests passed and 21 failed because the new optional provenance helper nested its default transformation tuple one level too deeply; no repository defect was masked. The helper was corrected and every focused, complete, and CI live suite was rerun. |
| Correction MyPy pass 1 | FAIL: corrected tuple typing | Runtime-live behavior passed, but MyPy found five child-record collections typed as `Sequence` instead of immutable tuples. The repository now materializes explicit tuples; MyPy then passed all 53 source files. |
| C01 complete-composition comparison | PASS | Target mismatch and stale revision retain precedence. The desired mutable state, ordered evidence, and provenance are validated together and compared through type-preserving canonical JSON. Boolean/integer/float identity and governed order remain significant; dictionary insertion order does not. |
| C01 evidence-only material writes | PASS | Changed title, source reference, source system, context attributes, and context `true` to integer `1` each used organization-scoped revision CAS, incremented once, used the database timestamp, replaced children, and preserved core mutable state. |
| C01 provenance-only material writes | PASS | Changed source reference and reordered transformation history each used the same CAS and one revision increment while preserving unrelated mutable state and evidence. |
| C01 strict complete no-op | PASS | Identical supplied evidence/provenance plus dictionary-insertion-only state/evidence changes preserved revision, `updated_at`, root `xmin`, and every child-table `xmin`; no root or child write occurred. |
| C01 failure and rollback behavior | PASS | Evidence-only stale and provenance-only stale calls returned `stale_revision`; target mismatch won first; missing complete evidence and incomplete provenance failed deterministically; evidence-only and provenance-only participant failures rolled back root and children. |
| Focused C01 correction suite | PASS | 10 live PostgreSQL cases passed and 15 unrelated T05 cases were deselected. |
| C02 coherent-read strategy | PASS | Each aggregate read performs at most three organization-scoped attempts: root/revision, all children, direct final revision check, then return only on equality; mismatch/deletion expires Session state and retries, and exhaustion raises typed `aggregate_read_retry_exhausted`. No global isolation or lock policy changed. |
| C02 forced root and multiple-child update | PASS | A SQLAlchemy execution hook committed changed root title/content plus tags, evidence, and provenance after the reader root query. The reader retried and returned the complete revision-2 aggregate with no old/new mixture. |
| C02 evidence/provenance-only interleave | PASS | The same deterministic hook forced a complete-composition-only commit between root and children; the reader returned coherent revision 2 evidence and provenance with unchanged core content. |
| C02 lifecycle and deletion interleaves | PASS | A lifecycle-only commit returned coherent captured revision 2; concurrent eligible deletion retried to deterministic missing-object `None`. |
| C02 bounded exhaustion and resource behavior | PASS | Three forced commits exhausted exactly three attempts with `aggregate_read_retry_exhausted`; the connection immediately executed `SELECT 1` and an ordinary subsequent read returned revision 4, proving no deadlock or leaked transaction. |
| Focused C02 correction suite | PASS | 5 live PostgreSQL cases passed and 20 unrelated T05 cases were deselected. |
| Corrected persistence suite | PASS | All 11 persistence tests passed, including organization scoping for the final revision verification query. |
| Corrected affected contracts | PASS | 472 T02/T03/T04/T08 tests passed. |
| Corrected combined live PostgreSQL suites | PASS | 30 tests passed with zero T05 skips: 25 T05 migration/persistence/correction tests and 5 Release 1.7 PostgreSQL API regressions. |
| Corrected full pytest | PASS | 565 tests passed and 28 opt-in tests skipped in default mode; all 25 T05 PostgreSQL items ran separately with zero skips. |
| Corrected static and dependency gates | PASS | MyPy passed 53 source files; repository-wide Ruff passed; all 75 files passed format checking; pip reported no broken requirements. |
| Corrected report-validator tests | PASS | 40 validator tests passed and one environment-configured test skipped. |
| Corrected all-report validation | PASS | All 19 committed/current execution reports passed the unchanged report-v2 validator with the exact required count. |
| Corrected T05 report-v2 validation | PASS | This correction report passes as `READY FOR INDEPENDENT RE-REVIEW` with reviewer and current weighted scores pending re-review. |
| Corrected Markdown local links | PASS | 409 Markdown files and 118 repository-local targets were checked with zero broken targets. |
| Exact correction-path ownership | PASS | The reviewed-head-to-current diff contains exactly the four authorized correction paths with no missing, unexpected, or untracked path. |
| Preserved release-base ownership | PASS | The release-base diff remains exactly the original 18 declared T05 paths; no migration, ORM, mapper, Unit of Work, dependency, CI, domain, API, or ADR path was added by correction. |
| Corrected safety and data scan | PASS | All 18 release-base paths remain text-only by Git numstat; the four correction paths contain no `.env` file, binary, secret-token format, private key, email, E.164 phone, personal-record marker, proprietary formulation, or real industrial-data marker. Fixtures remain synthetic metadata only. |
| Corrected diff checks | PASS | Worktree and complete release-base `git diff --check` returned zero whitespace errors. |
| Corrected implementation-head PR merge-ref CI | PASS | Pull-request run `30030301803`, associated with branch head `c222c279eceaeaa3b1d082adf8e78bd78889a00a`, passed Python 3.12 quality in 37 seconds and PostgreSQL 16 migrations/persistence in 49 seconds. The PostgreSQL job collected and passed all 30 tests, including C01 and C02, on the PR merge ref rather than claiming a literal raw-head checkout. |

## Migration State and Graph

Previous state:

- `database/migrations/0001_initial.sql` and
  `database/migrations/0002_repository_indexes.sql` were raw SQL inputs;
- `scripts/init_db.py` called `Base.metadata.create_all()`;
- there was no Alembic dependency, configuration, environment, version table,
  revision graph, upgrade command, downgrade command, or metadata comparison.

New graph:

`base -> 0001_release_1_7_baseline -> 0002_release_1_8_knowledge_v2 (head)`

Revision `0001_release_1_7_baseline` creates the legacy Release 1.7 tables on a
clean schema or detects and retains the existing unversioned tables while
adding only missing legacy indexes. Revision
`0002_release_1_8_knowledge_v2` adds the separate v2 aggregate. Supported
downgrade is head to the Release 1.7 baseline; the test does not destructively
downgrade an existing legacy deployment through base.

No `create_all()` result is cited as migration evidence. The existing opt-in
Release 1.7 API test continues to use it only for its explicitly labeled
ORM/API compatibility fixture.

## Schema Inventory

| Table | Representation | Integrity and Access Purpose |
|---|---|---|
| `knowledge_objects` | Unchanged Release 1.7 aggregate | Explicit legacy table boundary; no fabricated v2 governance or revision. |
| `decision_objects` | Unchanged Release 1.7 aggregate | Existing API plus Decision target and inbound-reference compatibility. |
| `enterprise_events` | Unchanged Release 1.7 events | T07 remains owner of the future canonical audit profile. |
| `knowledge_objects_v2` | Typed aggregate root | Organization boundary, revision CAS, lifecycle/history facts, owner, confidentiality, query fields, canonical content text, and server timestamps. |
| `knowledge_object_v2_tags` | Ordered normalized child rows | Stable order and later organization/tag filtering. |
| `knowledge_object_v2_evidence` | Ordered normalized identities plus canonical metadata text | Exact evidence-ID alignment and scalar-preserving structured evidence. |
| `knowledge_object_v2_provenance` | One canonical text record per root | Complete ProvenanceV2, transformations, completeness, and derivation pair. |
| `knowledge_object_v2_context` | Ordered typed link rows plus canonical attributes text | All T08 fields, bounded attributes, conflict identity, and later context lookup. |
| `knowledge_object_v2_knowledge_relationships` | Ordered source/target links | Target revision plus deterministic inbound checks and restrictive target foreign key. |
| `knowledge_object_v2_decision_relationships` | Ordered Knowledge-to-Decision links | Typed target revision and existing Decision foreign-key integrity. |
| `alembic_version` | Alembic-owned revision row | Exact schema-head identity in each isolated target schema. |

The obvious later T06 access indexes cover organization plus knowledge type,
lifecycle, owner, tag, context type/reference, created time, and updated time.
The deterministic collection order remains `updated_at DESC, object_id DESC`;
T05 does not implement query filters, cursor encoding, or pagination.

## Domain-to-Storage Matrix

| Domain fact | Storage representation | Reconstruction or guard |
|---|---|---|
| Object and organization identity | UUID and bounded organization columns | Every canonical read and mutation requires both values. |
| Revision | Positive integer root column | Create is 1; CAS changes are exactly expected plus one. |
| Lifecycle | Bounded root column plus check constraint | Only T04 `LifecycleMutationPlan` can stage lifecycle changes. |
| Lifecycle history | `has_ever_left_draft` and optional pre-deprecation lifecycle | Enables correction-draft deletion rejection and trusted projection facts. |
| Created and updated times | Timezone-aware server-default PostgreSQL timestamps | Commands cannot supply them; material/lifecycle writes use database clock. |
| Title, description, type | Typed root columns | T02 Pydantic validation reruns on reconstruction. |
| Owner | `owner_id` and `owner_role` | Reconstructs `OwnerReference`; no IAM proof is claimed. |
| Confidentiality | Bounded root column | Reconstructs accepted enum; no access-control claim. |
| Uncertainty | Canonical JSON text or null | Preserves kind, numeric type, note, and null semantics. |
| Tags | Ordered child rows | Position continuity and aggregate ownership fail closed. |
| Bounded content | Canonical JSON text | Preserves Boolean, integer, float, null, arrays, and object semantics. |
| Evidence IDs and references | Ordered evidence rows | Stored identity must exactly match reconstructed canonical evidence order. |
| Provenance | One canonical JSON text row | Missing, incomplete, or corrupt canonical provenance fails reconstruction. |
| T08 context | Ordered typed columns plus canonical attributes text | Every context-reference type and bounded attribute scalar reconstructs through T08 validation. |
| Knowledge relationships | Ordered child rows with same-organization target FK | Supports target revision and deterministic inbound-reference rejection. |
| Decision relationships | Ordered child rows with Decision target FK | Supports target revision and relationship integrity. |

Canonical JSON is stored as PostgreSQL `TEXT`, not JSONB, for bounded content,
uncertainty, evidence metadata, provenance, and context attributes. Python's
JSON decoder preserves Boolean, integer, float, null, array order, and object
meaning; deterministic compact serialization with sorted object keys provides
stable equivalence without turning `true` into `1` or `1` into `1.0`.

## Legacy Compatibility

The persistence discriminator is structural:

- `knowledge_objects` is Release 1.7 legacy storage;
- `knowledge_objects_v2.contract_version` is constrained to `2`;
- no v2 ORM class exists in the current Release 1.7 model module;
- no v2 repository is imported by the current API package path;
- the legacy mapper returns only a
  `LegacyKnowledgeObjectPersistenceAssessment` labeled `legacy_v1_table`;
- accepted T02 and T03 adapters report blockers and
  `legacy_incomplete` evidence/provenance.

Legacy rows receive no organization, structured owner, confidentiality,
revision, evidence actor, capture timestamp, context classification, or
revision history. Legacy revision remains absent rather than receiving a
technical value that could be mistaken for historical truth.

## Repository and Transaction Behavior

`KnowledgeObjectV2Repository` exposes:

- `stage_create`;
- organization-scoped `get`;
- `load_for_controlled_mutation`;
- `lifecycle_history_facts`;
- `stage_material_update`;
- `stage_lifecycle_transition`;
- `compute_inbound_governed_reference_facts`;
- `stage_eligible_draft_deletion`;
- `assess_legacy`.

The repository source contains no `commit()` call. Create and child staging use
`Session.flush()`. Material and lifecycle writes execute an atomic predicate
equivalent to:

```sql
WHERE object_id = :object_id
  AND organization_id = :organization_id
  AND revision = :expected_revision
```

Target and stale checks use the accepted T02 evaluator first. The repository
then constructs and validates the complete desired composition from the
replacement core plus supplied-or-current ordered evidence and
supplied-or-current provenance. A no-op requires canonical identity across all
three dimensions. Mutable state and evidence already retain deterministic
canonical JSON; provenance receives the same sorted-key, compact,
type-preserving serialization. Dictionary insertion order is ignored while
Boolean, integer, float, evidence order, and transformation order remain
distinct. A changed evidence-ID sequence still requires a complete structured
evidence replacement. Generic lifecycle, revision, and timestamp update
parameters do not exist.

Evidence-only and provenance-only changes use the same atomic root CAS as a
core material update, increment revision exactly once, assign `updated_at`
through PostgreSQL `clock_timestamp()`, and transactionally replace all
mutable children. Exact complete-composition identity returns before the root
update or any child delete/reinsert.

Aggregate reads use a bounded revision-verified retry under the existing
`READ COMMITTED` configuration. One attempt reads the organization-scoped
root, reads every child collection, then selects the same scoped root revision
directly from PostgreSQL. Equality permits reconstruction; mismatch or
deletion expires Session identity state and retries. Three consecutive
collisions raise `aggregate_read_retry_exhausted`. This changes neither global
isolation nor lock behavior and applies to `get`, controlled loads, and
post-create, post-material-update, and post-lifecycle reloads.

Draft deletion rechecks persisted lifecycle, revision,
`has_ever_left_draft`, inbound v2 Knowledge links, and inbound current Decision
links. It stages only hard deletion of an eligible never-left-draft aggregate.
The T04 tombstone remains content-free and is not stored by T05. No legal
erasure claim is made.

`KnowledgeUnitOfWork` creates one Session, exposes the v2 repository on that
Session, flushes participating work, invokes narrow `TransactionParticipant`
instances with the same Session, flushes again, and commits once. Any
participant or database exception rolls back the complete transaction.
Uncommitted context exit rolls back, close is explicit, and use after finish
or close is rejected.

The participant port defines no event type, audit payload, actor semantics,
history retrieval, or public arbitrary event creation. T07 must implement the
canonical audit participant before a public material-mutation orchestration
path can be complete.

## Acceptance-Criteria Evidence

- [x] Alembic is an explicit constrained dev dependency with configuration,
  environment, template, baseline, and additive Release 1.8 revision.
  Evidence: clean upgrade and exact head checks pass.
- [x] Clean, existing Release 1.7, downgrade, re-upgrade, ORM comparison, and
  cleanup paths run against PostgreSQL without `create_all()` migration
  evidence. Evidence: live migration test passes.
- [x] Release 1.7 rows remain readable and explicitly incomplete with no
  fabricated governance or revision. Evidence: historical-schema live test
  and current mapper/API regressions pass.
- [x] Complete T02/T03/T08 compositions round trip without order, UUID, UTC,
  null, or scalar-type loss. Evidence: pure mapper and live round-trip tests
  pass.
- [x] Create assigns identity, draft, revision 1, and database timestamps and
  rejects evidence misalignment. Evidence: live create test passes.
- [x] No-op, material, stale no-op, stale material, target mismatch, and
  two-session race behaviors are deterministic. Evidence: live `xmin`,
  revision, timestamp, and concurrency assertions pass.
- [x] Complete-composition material classification includes ordered evidence
  and provenance, preserves scalar identity, permits only exact no-op, and
  rolls evidence-only/provenance-only changes back atomically. Evidence: 10
  focused C01 live cases pass.
- [x] Root and all child collections reconstruct from one coherent committed
  state through a three-attempt revision-verified read. Evidence: deterministic
  execution-hook tests cover root/multiple children, evidence/provenance-only,
  lifecycle, deletion, exhaustion, resource release, and ordinary reads.
- [x] Lifecycle persistence consumes and stores a valid T04 plan exactly,
  rejects stale reuse, and exposes no generic lifecycle update. Evidence:
  live lifecycle and repository-surface tests pass.
- [x] Eligible deletion succeeds while non-draft, correction draft, stale,
  inbound Knowledge, and inbound Decision cases fail closed. Evidence: live
  deletion tests pass.
- [x] Repositories flush without commit; the Unit of Work commits once,
  rolls back participant failure and uncommitted material update, closes the
  Session, and rejects invalid reuse. Evidence: unit and live transaction
  tests pass.
- [x] Cross-organization reads fail closed without a production-tenancy claim.
  Evidence: live organization-boundary test passes.
- [x] The current Release 1.7 API, T02, T03, T04, and T08 contracts remain
  green and no current route imports v2. Evidence: full suite and targeted T02
  isolation tests pass.
- [x] Synthetic-only fixtures, explicit localhost/test-database guardrails,
  randomized test schemas, and zero-residual cleanup are enforced. Evidence:
  guardrail, fixture teardown, cleanup probe, and safety scans pass.
- [x] Implementation-head PR merge-ref GitHub Actions jobs finished
  successfully. Evidence: run `30027268394` passed both Python 3.12 quality
  and PostgreSQL 16 migration/persistence jobs.

## Architecture Impact

T05 adds a persistence-only parallel v2 aggregate while keeping the current
Release 1.7 model, mapper, repository, service, routes, and import graph
unchanged. Domain reconstruction reruns accepted Pydantic validation, and ORM
records never leak from mapper/repository outputs.

T04 remains the only lifecycle-policy authority. T05 stores history facts and
executes valid plans but does not recalculate transition policy. T07 remains
the canonical append-only audit authority. T06 remains collection filtering
and cursor authority. T09 remains API schema, route, and error-mapping
authority. No Project, Material, Experiment, Formulation, or Test Result entity
was introduced; T08 context remains link/value-object storage.

Issue #35 is addressed by an actual Alembic-only clean migration, structural
ORM comparison, historical-schema upgrade, supported downgrade/re-upgrade,
repository smoke test, and zero-residual cleanup. The issue must remain open
for independent review and administrative decision.

## Security and Data Impact

Only generalized synthetic organizations, actors, references, context values,
objects, and decisions are used. Evidence storage contains metadata and source
references only; no raw files, base64 payloads, document bodies, credentials,
or industrial measurements are stored.

The live test guard requires exact opt-in, PostgreSQL, localhost, a database
name beginning with `smartcoat_test`, and safe randomized schema names.
Migration and repository tests never mutate `public`. Cleanup executes in
`finally`-backed fixture teardown and verifies absence in `pg_namespace`.

Organization ID is an application boundary used in every v2 read and
mutation. This is defense in depth, not production IAM, row-level security,
authenticated tenancy, or legal authorization. Existing legacy Decision
references have no organization fact, so any matching inbound legacy Decision
blocks deletion conservatively rather than fabricating or assuming tenancy.

## Known Limitations

- T07 has not defined or implemented the canonical immutable audit record,
  append-only history, or final mutation-plus-audit participant.
- No public application material-mutation path is added; complete mutation
  orchestration remains intentionally unavailable until T07.
- T06 filtering, cursor encoding, pagination, and collection-query services
  are not implemented; T05 adds only obvious supporting indexes.
- T09 public request/response schemas, routes, error mapping, and OpenAPI are
  not implemented.
- The new Release 1.7 baseline describes repository compatibility and is not
  evidence of historic production Alembic use.
- Supported operational downgrade is Release 1.8 head to the Release 1.7
  baseline; destructive downgrade of an existing legacy deployment through
  Alembic base was not exercised.
- Organization predicates do not provide production tenant isolation.
- Hard delete is not legal erasure and retains no T05 audit tombstone because
  T07 owns the final audit model.
- Production IAM, authorization, retention policy, real-data approval,
  deployment readiness, and Release 1.8 completion are not claimed.
- Revision-verified reads intentionally fail with
  `aggregate_read_retry_exhausted` after three consecutive collisions; callers
  must retry at their orchestration boundary if sustained write contention
  continues.
- Coherence depends on the persistence contract that every governed child
  mutation is transactionally paired with a root revision increment. Direct
  out-of-band child-table DML is unsupported and is not represented as a
  repository behavior claim.

## Lost Points and Correction Items

| Item | Source | Points | Status | Action or Evidence |
|---|---|---:|---|---|
| C90 | Initial sandboxed localhost invocation | 0 | RESOLVED | Preserved the failed invocation, requested approved local-network access, and reran all required PostgreSQL tests successfully. |
| C91 | First live metadata comparison | 0 | RESOLVED | Aligned four legacy server-default declarations and reran clean upgrade, comparison, downgrade, re-upgrade, and smoke validation. |
| C92 | First full-suite T02 isolation findings | 0 | RESOLVED | Added a pre-modification owned-path amendment, separated v2 ORM models, restored the legacy shape/import graph, and reran affected and complete validation. |
| C93 | Original implementation-head CI evidence | 0 | RESOLVED | Both Python 3.12 quality and PostgreSQL 16 jobs in run `30027268394` passed; the latter executed all migration, downgrade/re-upgrade, repository, concurrency, rollback, cleanup, and Release 1.7 live API tests. |
| C01 | Independent review 4766496385: complete-composition updates | 7 | RESOLVED | Material classification now validates and canonically compares mutable state, ordered evidence, and provenance; evidence-only/provenance-only changes use CAS and one revision increment, while exact identity remains a zero-write no-op. Ten focused live cases pass. |
| C02 | Independent review 4766496385: coherent aggregate reads | 7 | RESOLVED | Every composition reload now uses an organization-scoped, three-attempt root/children/final-revision protocol with typed exhaustion. Five deterministic live interleaving cases pass. |
| C94 | First correction live test helper | 0 | RESOLVED | Preserved the 3-pass/21-fail invocation caused by one nested default transformation tuple, corrected only the helper, and reran focused, complete, and CI PostgreSQL suites. |
| C95 | First correction MyPy pass | 0 | RESOLVED | Converted five SQLAlchemy child `Sequence` results to explicit immutable tuples and reran MyPy successfully across 53 source files. |

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 25 | Original migration/CAS/deletion evidence plus complete-composition CAS/no-op behavior and deterministic coherent-read interleavings pass on PostgreSQL. | None. |
| Scope and acceptance criteria | 20 | 20 | Correction changes exactly the three implementation/test paths plus this report, all within the four authorized paths, and preserves T02/T03/T04/T08 plus current API ownership. | None. |
| Architecture and North-Star alignment | 15 | 15 | Separate v2 aggregate, fail-closed legacy adaptation, T04 plan authority, T07 participant boundary, bounded read consistency, and no false production claims align with accepted ADRs. | None. |
| Verification, tests, or validation | 15 | 15 | C01 10, C02 5, persistence 11, affected 472, live 30/0, full 565/28, MyPy 53, Ruff, format 75, pip, reports, and corrected implementation-head PR merge-ref CI pass. | None. |
| Security, privacy, and data governance | 10 | 10 | Synthetic metadata-only fixtures, source-payload bounds, test-target guardrails, organization predicates, and cleanup pass. | None. |
| Documentation and traceability | 10 | 10 | Original history, independent review, scores, failed invocations, C01/C02 design, merge-ref terminology, commands, corrections, and limits are recorded. | None. |
| Maintainability and clarity | 5 | 5 | Canonical comparison, immutable child bundles, bounded typed retry, deterministic SQLAlchemy hooks, and focused tests keep the correction localized and explicit. | None. |
| Total | 100 | 100 | All correction, original-scope, live PostgreSQL, safety, report, and corrected implementation-head CI evidence required for independent re-review passes. | None. |

## ChatGPT Reviewer Score

Reviewer status: Pending independent re-review.

Historical independent review ID: `4766496385`.

Historical reviewed head:
`c27f217513e237bb3e302354cae7c1dea777e694`.

Previous reviewer score: 86/100.

Previous decision: CORRECTION REQUIRED.

Historical reviewer findings:

- C01 required complete-composition update semantics across mutable state,
  ordered evidence, and provenance.
- C02 required snapshot-consistent aggregate reads with deterministic live
  concurrency proof.

Current reviewer score: Pending independent re-review.

Current corrected implementation head:
`c222c279eceaeaa3b1d082adf8e78bd78889a00a`.

## Final Score

Previous weighted score: 91.6/100.

Previous gate-adjusted score: 79/100.

Provisional weighted score: Pending

Gate-adjusted score: Pending

Independent re-review is required before current weighted or gate-adjusted
scoring.

## Critical-Gate Declaration

| Gate | Status | Evidence |
|---|---|---|
| G1 Verified claims | PASS | Claims map to exact local output, review 4766496385, GitHub state, migration inspection, PostgreSQL behavior, or PR merge-ref run 30030301803; all failed invocations and corrections are retained. |
| G2 Confidential data | PASS | Synthetic metadata-only fixtures, no raw evidence, and test-target guardrails preserve the approved data boundary. |
| G3 Approved scope and architecture | PASS | Correction modifies only the four authorized paths and changes no migration, ORM, mapper, Unit of Work, domain, API, dependency, CI, or ADR contract. |
| G4 Required validation | PASS | C01, C02, persistence, affected, full, type, lint, format, pip, migration, live PostgreSQL, regressions, cleanup, report, links, safety, and corrected implementation-head PR merge-ref CI pass. |
| G5 File ownership | PASS | Correction diff is exactly four authorized paths after report publication; the release-base diff remains exactly the original 18 declared T05 paths. |
| G6 Acceptance completeness | PASS | C01 and C02 plus every original in-scope criterion have code, deterministic live PostgreSQL evidence, validation, or an explicit downstream boundary. |

Critical-gate result: PASS

## Release 1.8 Additional Gates

| Gate | Status | Applicability Evidence |
|---|---|---|
| G7 Persistence alignment and PostgreSQL evidence | PASS | Original migration/ORM evidence plus complete-composition CAS, zero-write `xmin`, rollback, coherent read, deletion, bounded exhaustion, cleanup, and 30-test corrected CI ran on PostgreSQL 16. |
| G8 Lifecycle, trust, and audit bypass prevention | PASS | Lifecycle-only interleaving reconstructs coherently; only accepted T04 plans alter lifecycle; no public mutation service or arbitrary audit API exists; T07 remains required and unstarted. |

## Correction-Cycle History

| Cycle | Starting Score | Findings | Corrections | Ending Score | Validation Evidence | Status |
|---:|---:|---|---|---:|---|---|
| 1 | 97 | Initial local-network denial, four metadata defaults, and three T02 import/model-isolation regressions were exposed by required validation. | Reran with approved access, aligned metadata, moved v2 ORM records to a dedicated owned path, removed eager export, reran all required checks, and required both implementation-head CI jobs to pass. | 100 | 10 focused, 15/0 live, 564/13 full, MyPy 53, Ruff, format 75, pip, metadata, downgrade/re-upgrade, cleanup, T02 isolation, and run `30027268394` pass. | CLOSED |
| 2 | 86 | Independent review 4766496385 found C01 evidence/provenance-only changes were discarded by core-only no-op classification and C02 multi-statement reads could reconstruct mixed revisions. | Added validated type-preserving complete-composition comparison, CAS for evidence/provenance-only changes, strict zero-write no-op, bounded revision-verified aggregate reads, and deterministic PostgreSQL interleaving/exhaustion tests. Corrected one test-helper tuple and five static tuple types found during validation. | 100 | C01 10, C02 5, persistence 11, affected 472, live 30/0, full 565/28, MyPy 53, Ruff, format 75, pip, reports, links, ownership, safety, and run `30030301803` pass; independent re-review remains pending. | CLOSED |

## Recommended Follow-up Issues

- Independent ChatGPT re-review should evaluate PR #58 at its final correction
  report head, beginning from implementation SHA
  `c222c279eceaeaa3b1d082adf8e78bd78889a00a`.
- Issue #35 should remain open until independent review accepts the migration
  and metadata-alignment evidence.
- T07 issue #45 should implement the canonical audit participant on the same
  Session without adding repository commits or a public arbitrary event API.
- T06 should consume only the query-supporting indexes and must own filtering,
  deterministic pagination, and cursor contracts.
- T09 should own explicit public schemas, route orchestration, error mapping,
  and OpenAPI after T05 and T07 are accepted.
- Issue #46 should remain open for downstream context integration.
- PR #49 must remain draft and unmerged; no Release 1.8 integration is
  authorized by T05.

## Blockers

None.

## Recommendation

READY FOR INDEPENDENT RE-REVIEW
