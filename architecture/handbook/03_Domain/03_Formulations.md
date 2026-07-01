# 03 Formulations Domain

Version: 1.0

Status: Draft

---

# Purpose

This chapter defines the Formulations Domain.

The Formulations Domain represents the composition, logic, history, performance, and decision reasoning behind material systems.

---

# Core Entities

- Formulation
- Formula Version
- Ingredient
- Ingredient Ratio
- Processing Instruction
- Mixing Parameter
- Cure Condition
- Viscosity Target
- Pot Life
- Performance Target
- Substitution
- Formulation Decision
- Formulation Risk
- Customer Requirement
- Test Result
- Approval Status

---

# Key Relationships

- Formulation contains Ingredient
- Formulation uses Material
- Formulation targets Product Requirement
- Formulation belongs to Project
- Formulation has Version
- Formulation produces Product
- Formulation evaluated by Quality Test
- Formulation modified by Decision
- Formulation constrained by Regulation
- Formulation affected by Supplier Availability

---

# Strategic Importance

Formulations are not only recipes.

They are accumulated engineering and enterprise knowledge.

A formulation includes:

- scientific reasoning
- cost constraints
- customer requirements
- supplier realities
- production feasibility
- quality history
- regulatory limits
- historical decisions

---

# Domain Rule

Every formulation must preserve its reasoning, not only its composition.
