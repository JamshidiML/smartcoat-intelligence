# Data Ingestion Approval Template

Request ID:

Status (`draft`, `blocked`, `approved`, `expired`, `revoked`):

Governance schema version (`smartcoat-governance-v1.1-draft`):

Policy versions applied:

Effective / expiry / next-review dates:

Supersedes approval reference:

This record documents a decision; it is not legal advice or a substitute for
professional review.

## Source and Accountability

Organization/site and isolation boundary:

Generalized source ID/family (no confidential filename or content):

Data owner / steward / system owner roles:

Collection basis and evidence reference:

## Purpose and Minimum Package

Pilot use case and decision supported:

Minimum fields, records, and date range:

Expected outputs and recipients:

Explicit exclusions:

## Classification

Base classification (`Public`, `Internal`, `Confidential`, `Restricted`, `Strategic`):

Overlays (personal/employee, trade secret/IP, customer/supplier/contract,
licensed, safety/regulatory, jurisdiction/residency):

Sanitization/anonymization method and re-identification review:

## Separate Permitted-Use Decisions

| Purpose | Decision | Scope, conditions, expiry | Evidence / approver |
|---|---|---|---|
| `inventory` | `not_requested / in_review / approved / denied / expired / revoked` | | |
| `retrieval` | | | |
| `analytics` | | | |
| `human_review` | | | |
| `model_training` | | | |
| `external_sharing` | | | |

Approved users, roles, services, models/providers, subprocessors, and geography:

Prohibited uses:

## Lifecycle and Controls

Provenance and source-to-schema mapping:

Raw, normalized, derived, embedding/index, log, backup, and model-artifact retention:

Correction, revocation, deletion, and legal-hold authority:

Audit events and review cadence:

Incident contact, emergency-stop owner, restart authority, and stop-test evidence:

Operational authority (`l0_manual` through `l4_bounded_automation`):

Human-approval requirement (`not_required`, `required_single`, `required_joint`):

Human-approval status (`not_requested`, `pending`, `approved`, `rejected`, `expired`, `revoked`):

## Governance Gate

- [ ] Owner and steward authority is evidenced.
- [ ] Classification and all overlays are complete.
- [ ] Contract, license, privacy/employment, consent/lawful-basis, and IP review is complete as applicable.
- [ ] The applicable basis and professional/works-council determination are recorded; consent is not assumed.
- [ ] Voice/meeting capture is absent or specifically reviewed and permitted.
- [ ] Formulation, invention, unpublished R&D, price, and contract content is absent or specifically approved.
- [ ] Every intended purpose has a separate decision; unapproved uses default to denied.
- [ ] Company/site isolation, need-to-know access, processors/models, and geography are explicit.
- [ ] A synthetic or explicitly approved sanitized sample passed mapping and security review.
- [ ] Retention, correction, revocation, deletion, audit, and incident controls are testable.
- [ ] Human reviewers, autonomy level, high-risk gates, baseline, metrics, and expiry are defined.

Any unchecked item keeps status `blocked`.

## Approvals

| Role | Decision | Name/reference | Date | Conditions |
|---|---|---|---|---|
| Data owner | | | | |
| Data steward | | | | |
| Security/privacy | | | | |
| Legal/IP/employment (as applicable) | | | | |
| Pilot owner | | | | |
| Platform operator verification | | | | |

Final decision and rationale:

Effective/expiry dates and reassessment triggers:
