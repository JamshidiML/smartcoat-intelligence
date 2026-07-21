# SmartCoat Project History

Version: 1.0

Status: Curated Historical Record

Last updated: 2026-07-10

---

## Purpose

This document reconstructs the major evolution of SmartCoat from the original project conversations and the repository history.

It records important ideas, decisions, changes in direction, and implementation milestones without committing the raw chat archive or confidential enterprise data.

This is a curated historical record. It is not a replacement for accepted ADRs or the current project state.

---

## Stage 1 — Industrial Data Opportunity Discovery

The project began from a practical industrial question:

How can technical-textile and coating knowledge be structured so that it becomes usable for analytics, machine learning, engineering search, and future decision support?

Early work focused on identifying measurable variables across technical-textile systems, including:

- substrate and fabric identity
- fiber type and construction
- thickness, area weight, width, density, and porosity
- mechanical properties
- physical and surface properties
- coating formulation composition
- rheology and uncured formulation properties
- coating-process parameters
- curing and oven conditions
- final coating properties
- thermal and fire performance
- foil-lamination variables
- environmental and operational context
- production, quality, cost, and customer outcomes

The early conclusion was important:

A useful industrial AI system cannot be built only from final test results. It must preserve materials, formulations, process conditions, evidence, context, failures, and outcomes together.

---

## Stage 2 — Data Model and Feature-Space Expansion

The initial concept expanded from a few spreadsheet inputs into a much broader industrial data model.

The project recognized that future intelligence would require connected information across:

- materials
- fabrics
- formulations
- ingredients and functions
- process parameters
- machines and production runs
- tests and standards
- defects and root causes
- projects, trials, hypotheses, results, and lessons learned
- suppliers, offers, prices, lead times, availability, and logistics
- regulation and future restriction risk
- climate and geography
- cost, margin, market, and business outcomes

This stage established the idea that SmartCoat should not be a single machine-learning model. It should become a connected industrial intelligence system.

---

## Stage 3 — Capability Map

A capability map was defined to separate long-term product domains.

The principal capability domains became:

1. Product Intelligence
2. Formulation Intelligence
3. Material Intelligence
4. Supply Chain Intelligence
5. Manufacturing Intelligence
6. Regulatory Intelligence
7. Climate Intelligence
8. Business Intelligence
9. Decision Intelligence

Examples of envisioned capabilities included:

- application recommendation
- requirement analysis
- formulation search and optimization
- material comparison and substitution
- supplier selection and ranking
- logistics optimization
- lead-time forecasting
- process optimization
- defect prediction and root-cause analysis
- compliance checking
- future restriction prediction
- regional material optimization
- cost and margin forecasting
- integrated recommendation packages

A critical distinction was made:

The capability map describes the long-term platform vision. It does not mean that all domains should be implemented at once.

---

## Stage 4 — Enterprise Ontology v2

The project then moved from feature lists toward an enterprise ontology.

The central ontology rule was:

> Every meaningful item should be represented through connected entities and relationships. No important knowledge should remain isolated.

Examples included:

- Material → supplied_by → Supplier
- Formulation → contains → Material
- Material → has_alternative → Material
- Customer Requirement → requires → Standard
- Project → contains → Trial
- Trial → tests → Hypothesis
- Trial → produces → Result
- Failure → generates → Lesson Learned
- Batch → uses → Formulation
- Production Run → follows → Process
- Process Parameter → influences → Defect
- Test → follows → Test Standard
- Defect → caused_by → Root Cause
- Decision Package → recommends → Formulation
- Decision Package → recommends → Supplier

The ontology expanded across customer, market, materials, fabrics, formulations, manufacturing, tests, defects, R&D, supply chain, regulation, climate, and decision intelligence.

Governance attributes were also proposed for entities and relationships, including identity, source, timestamp, version, confidence, review status, confidentiality, ownership, and provenance.

---

## Stage 5 — Integrated Decision Vision

The project defined a long-term decision output for customer or engineering requests.

The envisioned Decision Package could eventually include:

- recommended formulation
- alternative formulations
- recommended fabric
- recommended raw materials
- alternative raw materials
- recommended suppliers
- supplier ranking
- material and logistics cost estimates
- lead time
- production and procurement plans
- shelf-life risk
- regulatory risk
- supply-chain risk
- climate suitability
- manufacturing risk
- project success probability
- suggested tests
- explanation and rationale

A strategic rule was established:

> SmartCoat must not optimize formulation performance in isolation.

Future recommendations should consider performance, cost, availability, logistics, shelf life, regulation, climate, manufacturing feasibility, and risk together.

---

## Stage 6 — Data Foundation Direction

Before large-scale ingestion, the project recognized a major engineering risk:

Loading thousands of spreadsheets, PDFs, images, emails, and enterprise records before defining a canonical model would create a larger data problem rather than intelligence.

The project therefore adopted a layered direction:

1. Vision
2. Ontology
3. Data Model
4. Data Foundation
5. Knowledge Graph
6. Engineering Search
7. Decision Intelligence
8. AI Engines

The proposed sequence was:

- define canonical schemas
- define how source data maps into canonical objects
- preserve provenance and confidence
- ingest documents and structured data
- build connected knowledge
- add search and retrieval
- add decision intelligence
- add specialized AI engines

---

## Stage 7 — Architecture-First Expansion

The repository evolved into a formal Enterprise Intelligence Architecture.

Releases established:

- Foundation
- Business Architecture
- Domain Architecture
- Information Architecture
- Knowledge Architecture
- Decision Architecture
- AI Architecture
- Agent Architecture
- Platform Architecture
- Deployment Architecture
- repository governance
- root documentation

The project identity evolved from a data and AI concept into a broader thesis:

SmartCoat is Enterprise Intelligence Infrastructure for Advanced Materials organizations.

The core transformation became:

Enterprise Knowledge

→ Enterprise Context

→ Enterprise Intelligence

→ Enterprise Decisions

→ Organizational Capability

→ Learning Enterprise

---

## Stage 8 — Architecture Consistency Review

Release 1.3 introduced architecture quality controls before implementation.

The repository added:

- consistency review
- terminology audit
- ADR coverage review
- release readiness checks
- architecture quality gates
- implementation readiness review
- refactoring guidance

The architecture was considered strong enough to support implementation, while terminology, indexes, traceability, and implementation scope still required active governance.

---

## Stage 9 — Knowledge Capture MVP Scaffold

Release 1.4 moved the project into implementation.

The first implementation intentionally focused on Knowledge Capture rather than the full long-term platform.

Initial components included:

- Python package structure
- FastAPI
- Pydantic domain models
- Knowledge Object
- Decision Object
- Enterprise Event
- application services
- Memory Agent skeleton
- Lab Agent skeleton
- PostgreSQL schema
- Docker development environment
- tests

The central implementation principle was:

> Capture knowledge correctly before adding advanced AI.

---

## Stage 10 — Persistence and Persistent API

Release 1.5 introduced database persistence using PostgreSQL, SQLAlchemy, repositories, and mapping between domain objects and persistence records.

Release 1.6 connected the FastAPI routes to repository-backed services.

Persistent API support was introduced for:

- Knowledge Objects
- Decision Objects
- Enterprise Events

This marked the transition from architecture and scaffolding into an operational backend foundation.

---

## Stage 11 — User-Experience Realization

During the first manual API tests, a critical product insight became explicit:

Requiring users to manually create JSON payloads is not a usable knowledge-capture experience.

The API is an engineering interface, not the end product.

The product must reduce user effort and improve completeness through:

- simple forms
- natural-language input
- voice input
- context-aware follow-up questions
- missing-information detection
- structured proposals
- human review and approval
- automatic provenance and metadata

This insight became the bridge from backend infrastructure to the actual Knowledge Capture MVP.

---

## Stage 12 — Project Reset and Team Operating Model

By July 2026, architecture, implementation, root documentation, indexes, roadmap, and working practices had drifted out of synchronization.

The project also expanded from a two-party working process into a three-role operating model:

- Mohsen as Founder, Product Owner, and Domain Authority
- ChatGPT as Product Architect and Technical Lead
- Codex as Implementation Engineer

Release 1.7 was therefore initiated to establish:

- a canonical project state
- a curated project history
- a focused MVP strategy
- a decision log
- Codex operating instructions
- issue-driven work
- branch and pull-request discipline
- engineering baseline validation
- synchronized documentation and implementation

---

## Historical Decisions Preserved

The following historical ideas remain strategically valid:

- knowledge should be connected, not isolated
- provenance, evidence, confidence, review status, and ownership are first-class requirements
- industrial intelligence requires more than documents or embeddings
- formulation optimization must not ignore supply, cost, regulation, manufacturing, and risk
- canonical models should precede uncontrolled bulk ingestion
- Knowledge Capture is a foundational MVP
- human review is required before enterprise knowledge becomes trusted
- architecture should guide implementation

---

## Historical Ideas Not Yet Approved for Immediate Implementation

The following remain future capabilities and should not automatically enter the active backlog:

- full enterprise knowledge graph
- autonomous industrial decision agent
- complete supplier and logistics optimization
- regulatory prediction engine
- climate-aware optimization
- full formulation optimizer
- project-success prediction
- production planning automation
- enterprise-wide ERP, email, Teams, and SharePoint integration
- multi-site platform deployment

Each future capability requires a separate validated product case, data-readiness review, security review, and release decision.

---

## Archive Rule

The original chat archive is preserved outside the repository as historical source material.

Raw conversation exports should not be committed because they may contain duplicated, obsolete, personal, or confidential information.

Only curated, reviewed, non-confidential project knowledge should enter the repository.
