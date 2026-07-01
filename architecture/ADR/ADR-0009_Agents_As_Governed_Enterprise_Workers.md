# ADR-0009 Agents As Governed Enterprise Workers

Status: Accepted

---

# Context

SmartCoat uses agents to support knowledge capture, context retrieval, decision preparation, workflow execution, and enterprise learning.

If agents are treated as generic chatbots, they may become unsafe, ungoverned, inconsistent, or disconnected from enterprise architecture.

---

# Decision

SmartCoat agents shall be treated as governed enterprise workers operating within domain boundaries, ontology, enterprise language, access control, knowledge governance, decision governance, and human accountability.

---

# Consequences

- Agents must have defined responsibilities and permissions.
- Agents must operate through approved tools.
- Agents must log important actions.
- Agents must respect knowledge security.
- Agents must support human decision-makers.
- Agent outputs must be connected to Knowledge Objects, Decision Objects, Events, or Workflows.
