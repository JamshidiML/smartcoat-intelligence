# Dataset Assessment Template

Assessment ID:

Scoring model version: `smartcoat-readiness-v1.1-draft`

Source ID:

Assessment timestamp (UTC):

Assessor role:

Assessment evidence references:

## Stop Check

- [ ] Assessment uses only synthetic, generalized, metadata-only, or explicitly approved sanitized content.
- [ ] Data owner and steward are identified.
- [ ] Confidentiality and every sensitivity indicator are classified as
  `unknown`, `none`, or `present`; no `unknown` is treated as false.
- [ ] Legal/contractual permission covers the exact assessment purpose.
- [ ] Organization/site and need-to-know access boundary are explicit.
- [ ] Retention, deletion, correction, and incident contacts are known.

If any item is unchecked, stop content assessment and record the source as
`blocked`. Do not attach raw examples to this document.

## Purpose

Pilot use case:

Decision or workflow supported:

Expected measurable value:

Explicitly excluded uses:

## Generalized Source Profile

Source family:

Business function:

Format and structure:

Volume/history bands:

Languages:

Update frequency:

Authoritative source or derivative:

## Governance

Owner role:

Steward role:

Confidentiality:

Personal-data state (`unknown`, `none`, `present`):

Employee-data state (`unknown`, `none`, `present`):

Customer-identity state (`unknown`, `none`, `present`):

Supplier/commercial state (`unknown`, `none`, `present`):

Trade-secret state (`unknown`, `none`, `present`):

Permission evidence reference:

Intended purposes (canonical T07 values):

Inventory permission (`not_requested`, `in_review`, `approved`, `denied`, `expired`, `revoked`):

Retrieval permission:

Analytics permission:

Human-review permission:

Model-training permission:

External-sharing permission:

Access boundary:

Retention/deletion rule:

## Quality Evidence

Completeness evidence:

Consistency evidence:

Identifier evidence:

Timestamp evidence:

Unit/basis evidence:

Provenance evidence:

Duplicate evidence:

Known conflicts/unknowns:

## Extraction and Mapping

Approved sanitized sample description:

Extraction approach and human review:

Target canonical objects:

Mapping ambiguities:

Expected correction process:

## Readiness Ratings

Record 0-4 rating and evidence for all 16 dimensions in
`docs/data/DATA_READINESS_MATRIX.md`.

Calculated score:

Scoring evidence references:

Governance gate (`passed` or `blocked`):

Recommended priority:

## Risks and Actions

| Risk or gap | Impact | Owner role | Required action | Due/review date |
|---|---|---|---|---|
| | | | | |

## Decision

- [ ] Defer
- [ ] Continue discovery
- [ ] Assess approved sanitized sample
- [ ] Prepare controlled package
- [ ] Approve bounded pilot ingestion

Decision owner:

Rationale and evidence references:

Next review trigger:

## Reassessment History

Previous assessment ID:

Previous readiness score:

Reassessment reason (`initial_assessment` when none):

Immutable history reference:

Do not replace a prior assessment row or evidence reference. Create a new
assessment ID and link it here.
