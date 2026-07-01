# ADR-0006 Knowledge Graph As Context Backbone

Status: Accepted

---

# Context

SmartCoat requires a way to connect enterprise knowledge across domains, systems, agents, and decisions.

Relational databases are necessary but insufficient for representing evolving semantic context.

---

# Decision

SmartCoat shall use a Knowledge Graph as the context backbone for Enterprise Intelligence.

The Knowledge Graph shall implement the Enterprise Ontology, Relationship Model, Entity Model, Event Model, and Knowledge Object Model.

---

# Consequences

- Knowledge Graph design must derive from ontology.
- Every node and relationship must have provenance.
- AI systems should use the graph for context retrieval.
- Agent memory should connect to graph objects.
- Decision Intelligence should reference graph-supported evidence.
