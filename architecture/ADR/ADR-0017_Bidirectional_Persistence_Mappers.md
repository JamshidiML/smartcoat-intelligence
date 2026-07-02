# ADR-0017 Bidirectional Persistence Mappers

Status: Accepted

---

# Context

SmartCoat separates domain models from persistence models.

Repositories need to convert objects in both directions.

---

# Decision

Persistence mappers shall be bidirectional.

Each persisted canonical object requires:

- domain object to ORM record mapper
- ORM record to domain object mapper

---

# Consequences

- Repository classes can return canonical domain objects.
- API and service layers remain independent from SQLAlchemy ORM records.
- Future storage changes can preserve domain object contracts.
