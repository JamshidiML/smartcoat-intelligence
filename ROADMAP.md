# SmartCoat Roadmap

Status: Active planning view

## Two Planning Horizons

The roadmap separates long-term platform direction from approved release
execution. Vision does not imply current implementation.

### North-Star Platform Direction

Over time SmartCoat aims to connect enterprise data, knowledge, context,
intelligence, decisions, execution, outcomes, and learning across reusable
Industry Hubs and isolated company instances. Potential later capabilities
include governed knowledge graphs, decision intelligence, specialized agents,
enterprise integrations, vision, simulation, and bounded automation.

Technical textiles are the first proof domain. Expansion to other companies or
industries requires evidence that the horizontal platform contracts are truly
reusable.

### Approved Release Execution

| Release | Status | Outcome |
|---|---|---|
| 0.1-1.2 | Historical | Foundation through root repository documentation. |
| 1.3 | Historical | Architecture consistency review and refactoring plan. |
| 1.4 | Historical | Python, FastAPI, domain, service, test, and Docker scaffold. |
| 1.5-1.5.2 | Historical | PostgreSQL persistence, repository pattern, bidirectional mappers, and mapper hotfixes. |
| 1.6 | Historical | Repository-backed persistent API routes. |
| 1.7 | **Active** | Project reset, documentation synchronization, engineering baseline, CI, persistence validation, and controlled-pilot preparation. |
| 1.8 | Next | Knowledge Capture Core. |
| 1.9 | Planned | Human Review Interface. |
| 2.0 | Planned | AI-Assisted Knowledge Capture MVP. |
| 2.1 | Planned | Controlled Technical-Textile Pilot. |

The active sequence is governed by D-015 in
[Decision Log](docs/project/DECISION_LOG.md). Changing it requires an explicit
decision.

## Near-Term Gates

### Release 1.7 Exit

- repository entry points match actual state
- reliable local Python 3.12 setup and CI evidence
- tests, linting, formatting, and typing measured honestly
- API-to-PostgreSQL contract and integration evidence
- no confidential industrial data in the execution wave
- controlled-pilot schema, inventory, governance, ingestion, and proof plans
  independently reviewed before integration

### Release 1.8 — Knowledge Capture Core

- minimum approved canonical entities
- evidence and provenance preservation
- reviewable lifecycle behavior
- repository-backed services and tests
- no manually authored JSON as the product UX

### Release 1.9 — Human Review Interface

- usable review, correction, rejection, and approval workflow
- uncertainty and conflicting evidence visible
- authentication and authorization decision before multi-user use

### Release 2.0 — AI-Assisted MVP

- approved model/provider and deployment decision
- evaluated extraction and retrieval behavior
- human review before AI output becomes trusted knowledge
- security, privacy, prompt-injection, and model-use controls

### Release 2.1 — Controlled Pilot

- limited approved and sanitized data package
- explicit owner, purpose, confidentiality, retention, and permitted use
- measurable baselines and success metrics
- no unreviewed high-impact autonomy

## Deferred Platform Expansion

The following remain North-Star capabilities, not committed near-term scope:

- enterprise-wide ingestion and integration
- cross-company learning
- autonomous industrial control
- self-driving laboratories and digital twins
- production robotics orchestration
- multi-industry commercialization

Each requires its own architecture, governance, evidence, and release decision.
