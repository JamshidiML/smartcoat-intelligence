# Release 1.6 — Persistent API Layer

Version: 1.6

Status: Draft

---

# Purpose

This release connects SmartCoat API routes to the persistence layer.

Release 1.4 introduced an in-memory API scaffold.

Release 1.5 introduced the database and repository layer.

Release 1.6 connects API routes to repositories so Knowledge Objects, Decision Objects, and Enterprise Events can be persisted through API calls.

---

# Scope

This release includes:

- API database session dependency
- persistent Knowledge API route
- persistent Decision API route
- new Enterprise Event API route
- service layer updates for repository-backed persistence
- FastAPI dependency injection
- route tests using dependency overrides
- persistent API architecture documentation
- persistent API ADR

---

# MVP Focus

This release supports the Knowledge Capture MVP by making API-created enterprise objects persistence-ready.

---

# Out of Scope

This release does not implement:

- authentication
- authorization
- production access control
- pagination beyond simple limits
- advanced filtering
- graph synchronization
- vector search
- UI
- external integrations

---

# Architectural Rule

API routes must not directly own enterprise logic.

Routes should delegate persistence and business behavior to services and repositories.
