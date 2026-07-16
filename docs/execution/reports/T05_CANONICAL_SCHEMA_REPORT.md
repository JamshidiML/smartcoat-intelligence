# T05 Canonical Schema Report

Thread ID: T05

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/19

Branch: `thread/05-technical-textile-canonical-schema`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/30

Final status: `READY FOR CHATGPT REVIEW`

## Objective

Define a minimum, extensible, implementation-ready Technical Textiles
Canonical Schema v1 for a controlled coating-trial pilot without changing
platform code or using proprietary data.

## Files Changed

- `docs/data/TECHNICAL_TEXTILE_CANONICAL_SCHEMA_V1.md`
- `schemas/technical_textiles/v1/README.md`
- `schemas/technical_textiles/v1/platform-envelope.schema.json`
- `schemas/technical_textiles/v1/material.schema.json`
- `schemas/technical_textiles/v1/formulation.schema.json`
- `schemas/technical_textiles/v1/coating-trial.schema.json`
- `schemas/technical_textiles/v1/test-result.schema.json`
- `docs/execution/reports/T05_CANONICAL_SCHEMA_REPORT.md`

## Work Completed

- Separated universal platform fields from technical-textile extensions.
- Modeled an end-to-end trial and representative material, formulation, and
  test-result objects.
- Added stable IDs, relationships, units, value states, provenance, evidence,
  governance, review, confidence, lifecycle, timestamps, and versioning.
- Embedded synthetic examples in every schema.
- Mapped pilot concepts to current Knowledge Object, Decision Object, and
  Enterprise Event contracts.

## Validation

Using Python 3.12 and temporary `jsonschema==4.25.1`:

```bash
/private/tmp/smartcoat-t05-schema-venv/bin/python -c '<register schemas, check Draft 2020-12, validate examples and negative cases>'
git diff --check
```

Actual results:

- 5 schemas parsed and passed `Draft202012Validator.check_schema`
- all URN references registered and resolved
- 5 embedded synthetic examples validated
- 2 invalid measurement cases were rejected: `known` without `value`, and
  `conflicting` with fewer than two values
- `git diff --check` passed

## Acceptance-Criteria Evidence

| Criterion | Evidence |
|---|---|
| Realistic R&D coating trial | Project, requirement, formulation, sample, process, machine, test, observation, failure/root cause, lesson, and decision links. |
| Platform/industry boundary | Platform envelope and separate extension schemas. |
| Governance/provenance modeled | Universal envelope fields and schema requirements. |
| Machine examples validate | Embedded examples validated by deterministic local tool. |
| No confidential content | Synthetic names, references, quantities, units, and outcomes only. |
| Open decisions separated | Accepted v1 and Open Design Decisions sections. |
| No app/database change | Only T05-owned docs and schemas. |

## Architecture Impact

The proposal specializes existing canonical concepts for the proof domain. It
does not approve application entities, APIs, persistence mappings, or migrations.

## Security and Data Impact

No company names, real materials, suppliers, formulations, prices, customers,
production records, or proprietary tests are included.

## Known Limitations

- JSON Schema validates structure, not dimensional physics or legal permission.
- Unit vocabulary, persistence mapping, and master-data ownership remain open.
- Representative schemas do not implement the entire technical-textile ontology.

## Lost Points and Correction Items

1. Reserve two points for independent domain/schema review.
2. Reserve one point until an approved unit vocabulary exists.
3. Reserve one point until company-extension compatibility is decided.

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 24 | Draft 2020-12 schemas and examples. | Independent domain review pending. |
| Scope and acceptance criteria | 20 | 20 | All issue deliverables in owned paths. | None. |
| Architecture and North-Star alignment | 15 | 15 | Universal/Hub boundary and canonical mappings explicit. | None. |
| Verification, tests, or validation | 15 | 15 | Schema and positive/negative validation executed. | None. |
| Security, privacy, and data governance | 10 | 10 | Synthetic only; confidentiality/use/provenance required. | None. |
| Documentation and traceability | 10 | 9 | Entity, relationship, quality, version, and mapping documentation. | Unit authority remains open. |
| Maintainability and clarity | 5 | 3 | Modular schemas with stable IDs and extension policy. | Company extension and unit policies remain open. |
| Total | 100 | 96 | Ready for independent review. | Four correction points remain above. |

## Critical-Gate Declaration

No critical gate failed. Machine validation and negative cases passed, no
confidential data is present, and all changes remain in T05-owned paths.

## Correction-Cycle History

| Cycle | Starting Score | Findings | Corrections | Ending Score |
|---:|---:|---|---|---:|
| 1 | 89 | Needed universal boundary, explicit unknown/conflict states, and executable examples. | Added platform envelope, four extension schemas, stateful measurements, examples, and validation plan. | 96 provisional. |

## Recommended Follow-up Issues

- Approve canonical unit vocabulary and conversion rules.
- Review schemas with technical-textile domain owner before application mapping.
- Design persistence/API mapping only after v1 acceptance.

## Blockers

None for independent review after successful validation.
