# T05 Canonical Schema Report

Report schema version: `smartcoat-execution-report-v2.0`

Thread ID: T05

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/19

Branch: `thread/05-technical-textile-canonical-schema`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/30

Final status: `READY FOR INDEPENDENT RE-REVIEW`

## Objective

Define an extensible, implementation-ready Technical Textiles Canonical Schema
proposal for a controlled coating-trial pilot without changing platform code or
using proprietary data.

## Files Changed

- `docs/data/TECHNICAL_TEXTILE_CANONICAL_SCHEMA_V1.md`
- `schemas/platform/v1/README.md`
- `schemas/platform/v1/platform-envelope.schema.json`
- `schemas/technical_textiles/v1/README.md`
- `schemas/technical_textiles/v1/material.schema.json`
- `schemas/technical_textiles/v1/formulation.schema.json`
- `schemas/technical_textiles/v1/coating-trial.schema.json`
- `schemas/technical_textiles/v1/test-result.schema.json`
- `docs/execution/reports/T05_CANONICAL_SCHEMA_REPORT.md`

The former Hub-local envelope source was deleted so the repository has one
canonical definition. All paths are owned by issue #19 or the explicitly
authorized Cycle 4 platform-schema boundary.

## Methods and Commands Executed

- `"$TMPDIR/smartcoat-cycle3-t05-venv/bin/python" -m pip show jsonschema`
- Python 3.12 inline validation registered the platform schema and four Hub
  schemas with `jsonschema==4.25.1`, checked Draft 2020-12, ran positive and
  negative cases, and asserted extension ownership.
- `jq empty schemas/platform/v1/platform-envelope.schema.json schemas/technical_textiles/v1/*.schema.json`
- `find schemas -name 'platform-envelope.schema.json' -print`
- `git diff --check`

## Actual Results

| Method or Command | Actual Result | Evidence |
|---|---|---|
| Schema meta-validation | PASS: 5 schemas | Draft202012Validator check_schema completed. |
| Embedded examples | PASS: 5 examples | Every example validated against its owning registered schema. |
| Negative contract matrix | PASS: 14 invalid cases rejected | Measurement states, review evidence, governance values, purposes, and subtype identity covered. |
| Hub extension boundary | PASS: 4 child schemas extend the platform ID and redefine only `object_type` as a subtype constraint | Python structural assertions. |
| Canonical envelope source | PASS: 1 schema path and 1 matching platform `$id` | Repository path and schema-ID scans. |
| JSON parsing | PASS: all schema files | `jq empty` exited zero. |
| Owned-path check | PASS: nine final changed paths, all T05-owned or Cycle 4-authorized | Branch diff against release baseline. |
| `git diff --check` | PASS: no whitespace errors | Command exited zero. |

## Acceptance-Criteria Evidence

- [x] Model a realistic R&D coating-trial chain.
  Evidence: material, formulation, trial, result, observation, failure, lesson, and decision links.
- [x] Enforce the platform and Industry Hub boundary.
  Evidence: one platform-owned industry-agnostic envelope and four child-owned textile type constraints.
- [x] Model provenance, evidence, governance, lifecycle, review, and uncertainty.
  Evidence: required universal envelope fields and conditional rules.
- [x] Provide machine-valid synthetic examples.
  Evidence: five positive examples passed registered-schema validation.
- [x] Reject incoherent states and governance values.
  Evidence: fourteen targeted negative cases were rejected.
- [x] Map ingestion to canonical platform outputs.
  Evidence: SourceManifest-to-envelope-to-Hub-to-object/event mapping section.
- [x] Use no confidential industrial content.
  Evidence: generalized names, references, quantities, and outcomes only.
- [x] Avoid application and database changes.
  Evidence: only T05 documentation and schema paths changed.

## Architecture Impact

The proposal specializes existing canonical concepts for the proof domain. The
platform envelope is industry-agnostic and has one platform-owned source; child
schemas reference its stable ID and own textile constraints. No application
entity, API, persistence model, or migration is approved here.

## Security and Data Impact

No real companies, materials, suppliers, formulations, prices, customers,
production records, or proprietary tests are included. Approval references are
metadata and do not replace authorization or IAM.

## Known Limitations

- JSON Schema validates structure, not dimensional physics or legal permission.
- Unit vocabulary, persistence mapping, and master-data ownership remain open.
- Historical `1.0.0` pilot records require an explicit `1.1.0` migration.
- The Cycle 3 reviewer score remains 94/100 until independent re-review verifies
  the validated platform-path correction; controlled integration is not claimed.

## Lost Points and Correction Items

| Item | Source | Points | Status | Action or Evidence |
|---|---|---:|---|---|
| C01 | PR #30 Cycle 1 correctness deduction | 8 | RESOLVED | Cycle 3 reviewer confirmed coherent envelope, measurement, and review rules. |
| C02 | PR #30 Cycle 1 scope deduction | 6 | RESOLVED | Cycle 3 reviewer confirmed platform fields are separated from Hub constraints. |
| C03 | PR #30 Cycle 1 architecture deduction | 8 | RESOLVED | Cycle 3 reviewer confirmed extensible platform type and child-owned textile types. |
| C04 | PR #30 Cycle 1 verification deduction | 1 | RESOLVED | Cycle 3 reviewer accepted expanded positive and negative coverage. |
| C05 | PR #30 Cycle 1 governance deduction | 3 | RESOLVED | Cycle 3 reviewer confirmed canonical T07 governance values. |
| C06 | PR #30 Cycle 1 traceability deduction | 1 | RESOLVED | Cycle 3 reviewer confirmed end-to-end contract mapping. |
| C07 | PR #30 Cycle 1 maintainability deduction | 1 | RESOLVED | Cycle 3 reviewer confirmed child-owned type constraints and explicit migration limits. |
| C08 | PR #30 Cycle 3 platform-ownership deduction | 6 | IN PROGRESS | One canonical envelope now lives under the platform path; four children, docs, registry text, five examples, fourteen negatives, and uniqueness checks pass. Independent re-review remains required. |

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 24 | Draft 2020-12 schemas, five examples, and fourteen negative cases. | Independent domain re-review pending. |
| Scope and acceptance criteria | 20 | 20 | All issue deliverables remain in owned paths. | None. |
| Architecture and North-Star alignment | 15 | 15 | Industry-agnostic envelope and Hub mapping are explicit. | None. |
| Verification, tests, or validation | 15 | 15 | Meta-schema, positive, negative, JSON, scope, and diff checks passed. | None. |
| Security, privacy, and data governance | 10 | 10 | Synthetic only and canonical governance required. | None. |
| Documentation and traceability | 10 | 9 | Entity, state, version, and platform mapping documented. | Unit authority remains open. |
| Maintainability and clarity | 5 | 3 | Modular schemas with stable IDs and extension policy. | Migration and unit policies remain open. |
| Total | 100 | 96 | Cycle 3 local evidence is complete. | Four self-score points remain. |

## ChatGPT Reviewer Score

Reviewer total: 94

Reviewer evidence: GitHub PR #30 Cycle 3 independent review submitted 2026-07-19.

## Final Score

Provisional weighted score: 94.8

Gate-adjusted score: 94.8

## Critical-Gate Declaration

| Gate | Status | Evidence |
|---|---|---|
| G1 Verified claims | PASS | Current local claims are tied to executed schema checks. |
| G2 Confidential data | PASS | Synthetic generalized fixtures only. |
| G3 Approved scope and architecture | PASS | Cycle 4 uses the explicitly authorized platform path and retains Hub-owned child constraints. |
| G4 Required validation | PASS | Expanded positive and negative validation passed. |
| G5 File ownership | PASS | Nine final changed paths are issue-owned or explicitly authorized for Cycle 4. |
| G6 Acceptance completeness | PASS | All criteria are checked; the remaining six points require independent verification, not missing implementation. |

Critical-gate result: PASS

## Correction-Cycle History

| Cycle | Starting Score | Findings | Corrections | Ending Score | Validation Evidence | Status |
|---:|---:|---|---|---:|---|---|
| 1 | 89 | Needed universal boundary, explicit states, and executable examples. | Added envelope, four child schemas, stateful measurements, examples, and validation. | 96 | Initial schema and example checks. | CLOSED |
| 2 | 96 | Reviewer found domain-bound core, governance conflicts, incoherent states, and incomplete mapping. | Recorded 72 reviewer score and G3/G6 failures. | 72 | PR #30 independent review. | CLOSED |
| 3 | 72 | Twenty-eight reviewer points became correction items. | Generalized envelope, aligned T07, hardened state/review rules, mapped contracts, and migrated report. | 96 | Five schemas, five examples, fourteen negative cases, JSON, scope, and diff checks passed. | CLOSED |
| 4 | 94 | Cycle 3 reviewer retained six points because the platform envelope was stored under a Hub-owned path. | Moved the sole envelope source to the platform path and updated ownership, registry text, references, and validation. | 96 | Five schemas, five examples, fourteen negatives, four extension checks, one envelope source/ID, JSON, scope, and diff checks pass. | OPEN |

## Recommended Follow-up Issues

- Approve canonical units and conversion rules.
- Review schemas with the technical-textile domain owner.
- Migrate any pilot `1.0.0` records before adopting `1.1.0`.
- Design persistence/API mapping only after schema acceptance.

## Blockers

None.
