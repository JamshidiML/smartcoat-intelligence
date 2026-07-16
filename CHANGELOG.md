# Changelog

Notable SmartCoat architecture and implementation releases are summarized here.
Release records are indexed in
[architecture/indexes/RELEASE_INDEX.md](architecture/indexes/RELEASE_INDEX.md).

## Release 1.7 — Project Reset & Engineering Baseline

Status: In progress

- established the active project-state, history, MVP, decision, and North-Star documents
- added execution control for ten isolated review threads
- focused work on documentation synchronization, engineering baselines, CI,
  persistent API validation, and controlled-pilot preparation
- prohibited real confidential industrial data in this execution wave

## Release 1.6 — Persistent API Layer

- connected FastAPI routes to repository-backed application services
- exposed persistent Knowledge Object, Decision Object, and Enterprise Event paths
- recorded the API persistence architecture and ADR-0019

## Release 1.5.2 — Mapper Datetime Hotfix

- added deterministic datetime fallback for unpersisted records
- recorded ADR-0018

## Release 1.5.1 — Persistence Mapper Hotfix

- added bidirectional persistence mapping
- recorded ADR-0017

## Release 1.5 — Database & Persistence Layer

- added PostgreSQL/SQLAlchemy persistence infrastructure and repositories
- added database models, migrations, mapper tests, and ADR-0016

## Release 1.4 — Implementation Scaffold

- added the Python package, canonical domain models, services, API scaffold,
  agents, AI placeholders, tests, and Docker development files
- documented the Knowledge Capture MVP architecture and ADR-0015

## Release 1.3 — Architecture Consistency Review & Refactoring Plan

- audited terminology, numbering, links, duplicate structures, and implementation readiness
- added architecture quality and refactoring assets
- recorded ADR-0014

## Release 1.2 — Root Repository Documentation

- added root README, structure guide, roadmap, contribution/security documents,
  root documentation index, and ADR-0013

## Release 1.1 — Repository Governance & Documentation Quality

- added architecture portal, governance documents, indexes, glossary,
  documentation lifecycle, review workflow, and ADR-0012

## Release 1.0 — Deployment Architecture

- added cloud, on-premise, hybrid, Docker, Kubernetes, backup, monitoring,
  incident-response, and deployment-governance architecture
- recorded ADR-0011

## Releases 0.2-0.9 — Architecture Volumes

| Release | Architecture output | ADR |
|---|---|---|
| 0.2 | Business Architecture | ADR-0003 |
| 0.3 | Domain Architecture | ADR-0004 |
| 0.4 | Information Architecture | ADR-0005 |
| 0.5 | Knowledge Architecture | ADR-0006 |
| 0.6 | Decision Architecture | ADR-0007 |
| 0.7 | AI Architecture | ADR-0008 |
| 0.8 | Agent Architecture | ADR-0009 |
| 0.9 | Platform Architecture | ADR-0010 |

## Release 0.1 — Foundation

- established identity, mission, vision, first principles, strategic thesis,
  Enterprise Intelligence model, knowledge/decision philosophy, ontology, and
  enterprise language
