# 11 Domain Boundaries

Version: 1.0

Status: Draft

---

# Purpose

This chapter defines domain boundaries within SmartCoat.

Boundaries prevent conceptual confusion and support scalable architecture.

---

# Boundary Principle

Domains are separated by responsibility, not by department.

A domain owns meaning.

A department owns work.

---

# Examples

Materials owns material meaning.

Suppliers owns supplier meaning.

Manufacturing owns production execution meaning.

Quality owns test and failure meaning.

Customers owns requirement and feedback meaning.

Regulations owns compliance meaning.

R&D owns experimentation and learning meaning.

---

# Cross-Domain Objects

Some objects appear across domains.

Examples:

- Product
- Project
- Decision
- Risk
- Cost
- Requirement
- Evidence
- Lesson Learned

These objects must follow canonical definitions from Enterprise Language and Ontology.

---

# Boundary Rule

When a concept crosses domain boundaries, its canonical definition must come from the Foundation and Reference Models.
