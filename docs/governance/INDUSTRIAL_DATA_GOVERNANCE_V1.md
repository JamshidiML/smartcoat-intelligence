# Industrial Data Governance V1

Status: Draft policy for controlled-pilot review

Owner: Founder/Product Owner and designated Data Governance Lead

This document is an operational design, **not legal advice**. Qualified legal,
privacy, employment, intellectual-property, security, and works-council review
is required where applicable before real industrial data is processed.

## Purpose and Scope

This policy governs data proposed for SmartCoat discovery, ingestion, retrieval,
analytics, model training, recommendations, and sharing. It applies across every
company, site, industry extension, user, service, model provider, and processor.
It implements the security boundary in `SECURITY.md` and Decisions D-003,
D-006, D-007, and D-014 without changing those sources.

## Governing Principles

1. **Company isolation by default.** Data, embeddings, indexes, prompts, logs,
   caches, model artifacts, and derived knowledge remain within one approved
   organization boundary unless separately authorized.
2. **Purpose limitation.** Discovery is not access; access is not ingestion;
   retrieval is not analytics; analytics is not model training; training is not
   external sharing. Each purpose requires an explicit decision.
3. **Least privilege and need to know.** Grant the minimum data, action, scope,
   and duration needed for an approved role and use case.
4. **Owner authority and stewardship.** Every source has an accountable owner
   and operational steward. Neither platform availability nor employee access
   proves ownership or permission.
5. **Provenance before trust.** Preserve source, actor, collection basis,
   timestamps, transformations, evidence, version, and review state.
6. **Human-reviewed knowledge.** Extraction and AI output remain draft until an
   authorized reviewer accepts, corrects, or rejects them.
7. **Minimize and separate.** Use the smallest approved package; exclude fields,
   content, people, companies, and time ranges not needed for the purpose.
8. **Reversible lifecycle.** Retention, correction, revocation, deletion, legal
   hold, and derived-artifact handling are defined before ingestion.
9. **No silent secondary use.** A new user, model, tenant, purpose, destination,
   or material transformation triggers reassessment.
10. **Evidence over score.** Business value, readiness, and model confidence
    never override confidentiality, consent, safety, legal, or contractual gates.

## Role and Responsibility Matrix

R = responsible, A = accountable, C = consulted, I = informed.

| Activity | Data owner | Data steward | Security/privacy | Legal/IP | Pilot owner | Platform operator | Human reviewer |
|---|---|---|---|---|---|---|---|
| Classify source and identify rights | A | R | C | C | I | I | I |
| Define purpose and minimum fields | C | C | C | C | A/R | I | C |
| Approve access and permitted use | A | R | C | C | C | I | I |
| Approve restricted/strategic material | A | C | A | A | C | I | I |
| Prepare sanitized package and manifest | C | A/R | C | I | C | C | I |
| Configure isolation and access | I | C | A | I | C | R | I |
| Validate extraction and knowledge | C | C | I | I | A | I | R |
| Correct source-derived records | A | R | I | I | C | C | R |
| Revoke, retain, or delete | A | R | C | C | I | R | I |
| Investigate incident and stop processing | I | C | A | C | C | R | I |

One person may hold multiple roles in a small pilot, but accountability,
approval evidence, and separation of reviewer from automated output remain.

## Special Data Rules

- **Formulations, inventions, unpublished R&D, process parameters, and failure
  knowledge:** classify at least Restricted, or Strategic when disclosure could
  materially harm the company. Do not include composition or enabling detail in
  a pilot unless the owner and Legal/IP explicitly approve the exact use.
- **Customer, supplier, pricing, tender, and contract data:** contractual rights
  and confidentiality control use. De-identification does not cancel a contract.
- **Personal and employee data:** apply minimization, lawful-basis, transparency,
  access, retention, and rights analysis. Sensitive personal data is Restricted.
- **Voice, meetings, email, and tacit knowledge:** never assume permission from
  attendance, employment, device access, or recording capability. Confirm notice,
  consent or other lawful basis, labor/works-council obligations, purpose, and
  recording/transcription retention before capture.
- **Licensed standards, literature, test reports, and supplier documents:**
  verify copyright, database, redistribution, and machine-processing rights.
- **Safety and regulatory records:** preserve authoritative evidence and route
  interpretations to qualified humans; SmartCoat output is not certification.

## Permitted-Use Metadata

Every approved package records at least:

| Field | Required meaning |
|---|---|
| `organization_id` / `site_scope` | Isolation and residency boundary |
| `source_id`, owner, steward | Accountable identity without secret content |
| `classification` and overlays | Base class plus personal, trade-secret, contractual, safety flags |
| `collection_basis` | How and under what authority the source was obtained |
| `allowed_purposes` | Separate booleans for inventory, retrieval, analytics, training, external sharing |
| `prohibited_purposes` | Explicit exclusions, including competitive or employee-evaluation uses |
| `approved_users_services_models` | Need-to-know principals and processor/model boundary |
| `geography` / `transfer_rules` | Storage, processing, and cross-border limits |
| `effective_at`, `expires_at` | Approval validity window |
| `retention_rule`, `deletion_authority` | Source and derived-artifact lifecycle |
| `evidence_reference` | Approval, contract, consent, or legal-review reference |
| `review_status` / `reviewer` | Human validation state for extracted knowledge |

Unknown values are not permissive defaults. A material mismatch produces
`blocked`, not a warning-only state.

## Ingestion Approval Workflow

1. Register generalized metadata without opening or copying raw content.
2. Identify owner, steward, system owner, processor, and organization/site.
3. Classify content and overlays under the classification policy.
4. Define one bounded use case, minimum fields, recipients, models, and outputs.
5. Record rights, contract, consent/lawful-basis, and professional-review evidence.
6. Define isolation, access, logging, retention, correction, deletion, and stop controls.
7. Prepare a synthetic or explicitly approved sanitized sample and schema mapping.
8. Security/privacy, Legal/IP, data owner, and pilot owner approve as required.
9. Platform operator verifies manifest-to-configuration consistency before ingestion.
10. Human reviewers validate extracted objects; measure corrections and incidents.
11. Reassess on expiry, purpose/model/schema change, incident, owner revocation, or scale-up.

Rejection at any gate preserves the request and reason for audit but does not
copy source content into SmartCoat.

## Retention, Correction, Deletion, and Audit

- Record approvals, access, transformations, review decisions, exports, failures,
  and deletion outcomes with tamper-evident identifiers and timestamps.
- Keep raw, normalized, derived, embedding/index, prompt/log, and model-artifact
  retention rules explicit; deletion must address every applicable derivative.
- Preserve source corrections, supersession, uncertainty, and reviewer history.
- Legal holds require authorized legal direction and must not silently expand use.
- Periodically review access and approvals; remove stale principals and expired data.

## Incident and Emergency Stop

Any suspected unauthorized access, tenant crossover, secret exposure, consent
failure, prohibited model use, unsafe recommendation, or uncontrolled export
triggers: stop affected ingestion/retrieval/automation; preserve minimal evidence;
notify Security and accountable owners privately; contain credentials and access;
assess notification/deletion obligations; document restart authority. Only the
designated incident authority may resume processing after controls are verified.

## Pilot Minimum Governance Gate

The pilot cannot process real data until all are evidenced:

- [ ] one organization/site boundary and approved sanitized package
- [ ] owner, steward, source system, confidentiality, and overlay classification
- [ ] separate decisions for retrieval, analytics, training, and external sharing
- [ ] no raw formulation, invention, voice, meeting, or personal data unless
      specifically necessary and professionally reviewed
- [ ] need-to-know roles, processor/model list, retention/deletion, and audit plan
- [ ] provenance mapping and authorized human reviewers
- [ ] autonomy level, high-impact approval gates, incident contact, and stop test
- [ ] baseline, success metrics, expiry date, and post-pilot disposition

## Professional-Review Questions

Before real-data approval, qualified professionals must determine: applicable
privacy/employment and works-council law; lawful basis and notice/consent; trade-
secret and invention ownership; customer/supplier contract rights; copyright and
database rights; cross-border transfer and processor terms; regulated retention,
deletion, incident-notification, product-safety, and recordkeeping duties; whether
an AI system or use is legally high risk; and required impact assessments.

