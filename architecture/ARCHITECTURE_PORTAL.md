# SmartCoat Architecture Portal

This is the primary navigation entry point for SmartCoat architecture and its
relationship to current implementation and project execution.

## Current Context

- [North Star](../docs/strategy/SMARTCOAT_NORTH_STAR.md)
- [Project State](../docs/project/PROJECT_STATE.md)
- [Project History](../docs/project/PROJECT_HISTORY.md)
- [MVP Strategy](../docs/project/MVP_STRATEGY.md)
- [Decision Log](../docs/project/DECISION_LOG.md)
- [Execution Control Center](../docs/execution/EXECUTION_CONTROL_CENTER.md)

The North Star describes the horizontal mother platform. Technical textiles are
the first proof domain. Knowledge Capture is the first vertical implementation
slice. Release 1.7 is the active project-reset and engineering-baseline release.

## Architecture Volumes

| Area | Entry point | Purpose |
|---|---|---|
| Foundation | [01_Foundation](handbook/01_Foundation/README.md) | Identity, theory, mission, vision, principles, and Enterprise Intelligence. |
| Business | [02_Business](handbook/02_Business/README.md) | Market, value, strategy, beachhead, and capability map. |
| Domain | [03_Domain](handbook/03_Domain/README.md) | Advanced-materials domain language and boundaries. |
| Information | [04_Information](handbook/04_Information/README.md) | Canonical objects, relationships, events, provenance, quality, and governance. |
| Knowledge | [05_Knowledge](handbook/05_Knowledge/README.md) | Capture, graph, lifecycle, validation, and governance. |
| Decision | [06_Decision](handbook/06_Decision/README.md) | Evidence, alternatives, recommendations, execution, outcomes, and learning. |
| AI | [07_AI](handbook/07_AI/README.md) | AI capabilities, RAG, lifecycle, governance, safety, and evaluation. |
| Agents | [08_Agents](handbook/08_Agents/README.md) | Governed agent types, tools, orchestration, memory, safety, and evaluation. |
| Platform | [09_Platform](handbook/09_Platform/README.md) | Services, APIs, data, graph, events, integration, IAM, and operations. |
| Deployment | [10_Deployment](handbook/10_Deployment/README.md) | Cloud/on-premise strategy, environments, reliability, and compliance. |

## Implementation Architecture

- [Implementation overview](implementation/README.md)
- [Release 1.4 scope](implementation/IMPLEMENTATION_SCOPE_1_4.md)
- [MVP architecture](implementation/MVP_ARCHITECTURE.md)
- [Database persistence layer](implementation/DATABASE_PERSISTENCE_LAYER.md)
- [Persistent API layer](implementation/PERSISTENT_API_LAYER.md)
- [Application source](../src/smartcoat/)
- [Tests](../tests/)
- [Database assets](../database/README.md)

Implementation files are evidence of the current scaffold, not proof that all
North-Star capabilities exist or are production ready.

## Decisions, Releases, and Navigation

- [ADR index](indexes/ADR_INDEX.md)
- [Release index](indexes/RELEASE_INDEX.md)
- [Handbook index](indexes/HANDBOOK_INDEX.md)
- [Reference-model index](indexes/REFERENCE_MODEL_INDEX.md)
- [Diagram index](indexes/DIAGRAM_INDEX.md)
- [Template index](indexes/TEMPLATE_INDEX.md)
- [Governance index](indexes/GOVERNANCE_INDEX.md)

## Governance and Quality

- [Architecture governance](governance/README.md)
- [Canonical glossary](glossary/README.md)
- [Architecture quality](quality/README.md)
- [Consistency/refactoring plan](refactoring/README.md)
- [Implementation readiness review](reviews/IMPLEMENTATION_READINESS_REVIEW.md)

Update this portal whenever a major architecture area, implementation entry
point, index, or active project-state source changes.
