# Release 1.5 — Database & Persistence Layer

Version: 1.5

Status: Draft

---

# Purpose

This release introduces the first real database and persistence layer for SmartCoat.

Release 1.4 used in-memory services for the initial scaffold. Release 1.5 introduces SQLAlchemy database models, session management, repository classes, database initialization script, and persistence-ready service patterns.

---

# Scope

This release includes:

- SQLAlchemy declarative base
- database session management
- ORM models for Knowledge Objects, Decision Objects, and Enterprise Events
- repository pattern
- persistent Knowledge Repository
- persistent Decision Repository
- persistent Event Repository
- database initialization script
- repository tests
- database architecture documentation
- persistence ADR

---

# Architectural Rule

Persistence must preserve canonical enterprise object identity, provenance, lifecycle, and decision usefulness.
