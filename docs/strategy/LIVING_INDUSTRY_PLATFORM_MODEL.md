# Living Industry Platform Model

Version: 1.0

Status: Proposed clarification of the active North Star

Issue: #15

## One-Sentence Definition

SmartCoat is a horizontal, governed Enterprise Intelligence mother platform
that turns each participating industrial company into a connected and learning
system by linking data, knowledge, context, intelligence, decisions, execution,
outcomes, and feedback through reusable Industry Hubs and company-specific
instances.

## Interpretation Boundary

This document clarifies the active vision in
`docs/strategy/SMARTCOAT_NORTH_STAR.md`; it does not replace approved
architecture or expand the active Release 1.7 implementation scope.

The following statements have different planning horizons:

| Horizon | Meaning | Current implication |
|---|---|---|
| North Star | Long-term direction for a Living Industry platform | Guides architecture and sequencing; not a claim of deployed capability. |
| Mother platform | Reusable horizontal capabilities and contracts | Must stay industry-agnostic and governed. |
| Industry Hub | Reusable specialization for one industry | Technical textiles are the first proof Hub. |
| Company instance | Isolated adaptation for one organization | Applies company identity, data, policy, process, and integration context. |
| Pilot | Controlled experiment with approved data and measures | Proves selected loops, not the whole vision. |
| MVP | Smallest usable product increment | Knowledge Capture is the active first vertical slice. |
| Release 1.7 | Project reset and engineering baseline | Improves coherence and reliability; it is not a product-autonomy release. |

## Three-Level Platform Model

### 1. Mother Platform

The mother platform supplies reusable capabilities that should not encode a
single industry's terminology or a single company's operating rules:

1. identity, tenancy, authorization, confidentiality, and auditability
2. governed source registration and ingestion
3. canonical Enterprise Objects, Knowledge Objects, Decision Objects, Enterprise
   Events, Evidence, Provenance, Context, and lifecycle semantics
4. data, event, and integration contracts
5. search, graph, reasoning, analytics, simulation, and evaluation services
6. agent orchestration, tool permissions, and human-approval controls
7. decision, execution, outcome, and learning-loop support
8. observability, deployment, reliability, and platform governance

This aligns with the layered platform described in
`architecture/handbook/09_Platform/01_Platform_Architecture_Overview.md` and
the canonical information categories in
`architecture/handbook/04_Information/01_Enterprise_Information_Model.md`.

### 2. Industry Hub

An Industry Hub is a governed specialization package that reuses the mother
platform and adds the common language and constraints of an industry.

Each Hub may define:

- an industry ontology and canonical extensions
- standard processes, events, tests, units, and evidence expectations
- regulations, standards, hazards, and approval patterns
- reusable integrations and source mappings
- industry evaluation sets and quality rules
- specialized reasoning, agent skills, and user workflows
- benchmark metrics and reference scenarios

A Hub may extend platform contracts but must not silently redefine them. New
industry concepts require traceable mappings to the canonical platform model.

### 3. Company Instance

A company instance applies an Industry Hub to one isolated organization. It
adds configuration and governed knowledge rather than forking the platform.

Company adaptation includes:

- organization and site boundaries
- company vocabulary mapped to Hub and platform terms
- roles, permissions, confidentiality, retention, and permitted-use rules
- products, customers, suppliers, machines, materials, and process context
- company objectives, quality limits, economics, risk appetite, and workflows
- approved source connections and data mappings
- human approval authorities and autonomy ceilings
- company-specific evaluation evidence and feedback

Company data is isolated by default. Cross-company learning or model training
requires a separately approved purpose, lawful basis, technical isolation
design, and evidence that confidential information cannot leak.

## Reusable Industry Hub Contract

Every Industry Hub should declare the following contract before production use:

| Contract area | Required declaration |
|---|---|
| Identity | Hub ID, version, owner, and supported company-instance versions. |
| Vocabulary | Terms, definitions, aliases, and mappings to platform language. |
| Information | Industry entities, relationships, events, units, and extension rules. |
| Evidence | Acceptable source classes, provenance minimums, and quality thresholds. |
| Governance | Confidentiality defaults, permitted uses, human approvals, and prohibited actions. |
| Intelligence | Supported analyses, assumptions, evaluation evidence, and uncertainty behavior. |
| Workflows | Actors, states, inputs, outputs, exceptions, and audit events. |
| Integration | Supported source/target contracts and failure behavior. |
| Evaluation | Test scenarios, safety checks, quality metrics, and release gates. |
| Evolution | Compatibility, migration, deprecation, and rollback policy. |

## Enterprise Nervous System and Learning Loop

The platform is a nervous system only when it connects sensing to governed
learning. A database, chatbot, agent, or integration alone does not satisfy the
model.

```text
Sources and signals
    -> governed data and Enterprise Events
    -> Enterprise Knowledge and Evidence
    -> Enterprise Context and relationships
    -> intelligence, alternatives, risk, and confidence
    -> recommendation and human/automated decision
    -> authorized workflow, software, agent, machine, or robot execution
    -> observed outcome and feedback
    -> reviewed learning and updated knowledge
```

The loop follows the Enterprise Intelligence and Decision Architecture in:

- `architecture/handbook/01_Foundation/11_Enterprise_Intelligence_Model.md`
- `architecture/reference_models/RM-01_Enterprise_Intelligence.md`
- `architecture/handbook/06_Decision/01_Decision_Architecture_Overview.md`
- `architecture/reference_models/RM-04_Enterprise_Capability_Model.md`

### Layer Responsibilities

| Layer | Responsibility | Must preserve |
|---|---|---|
| Sensing | Receive human, software, document, machine, and external signals. | Source identity, time, authorization, and raw/derived distinction. |
| Data | Represent observations and records consistently. | Tenancy, units, quality, uncertainty, and provenance. |
| Knowledge | Create reusable understanding from evidence. | Lifecycle, review status, ownership, confidence, and contradiction. |
| Context | Connect objects, constraints, history, objectives, and dependencies. | Relationship provenance and temporal validity. |
| Intelligence | Search, analyze, infer, simulate, optimize, and compare. | Assumptions, limitations, evidence, uncertainty, and evaluation. |
| Decision | Record alternatives, rationale, risk, approval, and commitment. | Accountable owner and human-approval requirement. |
| Execution | Coordinate authorized people, workflows, software, agents, and equipment. | Permission, rollback, observability, and emergency stop. |
| Feedback | Observe outcomes and deviations. | Baseline, measurement method, timing, and causal caution. |
| Learning | Review outcomes and update reusable knowledge. | Human validation for trusted or high-impact learning. |

## Human Governance and Autonomy

Human oversight increases with impact, uncertainty, irreversibility, safety,
legal consequence, confidentiality, and strategic importance. Autonomy is a
permission level for a bounded workflow, not a property granted permanently to
an AI model or agent.

| Level | System authority | Human role | Example boundary |
|---:|---|---|---|
| A0 | Observe and record only | Performs the task | Capture an approved event or measurement. |
| A1 | Retrieve, summarize, and flag | Reviews output before use | Find prior lessons with evidence links. |
| A2 | Recommend ranked alternatives | Decides and records rationale | Suggest test plans or material alternatives. |
| A3 | Execute a reversible, pre-approved action | Supervises; can stop or override | Create a draft workflow task within limits. |
| A4 | Execute bounded operations with monitored exceptions | Approves policy and exception thresholds | Adjust a non-safety-critical schedule inside an approved range. |
| A5 | High autonomy within a certified control envelope | Retains governance and emergency authority | Future closed-loop industrial control after validation and approval. |

### Mandatory Human Approval

Human approval is always required for actions that can materially affect:

- worker or product safety
- legal, regulatory, contractual, or certification compliance
- proprietary formulations, inventions, or highly confidential information
- customer commitments, pricing, contracts, or external publication
- destructive, irreversible, or high-cost operations
- production release, quality disposition, or safety-critical process limits
- cross-company data access or model-training permission
- autonomy-level changes and emergency-stop recovery

Agents that influence high-impact decisions or enterprise systems remain
governed like production software, consistent with
`architecture/handbook/08_Agents/15_Agent_Governance.md`.

## Technical-Textile Proof Domain

Technical textiles and functional coatings are the first proof domain because
they combine complex materials, formulations, process variability, supplier
dependencies, testing, regulations, customer-specific requirements, and tacit
knowledge. This is the beachhead rationale recorded in
`architecture/handbook/02_Business/10_Beachhead_Strategy.md`.

The proof should demonstrate a narrow cross-functional loop, for example:

1. capture an approved customer or engineering requirement
2. retrieve relevant projects, trials, failures, evidence, and lessons
3. identify missing information and candidate alternatives
4. create a reviewable recommendation or test-plan Decision Object
5. obtain the required human approval
6. record controlled execution and test outcomes
7. convert reviewed outcomes into reusable knowledge

Technical-textile fields belong in the Technical Textiles Industry Hub. The
mother platform retains universal concepts such as evidence, provenance,
context, decisions, events, lifecycle, confidence, and governance.

No real industrial data is authorized by this model. The pilot remains limited
to approved, sanitized, measurable data under Decision D-014 in
`docs/project/DECISION_LOG.md`.

## Non-Goals and Anti-Misinterpretations

SmartCoat is not:

- a voice agent; voice is one possible input channel
- a document store or search interface; retrieval is one capability
- the Knowledge Capture MVP; that MVP is the first vertical slice
- a technical-textile-only product; technical textiles are the first Hub
- a generic chatbot or general-purpose automation suite
- a formulation calculator or a replacement for domain experts
- an ungoverned autonomous factory controller
- a promise that robots, machines, digital twins, or full autonomy exist today
- a license to centralize company data without tenancy and permitted-use controls
- a replacement architecture for the repository's approved canonical models

## Traceability

| Model statement | Repository evidence | Relationship |
|---|---|---|
| Living, connected, adaptive system under human governance | `docs/strategy/SMARTCOAT_NORTH_STAR.md` | Active strategic vision. |
| Knowledge -> context -> intelligence -> decisions -> capability | `architecture/handbook/01_Foundation/11_Enterprise_Intelligence_Model.md`; `architecture/reference_models/RM-01_Enterprise_Intelligence.md` | Core conceptual chain. |
| Decisions connect evidence through outcome and learning | `architecture/handbook/06_Decision/01_Decision_Architecture_Overview.md` | Decision loop. |
| Canonical enterprise information categories | `architecture/handbook/04_Information/01_Enterprise_Information_Model.md` | Platform information contract. |
| Modular platform layers | `architecture/handbook/09_Platform/01_Platform_Architecture_Overview.md` | Existing platform architecture. |
| Knowledge belongs to the enterprise but remains governed | `architecture/handbook/05_Knowledge/06_Enterprise_Knowledge.md` | Ownership and reuse principle. |
| Technical textiles as first beachhead | `architecture/handbook/02_Business/10_Beachhead_Strategy.md` | Proof-domain rationale. |
| Knowledge Capture as first implementation | `docs/project/MVP_STRATEGY.md`; `architecture/ADR/ADR-0015_Knowledge_Capture_MVP_First_Implementation.md` | Current product slice. |
| Release 1.7 before Knowledge Capture Core | `docs/project/PROJECT_STATE.md`; `docs/project/DECISION_LOG.md` D-015 | Active execution sequence. |
| Agent governance for high-impact systems | `architecture/handbook/08_Agents/15_Agent_Governance.md` | Autonomy controls. |

## Open Questions

These are not resolved by this document:

1. What is the minimum stable mother-platform contract before a second Industry
   Hub may be created?
2. Which Technical Textiles Hub concepts are shared across companies, and which
   remain company-private extensions?
3. Which evidence and evaluation thresholds authorize each autonomy level for
   a specific workflow?
4. What tenancy, identity, and cryptographic isolation design is required before
   multi-company operation?
5. What lawful bases and contracts govern employee voice, cross-company
   benchmarking, retrieval, analytics, and model training?
6. Which first pilot loop provides the strongest measurable proof with the
   smallest approved dataset?

Each question requires a bounded product, architecture, security, governance,
or legal decision before implementation.
