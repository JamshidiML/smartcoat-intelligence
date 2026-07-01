# 05 Manufacturing Domain

Version: 1.0

Status: Draft

---

# Purpose

This chapter defines the Manufacturing Domain.

The Manufacturing Domain represents how products are physically produced, processed, inspected, and improved.

---

# Core Entities

- Production Site
- Production Line
- Machine
- Process
- Process Step
- Batch
- Production Order
- Operator
- Process Parameter
- Temperature
- Speed
- Pressure
- Coating Thickness
- Cure Condition
- Mixing Condition
- Machine Setting
- Production Event
- Production Deviation
- Production Report

---

# Key Relationships

- Batch uses Formulation
- Batch uses Material Batch
- Batch produced on Machine
- Machine belongs to Production Line
- Process Parameter affects Quality Result
- Production Event creates Observation
- Deviation triggers Investigation
- Operator records Experience
- Production Report creates Knowledge

---

# Strategic Importance

Manufacturing knowledge is often tacit and operational.

Small variations in process parameters, machine behavior, operator observations, and environmental conditions can strongly affect product performance.

SmartCoat must preserve production context and connect it to materials, formulations, quality, defects, cost, and customer outcomes.

---

# Domain Rule

Manufacturing data must be transformed into manufacturing knowledge by preserving context, reasoning, deviations, and lessons learned.
