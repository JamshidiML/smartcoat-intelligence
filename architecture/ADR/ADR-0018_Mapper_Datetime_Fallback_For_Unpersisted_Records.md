# ADR-0018 Mapper Datetime Fallback For Unpersisted Records

Status: Accepted

---

# Context

Persistence mappers must support tests where ORM records are created in memory before database flush.

Database-generated timestamps are unavailable in that state.

---

# Decision

Record-to-domain mapper functions shall use safe fallback timestamps when ORM records do not yet contain database-generated timestamps.

---

# Consequences

- Mapper tests do not require a live database.
- Domain objects remain valid.
- Persisted database records still preserve database timestamps when available.
