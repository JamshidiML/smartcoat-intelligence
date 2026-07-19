# SmartCoat Repository Structure

This guide describes the repository as it exists in Release 1.7. Empty or
future directories are not presented as implemented capability.

## Root Entry Points

| File | Purpose |
|---|---|
| [README.md](README.md) | Project identity, current state, navigation, and development entry point. |
| [ROADMAP.md](ROADMAP.md) | North-Star direction and approved release execution. |
| [CHANGELOG.md](CHANGELOG.md) | Human-readable release history. |
| [AGENTS.md](AGENTS.md) | Repository-wide agent and engineering instructions. |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution workflow. |
| [SECURITY.md](SECURITY.md) | Sensitive-data and security boundary. |

## Architecture

`architecture/` contains the conceptual, implementation, governance, and
release architecture:

- `handbook/`: foundation through deployment volumes
- `reference_models/`: reusable conceptual contracts
- `ADR/`: accepted architecture decisions
- `implementation/`: Release 1.4-1.6 implementation architecture
- `diagrams/`: Mermaid architecture diagrams
- `templates/`: repeatable architecture and implementation templates
- `glossary/`: canonical terminology and forbidden synonyms
- `governance/`: documentation, release, ADR, diagram, review, and versioning rules
- `indexes/`: navigation for releases, ADRs, diagrams, templates, and handbook assets
- `quality/` and `refactoring/`: consistency and readiness evidence
- `releases/`: release records through active Release 1.7
- `legacy/`: retained historical architecture, not current source of truth

Start at [Architecture Portal](architecture/ARCHITECTURE_PORTAL.md).

## Project and Strategy Documents

`docs/` contains curated active project context:

- `strategy/SMARTCOAT_NORTH_STAR.md`: long-term strategic vision
- `project/PROJECT_STATE.md`: verified current state
- `project/PROJECT_HISTORY.md`: historical chronology
- `project/MVP_STRATEGY.md`: focused product path
- `project/DECISION_LOG.md`: accepted and open decisions
- `execution/`: merged Release 1.7 control and thread instructions; individual
  reports become merged repository evidence only through their owning PRs

Cross-thread draft targets are not treated as current files merely because they
exist in another worktree. Notable targets include the proposed T01 Living
Industry model and the independently reviewed T03 engineering baseline and
constraints. Root links to those targets are valid for the planned integrated
branch, but their status remains proposed or independently reviewed until merge.

## Application

`src/smartcoat/` contains the current implementation scaffold:

- `domain/`: canonical domain models
- `services/`: application services
- `storage/`: database sessions, records, repositories, and mappers
- `api/`: FastAPI application, dependencies, and routes
- `agents/`: early Memory/Lab agent scaffolds
- `ai/`: early retrieval/embedding placeholders
- `core/` and `config.py`: configuration and shared support

The presence of a scaffold does not imply production readiness.

## Validation and Persistence

- `tests/`: domain, agent, API, mapper, and repository-oriented tests
- `database/`: SQL schema, migrations, and database notes
- `scripts/`: development/validation scripts
- `docker-compose.yml` and `Dockerfile`: local container setup
- `pyproject.toml`: Python package and tool configuration

## Data Safety

`data/`, attachments, local databases, and environment files must not be used as
a route for committing sensitive enterprise information. Follow
[SECURITY.md](SECURITY.md) and use synthetic or explicitly approved fixtures.

## Ownership Rule

Architecture defines canonical language and constraints; implementation must
remain traceable to approved use cases and decisions. Historical and draft
documents provide context but do not automatically become active requirements.

## Documentation Preservation Rule

Synchronization adds current summaries and navigation without deleting valid
historical detail. If a statement becomes obsolete, label it superseded and
link its accepted replacement. Before removing content, compare the target
branch, release records, and accepted decisions, then document the reason and
coverage impact in the pull request.
