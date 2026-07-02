# Release 1.5.1 — Persistence Mapper Hotfix

Version: 1.5.1

Status: Draft

---

# Purpose

This hotfix fixes missing mapper functions in the Database & Persistence Layer.

---

# Problem

The test suite failed because `decision_repository.py` imported `record_to_decision`, but `mappers.py` did not define it.

The same issue could affect Enterprise Event conversion.

---

# Fix

This release adds:

- `record_to_decision`
- `record_to_event`

It also updates mapper tests to verify round-trip conversion from domain objects to ORM records and back to domain objects.

---

# Architectural Rule

Repository mappers must support both directions:

Domain Object → Persistence Record

Persistence Record → Domain Object
