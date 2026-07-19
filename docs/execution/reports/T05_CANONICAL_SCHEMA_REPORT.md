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
- `schemas/technical_textiles/v1/README.md`
- `schemas/technical_textiles/v1/platform-envelope.schema.json`
- `schemas/technical_textiles/v1/material.schema.json`
- `schemas/technical_textiles/v1/formulation.schema.json`
- `schemas/technical_textiles/v1/coating-trial.schema.json`
- `schemas/technical_textiles/v1/test-result.schema.json`
- `docs/execution/reports/T05_CANONICAL_SCHEMA_REPORT.md`

All paths are owned by issue #19.

## Methods and Commands Executed

- `"$TMPDIR/smartcoat-cycle3-t05-venv/bin/python" -m pip show jsonschema`
- Python 3.12 inline validation registered all five schemas with
  `jsonschema==4.25.1`, checked Draft 2020-12, and ran positive/negative cases.
- `jq empty schemas/technical_textiles/v1/*.schema.json`
- `git diff --check`

## Actual Results

| Method or Command | Actual Result | Evidence |
|---|---|---|
| Schema meta-validation | PASS: 5 schemas | Draft202012Validator check_schema completed. |
| Embedded examples | PASS: 5 examples | Every example validated against its owning registered schema. |
| Negative contract matrix | PASS: 14 invalid cases rejected | Measurement states, review evidence, governance values, purposes, and subtype identity covered. |
| JSON parsing | PASS: all schema files | `jq empty` exited zero. |
| Owned-path check | PASS: eight changed paths, all T05-owned | Branch diff against release baseline. |
| `git diff --check` | PASS: no whitespace errors | Command exited zero. |

## Acceptance-Criteria Evidence

- [x] Model a realistic R&D coating-trial chain.
  Evidence: material, formulation, trial, result, observation, failure, lesson, and decision links.
- [x] Enforce the platform and Industry Hub boundary.
  Evidence: extensible industry-agnostic envelope and child-owned textile type constraints.
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
platform envelope is industry-agnostic; child schemas own textile constraints.
No application entity, API, persistence model, or migration is approved here.

## Security and Data Impact

No real companies, materials, suppliers, formulations, prices, customers,
production records, or proprietary tests are included. Approval references are
metadata and do not replace authorization or IAM.

## Known Limitations

- JSON Schema validates structure, not dimensional physics or legal permission.
- Unit vocabulary, persistence mapping, and master-data ownership remain open.
- Historical `1.0.0` pilot records require an explicit `1.1.0` migration.
- The prior G3/G6 failures remain authoritative until independent re-review.

## Lost Points and Correction Items

| Item | Source | Points | Status | Action or Evidence |
|---|---|---:|---|---|
| C01 | PR #30 correctness deduction | 8 | IN PROGRESS | Generalized envelope and coherent state/review rules implemented; re-review pending. |
| C02 | PR #30 scope deduction | 6 | IN PROGRESS | Platform fields are separated from textile child constraints. |
| C03 | PR #30 architecture deduction | 8 | IN PROGRESS | Mother-platform dependency on textile object enums removed. |
| C04 | PR #30 verification deduction | 1 | IN PROGRESS | Five positive and fourteen negative checks now pass. |
| C05 | PR #30 governance deduction | 3 | IN PROGRESS | Canonical T07 confidentiality, purposes, decisions, and schema version applied. |
| C06 | PR #30 traceability deduction | 1 | IN PROGRESS | End-to-end SourceManifest and canonical-object mapping documented. |
| C07 | PR #30 maintainability deduction | 1 | IN PROGRESS | Child schemas constrain type and v1.1 migration is explicit. |

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

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 17 | Reviewer confirmed a concrete schema chain. | Envelope and measurement claims conflicted with machine rules. |
| Scope and acceptance criteria | 20 | 14 | Required artifacts were present. | Platform-core boundary was not actually enforced. |
| Architecture and North-Star alignment | 15 | 7 | Canonical mapping intent was visible. | Mother platform depended on textile object types. |
| Verification, tests, or validation | 15 | 14 | Synthetic schema checks existed. | Cross-schema negative coverage was incomplete. |
| Security, privacy, and data governance | 10 | 7 | Governance fields were modeled. | Taxonomies conflicted with T07/T08. |
| Documentation and traceability | 10 | 9 | Design and examples were documented. | End-to-end contract mapping was missing. |
| Maintainability and clarity | 5 | 4 | Schemas were modular. | Core/extension naming and behavior diverged. |
| Total | 100 | 72 | GitHub PR #30 Cycle 1 review. | Twenty-eight reviewer points remain authoritative. |

## Final Score

Provisional weighted score: 81.6

Gate-adjusted score: 79.0

## Critical-Gate Declaration

| Gate | Status | Evidence |
|---|---|---|
| G1 Verified claims | PASS | Current local claims are tied to executed schema checks. |
| G2 Confidential data | PASS | Synthetic generalized fixtures only. |
| G3 Approved scope and architecture | FAIL | PR #30 architecture gate remains until independent re-review. |
| G4 Required validation | PASS | Expanded positive and negative validation passed. |
| G5 File ownership | PASS | All eight changed paths are T05-owned. |
| G6 Acceptance completeness | FAIL | PR #30 completeness gate remains until re-review verifies boundary correction. |

Critical-gate result: FAIL

## Correction-Cycle History

| Cycle | Starting Score | Findings | Corrections | Ending Score | Validation Evidence | Status |
|---:|---:|---|---|---:|---|---|
| 1 | 89 | Needed universal boundary, explicit states, and executable examples. | Added envelope, four child schemas, stateful measurements, examples, and validation. | 96 | Initial schema and example checks. | CLOSED |
| 2 | 96 | Reviewer found domain-bound core, governance conflicts, incoherent states, and incomplete mapping. | Recorded 72 reviewer score and G3/G6 failures. | 72 | PR #30 independent review. | CLOSED |
| 3 | 72 | Twenty-eight reviewer points became correction items. | Generalized envelope, aligned T07, hardened state/review rules, mapped contracts, and migrated report. | 96 | Five schemas, five examples, fourteen negative cases, JSON, scope, and diff checks passed. | OPEN |

## Recommended Follow-up Issues

- Approve canonical units and conversion rules.
- Review schemas with the technical-textile domain owner.
- Migrate any pilot `1.0.0` records before adopting `1.1.0`.
- Design persistence/API mapping only after schema acceptance.

## Blockers

None.
