# SmartCoat Intelligence

SmartCoat is a horizontal Enterprise Intelligence mother platform whose North
Star is to help industrial companies become connected, learning, adaptive
systems under explicit human governance.

Technical textiles and functional coatings are the first proof domain, not the
platform boundary. The current product path begins with a focused Knowledge
Capture MVP; it does not claim the full Living Industry vision is implemented.

## Current State

Active work is **Release 1.7 - Project Reset & Engineering Baseline**. Its core
project-state and execution-control documents are merged. The ten specialized
thread outputs have been independently reviewed and corrected on draft pull
requests, but they are not accepted or merged by that review alone.

The repository already contains:

- architecture and governance through Release 1.3
- a Python/FastAPI implementation scaffold from Release 1.4
- SQLAlchemy/PostgreSQL persistence and mappers from Releases 1.5-1.5.2
- repository-backed persistent API routes from Release 1.6
- merged Release 1.7 project-state, decision, strategy, and execution-control documents

Release 1.7 engineering, persistence, governance, schema, ingestion, pilot, and
quality-system changes remain in progress until their draft pull requests are
accepted, merged in the approved order, and validated together.

See [Project State](docs/project/PROJECT_STATE.md) for verified current facts
and [Project History](docs/project/PROJECT_HISTORY.md) for chronology.

## Work Status

| Status | Current meaning |
|---|---|
| Accepted | Project decisions in the Decision Log and ADRs listed by the accepted ADR index. |
| Merged | Historical Releases 0.1-1.6 and the core Release 1.7 reset/control documents present on the integration baseline. |
| In progress | Release 1.7 and Correction Cycle 3. Release completion has not been declared. |
| Independently reviewed | Draft PRs #25-#34 received reviewer scores and corrections; review did not accept or merge them. |
| Proposed | The T01 Living Industry Platform Model and other new thread contracts remain proposals until separately accepted and merged. |

The [Living Industry Platform Model](docs/strategy/LIVING_INDUSTRY_PLATFORM_MODEL.md)
is a proposed clarification, not an accepted replacement for the active North
Star or existing ADRs. It is supplied by draft PR #28 and is intentionally
integrated only after its governance dependencies are accepted.

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

Python 3.12 or newer is required. The constrained baseline is documented in
[Engineering Baseline](docs/development/ENGINEERING_BASELINE.md) and pinned by
[Python 3.12 constraints](requirements/constraints-py312.txt).

```bash
python -m venv .venv
.venv/bin/python -m pip install \
  --constraint requirements/constraints-py312.txt -e '.[dev]'
.venv/bin/python -m pip check
.venv/bin/python -m pytest
```

Those two baseline files are owned by T03 draft PR #25. On the current isolated
T02 branch they are cross-thread integration targets; use this command after T03
is accepted and merged into the integration branch.

Additional measured checks:

```bash
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy src
```

Do not report these checks as passing unless they were actually run. The T03
baseline records remaining Ruff/format debt and the isolated-versus-integrated
MyPy evidence explicitly.

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
