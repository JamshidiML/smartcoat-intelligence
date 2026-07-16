# SmartCoat Intelligence

SmartCoat is a horizontal Enterprise Intelligence mother platform whose North
Star is to help industrial companies become connected, learning, adaptive
systems under explicit human governance.

Technical textiles and functional coatings are the first proof domain, not the
platform boundary. The current product path begins with a focused Knowledge
Capture MVP; it does not claim the full Living Industry vision is implemented.

## Current State

Active work is **Release 1.7 — Project Reset & Engineering Baseline**. It aligns
documentation and implementation, establishes reliable development and CI
baselines, and validates the current FastAPI-to-PostgreSQL path before Release
1.8 Knowledge Capture Core.

The repository already contains:

- architecture and governance through Release 1.3
- a Python/FastAPI implementation scaffold from Release 1.4
- SQLAlchemy/PostgreSQL persistence and mappers from Releases 1.5-1.5.2
- repository-backed persistent API routes from Release 1.6
- Release 1.7 reset, validation, and controlled-pilot preparation

See [Project State](docs/project/PROJECT_STATE.md) for verified current facts
and [Project History](docs/project/PROJECT_HISTORY.md) for chronology.

## Strategic Boundaries

| Concept | Meaning |
|---|---|
| North Star | Long-term Living Industry and Enterprise Intelligence direction. |
| Mother platform | Reusable horizontal knowledge, context, decision, event, governance, and learning capabilities. |
| Technical-textile proof domain | First real industry context used to validate the platform thesis. |
| Knowledge Capture MVP | First implementation slice for capture, review, retrieval, and reuse. |
| Release 1.7 | Current coherence and engineering-baseline work, not a new autonomy claim. |

## Start Here

- [SmartCoat North Star](docs/strategy/SMARTCOAT_NORTH_STAR.md)
- [Project State](docs/project/PROJECT_STATE.md)
- [MVP Strategy](docs/project/MVP_STRATEGY.md)
- [Decision Log](docs/project/DECISION_LOG.md)
- [Execution Control Center](docs/execution/EXECUTION_CONTROL_CENTER.md)
- [Architecture Portal](architecture/ARCHITECTURE_PORTAL.md)
- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)
- [Repository Structure](REPOSITORY_STRUCTURE.md)

## Core Model

```text
Enterprise Knowledge
    -> Enterprise Context
    -> Enterprise Intelligence
    -> Enterprise Decisions
    -> Execution and Outcomes
    -> Learning and Organizational Capability
```

Artificial intelligence, agents, data platforms, knowledge graphs, software,
machines, and automation are capabilities inside this model. High-impact,
safety-critical, legal, strategic, irreversible, or uncertain decisions require
stronger human oversight.

## Architecture and Implementation

- [Architecture handbook](architecture/handbook/README.md)
- [Reference models](architecture/reference_models/README.md)
- [Accepted ADR index](architecture/indexes/ADR_INDEX.md)
- [Release index](architecture/indexes/RELEASE_INDEX.md)
- [Implementation architecture](architecture/implementation/README.md)
- [Application source](src/smartcoat/)
- [Automated tests](tests/)
- [Database assets](database/README.md)

## Development

Python 3.12 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
```

Additional measured checks:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy src
```

Do not report these checks as passing unless they were actually run. Current
baseline details belong in Release 1.7 engineering reports.

## Data Boundary

Do not commit secrets, credentials, `.env` files, proprietary formulations,
customer or supplier confidential information, prices, production records,
personal data, internal communications, or unapproved industrial datasets. Use
synthetic, anonymized, generalized, or explicitly approved data only. Read
[SECURITY.md](SECURITY.md) before data work.

## Contribution Workflow

Read [AGENTS.md](AGENTS.md), [CONTRIBUTING.md](CONTRIBUTING.md), the relevant
project decisions, architecture, and issue acceptance criteria. Use a dedicated
branch and reviewed pull request; do not expand scope silently.
