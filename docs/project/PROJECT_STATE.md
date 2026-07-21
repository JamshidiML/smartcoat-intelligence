# SmartCoat Project State

Version: 1.0

Status: Release 1.8 Active

Last updated: 2026-07-22

---

## Purpose

This document is the canonical, concise statement of where SmartCoat is today.

It reconciles the original project conversations, the enterprise architecture, the repository history, and the implementation currently present in `main`.

When older documents, chat messages, roadmap statements, or release indexes conflict with this file, the conflict must be reviewed and resolved explicitly. This file does not silently erase history.

---

## Product Identity

SmartCoat Intelligence is an Enterprise Intelligence Infrastructure for Advanced Materials organizations.

The initial beachhead is technical textiles, functional coatings, high-temperature materials, formulations, production, quality, suppliers, and industrial R&D decision-making.

SmartCoat is not only:

- a formulation calculator
- a document search tool
- a chatbot
- a generic AI assistant
- a data lake
- a knowledge graph

SmartCoat connects enterprise knowledge, context, evidence, decisions, outcomes, and learning so that industrial organizations can make better, explainable, traceable decisions.

---

## Core Transformation

Enterprise Knowledge

→ Enterprise Context

→ Enterprise Intelligence

→ Enterprise Decisions

→ Organizational Capability

→ Learning Enterprise

---

## Long-Term Capability Domains

SmartCoat's long-term capability map includes:

1. Product Intelligence
2. Formulation Intelligence
3. Material Intelligence
4. Supply Chain Intelligence
5. Manufacturing Intelligence
6. Regulatory Intelligence
7. Climate and Geography Intelligence
8. Business Intelligence
9. Decision Intelligence

These are strategic capability domains, not immediate implementation scope.

---

## Current Technical Baseline

The repository currently contains:

- multi-volume enterprise architecture
- reference models and canonical enterprise language
- architecture decision records
- architecture governance and quality assets
- Python 3.12 package scaffold
- FastAPI application
- Pydantic domain models
- Knowledge Object model
- Decision Object model
- Enterprise Event model
- SQLAlchemy persistence layer
- PostgreSQL schema and local Docker development setup
- repository-backed API routes
- initial unit and API tests
- Memory Agent skeleton
- Lab Agent skeleton

The latest implementation release present in the repository is Release 1.6 — Persistent API Layer.

---

## Current Product Maturity

SmartCoat is between implementation foundation and usable MVP.

The project has moved beyond concept and architecture, but it is not yet a product that an R&D engineer can use naturally in daily work.

Current maturity by area:

| Area | Status |
|---|---|
| Product thesis | Strong baseline |
| Enterprise architecture | Broad baseline established |
| Domain and knowledge models | Strong conceptual baseline |
| Backend scaffold | Implemented |
| PostgreSQL persistence | Implemented at initial level |
| API | Initial persistent routes implemented |
| Agent behavior | Skeleton only |
| Human-friendly knowledge capture | Not implemented |
| User interface | Not implemented |
| AI-assisted extraction | Not implemented |
| Semantic search | Not implemented |
| Knowledge graph runtime | Not implemented |
| Enterprise integrations | Not implemented |
| Production security | Not implemented |
| Real industrial pilot | Not started |

---

## Current Primary Problem

The architecture and implementation advanced faster than the root documentation, roadmap, indexes, release records, engineering workflow, and product focus.

This created several sources of confusion:

- `README.md`, `ROADMAP.md`, `CHANGELOG.md`, and indexes do not fully reflect Releases 1.3–1.6.
- implementation exists, but the repository still describes architecture engineering as the current phase
- development was largely committed directly to `main`
- no active issue and pull-request workflow was established
- the first API requires structured JSON and is not a user experience
- tests do not yet prove the complete API-to-PostgreSQL path end to end
- several implementation consistency items require review

---

## Current Strategic Decision

SmartCoat will not expand immediately into all long-term intelligence domains.

The next product objective is a narrow, complete, industrially useful vertical slice:

> An R&D engineer records an experiment, observation, failure, result, lesson, or decision in natural language or a simple form. SmartCoat identifies missing context, asks focused follow-up questions, proposes a structured Knowledge Object, preserves evidence and provenance, requests human confirmation, stores the approved knowledge, and makes it retrievable later.

This is the Knowledge Capture MVP.

---

## Immediate Release

Release 1.7 - Project Reset & Engineering Baseline is completed.

Current release in progress:

**Release 1.8 - Knowledge Capture Core**

Canonical scope:

- `docs/project/RELEASE_1_8_DEFINITION_PACK.md`
- parent issue [#38](https://github.com/JamshidiML/smartcoat-intelligence/issues/38)

Primary outcomes:

- implement a governed Knowledge Object v2 backend contract
- provide structured evidence, provenance, and minimum context references
- enforce explicit lifecycle transitions, revision checks, and safe mutation
- align persistence and migrations with one atomic audit transaction boundary
- provide deterministic filtering and cursor pagination
- prove the end-to-end PostgreSQL workflow with synthetic data

---

## Next Product Releases

### Release 1.9 — Human Review Interface

Expected focus:

- simple web interface
- no manual JSON requirement
- guided knowledge capture
- review and approval workflow
- project timeline and knowledge browsing

### Release 2.0 — AI-Assisted Knowledge Capture MVP

Expected focus:

- free-text and voice input
- structured extraction
- adaptive follow-up questions
- confidence and uncertainty
- human-in-the-loop validation
- semantic retrieval
- related lessons learned

### Release 2.1 — Technical Textiles Pilot

Expected focus:

- controlled pilot with approved R&D and technical-textile data
- measurable value in capture completeness, retrieval quality, time saved, and reuse of prior knowledge

---

## Team Operating Model

### Mohsen Jamshidi — Founder, Product Owner, Domain Authority

Owns:

- product direction
- industrial truth
- domain priorities
- approval of sensitive data use
- final product decisions

### ChatGPT — Product Architect and Technical Lead

Owns:

- product framing
- architecture coherence
- requirements and acceptance criteria
- roadmap and backlog design
- task definition
- architecture and code review
- decision traceability

### Codex — Implementation Engineer

Owns assigned engineering work:

- repository inspection
- implementation
- refactoring
- tests
- CI fixes
- documentation related to code changes
- pull-request preparation

Codex does not independently redefine product scope, canonical domain language, core architecture, security policy, or data-governance rules.

---

## Source-of-Truth Order

For active development, use this order:

1. accepted ADRs and security rules
2. `docs/project/PROJECT_STATE.md`
3. `docs/project/MVP_STRATEGY.md`
4. current approved release scope
5. current GitHub issues and acceptance criteria
6. architecture reference models and canonical language
7. implementation and tests
8. historical chat archive and superseded documents

Historical chat content is evidence of project evolution, not automatically an active requirement.

---

## Security Boundary

Raw chat exports, internal company emails, proprietary formulations, pricing, customer data, supplier-confidential information, private reports, and raw enterprise datasets must not be committed to this repository without explicit approval and sanitization.

Curated, non-confidential project knowledge may be committed when it improves traceability and implementation quality.

---

## Definition of Progress

SmartCoat progress is not measured by the number of architecture documents, agents, models, or integrations.

Progress is measured by validated user value:

- better capture of industrial knowledge
- less knowledge loss
- faster retrieval of relevant experience
- more complete evidence and provenance
- more explainable decisions
- measurable time saved
- improved reuse of prior R&D learning
