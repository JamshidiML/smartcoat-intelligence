# SmartCoat Decision Log

Version: 1.0

Status: Active

Last updated: 2026-07-10

---

## Purpose

This log records project-level product and execution decisions that may not require a full Architecture Decision Record.

Use an ADR when a decision changes core architecture, platform boundaries, canonical models, security posture, or long-term technical direction.

Use this log for product focus, sequencing, working agreements, scope control, and project operating decisions.

---

## Decision Status

- Proposed
- Accepted
- Superseded
- Rejected
- Deferred

---

## D-001 — SmartCoat Is Enterprise Intelligence Infrastructure

Status: Accepted

Decision:

SmartCoat is defined as Enterprise Intelligence Infrastructure for Advanced Materials organizations, beginning with technical textiles and functional coatings.

Rationale:

The product must connect knowledge, context, evidence, decisions, outcomes, and learning. A generic AI assistant or isolated optimization model is too narrow.

Consequences:

- architecture remains broader than a single AI use case
- product delivery must still begin with narrow validated workflows

---

## D-002 — Architecture Guides Implementation

Status: Accepted

Decision:

Core implementation concepts must derive from approved architecture, canonical language, reference models, governance, and ADRs.

Rationale:

The repository already contains a substantial architecture baseline. Allowing implementation to invent conflicting concepts would destroy traceability.

Consequences:

- major implementation changes require architecture review
- architecture may be refined when product evidence shows a better model
- architecture is not immutable, but changes must be explicit

---

## D-003 — Canonical Models Before Uncontrolled Bulk Ingestion

Status: Accepted

Decision:

Large-scale ingestion of spreadsheets, PDFs, emails, images, ERP records, and other enterprise sources will not begin before source mapping, canonical object definitions, provenance, confidentiality, and validation rules are defined for the selected pilot scope.

Rationale:

Uncontrolled ingestion would create an ungoverned data swamp and make later normalization more expensive.

Consequences:

- pilot ingestion must be narrow and mapped
- raw enterprise data remains outside the source-code repository

---

## D-004 — Knowledge Capture Is the First Product MVP

Status: Accepted

Decision:

The first product MVP is Knowledge Capture for industrial R&D, not formulation optimization, full knowledge graph, autonomous decision-making, or enterprise-wide integration.

Rationale:

Reliable capture is foundational for future search, knowledge graph, reasoning, decision intelligence, and AI.

Consequences:

- Releases 1.8–2.1 prioritize capture, review, persistence, retrieval, and pilot validation
- long-term capability domains remain strategic, not immediate scope

---

## D-005 — Manual JSON Is Not an End-User Experience

Status: Accepted

Decision:

End users will not be required to create JSON payloads manually.

Rationale:

Manual JSON increases effort, errors, incomplete records, and adoption risk.

Consequences:

- JSON remains an API representation
- user interaction will move toward simple forms, natural language, and voice

---

## D-006 — Human Review Before Knowledge Becomes Trusted

Status: Accepted

Decision:

AI-generated or automatically extracted knowledge must remain in a draft or captured state until reviewed according to governance rules.

Rationale:

Industrial knowledge may affect engineering, quality, safety, procurement, and business decisions.

Consequences:

- lifecycle and review status are required
- confidence is not a substitute for validation
- uncertainty must be preserved

---

## D-007 — Evidence and Provenance Are First-Class

Status: Accepted

Decision:

Knowledge and decision workflows must preserve source, evidence, creator or actor, method, timestamps, and relevant context.

Rationale:

A recommendation without traceable evidence is difficult to trust, audit, or improve.

Consequences:

- evidence and provenance remain part of domain and UI design
- future retrieval should expose why an item is relevant and where it came from

---

## D-008 — The Full Enterprise Ontology Will Not Be Implemented in the MVP

Status: Accepted

Decision:

The MVP will implement only the minimum domain context needed for the first vertical slice.

Rationale:

Implementing every entity and relationship before user validation would create excessive complexity and delay value.

Consequences:

- the enterprise ontology remains a long-term reference
- minimum entities will be selected through use cases and acceptance criteria

---

## D-009 — Release 1.7 Is a Reset Without Rebuilding From Zero

Status: Accepted

Decision:

The existing architecture and implementation will be preserved. Release 1.7 will reconcile, synchronize, test, document, and govern the current baseline rather than discard it.

Rationale:

Substantial valuable work already exists. The problem is drift and coordination, not absence of foundation.

Consequences:

- no unnecessary rewrite
- technical inconsistencies are corrected through reviewed changes
- outdated documents are updated rather than silently ignored

---

## D-010 — GitHub Becomes the Operational Source of Truth

Status: Accepted

Decision:

Active requirements, tasks, implementation changes, and reviews will be managed through GitHub issues, branches, pull requests, and approved repository documents.

Rationale:

Chat is useful for thinking but poor as the only system of record.

Consequences:

- important decisions are curated into repository documents or ADRs
- implementation work starts from an issue or approved release task
- direct commits to `main` should be avoided

---

## D-011 — Three-Role Team Model

Status: Accepted

Decision:

The project will use this operating model:

- Mohsen: Founder, Product Owner, Domain Authority
- ChatGPT: Product Architect, Technical Lead, requirements and review
- Codex: Implementation Engineer for assigned tasks

Rationale:

Clear role separation reduces ambiguity and allows AI tools to complement rather than duplicate each other.

Consequences:

- Codex receives bounded tasks and acceptance criteria
- architecture and product decisions remain reviewed
- Mohsen retains final authority over product direction and sensitive data

---

## D-012 — Codex Works Through Branches and Pull Requests

Status: Accepted

Decision:

Codex implementation work should use a dedicated branch and pull request unless an explicitly approved exception exists.

Rationale:

Reviewed changes improve traceability, safety, testing, and collaboration.

Consequences:

- `AGENTS.md` defines repository-wide instructions
- each task should include scope, non-goals, tests, and acceptance criteria

---

## D-013 — Raw Chat Archive Stays Outside the Repository

Status: Accepted

Decision:

The raw exported project conversation will not be committed to the source repository.

Rationale:

Raw chat may contain duplicated, obsolete, personal, proprietary, or confidential content.

Consequences:

- curated project history and decisions may be committed
- the raw archive remains an external historical source

---

## D-014 — Initial Pilot Must Be Controlled and Measurable

Status: Accepted

Decision:

The first technical-textile pilot will use a limited, approved, sanitized dataset and explicit success metrics.

Rationale:

A narrow pilot reduces security and integration risk while producing evidence of product value.

Consequences:

- no unrestricted company-wide ingestion
- pilot metrics include capture completeness, correction rate, retrieval quality, time saved, and reuse of prior knowledge

---

## D-015 — Current Release Sequence

Status: Accepted

Decision:

The active sequence is:

1. Release 1.7 — Project Reset & Engineering Baseline
2. Release 1.8 — Knowledge Capture Core
3. Release 1.9 — Human Review Interface
4. Release 2.0 — AI-Assisted Knowledge Capture MVP
5. Release 2.1 — Controlled Technical-Textile Pilot

Rationale:

This sequence moves from project coherence to reliable backend behavior, usable interaction, AI assistance, and real-world validation.

Consequences:

- new ideas are evaluated against this sequence
- scope additions require an explicit decision

---

## Open Decisions

The following require future product and technical decisions:

- minimum canonical entities for Release 1.8
- frontend technology for Release 1.9
- model-provider and deployment approach for Release 2.0
- embedding and retrieval architecture
- whether `pgvector` is sufficient for the first semantic-search scope
- pilot data boundary and anonymization rules
- authentication and authorization design before multi-user use
- graph synchronization timing and technology
