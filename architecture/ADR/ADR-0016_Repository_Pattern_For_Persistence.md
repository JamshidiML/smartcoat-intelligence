# ADR-0016 Repository Pattern For Persistence

Status: Accepted

---

# Context

SmartCoat must persist Knowledge Objects, Decision Objects, and Enterprise Events.

Direct database access from API routes or agents would couple implementation logic to storage details.

---

# Decision

SmartCoat shall use a repository pattern for persistence.

Application services and API routes should interact with repositories rather than directly with SQLAlchemy sessions.

---

# Consequences

- SQLAlchemy ORM models remain in the storage layer.
- Domain models remain independent Pydantic models.
- Repositories map domain objects to database objects.
- Future services can replace or extend repositories without changing API contracts.
