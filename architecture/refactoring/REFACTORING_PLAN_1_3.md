# Refactoring Plan 1.3

Version: 1.0

Status: Draft

---

# Purpose

This document defines the recommended refactoring actions after the architecture consistency review.

---

# Refactoring Goals

- improve repository navigation
- reduce terminology drift
- align indexes with actual files
- confirm ADR coverage
- prepare implementation scaffold
- preserve release history
- avoid unnecessary restructuring

---

# Refactoring Actions

## Action 1 — Verify Folder Structure

Expected architecture structure:

```text
architecture/
├── ARCHITECTURE_PORTAL.md
├── ADR/
├── diagrams/
├── glossary/
├── governance/
├── handbook/
├── indexes/
├── reference_models/
├── refactoring/
├── releases/
├── reviews/
├── quality/
└── templates/
```

## Action 2 — Verify Handbook Volumes

Expected handbook volumes:

```text
01_Foundation
02_Business
03_Domain
04_Information
05_Knowledge
06_Decision
07_AI
08_Agents
09_Platform
10_Deployment
```

## Action 3 — Terminology Cleanup

Search for deprecated terms:

```text
Industrial Intelligence
Engineering Intelligence
Industrial Knowledge
AI Platform
Knowledge Platform
Decision Platform
```

Replace or clarify using canonical terms:

```text
Enterprise Intelligence
Enterprise Knowledge
Enterprise Context
Enterprise Decision Intelligence
Organizational Capability
Learning Enterprise
```

## Action 4 — ADR Coverage Check

Confirm all major architecture decisions have ADRs.

Missing physical ADR files should be created if they are still relevant.

## Action 5 — Index Completeness

Update:

- RELEASE_INDEX.md
- ADR_INDEX.md
- DIAGRAM_INDEX.md
- TEMPLATE_INDEX.md
- HANDBOOK_INDEX.md
- REFERENCE_MODEL_INDEX.md
- GOVERNANCE_INDEX.md

## Action 6 — Link Review

Check major links in:

- README.md
- ARCHITECTURE_PORTAL.md
- indexes
- governance documents
- release records

## Action 7 — Implementation Scope Lock

Before implementation starts, define the exact scope of Release 1.4.

Recommended:

Implementation Scaffold for Knowledge Capture MVP.

---

# Refactoring Decision

Do not reorganize folders unless necessary.

The current structure is acceptable.

Prioritize consistency, indexes, glossary, and implementation readiness.
