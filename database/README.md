# SmartCoat Database

Version: 1.0 Draft

---

# Purpose

This directory contains database schemas, migrations, seed data, and database documentation.

Release 1.4 introduces the first PostgreSQL migration for the Knowledge Capture MVP scaffold.

---

# Current Migration

`database/migrations/0001_initial.sql`

Creates:

- knowledge_objects
- decision_objects
- enterprise_events

---

# Database Rule

Database objects must derive from the Canonical Information Model, Knowledge Architecture, and Decision Architecture.
