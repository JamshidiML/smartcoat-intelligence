# T08 Ingestion Foundation Report

Thread ID: T08

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/22

Branch: `thread/08-ingestion-foundation-prototype`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/27

Final status: `CORRECTION CYCLE 3 COMPLETE; READY FOR INDEPENDENT RE-REVIEW`

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
- Enforced literal `dry_run=True`, blocked unverified model-training decisions,
  stable UUIDv5 candidate identity, meaningful fingerprints, and provenance
  retention.
- Adopted T07's canonical confidentiality, purpose, decision-status, and
  governance-version values.
- Added five synthetic metadata-only example manifests.
- Added safety tests for rejected, blocked, duplicate, dry-run, model-training,
  tenant isolation, site scope, stable identity, provenance, fingerprints,
  warning fields, repeated blocked submissions, governance vocabulary, and
  package exports.
- Documented ingestion stages, boundaries, risks, and extension points.

## Commands and Tests Executed

```bash
"$TMPDIR/smartcoat-cycle3-t08-venv/bin/python" -m pytest tests/ingestion -q
"$TMPDIR/smartcoat-cycle3-t08-venv/bin/python" -m ruff check src/smartcoat/ingestion tests/ingestion
"$TMPDIR/smartcoat-cycle3-t08-venv/bin/python" -m mypy src/smartcoat/ingestion
PYTHONPATH=src "$TMPDIR/smartcoat-cycle3-t08-venv/bin/python" -c '<validate example manifests>'
```

## Actual Results

| Command | Result |
|---|---|
| `python -m pytest tests/ingestion -q` | Passed: 22 tests in 0.46 seconds, including canonical governance and authorization-boundary cases. |
| First scoped Ruff rerun | Failed: one import-order issue introduced in Cycle 3. |
| Final `python -m ruff check src/smartcoat/ingestion tests/ingestion` | Passed after the import-order correction. |
| `python -m mypy src/smartcoat/ingestion` | Passed: no issues found in 3 source files. |
| Synthetic example validation | Passed: all 5 JSON manifests validate under the Cycle 2 model. |

## Acceptance-Criteria Evidence

| Criterion | Evidence |
|---|---|
| Industry-agnostic | Manifest model has no technical-textile fields. |
| Provenance and governance metadata preserved | Candidate retains every required source, time, boundary, canonical confidentiality, purpose-decision, and schema field. |
| Structured errors and warnings | `ManifestValidationIssue` and `ManifestValidationResult`. |
| Stable candidate identity | UUIDv5 uses organization-scoped source identity plus schema target/version. |
| Tenant-scoped duplicates | Same checksum collides within one organization, not across organizations. |
| Candidate safety | Rejected, blocked, duplicate, `dry_run=False`, and declared model-training approval return no candidate without service authorization. |
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
- Governance approval references remain opaque metadata, not IAM authorization;
  their issuer/version/expiry/authenticity contract is intentionally deferred.
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

## Cycle 2 Independent Review

- Authoritative reviewer score: **95/100**; provisional weighted score: **95.0**.
- The prior critical gate was closed and its 79-point cap was removed.
- Six Cycle 3 corrections remained: canonical confidentiality, explicit
  approval-reference semantics and deferred contract, site duplicate rationale,
  private-helper threat boundary, and T10 report-contract alignment.

## Cycle 3 Corrections

- Replaced `highly_confidential` with canonical `strategic` and consumed the
  complete T07 purpose-decision vocabulary and governance schema version.
- Kept model-training candidates blocked when the declared status is
  `in_review` or `approved`, even when an opaque approval reference is present.
- Documented that approval reference issuer, version, expiry, revocation, and
  authenticity validation require a future governed integration contract.
- Defined why duplicate identity is organization-scoped, why site is
  provenance, and how same-source submissions from two sites resolve.
- Declared that Python private helpers are not a security boundary and that
  service/API authorization remains mandatory.
- Added two governance tests and reran all required validation. Final migration
  to the corrected T10 report contract remains a Wave B cross-thread action.

## Lost Points and Correction Items

- One point remains reserved for independent Cycle 3 re-review.
- One point remains deducted because approval-reference verification is deferred.
- One point remains deducted because the registry is in-memory and process-local.
- One point remains deducted until Wave B applies the corrected T10 report contract.
- One point remains deducted for future candidate-namespace migration policy.

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 24 | Safety and governance invariants are implemented and tested. | Independent Cycle 3 review is pending. |
| Scope and acceptance criteria | 20 | 20 | Owned paths only; all criteria addressed. | None. |
| Architecture and North-Star alignment | 15 | 14 | Tenant-scoped governed preparation layer. | Persistent enforcement remains future work. |
| Verification, tests, or validation | 15 | 15 | Pytest, ruff, and mypy run for ingestion scope. | None. |
| Security, privacy, and data governance | 10 | 9 | Synthetic-only, dry-run enforced, model use blocked without external authorization. | Approval-reference verification contract is deferred. |
| Documentation and traceability | 10 | 9 | Identity, site scope, and governance behavior documented. | T10 report-contract migration remains. |
| Maintainability and clarity | 5 | 4 | Single public workflow and private builder. | Namespace migration policy remains future work. |
| Total | 100 | 95 | Cycle 3 corrections are locally evidenced; authoritative score remains 95. | Five provisional points remain above. |

## Critical-Gate Declaration

No confidential data was used or committed. The Cycle 2 independent review
closed the prior critical gate. Cycle 3 has passing local evidence, but only a
new independent review may replace the authoritative 95/100 score.

## Correction-Cycle History

| Cycle | Starting Score | Findings | Changes Made | Ending Score |
|---:|---:|---|---|---:|
| 1 | 94 | Initial design needed explicit model-training warning and duplicate behavior. | Added blocked warning and registry tests. | 100 self-score; reviewer scored 68 and applied a critical cap. |
| 2 | 68 reviewer score | Bypassable validation, UUIDv4, global duplicates, lost provenance, weak fingerprints, inconsistent blocked behavior, and missing tests. | Added governed workflow, UUIDv5, organization scope, provenance, enforcement, and 20 safety tests. | 95 provisional self-score; independent re-review pending. |
| 3 | 95 authoritative | Governance vocabulary conflict, approval-reference ambiguity, site-scope rationale, private-helper threat boundary, and report-contract alignment. | Aligned T07 vocabulary, made model-training authorization non-bypassable by metadata, documented deferred contracts and site behavior, and passed 22 tests plus Ruff/MyPy/examples. | 95 provisional self-score; authoritative re-review remains pending. |

## Recommended Follow-up Issues

- Add governed checksum calculation after raw-content handling rules are
  approved.
- Add persistence and API endpoints only after ingestion governance is accepted.

## Blockers

No implementation blocker after final validation. Independent ChatGPT re-review
is required to remove the authoritative critical-gate cap.
