# SmartCoat Repository Structure

Version: 1.0 Draft

---

# Purpose

This document explains the intended repository structure of SmartCoat Intelligence.

---

# Root Files

## README.md

Main repository introduction and navigation.

## ROADMAP.md

High-level development roadmap.

## CHANGELOG.md

Human-readable release history.

## CONTRIBUTING.md

Contribution rules and workflow.

## SECURITY.md

Security policy and responsible handling of sensitive knowledge.

## REPOSITORY_STRUCTURE.md

Explanation of repository organization.

---

# Architecture Directory

`architecture/`

The architecture directory contains the Enterprise Intelligence Architecture.

## handbook/

Main multi-volume architecture handbook.

## reference_models/

Stable reference models used across all architecture and implementation.

## ADR/

Architecture Decision Records.

## diagrams/

Mermaid diagrams for architecture visualization.

## templates/

Reusable templates for architecture and implementation artifacts.

## glossary/

Canonical enterprise language and terminology governance.

## governance/

Architecture governance documents.

## indexes/

Navigation indexes.

## releases/

Release records.

---

# Implementation Directories

## src/

Application source code.

## tests/

Automated tests.

## database/

Database schemas, migrations, seed data, and database architecture.

## data/

Local data directory.

Sensitive or raw data should not be committed unless explicitly allowed.

## notebooks/

Exploration, experiments, and research notebooks.

## agents/

Agent specifications, prototypes, and workflows.

## ai/

AI, ML, retrieval, prediction, and reasoning modules.

## integrations/

Integration connectors for ERP, email, Teams, supplier APIs, and other systems.

## knowledge/

Knowledge rules, taxonomies, standards, and ontology implementation artifacts.

---

# Repository Rule

Architecture defines implementation.

Implementation must not introduce core concepts that conflict with architecture.
