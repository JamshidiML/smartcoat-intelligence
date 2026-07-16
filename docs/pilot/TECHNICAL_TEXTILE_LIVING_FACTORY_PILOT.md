# Technical Textile Living-Factory Pilot

Status: Blueprint for Release 2.1 planning; not production-ready

## Pilot Thesis

SmartCoat can make one industrial learning loop more complete, traceable, and
reusable: connect an approved customer/engineering requirement to relevant prior
lessons, capture a new R&D experiment or failure, obtain human approval, and
retrieve that approved knowledge for a later decision.

The pilot tests this thesis. It does not claim a complete Living Factory,
autonomous formulation, production control, ERP integration, or enterprise-wide
intelligence. Current repository maturity is backend foundation; usable capture,
human review UI, AI extraction, semantic retrieval, production security, and the
real pilot are not yet implemented.

## Why Technical Textiles First

Technical-textile product development exposes the platform thesis in a bounded
domain: customer performance requirements, fabrics, coatings, process conditions,
tests, failures, suppliers, quality evidence, and production observations must be
connected across functions. Experiments are evidence-rich and repeated learning
has measurable cost. The domain also tests reusable platform primitives without
requiring every enterprise system.

## Boundary

Recommended starting boundary:

- one consenting company, one approved site, one product-development theme
- 6-10 named users across Sales/Technical Service, R&D, Laboratory/Quality, and
  one management sponsor; Production and Materials/Supplier roles are consulted
- 20-40 sanitized historical knowledge records plus 10-20 new pilot captures
- 6-8 operational weeks after technical and governance readiness
- approved metadata, requirement abstractions, project/trial references, test
  results, observations, failures, lessons, and decisions only
- L2 recommendation support; every knowledge promotion and consequential
  decision remains human-approved

Packaging/logistics participates only when packaging, storage, transport, or
handling materially affects the selected performance problem. The pilot does not
write to production, ERP, supplier, customer, certification, or external systems.

## Participating Functions

| Function | Pilot contribution | Human authority retained |
|---|---|---|
| Sales / customer requirements | Sanitized requirement and intended-use context | Confirms interpretation and customer disclosure boundary |
| R&D / product development | Experiment, observation, hypothesis, lesson, next action | Owns technical capture and recommendation decisions |
| Materials / suppliers | Approved material references and constraints | Approves source rights and substitution claims |
| Laboratory / quality | Method, condition, result, unit, evidence, disposition context | Validates test meaning and quality status |
| Production | Approved trial context and observations | Approves production truth; no machine action |
| Packaging / logistics | Handling constraints where causal/relevant | Approves logistics interpretation |
| Management / decision layer | Scope, resources, baseline, risk and scale decision | Owns go/no-go and investment decision |

## First End-to-End Demonstrator

**Name:** Requirement-to-reviewed-learning loop

**Scenario:** A product-development engineer receives a generalized performance
requirement and needs to understand prior evidence before planning a test. After
the test, the engineer captures an observation or failure and makes it reusable.

### Actors

- Technical Service or project owner supplies the approved requirement abstraction.
- R&D engineer searches, reviews evidence, captures the new work, and decides next action.
- Laboratory/Quality reviewer validates method, result, units, and evidence.
- Data steward confirms provenance, classification, and permitted use.
- Pilot observer records baseline and assisted metrics without deciding technical truth.

### Inputs

- sanitized requirement and project identifier
- approved prior project, experiment, observation, failure, and lesson records
- material/fabric/formulation **references**, not composition unless separately approved
- normalized test result with method, condition, unit/basis, evidence reference
- provenance, review status, confidentiality, purpose, owner, and timestamps

### Workflow and Approval Points

1. **Authorize session:** verify organization, role, source purposes, and expiry.
2. **Frame requirement:** user confirms requirement, use environment, constraints,
   success measure, and unknowns. Customer meaning remains human-approved.
3. **Retrieve context:** system presents prior reviewed records with evidence and
   relevance rationale. The engineer selects useful items; retrieval is not truth.
4. **Plan:** system flags missing information and drafts questions or a test-plan
   suggestion. R&D/Quality approves any plan; no automated commitment or actuation.
5. **Capture outcome:** user enters simple text/form input and evidence references.
   Assistance structures facts, observations, hypotheses, results, and recommendations.
6. **Review:** engineer corrects the draft; Quality validates test semantics;
   uncertain or conflicting fields remain explicit. No approval by silence.
7. **Promote and store:** authorized reviewer approves; audit event records who,
   what, evidence, correction, time, and source. Drafts cannot masquerade as trusted.
8. **Reuse test:** another authorized user later retrieves the approved lesson for
   a comparable generalized question and records relevance and decision influence.

### Outputs

- requirement/context record and missing-information list
- evidence-backed retrieval set and user relevance judgments
- human-approved experiment/observation/lesson object with provenance
- review/correction history and audit trail
- human-owned next action or test-plan decision
- metric events and a claim/evidence package

## Baseline Versus Assisted Process

| Stage | Current/manual baseline | SmartCoat-assisted condition |
|---|---|---|
| Find prior work | Search folders, spreadsheets, email, or ask colleagues | Search approved reviewed records with evidence and filters |
| Reconstruct context | Manually connect requirement, trial, test, and lesson | Present linked context and visibly missing fields |
| Capture result | Free-form notes/report assembled later | Guided draft separates fact, observation, hypothesis, recommendation |
| Validate | Informal review and version exchange | Named field-level correction and approval state |
| Reuse | Memory and repeated document search | Retrieve approved lesson; record relevance and influence |

Use the same scenario set, user cohort, time convention, and completion rubric in
baseline and assisted observations. Baseline values are measured before setting
improvement claims; they are not invented in this blueprint.

## Controlled Data and Permission Gate

Before pilot access, approve the exact company/site, source package, fields,
users, processors/models, retrieval/analytics purposes, retention, deletion,
audit, incident stop, and evidence owners. Model training and external sharing
default to denied. Voice, meeting/email, personal, customer-identifying, price,
contract, formulation composition, invention, and raw production data are
excluded unless essential and separately reviewed. Synthetic rehearsal precedes
any approved sanitized data.

## Delivery Gates

| Gate | Required evidence | Stop condition |
|---|---|---|
| G0 Sponsor and workflow | Named owner, users, scenario, baseline protocol | No accountable owner or decision |
| G1 Governance | Approved package, purposes, isolation, retention/deletion | Permission, consent, contract, or IP uncertainty |
| G2 Product readiness | Human-friendly capture/review/retrieval, audit, access controls | Manual JSON, unreviewed trust, tenant/security gap |
| G3 Synthetic rehearsal | End-to-end test, metric events, stop/deletion test | Critical defect or unmeasurable metric |
| G4 Limited live pilot | Training, support, incident channel, rollback | Safety/security incident or unacceptable error |
| G5 Evidence review | Metric analysis, limitations, claim ledger, user evidence | Selective reporting or insufficient sample |

## Honest Capability Gaps

The baseline does not yet provide the required user interface, AI-assisted
extraction, semantic retrieval, complete lifecycle/audit behavior, production
IAM, tenant isolation proof, governed ingestion, deletion verification, or pilot
telemetry. Releases 1.8-2.0 and independent governance/security review must close
these gaps before G3/G4. Documentation alone does not make the pilot executable.

## Scale-Out Path

1. Repeat the same workflow at a second project theme in the same site.
2. Prove isolated configuration at a second site/company without shared records.
3. Add one adjacent workflow only after separate data, risk, and value approval.
4. Generalize reusable capabilities: organization boundary, identity, provenance,
   review, retrieval, metrics, and audit.
5. Package industry extensions separately: textile/material/process/test language,
   schemas, constraints, methods, and regulatory context.
6. Enter another industry with a new domain authority, canonical mapping,
   governance review, synthetic rehearsal, and measured first learning loop.

