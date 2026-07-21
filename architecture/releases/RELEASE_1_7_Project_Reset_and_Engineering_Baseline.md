# Release 1.7 — Project Reset & Engineering Baseline

Version: 1.7

Status: In Progress

Started: 2026-07-10

---

## Purpose

Release 1.7 reconciles SmartCoat's project history, enterprise architecture, implementation baseline, documentation, engineering workflow, and active product direction.

This is not a rewrite and not a restart from zero.

It is a controlled reset that preserves valuable work while creating one reliable foundation for the next product phase.

---

## Why This Release Exists

SmartCoat advanced through architecture, implementation scaffolding, persistence, and a persistent API.

However, several project systems drifted out of alignment:

- root documentation did not fully reflect Releases 1.3–1.6
- indexes and changelog lagged behind the repository
- architecture and implementation status were described inconsistently
- development was largely performed without an issue and pull-request workflow
- the first API exposed engineering capability but not an end-user product experience
- the project needed a clear operating model for Mohsen, ChatGPT, and Codex
- baseline technical inconsistencies required systematic reproduction and review

---

## Release Outcomes

Release 1.7 should deliver:

### Project Coherence

- canonical project state
- curated project history
- focused MVP strategy
- active decision log
- synchronized roadmap and release status

### Team Operating Model

- clear roles for Founder/Product Owner, Product Architect/Technical Lead, and Codex Implementation Engineer
- repository-level `AGENTS.md`
- issue-driven work
- dedicated branches
- pull-request review before merge

### Engineering Baseline

- reproducible local setup
- test baseline
- lint baseline
- type-check baseline
- continuous integration
- verified Docker configuration
- verified API and persistence behavior
- integration test strategy and implementation

### Documentation Synchronization

- update `README.md`
- update `ROADMAP.md`
- update `CHANGELOG.md`
- update release index
- update ADR index
- verify architecture portal and implementation entry points

### MVP Scope Lock

- confirm Knowledge Capture as the active MVP
- define Release 1.8 boundaries
- prevent uncontrolled expansion into all long-term intelligence domains

---

## Initial Files Added

- `docs/project/PROJECT_STATE.md`
- `docs/project/PROJECT_HISTORY.md`
- `docs/project/MVP_STRATEGY.md`
- `docs/project/DECISION_LOG.md`
- `AGENTS.md`
- this release record

---

## Engineering Audit Scope

The Release 1.7 audit should reproduce and evaluate:

1. root documentation lag
2. release and ADR index incompleteness
3. Docker API-to-PostgreSQL connectivity
4. repository return-type consistency
5. Enterprise Event persistence behavior
6. API-to-PostgreSQL integration coverage
7. CI availability and completeness
8. Ruff status
9. MyPy status
10. Pytest status
11. migration and SQLAlchemy model alignment
12. API parameter validation
13. local setup reproducibility
14. secret and data-protection controls

Findings must distinguish:

- confirmed defect
- design inconsistency
- missing test
- documentation drift
- future improvement

Do not change behavior solely from assumption. Reproduce findings first.

---

## Out of Scope

Release 1.7 does not implement:

- end-user UI
- AI extraction
- voice capture
- semantic search
- full Knowledge Graph
- formulation optimization
- supplier optimization
- ERP integration
- bulk document ingestion
- production deployment
- autonomous decision-making

---

## Exit Criteria

Release 1.7 is complete when:

- project state and MVP direction are approved
- documentation reflects the actual implementation baseline
- `AGENTS.md` is approved
- GitHub issue, branch, PR, review, and merge workflow is in use
- CI runs core checks
- baseline tests pass in the supported environment
- confirmed persistence and Docker defects are fixed
- at least one real API-to-PostgreSQL integration path is tested
- known remaining risks are documented
- Release 1.8 scope and acceptance criteria are approved

---

## Architectural Rule

Reset improves coherence without discarding the architecture baseline.

Implementation must continue to derive from canonical language, reference models, governance, and explicit decisions while remaining focused on validated product value.
