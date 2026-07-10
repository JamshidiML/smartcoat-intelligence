# AGENTS.md

Repository: SmartCoat Intelligence

Applies to: Entire repository unless a deeper `AGENTS.md` overrides a specific subdirectory.

Last updated: 2026-07-10

---

## 1. Project Mission

SmartCoat Intelligence is Enterprise Intelligence Infrastructure for Advanced Materials organizations.

The initial beachhead is technical textiles, functional coatings, high-temperature materials, formulations, production, quality, suppliers, and industrial R&D decision-making.

The active product focus is a Knowledge Capture MVP that helps industrial users capture, review, preserve, retrieve, and reuse trustworthy knowledge with evidence and provenance.

Do not treat SmartCoat as a generic chatbot, a simple formulation calculator, or an ungoverned document-ingestion system.

---

## 2. Read Before Making Changes

Before implementing a task, read the relevant parts of:

1. `docs/project/PROJECT_STATE.md`
2. `docs/project/MVP_STRATEGY.md`
3. `docs/project/DECISION_LOG.md`
4. `SECURITY.md`
5. `CONTRIBUTING.md`
6. relevant architecture handbook and reference-model files
7. relevant ADRs
8. the issue or task acceptance criteria

For historical context only:

- `docs/project/PROJECT_HISTORY.md`

Historical documents and chat-derived ideas are not automatically active requirements.

---

## 3. Current Release Focus

Current active release:

**Release 1.7 — Project Reset & Engineering Baseline**

Primary goals:

- synchronize documentation and implementation
- establish a reliable engineering baseline
- add or improve CI
- validate tests, linting, typing, and local development
- inspect and correct persistence and Docker inconsistencies
- prove the API-to-PostgreSQL path with integration testing
- prepare a stable base for Release 1.8

Do not add major new product capabilities during Release 1.7 unless the issue explicitly requires them.

---

## 4. Architecture Rules

### Architecture First, Not Architecture Only

Implementation must align with the approved architecture and canonical language.

However, do not create unnecessary abstractions, services, entities, or documents without a validated use case.

### Preserve Canonical Concepts

Use established terms consistently, including:

- Enterprise Knowledge
- Knowledge Object
- Decision Object
- Enterprise Event
- Evidence
- Provenance
- Context
- Lifecycle State
- Review Status
- Confidence
- Outcome
- Learning

Do not introduce synonyms that fragment the domain language without explicit approval.

### Thin Routes

FastAPI routes should primarily:

- validate requests
- resolve dependencies
- call application services
- map expected errors to HTTP responses
- return response models

Do not put persistence or complex domain logic directly in routes.

### Services Own Application Behavior

Application services should coordinate use cases and domain behavior.

### Repositories Own Persistence

Repositories should isolate database access and return canonical domain objects or explicitly documented persistence types.

Avoid inconsistent repository return types.

### Domain Models Remain Canonical

Do not allow database records, external payloads, or framework-specific objects to silently become the source of domain truth.

---

## 5. Product Rules

### No Manual JSON as the Product UX

JSON is acceptable for APIs and tests. Do not design the end-user experience around manually authored JSON.

### Human in the Loop

AI-extracted or AI-generated knowledge must be reviewable and must not silently become trusted enterprise knowledge.

### Preserve Uncertainty

Do not convert unknown, assumed, inferred, or conflicting information into false certainty.

### Evidence and Provenance

New knowledge-related features must consider:

- source
- evidence
- actor or creator
- method
- timestamp
- lifecycle
- review or validation status

### Minimum Scope

Do not implement the complete enterprise ontology in the MVP.

Only add domain entities required by an approved use case and acceptance criteria.

---

## 6. Security and Data Rules

Read `SECURITY.md` before handling data.

Never commit:

- `.env` files
- passwords, tokens, API keys, or credentials
- private keys or certificates
- proprietary formulations
- customer-confidential information
- supplier-confidential information
- pricing data
- raw production data
- internal emails
- personal data
- unapproved technical reports
- raw chat exports
- unapproved enterprise datasets

Use synthetic, anonymized, or minimal test fixtures.

If a task appears to require confidential data, stop and request an explicit data-boundary decision.

---

## 7. Working Method

### Start From an Issue

Each non-trivial change should have:

- problem statement
- scope
- non-goals
- acceptance criteria
- test expectations
- documentation expectations

### Use a Dedicated Branch

Recommended names:

- `feature/<short-description>`
- `fix/<short-description>`
- `docs/<short-description>`
- `refactor/<short-description>`
- `release/<version-description>`

Do not commit directly to `main` unless explicitly instructed.

### Keep Changes Bounded

Avoid unrelated refactoring in the same pull request.

If an important unrelated problem is discovered:

1. document it in the PR
2. create or recommend a separate issue
3. do not expand scope silently

### Pull Request Content

Every PR should explain:

- what changed
- why it changed
- architecture impact
- security or data impact
- tests run
- documentation updated
- known limitations
- follow-up work

---

## 8. Development Setup

Expected Python version:

```text
Python 3.12+
```

Install:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Run unit tests:

```bash
pytest
```

Run lint checks:

```bash
ruff check .
```

Run formatting check when configured:

```bash
ruff format --check .
```

Run type checks:

```bash
mypy src
```

Run API locally:

```bash
uvicorn smartcoat.api.main:app --reload
```

Run local PostgreSQL:

```bash
docker compose up -d postgres
python scripts/init_db.py
```

Do not claim a command passed unless it was actually executed in the working environment.

---

## 9. Testing Rules

For behavior changes:

- add or update tests
- test success cases
- test expected failure cases
- preserve domain-model validation
- avoid tests that only duplicate implementation details

For persistence changes:

- include mapper tests where relevant
- include repository tests
- include integration coverage for the real persistence path when feasible

For API persistence behavior:

Do not rely only on dependency overrides with in-memory services. The project needs explicit integration coverage for:

```text
HTTP request
→ FastAPI route
→ service
→ repository
→ PostgreSQL
→ repository
→ domain response
```

Use isolated test data and a controlled test database.

---

## 10. Database and Migration Rules

- schema changes require migration consideration
- do not edit historical migrations casually after they are treated as applied
- keep SQLAlchemy models and migrations aligned
- preserve IDs, timestamps, lifecycle, provenance, and metadata semantics
- avoid storing all future domain structure in ungoverned JSON simply to move faster
- use JSONB deliberately for flexible content, not as a substitute for domain design

If adding a new canonical entity, explain why it is required now.

---

## 11. API Rules

- use explicit request and response models
- validate limits and query parameters
- provide deterministic error behavior
- avoid leaking internal exceptions or secrets
- keep endpoint naming consistent
- document new routes
- consider pagination for collection endpoints
- avoid breaking API changes without an explicit migration or versioning decision

---

## 12. Documentation Rules

Update documentation when code changes behavior, setup, architecture, or release status.

At minimum, consider:

- `README.md`
- `ROADMAP.md`
- `CHANGELOG.md`
- release records
- ADR index
- release index
- implementation architecture notes
- project state

Do not create duplicate documents when an existing canonical document should be updated.

Use clear English for repository documentation unless a task explicitly requires another language.

---

## 13. Definition of Done

A task is complete only when:

- acceptance criteria are met
- tests are added or updated
- relevant tests pass
- linting passes or remaining failures are documented
- type-check impact is reviewed
- documentation is updated
- security and data impact are reviewed
- no secrets or confidential data are included
- the PR clearly states limitations and follow-up work

---

## 14. Stop Conditions

Stop and request clarification before proceeding when a task would:

- change the core product definition
- redefine canonical domain language
- introduce a major new architecture pattern
- add a new infrastructure platform or database
- use confidential enterprise data
- weaken security controls
- bypass human review for trusted knowledge
- expand the MVP into multiple long-term capability domains
- require destructive migration or irreversible data loss

---

## 15. Current Known Baseline Review Items

During Release 1.7, inspect and verify at least:

- root documentation lag behind Releases 1.3–1.6
- release and ADR index completeness
- Docker API-to-PostgreSQL connection configuration
- repository return-type consistency, especially Enterprise Event persistence
- real integration testing for persistent API routes
- absence or incompleteness of CI
- lint and type-check status
- local setup reproducibility
- API parameter validation
- migration and model alignment

Do not assume these are all confirmed bugs. Reproduce and document findings before changing behavior.
