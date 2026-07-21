# SmartCoat MVP Strategy

Version: 1.0

Status: Active Product Direction

Last updated: 2026-07-10

---

## Strategic Choice

SmartCoat will begin with a focused Knowledge Capture MVP for industrial R&D and advanced-materials organizations.

The MVP will not attempt to deliver the complete long-term platform at once.

The first product must prove that SmartCoat can reduce knowledge loss, improve capture quality, preserve evidence and context, and make prior industrial learning reusable.

---

## Target User

Initial primary user:

An R&D engineer, product-development engineer, laboratory specialist, quality engineer, or technical project owner working with advanced materials, technical textiles, coatings, formulations, tests, production trials, suppliers, and customer requirements.

Initial pilot domain:

Technical textiles and functional coatings, including high-temperature materials and industrial product development.

---

## Core User Problem

Important industrial knowledge is fragmented across:

- personal memory
- notebooks
- spreadsheets
- laboratory reports
- quality files
- technical PDFs
- email
- meeting notes
- production observations
- images
- informal conversations

As a result:

- context is lost
- failures are repeated
- evidence is separated from decisions
- lessons learned are difficult to find
- employees must reconstruct old projects manually
- decisions are hard to explain later
- valuable tacit knowledge disappears when people leave or change roles

---

## MVP Job To Be Done

When an engineer completes or observes meaningful work, SmartCoat should help capture the knowledge completely and correctly with minimum effort, so that the organization can retrieve, trust, and reuse it later.

---

## MVP Experience

### Input

The user can provide one or more of:

- free text
- guided form
- voice transcript
- optional file or image reference
- project context

### Smart Assistance

SmartCoat should:

1. identify the likely knowledge type
2. extract known facts
3. detect missing critical context
4. ask only relevant follow-up questions
5. distinguish fact, observation, hypothesis, conclusion, and recommendation
6. identify uncertainty
7. preserve evidence and provenance
8. propose a structured Knowledge Object

### Human Review

The user should be able to:

- review extracted information
- edit fields
- reject incorrect suggestions
- add evidence
- approve the object
- leave it as a draft when uncertain

### Storage and Retrieval

The approved knowledge should be:

- stored persistently
- linked to relevant project context
- searchable
- filterable
- auditable
- retrievable with related lessons and evidence

---

## First Vertical Slice

The first complete vertical slice is:

> Capture one R&D experiment or observation from simple user input, clarify missing information, generate a structured draft, obtain human approval, persist it, and retrieve it later.

A representative example:

A user records that a high-temperature coating sample became brittle after long oven exposure.

SmartCoat should help capture:

- project
- sample or formulation reference
- substrate or material context
- process conditions
- test conditions
- expected outcome
- observed outcome
- evidence
- failure mode
- possible cause, clearly labeled as hypothesis when unconfirmed
- lesson learned
- next recommended action
- confidence and review status

---

## MVP Scope

### In Scope

- user-friendly knowledge capture
- Knowledge Objects
- minimum project and experiment context
- evidence and provenance
- lifecycle states
- human review and approval
- persistent storage
- list, filter, and retrieve
- basic audit trail
- initial semantic retrieval
- related knowledge suggestions

### Minimum Domain Context

The first implementation should evaluate a minimal set of domain entities:

- Project
- Experiment or Trial
- Material
- Fabric or Substrate
- Formulation Reference
- Process Conditions
- Test Result
- Observation
- Failure Mode
- Lesson Learned

These should remain minimal and architecture-aligned. The MVP must not attempt to implement the entire enterprise ontology.

### Out of Scope

- autonomous formulation generation
- full formulation optimization
- automatic supplier selection
- ERP integration
- email ingestion
- unrestricted bulk document ingestion
- full knowledge graph platform
- autonomous decision execution
- production planning
- complete regulatory engine
- complete climate engine
- enterprise-wide deployment
- customer-facing commercial product

---

## Product Principles

### 1. No Manual JSON for End Users

JSON may remain an API representation, but users must interact through natural language, voice, or clear forms.

### 2. Human Confirmation Before Trust

AI-generated knowledge remains a proposal until a human reviews or validates it according to governance rules.

### 3. Evidence Before Confidence

Confidence must not be presented as certainty. Important conclusions should preserve supporting evidence and source context.

### 4. Ask Less, Capture Better

The system should ask focused questions only when missing information materially affects reuse, trust, or interpretation.

### 5. Preserve Uncertainty

Unknown, unmeasured, assumed, and conflicting information must remain explicit.

### 6. Domain Language Matters

The interface should use the user's industrial language while storing canonical concepts consistently.

### 7. Architecture Supports the Product

Architecture is a constraint and an asset, but documentation volume is not a product outcome.

### 8. Start Narrow, Design to Expand

The first pilot is narrow. The underlying models should allow future expansion without prematurely implementing every domain.

---

## MVP Success Metrics

The pilot should measure:

### Capture Quality

- percentage of critical fields completed
- percentage of captured objects with evidence
- percentage with provenance
- percentage requiring major correction after AI extraction

### User Efficiency

- time required to record an experiment or lesson
- number of follow-up questions
- user-reported effort compared with current reporting

### Retrieval Value

- success rate for finding relevant prior knowledge
- relevance of retrieved lessons
- time saved when reconstructing past project context

### Trust and Governance

- approval rate of AI-generated drafts
- correction rate by field
- percentage of claims correctly labeled as fact, hypothesis, or recommendation
- audit completeness

### Business Signal

- repeated failures avoided
- duplicated work reduced
- faster project onboarding
- faster response to engineering questions

---

## Release Path

### Release 1.7 — Project Reset & Engineering Baseline

Establish one project state, engineering workflow, documentation synchronization, CI, technical audit, and locked MVP direction.

### Release 1.8 — Knowledge Capture Core

Build reliable domain, persistence, lifecycle, evidence, provenance, filtering, pagination, and audit behavior.

### Release 1.9 — Human Review Interface

Build the first usable interface and remove the need for manual JSON.

### Release 2.0 — AI-Assisted Knowledge Capture MVP

Add extraction, missing-information detection, adaptive questions, confidence, human approval, and semantic retrieval.

### Release 2.1 — Controlled Technical-Textile Pilot

Test the complete workflow on approved, sanitized, limited industrial data and measure value.

---

## Exit Criteria for MVP

The Knowledge Capture MVP is successful when a pilot user can complete this workflow without developer assistance:

1. open the application
2. record an experiment, observation, failure, result, lesson, or decision
3. answer a small number of relevant follow-up questions
4. review a structured draft
5. approve or edit it
6. retrieve the saved knowledge later
7. see evidence, provenance, status, and related context

The MVP must demonstrate measurable improvement over the user's current manual process.
