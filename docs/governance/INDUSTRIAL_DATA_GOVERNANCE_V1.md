# Industrial Data Governance V1

Policy schema version: `smartcoat-governance-v1.1-draft`

Approval status: Proposed; not yet effective

Effective date: Pending named governance approval

Review cadence: Before every pilot phase, on material change, and at least annually

Supersession: A later approved policy must name this version and preserve its decision history

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

## Canonical Governance Vocabulary

This proposal is the Cycle 3 source contract for downstream schemas, ingestion,
readiness, and pilot documents. Machine values are lowercase and stable within
this schema version.

- operational authority: `l0_manual`, `l1_assist`, `l2_recommend`,
  `l3_supervised_action`, `l4_bounded_automation`
- confidentiality: `public`, `internal`, `confidential`, `restricted`, `strategic`
- permitted-use purposes: `inventory`, `retrieval`, `analytics`, `human_review`,
  `model_training`, `external_sharing`
- purpose decision: `not_requested`, `in_review`, `approved`, `denied`, `expired`,
  `revoked`
- human-approval requirement: `not_required`, `required_single`, `required_joint`
- human-approval status: `not_requested`, `pending`, `approved`, `rejected`,
  `expired`, `revoked`

L0-L4 is the only current operational-authority model. Future closed-loop factory
control remains a North-Star research and architecture horizon; it is not an
active competing A0-A5 taxonomy and grants no present authority.

Canonical governance metadata includes `governance_schema_version`,
`policy_version`, `approval_status`, `effective_at`, `expires_at`, `supersedes`,
`approved_by`, `reviewed_at`, and `next_review_at`. Unknown or absent values fail
closed for any operation that requires approval.

```json
{
  "governance_schema_version": "smartcoat-governance-v1.1-draft",
  "confidentiality": "restricted",
  "operational_authority": "l2_recommend",
  "purpose_decisions": {
    "inventory": "approved",
    "retrieval": "approved",
    "analytics": "in_review",
    "human_review": "approved",
    "model_training": "denied",
    "external_sharing": "denied"
  },
  "human_approval_requirement": "required_single",
  "human_approval_status": "pending"
}
```

This JSON is a compact vocabulary proposal, not IAM configuration or verified
authorization.

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

R = responsible, A = the single accountable role, M = a mandatory joint approver,
C = consulted, I = informed. Multiple `M` roles mean every listed approval is
required; they do not create multiple RACI-accountable owners.

| Activity | Data owner | Data steward | Security/privacy | Legal/IP | Pilot owner | Platform operator | Human reviewer |
|---|---|---|---|---|---|---|---|
| Classify source and identify rights | A | R | C | C | I | I | I |
| Define purpose and minimum fields | C | C | C | C | A/R | I | C |
| Approve access and permitted use | A | R | C | C | C | I | I |
| Approve restricted/strategic material | A | C | M | M | C | I | I |
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
  the applicable lawful basis, notice, labor/works-council obligations, purpose,
  and recording/transcription retention before capture. Consent is one possible
  basis, not an assumed default; the professional determination and evidence must
  be recorded.
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
| `purpose_decisions` | Separate canonical decisions for inventory, retrieval, analytics, human review, model training, external sharing |
| `prohibited_purposes` | Explicit exclusions, including competitive or employee-evaluation uses |
| `approved_users_services_models` | Need-to-know principals and processor/model boundary |
| `geography` / `transfer_rules` | Storage, processing, and cross-border limits |
| `effective_at`, `expires_at` | Approval validity window |
| `retention_rule`, `deletion_authority` | Source and derived-artifact lifecycle |
| `evidence_reference` | Approval, contract, consent, or legal-review reference |
| `human_approval_requirement` / `human_approval_status` | Canonical approval requirement and current decision |
| governance/version fields | Schema/policy version, status, effective/expiry, supersession, approval and review timestamps |

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

## Cross-Thread Contract Targets

The following owned artifacts must consume this vocabulary on their own branches:
T01 Living Industry model, T05 technical-textile schemas, T06 readiness register,
T08 ingestion manifest, and T09 pilot blueprint. Cross-references are integration
targets, not evidence that those draft PRs are already accepted or merged.
