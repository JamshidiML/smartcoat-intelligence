# Confidentiality and Access Classification

Policy version: `confidentiality-v1.1-draft`

Approval status: Proposed; not yet effective

Effective date: Pending named governance approval

Review cadence: Before each pilot phase, on classification change, and annually

Supersession: Preserve prior labels and record the replacing approved version

This classification is **not legal advice**. It is a conservative operational
baseline; contracts, law, owners, and security review may impose stricter rules.

## Classification Levels

| Level | Definition and examples | Default access | SmartCoat default |
|---|---|---|---|
| Public (`public`) | Intentionally published, redistribution permitted | Authenticated or public as approved | May ingest after source/license check |
| Internal (`internal`) | Routine non-public operations with limited harm | Organization members with business need | Organization-isolated retrieval; no training or sharing by default |
| Confidential (`confidential`) | Customer/supplier requirements, ordinary R&D, test and quality records | Named roles and approved services | Bounded pilot only with owner approval |
| Restricted (`restricted`) | Personal data, employee communications, contracts, prices, unpublished inventions, detailed process or formulation data | Explicit named principals; monitored access | Excluded unless essential and separately approved |
| Strategic (`strategic`) | Enabling formulations, critical trade secrets, patent strategy, acquisition or existential-risk information | Executive/owner-approved compartment | Excluded from first pilot by default |

Classify to the highest applicable level. Derivatives inherit the source level
unless an owner-approved assessment demonstrates irreversible risk reduction.
`highly_confidential` is not a canonical value; existing drafts must map it to
`restricted` or `strategic` through documented owner/security review.

## Mandatory Overlays

Record overlays independently because one base label is not enough:

- personal data; sensitive personal data; employee/voice/meeting content
- trade secret, invention, unpublished R&D, export-control candidate
- customer, supplier, contractual, pricing, licensed/copyrighted material
- safety, regulatory, legal privilege or litigation hold
- source jurisdiction, residency, cross-border and retention constraints

Anonymization requires documented re-identification-risk testing. Pseudonymized
data remains personal/confidential and its key is separately protected. Removing
names does not remove trade-secret, contractual, copyright, or linkage risk.

## Access Decision

Access requires all of: verified identity; approved organization; role and need;
purpose match; classification clearance; valid time window; approved service and
model; permitted geography; auditability. Deny on any missing condition.

| Action | Internal | Confidential | Restricted | Strategic |
|---|---|---|---|---|
| Inventory metadata | Owner/steward | Owner/steward | Owner plus Security | Executive owner plus Security |
| Retrieval | Need-to-know | Named role | Explicit case approval | Normally prohibited in pilot |
| Analytics | Purpose approval | Owner approval | Security/privacy/Legal as applicable | Normally prohibited in pilot |
| Model training | Separate approval | Separate owner approval | Normally prohibited | Prohibited by default |
| External sharing | Separate approval | Contract/owner review | Legal/Security and owner | Prohibited by default |

Model providers, subprocessors, support access, telemetry, backups, exports,
embeddings, caches, and logs are part of the access boundary, not exceptions.

## Multi-Tenant and Cross-Industry Rules

- Use organization-scoped authorization and storage/index namespaces by default.
- Never retrieve, compare, train across, or expose one company from another
  company's context without explicit authority from every affected owner and
  professional review.
- Generalized industry learning must be derived through an approved process that
  prevents memorization, attribution, reconstruction, and competitive disclosure.
- Site-level sharing inside one company still requires purpose and need-to-know review.
- Tenant-isolation failure is a critical incident and invokes emergency stop.

## Handling Rules

Labels and permitted-use metadata travel with copies and derivatives. Exports
retain labels and expiry. Access is reviewed at role/source/model changes and at
least at the pilot review cadence. Revocation disables new use immediately and
starts the approved deletion or legal-hold workflow. Public issue trackers and
source repositories never receive confidential source content or secrets.
