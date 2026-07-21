# Technical Textile Data-Source Inventory

Status: Controlled discovery framework

Issue: #20

## Purpose

This framework inventories technical-textile information flows without copying,
opening, uploading, or ingesting raw confidential files. Discovery records that
a source family exists; it does not grant permission to access or process it.

## Non-Negotiable Boundary

A source may enter controlled pilot preparation only when it has:

1. an accountable data owner and steward
2. confidentiality and personal-data classification
3. documented legal/contractual permission for each intended use
4. approved organization/site and access boundary
5. retention, correction, deletion, and incident contacts
6. a sanitized or synthetic assessment sample

Unknown permission means **do not ingest**. Business value never overrides this
gate.

## Source Taxonomy

| Family | Typical information | Pilot value | Principal risks |
|---|---|---|---|
| R&D projects and reports | Objectives, hypotheses, trials, outcomes, failures, lessons | Reuse prior work and reduce repeated failure | Inventions, unpublished R&D, employee authorship |
| Formulations and recipe versions | Version references, ingredients, process logic, rationale | Trace decisions and experiment context | Trade secrets and product IP |
| Raw-material TDS/SDS | Properties, handling, regulatory and supplier references | Material context and evidence | License terms, supplier confidentiality |
| Fabric/textile specifications | Construction, substrate, treatment, target properties | Connect requirements, trials, and performance | Customer/product confidentiality |
| QC spreadsheets and PDFs | Test methods, results, dispositions, trends | Evidence and quality learning | Product/customer identification, inconsistent units |
| Production batches/process records | Batch, machine, settings, deviations, outcomes | Link R&D to production behavior | Raw production data, safety, employee attribution |
| ERP records | Material, supplier, inventory, order, lead-time references | Operational context and supply risk | Prices, contracts, customer/supplier confidentiality |
| Sales/customer/application requirements | Requirements, use environment, complaints, commitments | Requirement engineering and traceability | Customer identities, contracts, personal data |
| Supplier/logistics information | Availability, MOQ, lead time, logistics, alternatives | Resilience and substitution context | Commercial terms and contractual limits |
| Laboratory/fire/thermal tests | Method, conditions, results, evidence | Validate performance and decisions | Certification and test-license constraints |
| Machine/manual/maintenance sources | Equipment limits, setup, faults, maintenance history | Process context and troubleshooting | Safety, OEM rights, employee records |
| Defect/product images | Surface state, defect evidence, labels | Root-cause support and future vision | Customer/product identity and metadata leakage |
| Meetings, email, voice, tacit knowledge | Decisions, reasoning, exceptions, lessons | Preserve context not captured elsewhere | Consent, surveillance, personal data, privilege |
| Standards/regulations/certifications | Requirements, versions, applicability | Compliance context | Copyright/license and jurisdiction |
| Scientific literature/patents | External evidence and prior art | Technical currency and hypothesis support | License, citation, territorial/status ambiguity |

## Register Structure

The canonical inventory row is defined in
`docs/data/templates/DATA_SOURCE_REGISTER_TEMPLATE.csv`. Key groups are:

- identity: source ID, family, generalized name, organization/site
- assessment identity: assessment ID, scoring-model version, timestamp,
  assessor role, evidence references, and reassessment lineage
- accountability: owner, steward, system owner, contact role
- governance: canonical confidentiality; tri-state personal, employee, customer,
  supplier/commercial, and trade-secret sensitivity; separate decisions for all
  six canonical purposes; access boundary, retention, deletion authority
- shape: format, structure, volume band, history band, language
- quality: completeness, consistency, identifiers, timestamps, units,
  provenance, duplicate risk
- effort: extraction difficulty, mapping effort, dependencies
- value: business value, pilot relevance, use case, expected outcome
- disposition: readiness ratings, gate status, priority, next action, review date

The register stores generalized descriptions and metadata only. It must not
contain raw filenames, customer/supplier identities, formulas, prices, personal
data, or copied source content.

## Discovery-to-Pilot Workflow

```text
Discover source family
  -> record generalized metadata
  -> identify owner and steward
  -> classify confidentiality/personal data
  -> document intended purposes
  -> obtain legal/contractual and owner approval
  -> assess sanitized sample
  -> score readiness and risk
  -> map to pilot schema
  -> approve bounded package
  -> ingest only through controlled workflow
```

Every transition records reviewer, date, evidence reference, and unresolved
questions. A rejected or expired approval returns the source to `blocked`.

Canonical confidentiality values are `public`, `internal`, `confidential`,
`restricted`, and `strategic`. Each sensitivity indicator is `unknown`, `none`,
or `present`; `unknown` is never interpreted as absence. Each purpose decision
uses `not_requested`, `in_review`, `approved`, `denied`, `expired`, or `revoked`
for `inventory`, `retrieval`, `analytics`, `human_review`, `model_training`, and
`external_sharing`.

## Synthetic Example Interpretations

The CSV template includes three explicitly synthetic rows:

- a generalized R&D trial-summary register that is valuable but still blocked
  because contractual permission has not been confirmed
- a synthetic laboratory-result export with explicit test-only permission and
  stronger identifier/unit readiness
- a high-scoring synthetic quality archive that remains blocked because
  analytics is an intended purpose whose decision is still `in_review`

They demonstrate that readiness and permission are independent.

## Recommended First Controlled Dataset Package

Prepare a small, sanitized package around one measurable learning loop:

- 5-10 generalized completed R&D projects
- approved customer-requirement abstractions with identities removed
- trial/sample/formulation **references**; no proprietary composition unless
  separately approved
- normalized test-result extracts with method, unit, condition, and evidence references
- reviewed observations, failures, root-cause candidates, decisions, and lessons
- one data dictionary, source-to-canonical mapping, permission record, and
  package manifest

Recommended first use: retrieve prior evidence and lessons for a new generalized
requirement, identify missing information, and produce a human-reviewed test-plan
recommendation. Baseline and assisted time, retrieval relevance, correction
rate, evidence coverage, and lesson reuse are measurable.

## Missing Information for Founder/Domain Owner

1. Which organization and site owns each source family?
2. Who can authorize inventory, retrieval, analytics, human-review,
   model-training, and external-sharing purposes separately?
3. Which sources contain personal data, employee voice, customer identity, or supplier terms?
4. Which contracts or licenses restrict TDS/SDS, standards, literature, ERP, or customer data?
5. What retention and deletion obligations apply?
6. Which identifiers reliably connect projects, trials, samples, materials, batches, tests, and decisions?
7. Which units and method versions are authoritative?
8. How are corrected or superseded records represented?
9. What sanitized package can be created without exposing formulas, prices, or identities?
10. Which pilot decision and metric justify the first approved ingestion?

## Coverage and Gaps

This inventory aligns with `SECURITY.md`, domain source families, information
governance/provenance/quality concepts, project history, and Decision D-014's
controlled measurable pilot. It does not determine legal basis, approve access,
perform schema mapping, or ingest data.

Readiness model `smartcoat-readiness-v1.1-draft`, its weights, and its bands are
pilot hypotheses. A later calibration creates a new version and preserves every
prior assessment, score, evidence reference, and reassessment reason.
