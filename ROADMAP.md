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
| 0.1-1.2 | Merged (historical) | Foundation through root repository documentation. |
| 1.3 | Merged (historical) | Architecture consistency review and refactoring plan. |
| 1.4 | Merged (historical) | Python, FastAPI, domain, service, test, and Docker scaffold. |
| 1.5-1.5.2 | Merged (historical) | PostgreSQL persistence, repository pattern, bidirectional mappers, and mapper hotfixes. |
| 1.6 | Merged (historical) | Repository-backed persistent API routes. |
| 1.7 | **In progress** | Core reset/control documents are merged; ten independently reviewed draft thread PRs remain unmerged. |
| 1.8 | Proposed (sequence accepted) | Knowledge Capture Core. |
| 1.9 | Proposed (sequence accepted) | Human Review Interface. |
| 2.0 | Proposed (sequence accepted) | AI-Assisted Knowledge Capture MVP. |
| 2.1 | Proposed (sequence accepted) | Controlled Technical-Textile Pilot. |

The active sequence is governed by D-015 in
[Decision Log](docs/project/DECISION_LOG.md). Changing it requires an explicit
decision.

## Release 1.7 Integration Status

The ten thread PRs have been independently reviewed and their Correction Cycle
3 branches updated. They remain draft, are not accepted by review alone, and are
not merged. Their proposed outputs include the T01 Living Industry clarification,
T05-T09 governance/data/pilot contracts, and T10 execution-quality contract.
T03 and T04 contain independently reviewed engineering and persistence changes.

Root documentation must describe those artifacts as proposed or independently
reviewed until an authorized integration occurs. Release 1.7 remains in progress
until the combined branch is validated; no thread score is a merge decision.

## Near-Term Gates

### Release 1.7 Exit

- repository entry points match actual state
- reliable local Python 3.12 setup and CI evidence
- tests, linting, formatting, and typing measured honestly
- API-to-PostgreSQL contract and integration evidence
- no confidential industrial data in the execution wave
- controlled-pilot schema, inventory, governance, ingestion, and proof plans
  independently reviewed before integration
- thread artifacts accepted and merged before they are described as release facts

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
