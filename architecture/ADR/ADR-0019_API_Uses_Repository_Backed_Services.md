# ADR-0019 API Uses Repository Backed Services

Status: Accepted

---

# Context

SmartCoat API routes must expose Knowledge Objects, Decision Objects, and Enterprise Events.

Directly writing database logic inside routes would couple API design to persistence implementation and weaken service boundaries.

---

# Decision

SmartCoat API routes shall use dependency-injected repositories and service classes for persistent operations.

---

# Rationale

This supports:

- testability
- separation of concerns
- future authentication and authorization
- future graph synchronization
- future event publishing
- future agent workflows
- cleaner service boundaries

---

# Consequences

- API routes depend on database session dependencies.
- Repositories handle persistence.
- Services encapsulate application behavior.
- Tests can override dependencies.
