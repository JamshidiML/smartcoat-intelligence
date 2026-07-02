# Release 1.5.2 — Mapper Datetime Hotfix

Version: 1.5.2

Status: Draft

---

# Purpose

This hotfix fixes mapper round-trip tests for persistence records that have not yet been flushed to the database.

---

# Problem

SQLAlchemy records created in memory do not automatically receive database-generated `created_at` and `updated_at` timestamps.

The mapper attempted to pass `None` into Pydantic datetime fields, causing validation errors.

---

# Fix

Mapper functions now use safe datetime fallback values:

- use record timestamp if available
- otherwise use current UTC timestamp

---

# Architectural Rule

Mapper tests should validate object conversion without requiring a live database connection.
