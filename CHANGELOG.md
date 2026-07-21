# Changelog

Notable SmartCoat architecture and implementation releases are summarized here.
Release records are indexed in
[architecture/indexes/RELEASE_INDEX.md](architecture/indexes/RELEASE_INDEX.md).

## Status Vocabulary

- **Proposed:** planned or draft content without accepted authority.
- **In progress:** active work that is not release-complete.
- **Independently reviewed:** reviewed in a draft pull request; not thereby accepted or merged.
- **Accepted:** approved through the applicable decision or architecture process.
- **Merged:** present in the target repository branch.

## Release Summary

| Release | Status | Summary |
|---|---|---|
| 1.7 | In progress | Project reset and engineering baseline. Core project-state and execution-control documents are merged; ten thread outputs have been independently reviewed but remain draft and unmerged. |
| 1.6 | Merged (historical) | Repository-backed persistent API routes for Knowledge Objects, Decision Objects, and Enterprise Events. |
| 1.5.2 | Merged (historical) | Deterministic datetime fallback for unpersisted mapper records. |
| 1.5.1 | Merged (historical) | Bidirectional persistence mapping. |
| 1.5 | Merged (historical) | PostgreSQL/SQLAlchemy persistence, repositories, models, migrations, and tests. |
| 1.4 | Merged (historical) | Python, FastAPI, domain, service, agent, AI, test, and Docker scaffold for Knowledge Capture. |
| 1.3 | Merged (historical) | Architecture consistency review, quality gates, and refactoring plan. |
| 1.2 | Merged (historical) | Root repository documentation and repository-entry-point ADR. |
| 1.1 | Merged (historical) | Repository governance, indexes, glossary, lifecycle, and review workflow. |
| 1.0 | Merged (historical) | Deployment architecture and deployment-trust ADR. |
| 0.9 | Merged (historical) | Platform architecture. |
| 0.8 | Merged (historical) | Agent architecture. |
| 0.7 | Merged (historical) | AI architecture. |
| 0.6 | Merged (historical) | Decision architecture. |
| 0.5 | Merged (historical) | Knowledge architecture. |
| 0.4 | Merged (historical) | Information architecture. |
| 0.3 | Merged (historical) | Domain architecture. |
| 0.2 | Merged (historical) | Business architecture. |
| 0.1 | Merged (historical) | Foundation handbook and Enterprise Intelligence thesis. |

## Release 1.7 - Project Reset & Engineering Baseline

Status: In progress

Merged baseline work:

- established active project-state, history, MVP, decision, and North-Star documents
- established issue, branch, pull-request, review, and execution-control practices
- prohibited real confidential industrial data in the ten-thread execution wave

Independently reviewed but not accepted or merged:

- ten draft thread pull requests covering documentation, strategy, engineering,
  persistence, schemas, source readiness, governance, ingestion, pilot planning,
  and execution-quality controls
- Correction Cycle 3 changes on those same branches and pull requests

Release 1.7 is not complete until authorized integration and release-level
validation occur. Draft thread artifacts are not changelog facts until merged.

## Release 1.6 - Persistent API Layer

Status: Merged (historical)

- connected FastAPI routes to repository-backed application services
- exposed persistent Knowledge Object, Decision Object, and Enterprise Event paths
- recorded the API persistence architecture and ADR-0019

## Release 1.5.2 - Mapper Datetime Hotfix

Status: Merged (historical)

- added deterministic datetime fallback for unpersisted records
- recorded ADR-0018

## Release 1.5.1 - Persistence Mapper Hotfix

Status: Merged (historical)

- added bidirectional persistence mapping
- recorded ADR-0017

## Release 1.5 - Database & Persistence Layer

Status: Merged (historical)

- added PostgreSQL/SQLAlchemy persistence infrastructure and repositories
- added database models, migrations, mapper tests, and ADR-0016

## Release 1.4 - Implementation Scaffold

Status: Merged (historical)

- added the Python package, canonical domain models, services, API scaffold,
  agents, AI placeholders, tests, and Docker development files
- documented the Knowledge Capture MVP architecture and ADR-0015

## Release 1.3 - Architecture Consistency Review & Refactoring Plan

Status: Merged (historical)

- audited terminology, numbering, links, duplicate structures, and implementation readiness
- added architecture quality and refactoring assets
- recorded ADR-0014

## Detailed Historical Entries Preserved From the Baseline

The following detailed 0.1-1.2 entries retain the valid content present before
T02 synchronization. The summary above supplements this history; it does not
replace it.

## Release 1.2 - Root Repository Documentation

Added:

- root README
- repository structure guide
- roadmap
- contributing guide
- security policy
- code of conduct
- license notice
- root documentation index
- repository documentation ADR

## Release 1.1 - Repository Governance & Documentation Quality

Added:

- architecture portal
- governance documents
- indexes
- glossary
- documentation lifecycle
- review workflow
- repository governance ADR

## Release 1.0 - Deployment Architecture

Added:

- deployment architecture handbook
- cloud, on-premise, hybrid, Docker, Kubernetes architecture
- backup, monitoring, incident response, governance
- deployment trust ADR

## Release 0.9 - Platform Architecture

Added:

- platform architecture handbook
- services, APIs, data platform, knowledge graph platform
- event-driven architecture, security, IAM, observability, CI/CD
- platform infrastructure ADR

## Release 0.8 - Agent Architecture

Added:

- agent architecture handbook
- Memory Agent, Lab Agent, Production Agent, QC Agent, Supplier Agent, Warehouse Agent, Executive Agent
- agent orchestration, permissions, memory, governance, safety, evaluation
- agents as governed enterprise workers ADR

## Release 0.7 - AI Architecture

Added:

- AI architecture handbook
- materials, formulation, supply, quality, regulatory, computer vision intelligence
- foundation model layer, RAG, ML lifecycle, AI governance, safety, evaluation
- AI as enterprise intelligence capability ADR

## Release 0.6 - Decision Architecture

Added:

- decision architecture handbook
- decision lifecycle, decision objects, evidence, alternatives, recommendations, confidence, risk, execution, learning, governance, auditability
- decisions as primary value output ADR

## Release 0.5 - Knowledge Architecture

Added:

- knowledge architecture handbook
- industrial memory, knowledge capture, knowledge graph, semantic search, lessons learned, lifecycle, validation, governance, security
- knowledge graph as context backbone ADR

## Release 0.4 - Information Architecture

Added:

- information architecture handbook
- enterprise information model, canonical data model, entity model, relationship model, event model, governance, provenance, data quality, master data
- canonical information model ADR

## Release 0.3 - Domain Architecture

Added:

- domain architecture handbook
- materials, formulations, fabrics, manufacturing, quality, suppliers, customers, regulations, R&D
- domain-first architecture ADR

## Release 0.2 - Business Architecture

Added:

- business architecture handbook
- market landscape, value proposition, business model, customers, revenue model, competitive advantage, GTM, product strategy, capability map
- reference models before implementation ADR

## Release 0.1 - Foundation

Added:

- foundation handbook
- problem statement
- identity
- theory
- mission
- vision
- first principles
- core values
- constitution
- strategic thesis
- long-term goals
- enterprise intelligence model
- knowledge philosophy
- decision philosophy
- enterprise ontology
- enterprise language

## Documentation Preservation Rule

Future changelog synchronization must preserve valid detail. Add summaries above
existing entries or link to a retained release record; do not replace detailed
history with compressed prose. If content is superseded, keep or move the prior
statement, label it superseded, and identify the replacement and decision. Before
committing, compare release headings and detailed bullets with the prior target
branch and explain every intentional removal in the pull request.
