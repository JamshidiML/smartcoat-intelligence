# T08 Ingestion Foundation Report

Thread ID: T08

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/22

Branch: `thread/08-ingestion-foundation-prototype`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/27

Final status: `CYCLE 2 IMPLEMENTED; INDEPENDENT RE-REVIEW REQUIRED`

## Objective

Create an industry-agnostic ingestion foundation prototype that validates source
manifests, preserves provenance metadata, and produces governed dry-run
candidates with stable identifiers without ingesting real company data.

## Scope

Changed only:

- `src/smartcoat/ingestion/`
- `tests/ingestion/`
- `docs/ingestion/INGESTION_FOUNDATION_V1.md`
- `examples/ingestion/`
- `docs/execution/reports/T08_INGESTION_FOUNDATION_REPORT.md`

## Inputs Reviewed

- `AGENTS.md`
- `SECURITY.md`
- `docs/project/PROJECT_STATE.md`
- `docs/project/MVP_STRATEGY.md`
- `docs/project/DECISION_LOG.md`
- `architecture/handbook/04_Information/02_Canonical_Data_Model.md`
- `architecture/handbook/04_Information/08_Data_Governance.md`
- Issue #22

## Execution Plan

1. Define platform-core manifest models.
2. Add validation result, warning, error, and status models.
3. Implement deterministic manifest duplicate handling.
4. Add synthetic examples for required source families.
5. Add tests for valid, invalid, duplicate, blocked, and candidate paths.
6. Document boundaries and extension points.

## Work Completed

- Added typed ingestion manifest and validation models.
- Added an organization-scoped manifest registry and validated candidate
  workflow.
- Removed the bypassable free candidate-creation function.
- Enforced literal `dry_run=True`, governed model-training approval, stable
  UUIDv5 candidate identity, meaningful fingerprints, and provenance retention.
- Added five synthetic metadata-only example manifests.
- Added safety tests for rejected, blocked, duplicate, dry-run, model-training,
  tenant isolation, site scope, stable identity, provenance, fingerprints,
  warning fields, repeated blocked submissions, and package exports.
- Documented ingestion stages, boundaries, risks, and extension points.

## Commands and Tests Executed

```bash
/private/tmp/smartcoat-1-7-threads/.venv312/bin/python -m pytest tests/ingestion
/private/tmp/smartcoat-1-7-threads/.venv312/bin/python -m ruff check src/smartcoat/ingestion tests/ingestion
/private/tmp/smartcoat-1-7-threads/.venv312/bin/python -m mypy src/smartcoat/ingestion
PYTHONPATH=src /private/tmp/smartcoat-1-7-threads/.venv312/bin/python -c '<validate example manifests>'
```

## Actual Results

| Command | Result |
|---|---|
| `python -m pytest tests/ingestion` | Passed: 20 tests passed, including every requested safety path. |
| First scoped Ruff rerun | Failed: one 102-character parser line. |
| Final `python -m ruff check src/smartcoat/ingestion tests/ingestion` | Passed after the line-wrap correction. |
| `python -m mypy src/smartcoat/ingestion` | Passed: no issues found in 3 source files. |
| Synthetic example validation | Passed: all 5 JSON manifests validate under the Cycle 2 model. |

## Acceptance-Criteria Evidence

| Criterion | Evidence |
|---|---|
| Industry-agnostic | Manifest model has no technical-textile fields. |
| Provenance and governance metadata preserved | Candidate retains every required source, time, boundary, confidentiality, use, and schema field. |
| Structured errors and warnings | `ManifestValidationIssue` and `ManifestValidationResult`. |
| Stable candidate identity | UUIDv5 uses organization-scoped source identity plus schema target/version. |
| Tenant-scoped duplicates | Same checksum collides within one organization, not across organizations. |
| Candidate safety | Rejected, blocked, duplicate, and `dry_run=False` input return no candidate. |
| Synthetic-only tests | Tests and examples use `synthetic://` references only. |
| No extraction or persistence | No OCR, chunking, embeddings, database, or API code. |
| Existing behavior untouched | New package only. |
| Mapping extension explained | Ingestion documentation separates validation from canonical mapping. |

## Architecture Impact

Adds a narrow platform-core ingestion preparation layer that supports the
canonical data model without changing current API, service, repository, or
database behavior.

## Security and Data Impact

No raw industrial data, real file names, secrets, employee content, supplier
data, prices, formulations, or production records are included. Examples are
synthetic metadata placeholders.

## Known Limitations

- Duplicate registry is in-memory for prototype dry runs.
- Checksum calculation is not implemented because raw content extraction is out
  of scope.
- Governance approval remains metadata, not IAM authorization.
- The in-memory registry is process-local and not a persistence or concurrency
  mechanism.

## Cycle 1 Independent Review Findings

- Authoritative reviewer score: 68/100, provisionally capped at 79 while the
  critical validation and governance findings remain independently unverified.
- Candidate creation bypassed validation and used random UUIDv4 identifiers.
- Duplicate identity was global across organizations.
- Candidate provenance was incomplete.
- Blocked submissions were not tracked consistently.
- Fingerprint validation was weak and duplicate warnings named the wrong field.
- Safety-critical tests and a governed package API were missing.

## Cycle 2 Corrections

- Replaced `create_candidate(manifest)` with `ManifestRegistry.process()`.
- Candidate construction is private and defensively requires matching
  `VALIDATED` status, manifest ID, duplicate key, dry-run mode, and model-use
  approval.
- Added UUIDv5 candidate IDs from organization-scoped source identity and schema
  target/version.
- Scoped duplicates by organization; documented and tested that site is
  provenance but not duplicate identity.
- Preserved all required provenance and governance fields in candidates.
- Added meaningful normalized fingerprint rules and accurate warning fields.
- Repeated blocked submissions remain blocked and are tracked separately.
- Removed direct candidate and validator helpers from the package export list.
- Expanded ingestion tests from 5 to 20.

## Lost Points and Correction Items

- Two points remain reserved for independent verification that every former
  critical finding is closed.
- One point remains deducted because approval references are metadata, not IAM.
- One point remains deducted because the registry is in-memory and process-local.
- One point remains deducted for future namespace/version migration policy.

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 24 | Safety invariants are implemented and tested. | Independent Cycle 2 review is pending. |
| Scope and acceptance criteria | 20 | 20 | Owned paths only; all criteria addressed. | None. |
| Architecture and North-Star alignment | 15 | 14 | Tenant-scoped governed preparation layer. | Persistent enforcement remains future work. |
| Verification, tests, or validation | 15 | 15 | Pytest, ruff, and mypy run for ingestion scope. | None. |
| Security, privacy, and data governance | 10 | 9 | Synthetic-only, dry-run enforced, model use gated. | Approval reference is not IAM authorization. |
| Documentation and traceability | 10 | 9 | Identity and governance behavior documented. | Independent review remains open. |
| Maintainability and clarity | 5 | 4 | Single public workflow and private builder. | Namespace migration policy remains future work. |
| Total | 100 | 95 | Cycle 2 critical corrections are locally evidenced. | Authoritative re-review remains required. |

## Critical-Gate Declaration

No confidential data was used or committed. All previously identified critical
paths now have passing local tests, but the authoritative Cycle 1 score and its
critical-gate cap remain in force until ChatGPT independently re-reviews Cycle 2.

## Correction-Cycle History

| Cycle | Starting Score | Findings | Changes Made | Ending Score |
|---:|---:|---|---|---:|
| 1 | 94 | Initial design needed explicit model-training warning and duplicate behavior. | Added blocked warning and registry tests. | 100 self-score; reviewer scored 68 and applied a critical cap. |
| 2 | 68 reviewer score | Bypassable validation, UUIDv4, global duplicates, lost provenance, weak fingerprints, inconsistent blocked behavior, and missing tests. | Added governed workflow, UUIDv5, organization scope, provenance, enforcement, and 20 safety tests. | 95 provisional self-score; independent re-review pending. |

## Recommended Follow-up Issues

- Add governed checksum calculation after raw-content handling rules are
  approved.
- Add persistence and API endpoints only after ingestion governance is accepted.

## Blockers

No implementation blocker after final validation. Independent ChatGPT re-review
is required to remove the authoritative critical-gate cap.
