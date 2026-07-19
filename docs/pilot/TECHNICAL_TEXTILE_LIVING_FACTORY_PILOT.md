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

The following numbers are **planning assumptions**, not fixed product
requirements or approved commitments. The sponsor, Data Owner, domain authority,
and delivery lead must approve them after workflow discovery, baseline design,
data-readiness assessment, and product-capacity review:

- one consenting company, one approved site, one product-development theme
- 6-10 named users across Sales/Technical Service, R&D, Laboratory/Quality, and
  one management sponsor; Production and Materials/Supplier roles are consulted
- 20-40 sanitized historical knowledge records plus 10-20 new pilot captures
- 6-8 operational weeks after technical and governance readiness
- approved metadata, requirement abstractions, project/trial references, test
  results, observations, failures, lessons, and decisions only
- canonical `l2_assisted_recommendation`; every knowledge promotion and
  consequential decision remains human-approved

Packaging/logistics participates only when packaging, storage, transport, or
handling materially affects the selected performance problem. The pilot does not
write to production, ERP, supplier, customer, certification, or external systems.

### Product Proof Before Platform Proof

The North Star names two collaborating technical-textile companies as the wider
proof domain. Phase 1 deliberately starts with one company/site because product
workflow value, permission, and evidence quality can be tested without adding
cross-company identity, isolation, interoperability, contracting, and joint-data
governance variables at the same time.

| Phase | Question tested | Boundary | Entry gate | Evidence allowed |
|---|---|---|---|---|
| 1: single-company product proof | Does one governed learning loop help its intended users? | One company, one site, one theme | G0-G4 plus approved product build and data package | Workflow, quality, retrieval, reuse, user, and guardrail evidence for that boundary only |
| 2: multi-company platform proof | Can the reusable platform isolate and interoperate across collaborating companies? | Two separately governed companies; no shared records by default | Phase 1 exit plus independent tenant-isolation, legal, security, interoperability, and joint-controller/processor decisions | Isolation tests, configuration effort, permitted exchange, and company-specific value; no pooled-data claim by implication |

Phase 1 success does not prove Industry-Hub interoperability, cross-company
analytics, shared model training, or commercial scale. Phase 2 is a separate
gated experiment, not automatic pilot expansion.

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

## Capability-to-Release Dependency Map

`Current` means the Release 1.7 backend foundation, not a pilot-ready product.
Every row must satisfy its product, governance/security, and external dependency
before the corresponding step can enter a live pilot.

| Pilot step | Current / 1.7 | Release 1.8 dependency | Release 1.9 dependency | Release 2.0 dependency | Governance/security prerequisite | External blocker |
|---|---|---|---|---|---|---|
| 1. Authorize session | Basic API/auth concepts only | Tenant-aware persistence and audit events | Role-aware session UI | None required | Production IAM, tenant isolation, purpose/expiry enforcement | Named users, approved roles, company security review |
| 2. Frame requirement | Domain/API foundations only | Requirement/context lifecycle and evidence links | Guided capture and human confirmation | Adaptive questions and uncertainty | Approved fields, customer disclosure boundary, provenance | Sponsor-selected workflow and sanitized requirement set |
| 3. Retrieve context | Basic list/get behavior only | Filtered, paginated reviewed records | Evidence/status browsing UI | Semantic retrieval and relevance rationale | Purpose-scoped access, reviewed-only filter, audit | Approved historical package with sufficient coverage |
| 4. Plan | No recommendation capability | Persist missing-information and decision records | Review/approval interface | Missing-information detection and assisted recommendation | `l2_assisted_recommendation`, human approval, no actuation | Domain-approved rubric and test-planning authority |
| 5. Capture outcome | Manual API input only | Experiment/result/lesson models, lifecycle, provenance | Usable non-JSON capture UI | Extraction, confidence, adaptive follow-up | Source permission, classification, evidence handling | Approved new captures and trained users |
| 6. Review | Partial status concepts only | Review lifecycle, correction history, audit | Named reviewer workflow | Field-level uncertainty support | Segregation of duties and quality authority | Available R&D/Quality reviewers and agreed rubric |
| 7. Promote and store | Development persistence only | Governed persistence and immutable audit evidence | Explicit promotion action and status visibility | No autonomous promotion | Authorization, retention/deletion, rollback, incident stop | Production readiness and approved retention package |
| 8. Reuse test | Basic retrieval only | Decision/lesson links and metric events | Relevance/influence capture UI | Related lessons and semantic retrieval | Same-purpose access and evidence visibility | Later comparable scenario and independent observer |

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

## Cross-Thread Contract Dependencies

Integration review must reconcile this blueprint with these proposed Release 1.7
artifacts before implementation claims are made:

- T05: `docs/data/TECHNICAL_TEXTILE_CANONICAL_SCHEMA_V1.md` for platform/Hub
  object boundaries and explicit unknown/conflicting states;
- T06: `docs/data/TECHNICAL_TEXTILE_DATA_SOURCE_INVENTORY.md` and
  `docs/data/DATA_READINESS_MATRIX.md` for source-specific readiness evidence;
- T07: `docs/governance/INDUSTRIAL_DATA_GOVERNANCE_V1.md` and
  `docs/governance/HUMAN_OVERSIGHT_AND_AUTONOMY_LEVELS.md` for canonical
  purpose decisions and `l2_assisted_recommendation`;
- T08: `docs/ingestion/INGESTION_FOUNDATION_V1.md` for metadata-only source
  registration, duplicate identity, and the non-authorization boundary.

These are branch-level proposals until integrated. A cross-reference is not
evidence that a capability is implemented or approved.

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
