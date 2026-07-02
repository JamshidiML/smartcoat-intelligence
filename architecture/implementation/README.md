# Implementation Architecture

Version: 1.0 Draft

---

# Purpose

This directory contains implementation-specific architecture notes for SmartCoat.

It connects the multi-volume enterprise architecture to actual code, services, database objects, APIs, tests, and development environments.

---

# Current Implementation Scope

Release 1.4 introduces the Knowledge Capture MVP scaffold.

The implementation is intentionally narrow:

- Knowledge Objects
- Decision Objects
- Enterprise Events
- Memory Agent skeleton
- Lab Agent skeleton
- API skeleton
- PostgreSQL migration
- tests
- Docker Compose development environment

---

# Implementation Rule

Code must use canonical enterprise language.

Implementation must not redefine Foundation concepts.
