# T05 Canonical Schema Report

Thread ID: T05

Issue: https://github.com/JamshidiML/smartcoat-intelligence/issues/19

Branch: `thread/05-technical-textile-canonical-schema`

Draft PR: https://github.com/JamshidiML/smartcoat-intelligence/pull/30

Final status: `CORRECTION CYCLE 3 COMPLETE; READY FOR INDEPENDENT RE-REVIEW`

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

- Separated an industry-agnostic platform envelope from technical-textile
  extensions; the envelope no longer restricts `object_type` to textile types.
- Modeled an end-to-end trial and representative material, formulation, and
  test-result objects.
- Added stable IDs, relationships, units, coherent value states, provenance,
  evidence, canonical governance decisions, review, confidence, lifecycle,
  timestamps, and versioning.
- Embedded synthetic examples in every schema.
- Mapped ingestion candidates through the canonical platform contracts to
  Knowledge Object, Decision Object, and Enterprise Event outputs.

## Validation

Using Python 3.12 and a temporary, pinned `jsonschema==4.25.1` environment:

```bash
"$TMPDIR/smartcoat-cycle3-t05-venv/bin/python" - <<'PY'
# Register all schemas, check Draft 2020-12, and validate examples and
# positive/negative contract cases.
PY
git diff --check
```

Actual results:

- 5 schemas parsed and passed `Draft202012Validator.check_schema`
- all URN references registered and resolved
- 5 embedded synthetic examples validated
- 14 invalid cases were rejected, covering all measurement states, review
  evidence, governance vocabulary, purpose completeness, and subtype identity
- `git diff --check` passed

## Acceptance-Criteria Evidence

| Criterion | Evidence |
|---|---|
| Realistic R&D coating trial | Project, requirement, formulation, sample, process, machine, test, observation, failure/root cause, lesson, and decision links. |
| Platform/industry boundary | Industry-agnostic platform envelope and textile-only extension schemas. |
| Governance/provenance modeled | Canonical T07 confidentiality and purpose-decision values, governance schema version, and required provenance. |
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
- Unit vocabulary, persistence mapping, historical `1.0.0` migration, and
  master-data ownership remain open.
- Representative schemas do not implement the entire technical-textile ontology.

## Lost Points and Correction Items

Authoritative independent review scored the prior head **72/100** and applied a
**79-point critical-gate cap**. Every reviewer deduction became a Cycle 3 item:

1. Remove textile-type restrictions from the platform envelope.
2. Replace conflicting governance values with the T07 canonical vocabulary.
3. Make every measurement state internally coherent and test each invalid form.
4. Distinguish object lifecycle from review state and require reviewer evidence
   for accepted/validated records.
5. Document the ingestion-to-platform mapping and clarify that approval
   references are metadata, not authorization.
6. Expand machine validation and record the exact results.

Remaining provisional deductions after correction:

1. Reserve two points for independent domain/schema re-review.
2. Reserve one point until an approved unit vocabulary exists.
3. Reserve one point for explicit migration of any `1.0.0` pilot records.

## Codex Self-Score

| Category | Maximum | Awarded | Evidence | Deduction Reason |
|---|---:|---:|---|---|
| Correctness and evidence | 25 | 24 | Draft 2020-12 schemas, examples, and 14 negative cases. | Independent domain re-review pending. |
| Scope and acceptance criteria | 20 | 20 | All issue deliverables in owned paths. | None. |
| Architecture and North-Star alignment | 15 | 15 | Universal/Hub boundary and canonical mappings explicit. | None. |
| Verification, tests, or validation | 15 | 15 | Schema and positive/negative validation executed. | None. |
| Security, privacy, and data governance | 10 | 10 | Synthetic only; confidentiality/use/provenance required. | None. |
| Documentation and traceability | 10 | 9 | Entity, relationship, quality, version, and platform mapping documentation. | Unit authority remains open. |
| Maintainability and clarity | 5 | 3 | Modular schemas with stable IDs and extension policy. | `1.0.0` migration and unit policy remain open. |
| Total | 100 | 96 | Cycle 3 local evidence complete; independent score remains 72 until re-review. | Four provisional points remain above. |

## Critical-Gate Declaration

The previous independent review applied the 79-point gate because the platform
envelope was domain-bound and cross-thread governance values conflicted. Cycle
3 corrected those local causes and machine validation now passes. Only a new
independent review can remove the prior gate and replace the authoritative
72/100 score. No confidential data is present, and all changes remain in
T05-owned paths.

## Correction-Cycle History

| Cycle | Starting Score | Findings | Corrections | Ending Score |
|---:|---:|---|---|---:|
| 1 | 89 | Needed universal boundary, explicit unknown/conflict states, and executable examples. | Added platform envelope, four extension schemas, stateful measurements, examples, and validation plan. | 96 provisional. |
| 2 | 96 self-score | Independent review found a domain-bound envelope, governance conflicts, state inconsistencies, weak lifecycle/review semantics, and insufficient negative evidence. | Findings accepted; authoritative reviewer score recorded as 72 with a 79-point gate. | 72 authoritative. |
| 3 | 72 authoritative | Six correction items derived from every reviewer deduction. | Generalized the envelope, aligned T07 vocabulary, hardened state/review rules, documented canonical mapping, and passed 5 positive plus 14 negative checks. | 96 provisional self-score; 72 remains authoritative pending re-review. |

## Recommended Follow-up Issues

- Approve canonical unit vocabulary and conversion rules.
- Review schemas with technical-textile domain owner before application mapping.
- Migrate any pilot `1.0.0` records explicitly before adopting `1.1.0`.
- Design persistence/API mapping only after v1.1 acceptance.

## Blockers

None for independent review after successful validation.
