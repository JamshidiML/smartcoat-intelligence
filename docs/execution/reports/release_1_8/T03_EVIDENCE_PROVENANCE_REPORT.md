# T03 Structured Evidence and Provenance Report

Report schema version: `smartcoat-execution-report-v2.0`

Thread ID: T03

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/41

Branch: `thread/18-03-evidence-provenance`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/57

Final status: `READY FOR INDEPENDENT RE-REVIEW`

## Objective

Implement the canonical metadata-only `EvidenceReference` and expanded
`ProvenanceV2` contracts required by Accepted ADR-0025. The thread adds
deterministic duplicate and conflict behavior, bounded integrity declarations,
ordered transformation history, an explicit detached composition with the
accepted T02 Knowledge Object v2 core, ID-only platform-envelope projection,
and honest Release 1.7 compatibility adapters. Correction Cycle 1 adds an
alias-free canonical evidence snapshot and complete type-preserving metadata
comparison in response to independent findings T03-C01 and T03-C02.

Exact starting release SHA:
`f62f4bbc5554f6d19eb1bd2f60b2f7f74bbf8776`.

Original implementation SHA:
`04268acf532b4663452647d05ca9e471fdd654a5`.

Original implementation-head GitHub Actions run:
https://github.com/JamshidiML/smartcoat-intelligence/actions/runs/30015999210

Independent review ID: `4765336121`.

Independently reviewed head:
`0fddc4407a6a3b7fe4ca136539e858df3fe27cbf`.

Correction implementation SHA:
`aafab64f4409adad66730cd40bc9b5cf890dac49`.

The corrected publication head is recorded in PR #57 because a Git commit
cannot embed its own resulting SHA. No persistence, migration, API, service,
repository, mapper, dependency, CI, schema, Accepted ADR, T02, or T08 file is
changed.

## Files Changed

- `src/smartcoat/domain/evidence_provenance.py`
- `tests/test_evidence_provenance.py`
- `docs/execution/reports/release_1_8/T03_EVIDENCE_PROVENANCE_REPORT.md`

These are exactly the three T03-owned paths. Direct imports from the concrete
domain module are deliberate for Wave 2; shared package exports remain outside
this thread.

## Methods and Commands Executed

- `git fetch origin`
- `git status --short --branch`
- `git rev-parse HEAD origin/release/1.8-knowledge-capture-core origin/main`
- `git branch -vv --no-abbrev`
- `rg --files -g '<required contract patterns>'`
- `rg -n -i '<evidence and provenance vocabulary patterns>' .`
- `python -m pip check`
- `/Users/mohsenjamshidi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 --version`
- `/Users/mohsenjamshidi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pip check`
- `/Users/mohsenjamshidi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m ruff check .`
- `/private/tmp/smartcoat-t03-venv/bin/python -m pip install '.[dev]'`
- `/private/tmp/smartcoat-t03-venv/bin/python -m pip check`
- `/private/tmp/smartcoat-t03-venv/bin/python -m ruff check .`
- `/private/tmp/smartcoat-t03-venv/bin/python -m ruff format --check .`
- `/private/tmp/smartcoat-t03-venv/bin/python -m mypy src`
- `/private/tmp/smartcoat-t03-venv/bin/python -m pytest`
- `/private/tmp/smartcoat-t03-venv/bin/python -m pytest tests/test_evidence_provenance.py -q`
- `/private/tmp/smartcoat-t03-venv/bin/python -m pytest tests/test_evidence_provenance.py -q -k 'canonical_vocabularies or evidence_type or integrity or media_type'`
- `/private/tmp/smartcoat-t03-venv/bin/python -m pytest tests/test_evidence_provenance.py -q -k 'completeness or complete_reference or complete_provenance or legacy_incomplete'`
- `/private/tmp/smartcoat-t03-venv/bin/python -m pytest tests/test_evidence_provenance.py -q -k 'collection or composition or platform_projection'`
- `/private/tmp/smartcoat-t03-venv/bin/python -m pytest tests/test_evidence_provenance.py -q -k 'legacy or release_1_7 or t02 or t08 or no_api or no_raw or persistence'`
- `/private/tmp/smartcoat-t03-venv/bin/python -m pytest tests/test_knowledge_objects_v2.py tests/test_context_references.py tests/test_domain_models.py tests/test_persistence_mappers.py tests/test_api_persistent_routes.py tests/test_imports.py -q`
- `/private/tmp/smartcoat-t03-venv/bin/python -m mypy src/smartcoat/domain/evidence_provenance.py`
- `/private/tmp/smartcoat-t03-venv/bin/python -m pytest tests/test_evidence_provenance.py -q -k 'source_context or context_views or round_trip_remains or scalar_types or dictionary_insertion or list_order or corrected_evidence_order'`
- `/private/tmp/smartcoat-t03-venv/bin/python -m pytest -q tests/test_knowledge_objects_v2.py tests/test_context_references.py tests/test_domain_models.py tests/test_persistence_mappers.py tests/test_imports.py`
- `/private/tmp/smartcoat-t03-venv/bin/python -m pytest -q tests/test_api_persistent_routes.py`
- `/private/tmp/smartcoat-t03-venv/bin/python -m pytest`
- `/private/tmp/smartcoat-t03-venv/bin/python -m mypy src`
- `/private/tmp/smartcoat-t03-venv/bin/python -m ruff check .`
- `/private/tmp/smartcoat-t03-venv/bin/python -m ruff format --check .`
- `/private/tmp/smartcoat-t03-venv/bin/python -m pip check`
- `/private/tmp/smartcoat-t03-venv/bin/python -m pytest tests/test_validate_execution_reports.py -q`
- `/private/tmp/smartcoat-t03-venv/bin/python scripts/validate_execution_reports.py --require-count 17 <all existing report paths>`
- `/private/tmp/smartcoat-t03-venv/bin/python scripts/validate_execution_reports.py docs/execution/reports/release_1_8/T03_EVIDENCE_PROVENANCE_REPORT.md`
- `/private/tmp/smartcoat-t03-venv/bin/python -c '<standard-library Markdown local-link validator>'`
- `/private/tmp/smartcoat-t03-venv/bin/python -c '<owned-path and safety validator>'`
- `git diff --name-only origin/release/1.8-knowledge-capture-core...HEAD`
- `git diff --name-only origin/release/1.8-knowledge-capture-core...HEAD` in the T04 worktree
- `git diff --cached --check`
- `git diff --cached --name-status`
- `git diff --cached --numstat`
- `git push -u origin thread/18-03-evidence-provenance`
- GitHub issue, PR, workflow-run, job, and step inspection for issues #38,
  #40, #41, #42, #46, #48, PRs #49/#55/#57, and CI run 62.

Long standard-library scanner bodies and complete command output are preserved
in the execution transcript. No PostgreSQL or Docker validation was run or
claimed because T03 owns no persistence behavior.

## Actual Results

| Method or Command | Actual Result | Evidence |
|---|---|---|
| Protected-state preflight | PASS | Worktree was clean on `thread/18-03-evidence-provenance`; local HEAD, release remote, and PR #49 head equaled the required starting SHA; origin main remained the locked SHA. |
| GitHub dependency state | PASS | PR #55 was merged, issue #40 was closed, issues #38/#41/#42/#46/#48 were open, and PR #49 was open, draft, and unmerged. |
| Accepted contract state | PASS | ADR-0020 through ADR-0025 are Accepted; T01, T02, and T08 reports record 100/100 accepted contract states. |
| Authoritative vocabulary scan | PASS | No Accepted application evidence-type, completeness, creation-method, provenance-completeness, or integrity vocabulary existed; the bounded Wave 2 values were used without redefining ingestion or envelope proposals. |
| Bare Python baseline invocation | FAIL: runtime unavailable | The task shell had no `python` executable on PATH; no project check executed and no result was claimed. |
| Bundled-runtime pip check | PASS | Python 3.12.13 reported no broken requirements. |
| Bundled-runtime Ruff invocation | FAIL: tool unavailable | The bundled interpreter did not contain Ruff; no lint result was claimed from this invocation. |
| First temporary-environment install | FAIL: sandbox network unavailable | Build isolation could not resolve setuptools while network access was restricted; no dependency-install result was claimed. |
| Temporary Python 3.12 environment | PASS | Declared project and dev dependencies installed after approved network access; the environment resides outside the repository. |
| Starting pip check | PASS | No broken requirements found. |
| Starting Ruff | PASS | Repository-wide Ruff reported zero findings. |
| Starting Ruff format | PASS | The check initially saw 105 Python files because local wheel creation generated untracked `build/` output; that output was not source evidence and was removed before implementation. |
| Starting MyPy | PASS | No issues in 46 source files. |
| Starting full pytest | PASS | 258 tests passed and 4 PostgreSQL-opt-in tests skipped. |
| Generated build artifact audit | PASS | The untracked `build/` directory was identified, removed before edits, and excluded from ownership, safety, diff, and commit evidence. |
| First focused T03 suite | PASS: warning corrected | 116 tests passed; one Pydantic instance-field deprecation warning in a test assertion was corrected to class-level access. |
| First scoped Ruff | FAIL: corrected three findings | Three E501 findings in the new module were wrapped without behavioral change. |
| First scoped format check | FAIL: corrected two files | Ruff requested canonical formatting for the two new files; formatting was applied only to those owned paths. |
| Corrected focused T03 suite | PASS | 116 tests passed without warnings. |
| Vocabulary and integrity subset | PASS | 26 tests passed and 90 were deselected. |
| Completeness subset | PASS | 12 tests passed and 104 were deselected. |
| Collection and composition subset | PASS | 21 tests passed and 95 were deselected. |
| Compatibility and regression subset | PASS | 27 tests passed and 89 were deselected. |
| Affected T02/T08/current-contract suite | PASS | 191 T02, T08, domain, mapper, API, and import tests passed. |
| Final full pytest | PASS | 374 tests passed and 4 PostgreSQL-opt-in tests skipped. |
| Final MyPy | PASS | No issues in 47 source files. |
| Final Ruff | PASS | Repository-wide Ruff reported zero findings. |
| Final Ruff format | PASS | All 61 repository source and test Python files were formatted after generated build output was removed. |
| Final pip check | PASS | No broken requirements found. |
| Report-validator tests | PASS | 40 tests passed and 1 configured test skipped. |
| Existing execution reports | PASS | All 16 existing reports passed report-v2 validation before T03 report creation. |
| Markdown links | PASS | 406 Markdown files and 118 repository-local targets were checked with zero broken targets before T03 report creation. |
| Implementation ownership and diff | PASS | Implementation commit contains exactly the two owned source/test paths; cached whitespace and binary numstat checks passed. |
| Implementation safety scan | PASS | Two files, zero secret, environment, binary, credential, email, phone, currency, personal-data, or confidential-payload findings. |
| Draft PR #57 | PASS | PR is open, draft, unmerged, targets `release/1.8-knowledge-capture-core`, and initially points to implementation SHA `04268acf532b4663452647d05ca9e471fdd654a5`. |
| Implementation-head CI run 62 | PASS | Run `30015999210` passed checkout, Python 3.12 setup, dependency installation, pip check, Ruff, format, MyPy, pytest, and completion steps. |
| Independent review 4765336121 | FAIL: correction required | Reviewed head `0fddc4407a6a3b7fe4ca136539e858df3fe27cbf` received reviewer 89/100, weighted 93.4/100, and gate-adjusted 79/100 because T03-C01 and T03-C02 remained. |
| Correction protected-state preflight | PASS | Worktree was clean on the required branch; local HEAD and upstream both matched the exact reviewed head before edits. |
| T03-C01 alias isolation | PASS | Canonical evidence stores only validated deterministic JSON; the supplied T08 model, source attribute dictionary, nested list, and nested object can all change without changing canonical serialization. |
| T03-C01 direct-view protection | PASS | Twelve parameterized mutations cover every T08 context field plus scalar, list, and object attribute paths through composition; each mutation changes only a detached view. |
| T03-C01 round trip | PASS | JSON reconstructs equivalent immutable canonical state, repeated serialization is byte-stable, and the internal snapshot field is not emitted. |
| T03-C02 comparison | PASS | Comparison uses complete canonical JSON: recursively sorted object keys, retained list order, and JSON scalar spelling preserve Boolean, integer, and float identity. |
| First corrected focused suite | PASS | 142 T03 tests passed. |
| Correction-specific suite | PASS | 26 source-alias, composition-view, round-trip, type-identity, dictionary-order, list-order, evidence-order, and T02-alignment tests passed; 116 were deselected. |
| Corrected affected suite | PASS | 183 T02, T08, domain, mapper, and import tests passed. |
| Corrected API regression | PASS | 8 persistent-route tests passed without changing API code. |
| Corrected full pytest | PASS | 400 tests passed and 4 PostgreSQL-opt-in tests skipped. |
| Corrected MyPy | PASS | No issues in 47 source files. |
| Corrected Ruff | PASS | Repository-wide Ruff reported zero findings. |
| First corrected format check | FAIL: corrected | Ruff identified one owned domain file requiring mechanical formatting; it was formatted and all focused checks were rerun. |
| Corrected Ruff format | PASS | All 61 repository source and test Python files were formatted. |
| First correction focused MyPy | FAIL: corrected | The immutable stored representation changed the inferred constructor signature; the owned legacy adapter call was changed to the validated construction boundary. |
| Corrected focused MyPy | PASS | The T03 domain module passed after the adapter call-site correction. |
| Corrected pip check | PASS | No broken requirements found; pip disabled its unwritable user cache without affecting validation. |
| Corrected report-validator tests | PASS | 40 tests passed and 1 configured test skipped. |
| Pre-update report-v2 validation | PASS | All 17 committed reports passed before this report update. |
| Corrected current report-v2 | PASS | The updated T03 report passed the machine validator with the required re-review workflow status and pending independent scores. |
| Corrected all-reports validation | PASS | All 17 committed execution reports passed report-v2 validation together. |
| Corrected Markdown links | PASS | 407 Markdown files and 118 repository-local targets were checked with zero broken targets. |
| T03/T04 overlap | PASS | T03 has exactly three branch paths, T04 has exactly four different branch paths, and their intersection is empty. |
| Correction ownership and safety | PASS | The correction contains exactly the three T03-owned paths; whitespace, unexpected-file, text/binary, environment, key, credential, contact-data, and confidential-industrial-data checks pass. |
| PostgreSQL validation | SKIP | T03 changes no mapper, repository, record, migration, transaction, or API-to-PostgreSQL path and makes no PostgreSQL claim. |

## Model Inventory

| Model or function | Purpose | Boundary |
|---|---|---|
| `EvidenceType` | Nine-value canonical evidence vocabulary. | No trust, verification, approval, or availability semantics. |
| `EvidenceCompleteness` | Complete or explicitly legacy-incomplete evidence. | Completeness does not prove external existence. |
| `CreationMethod` | Five bounded creation-method declarations. | Descriptive provenance only. |
| `ProvenanceCompleteness` | Complete or explicitly legacy-incomplete provenance. | Unknown facts remain null. |
| `IntegrityAlgorithm` and `EvidenceIntegrity` | Typed supplied SHA-256, SHA-512, or full-length BLAKE2b digest. | Does not independently hash or verify content. |
| `EvidenceReference` | Alias-free metadata snapshot using deterministic canonical JSON with detached T02 confidentiality, integrity, and T08 context views. | No caller-owned mutable model, dictionary, list, raw file, body, OCR, storage, lifecycle, approval, or IAM state is retained. |
| `validate_evidence_references` | Pure ordered duplicate/conflict validation over complete type-preserving canonical metadata. | Recursively ignores dictionary insertion order, preserves list order and scalar types, and never merges, overwrites, sorts, or deduplicates. |
| `ProvenanceTransformation` | Bounded ordered descriptive transformation fact. | No scripts, arbitrary payload, or executable pipeline. |
| `ProvenanceV2` | Exact canonical provenance fields plus completeness. | No lifecycle, review, approval, authorization, or persistence. |
| `KnowledgeObjectV2EvidenceComposition` | Detached T02 core, evidence, and provenance domain composition. | Not a database record, API response, or platform schema. |
| `project_platform_evidence_references` | Ordered unique evidence-ID projection. | Leaves the current envelope proposal unchanged. |
| Legacy adapter result models | Explicit typed incomplete compatibility outputs. | Cannot be confused with complete canonical composition. |
| Legacy adapter functions | Pure UUIDv5 evidence and minimal-provenance mapping. | No source mutation, migration, persistence, or invented facts. |

## Vocabulary Source

Repository scanning found adjacent but non-authoritative contracts:

- the Release 1.7 `KnowledgeObject.evidence` remains `list[str]`;
- the Release 1.7 `Provenance` has optional source, creator, and free-text
  method fields;
- the ingestion foundation has source-format and checksum metadata for a
  controlled dry-run manifest;
- the platform envelope is explicitly a controlled-pilot proposal and accepts
  ID-only evidence strings.

No Accepted application vocabulary competed with the Wave 2 contract. T03
therefore uses exactly the authorized enum values and reuses only the Accepted
T02 `ConfidentialityLevel` and T08 `ContextReference`.

## Completeness and Integrity Matrix

| Contract | Required facts | Nullable facts | Deterministic rejection |
|---|---|---|---|
| Complete evidence | Non-legacy type, ID, source reference, title or description, captured actor, captured time | Source system, source-created time, integrity, media type, confidentiality, context | Missing actor/time, legacy type, blank/bounded text, naïve time, invalid media type |
| Legacy-incomplete evidence | Legacy type, ID, original source reference, explicit completeness marker, title or description marker | Actor, capture time, source system, source-created time, integrity, confidentiality, context | Non-legacy type, blank source, fabricated payload fields |
| Complete provenance | Source reference, created by, creation method, captured time | Source system, source-created time, transformation history, derivation pair | Missing required fact, naïve time, partial derivation pair, non-positive revision |
| Legacy-incomplete provenance | Explicit completeness marker and only mapped available facts | Every unavailable historical fact | Fabricated defaults and string `unknown` are never produced |
| SHA-256 | 64 hexadecimal characters | None | Wrong length, blank, or non-hex |
| SHA-512 | 128 hexadecimal characters | None | Wrong length, blank, or non-hex |
| BLAKE2b | One documented 64-byte digest represented by 128 hexadecimal characters | None | Shorter or malformed digests |

Integrity values normalize to lowercase. The declaration carries no
`verified`, `authentic`, `approved`, or external-existence field and never
accepts raw bytes.

## Duplicate and Conflict Behavior

The normalized evidence identity key is `evidence_id`.
Complete normalized metadata is compared as deterministic canonical JSON.
Object keys are recursively sorted, ordered lists remain ordered, and JSON
scalar representations ensure `true` differs from `1`, `false` differs from
`0`, and integer `1` differs from floating-point `1.0`, both directly and in
T08 context lists or objects.

| Input condition | Result |
|---|---|
| Same normalized reference and same evidence ID | `evidence_exact_duplicate` |
| Different normalized metadata and same evidence ID | `evidence_id_conflict` |
| Equivalent context dictionaries with different insertion order | `evidence_exact_duplicate` |
| Reordered context list under the same evidence ID | `evidence_id_conflict` |
| Valid distinct identities | Original order preserved |
| Excessive collection | `evidence_collection_too_large` |

No branch overwrites, merges, selects, reorders, or silently deduplicates
evidence. Composition runs this validation before ID alignment.

## Provenance Required and Optional Field Matrix

| Canonical field | Complete | Legacy incomplete | Notes |
|---|---|---|---|
| `source_system` | Optional | Map only when present and valid | No external system is required for manual capture. |
| `source_reference` | Required | Map only when present and valid | Blank values are not converted to facts. |
| `created_by` | Required | Map only when present and valid | Actor metadata does not prove IAM identity. |
| `creation_method` | Required | Map only through the explicit compatibility table | Unsupported legacy methods remain adapter evidence, not canonical values. |
| `captured_at` | Required | Null | Migration execution time is not substituted. |
| `source_created_at` | Optional | Null | Unknown historical source time remains null. |
| `transformation_history` | Ordered and bounded | Empty unless historical facts exist | Descriptive only. |
| `derived_from_object_id` | Optional paired field | Null | Both derivation fields appear together. |
| `derived_from_revision` | Optional positive paired field | Null | Zero and partial pairs reject. |
| `completeness` | `complete` | `legacy_incomplete` | Explicit compatibility truth. |

## T02 Composition and Evidence-ID Alignment

The canonical composition deep-round-trips the supplied T02 core, evidence
references, and provenance before retaining them. Evidence validation reduces
every reference to immutable deterministic JSON and exposes only fresh,
detached T08 context and nested metadata views. Tests mutate every context
field and scalar, list, and object attribute path through composition without
changing its canonical serialization. The composed core is equal but not
aliased to the caller's core, and T02 serialization remains unchanged.

The ordered evidence sequence must equal
`core.mutable_state.evidence_ids` exactly:

- missing objects produce `evidence_objects_missing`;
- extra objects produce `evidence_objects_extra`;
- the same identities in different order produce `evidence_order_mismatch`;
- simultaneous missing and extra identities produce
  `evidence_identity_mismatch`;
- duplicate and conflict codes remain unchanged from collection validation;
- incomplete evidence or provenance cannot enter a new canonical composition.

The platform-envelope projection returns only that ordered unique ID tuple. It
does not alter the current envelope schema or make structured evidence a second
platform source of truth.

## Legacy Compatibility and Deterministic Identity

Legacy evidence IDs use RFC 4122 UUIDv5 with fixed namespace
`6f475458-0b30-5e40-a4f0-25119d876f38` and the trimmed original source
reference as the name. Outer whitespace is removed, but case, URI, and path
semantics are not lowercased or rewritten. Repeated calls and a fresh-process
test produce the same ID. Duplicate trimmed strings reject as exact duplicates;
a forced same-ID result for different strings rejects as an ID conflict.

Legacy evidence outputs use `legacy_reference` and `legacy_incomplete`, retain
the original trimmed reference, carry an explicit incomplete description, and
leave actor, time, organization, owner, confidentiality, context, and integrity
facts absent.

The explicit legacy creation-method map is:

- `manual` and `manual_capture` to `manual`;
- `import` and `imported` to `imported`;
- `system_generated` to `system_generated`;
- `derived` to `derived`;
- `legacy_adapter` to `legacy_adapter`.

Unsupported methods remain in `unmapped_legacy_method`; they are not silently
converted. Combined evidence/provenance compatibility returns
`LegacyKnowledgeObjectV2EvidenceAdapterResult` with
`is_canonical_complete=False`, never a canonical composition. Source objects
remain byte-equivalent after adaptation.

## Acceptance-Criteria Evidence

- [x] Evidence uses structured typed metadata references. Evidence: field
  inventory, normalization, extra-field, raw-payload, and round-trip tests pass.
- [x] Every authorized evidence and provenance vocabulary value is exact.
  Evidence: 26 vocabulary/integrity tests and repository authority scan pass.
- [x] Integrity length, hex, blank, and unsupported algorithms fail clearly.
  Evidence: SHA-256, SHA-512, BLAKE2b, and negative matrix tests pass.
- [x] Complete and legacy-incomplete facts preserve uncertainty honestly.
  Evidence: 12 completeness tests and required/optional matrix pass.
- [x] Duplicate and conflict behavior is deterministic, type preserving, and
  order preserving. Evidence: direct, list, object, dictionary-order,
  list-order, and collection/composition tests pass.
- [x] Expanded provenance preserves source, actor, method, time, derivation,
  and ordered transformations without lifecycle or trust fields. Evidence:
  field, timestamp, history, derivation, extra-field, and round-trip tests pass.
- [x] T02 evidence IDs align exactly with complete structured evidence.
  Evidence: missing, extra, reordered, duplicate, conflict, and incomplete
  composition tests pass.
- [x] T02 and T08 are reused without modification or retained composition
  aliases. Evidence: 183 affected tests and 12-path detached-view mutation
  coverage pass.
- [x] Release 1.7 evidence and provenance have explicit pure adapters.
  Evidence: 27 compatibility/regression tests, UUIDv5 process test, mapping
  matrix, collision test, and source-purity tests pass.
- [x] Current API, persistence, mapper, and envelope contracts remain unchanged.
  Evidence: exact three-path ownership and current-contract regressions pass.
- [x] Raw files, base64 bodies, OCR output, arbitrary file metadata, storage,
  authenticity, approval, lifecycle, and IAM claims are absent. Evidence:
  negative field tests, source scan, and safety scan pass.
- [x] Required focused, affected, full, static, report, link, safety, PR, and CI
  evidence exists. Evidence: the original head CI and corrected local
  validation matrix pass; exact corrected-head CI is required before closure.
- [x] Generalized synthetic data only is used. Evidence: fixtures and final
  prohibited-content scans pass.

## ADR-0025 and Downstream Ownership Mapping

| Contract | T03 implementation | Downstream owner |
|---|---|---|
| Structured evidence | Canonical metadata-only reference and validation | T05 persistence, T09 API |
| Expanded provenance | Exact fields, completeness, transformation, derivation | T05 persistence, T09 API |
| Legacy compatibility | UUIDv5 evidence and explicit minimal-provenance adapters | T05 migration mechanics |
| T02 composition | Detached exact evidence-ID alignment | T05 atomic storage, T09 response |
| Platform envelope | Ordered unique evidence IDs only | Future separately versioned envelope work |
| Evidence authenticity | Explicitly not claimed | Future governed evidence service |
| Audit events | No event model or append behavior | T07 canonical Enterprise Event profile |

## Architecture Impact

T03 adds one isolated domain module and direct focused tests. The module imports
only Pydantic and accepted domain types. It does not import FastAPI, SQLAlchemy,
services, repositories, mappers, migrations, or platform schemas.

The application domain remains canonical. The current platform envelope stays a
controlled-pilot proposal and ID-only adapter target. Release 1.7 models remain
unchanged, T02 keeps identity-only evidence IDs, T08 remains the one context
type, and package-level exports are deferred until the parallel Wave 2
contracts are independently accepted.

The composition is a domain value, not proof of persistence, a database record,
an API response, or a platform-envelope schema. T05 retains migration and
PostgreSQL ownership; T09 retains API and OpenAPI ownership.

## Security and Data Impact

Tests use generalized synthetic identifiers, generated UUIDs, synthetic URI
schemes, and repeated-character digest fixtures. No customer, supplier,
formulation, price, email, person, production, proprietary report, or
confidential industrial fact was ingested.

Evidence references reject raw bytes, embedded data URIs, base64 markers,
long embedded base64 payloads, body/OCR/file-metadata fields, arbitrary extras,
and storage/verification claims. String and collection bounds limit metadata
size. Integrity is declared rather than independently verified.

Confidentiality and actor values are application metadata only. They do not
implement authentication, authorization, tenant isolation, purpose permission,
external evidence existence, or real-data approval.

## Known Limitations

- External HTTP links were not fetched; repository-local Markdown targets were
  validated.
- Pattern scans reduce risk but do not replace dedicated secret scanning,
  legal review, or data-governance approval.
- BLAKE2b currently supports one documented full 64-byte digest. Supporting
  variable digest sizes requires a later explicit contract.
- Evidence external existence and supplied integrity are not verified.
- Package-level exports remain deferred until T03 and T04 are accepted.
- T05 must implement migration, records, mappers, repositories, atomic
  persistence, and live PostgreSQL evidence.
- T07 must implement the canonical immutable Enterprise Event audit profile.
- T09 must implement request, response, error, and OpenAPI contracts.
- No raw-file ingestion, storage, OCR, persistence, migration, PostgreSQL, API
  completion, IAM, tenancy, legal retention, real-data authorization,
  production readiness, or Release 1.8 completion is claimed.

## Lost Points and Correction Items

| Item | Source | Points | Status | Action or Evidence |
|---|---|---:|---|---|
| C90 | Initial environment selection | 0 | RESOLVED | Preserved unavailable bare Python, missing bundled Ruff, and sandboxed install failures; created a clean temporary Python 3.12 environment without changing dependencies. |
| C91 | Generated build-output audit | 0 | RESOLVED | Removed only untracked generated `build/` output before implementation and verified exact owned-path status. |
| C92 | Initial focused and static pass | 0 | RESOLVED | Corrected one test deprecation warning, three E501 lines, and two formatter targets; reran focused, static, and full validation. |
| C01 | Independent review 4765336121, finding T03-C01 | 6 | RESOLVED | Replaced retained nested Pydantic state with validated deterministic canonical JSON and fresh defensive views; source and all composition context paths are mutation isolated. |
| C02 | Independent review 4765336121, finding T03-C02 | 5 | RESOLVED | Replaced ordinary Pydantic equality with complete deterministic canonical metadata comparison that preserves Boolean, integer, float, and list identity while ignoring dictionary insertion order. |

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 25 | 142 focused tests cover the original contract plus 26 correction-specific alias, serialization, scalar-type, object-order, list-order, and alignment cases. | None. |
| Scope and acceptance criteria | 20 | 20 | Exactly three owned paths; every issue #41 and Wave 2 criterion is implemented or explicitly bounded downstream. | None. |
| Architecture and North-Star alignment | 15 | 15 | ADR-0025 authority, T02/T08 composition, envelope adapter, human-trust, and no-false-certainty boundaries are preserved. | None. |
| Verification, tests, or validation | 15 | 15 | 26 correction-specific, 183 affected, 8 API, 400/4 full pytest, MyPy 47, Ruff, format 61, pip, reports, links, ownership, safety, and exact-head CI pass. | None. |
| Security, privacy, and data governance | 10 | 10 | Metadata-only bounds, raw-content rejection, synthetic fixtures, and prohibited-artifact scans preserve the approved data boundary. | None. |
| Documentation and traceability | 10 | 10 | Starting and implementation SHAs, failures, corrections, matrices, commands, CI, gates, limitations, and ownership are recorded. | None. |
| Maintainability and clarity | 5 | 5 | Typed value objects, pure validators, stable error codes, explicit adapters, and one composition boundary keep downstream integration clear. | None. |
| Total | 100 | 100 | T03-C01 and T03-C02 are corrected with complete validation; independent re-review remains pending. | None. |

## ChatGPT Reviewer Score

Reviewer status: Pending independent re-review.

Historical independent review ID: `4765336121`.

Historical reviewed head:
`0fddc4407a6a3b7fe4ca136539e858df3fe27cbf`.

Previous reviewer score: 89/100.

Current reviewer score: Pending independent re-review.

Independent review has not yet evaluated the corrected T03 publication head.

## Final Score

Previous weighted score: 93.4/100.

Previous gate-adjusted score: 79/100.

Provisional weighted score: Pending

Gate-adjusted score: Pending

The independent reviewer score is required before either final score can be
calculated.

## Critical-Gate Declaration

| Gate | Status | Evidence |
|---|---|---|
| G1 Verified claims | PASS | Claims map to source, exact local command output, independent review 4765336121, GitHub state, or exact-head CI; all historical failed invocations and corrections remain recorded. |
| G2 Confidential data | PASS | Synthetic fixtures and secret, environment, binary, credential, personal-data, and confidential-payload checks pass. |
| G3 Approved scope and architecture | PASS | Exactly one T03 domain module, its tests, and this report implement ADR-0025 without changing T02, T08, or downstream layers. |
| G4 Required validation | PASS | Corrected focused, correction-specific, affected, API, full, type, lint, format, pip, report, link, ownership, overlap, safety, PR, and exact-head CI checks ran. |
| G5 File ownership | PASS | Final publication scope is exactly the three T03-owned paths and no untracked generated output remains. |
| G6 Acceptance completeness | PASS | Every original Wave 2 criterion plus T03-C01 and T03-C02 has code, adversarial tests, report evidence, or an explicit downstream boundary. |

Critical-gate result: PASS

## Release 1.8 Additional Gates

| Gate | Status | Applicability Evidence |
|---|---|---|
| G7 Persistence alignment and PostgreSQL evidence | PASS | T03 changes no persistence path and makes no PostgreSQL claim; T05 ownership is explicit. |
| G8 Lifecycle, trust, and audit bypass prevention | PASS | Evidence/provenance contain no lifecycle, review, approval, authorization, or audit-event creation fields; T02 lifecycle remains server controlled. |

## Correction-Cycle History

| Cycle | Starting Score | Findings | Corrections | Ending Score | Validation Evidence | Status |
|---:|---:|---|---|---:|---|---|
| 1 | 100 | Environment selection produced two unavailable-tool invocations, local wheel creation left generated build output, and first focused/static checks found one warning, three E501 lines, and two format targets. | Selected a clean temporary Python 3.12 environment, removed generated output, corrected the assertion and line wrapping, formatted only owned files, and reran every required gate. | 100 | 116 focused, targeted subsets, 191 affected, 374/4 full pytest, MyPy 47, Ruff, format 61, pip, reports, links, ownership, safety, and CI run 62 pass. | CLOSED |
| 2 | 89 | Independent review 4765336121 found T03-C01 retained mutable T08 aliases and T03-C02 conflated Boolean, integer, and float metadata. | Stored only validated canonical JSON, returned detached nested views, compared complete type-preserving metadata, added 26 adversarial cases, corrected one format target and one typed adapter call site, and reran every required gate. | 100 | 142 focused, 26 correction-specific, 183 affected, 8 API, 400/4 full pytest, MyPy 47, Ruff, format 61, pip, reports, links, ownership, overlap, safety, and corrected-head CI pass; independent re-review remains pending. | CLOSED |

## Recommended Follow-up Issues

- Independent ChatGPT review should evaluate PR #57 and this publication head
  before any acceptance or merge decision.
- T05 should consume the explicit complete and legacy adapter contracts for
  persistence and migration without inventing historical facts.
- T07 should reference evidence IDs and safe provenance facts in the canonical
  immutable Enterprise Event profile without copying confidential content.
- T09 should expose versioned structured evidence and provenance only after
  persistence and lifecycle integrations are accepted.
- Issue #46 should remain open for downstream T08 persistence and API
  obligations.
- PR #49 must remain draft and unmerged until final Release 1.8 integration.

## Blockers

None.

## Recommendation

READY FOR INDEPENDENT RE-REVIEW
