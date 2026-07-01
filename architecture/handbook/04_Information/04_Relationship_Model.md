# 04 Relationship Model

Version: 1.0

Status: Draft

---

# Purpose

This chapter defines the Relationship Model of SmartCoat.

Relationships are the foundation of enterprise context.

---

# Definition

A relationship is a typed, directional, versioned connection between two or more enterprise objects.

Relationships transform isolated data into enterprise context.

---

# Relationship Structure

Every relationship should include:

- relationship_id
- relationship_type
- source_object
- target_object
- direction
- confidence
- evidence
- provenance
- valid_from
- valid_to
- lifecycle_state

---

# Relationship Examples

- Material supplied by Supplier
- Formulation contains Material
- Product serves Customer
- Batch uses Formulation
- Quality Test evaluates Batch
- Regulation constrains Material
- Decision modifies Process
- Failure has Root Cause
- Lesson Learned improves Future Decision

---

# Relationship Rule

No enterprise object should remain isolated if meaningful relationships exist.

Context is created through relationships.
