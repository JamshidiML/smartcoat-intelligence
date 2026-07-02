# Contributing to SmartCoat Intelligence

Version: 1.0 Draft

---

# Purpose

This document defines how contributors should work with the SmartCoat repository.

SmartCoat is an architecture-first project.

Contributions must preserve conceptual consistency, terminology, governance, and traceability.

---

# Contribution Principles

## Architecture First

Do not introduce implementation concepts that conflict with architecture.

## Canonical Language

Use the Enterprise Language and Glossary.

## ADR for Major Decisions

Major decisions require an ADR.

## Release-Based Changes

Large architecture changes should be packaged as releases.

## Review Before Merge

Important changes should be reviewed for terminology, architecture consistency, and governance.

---

# Branching

Recommended branch naming:

```text
feature/<short-description>
architecture/<short-description>
docs/<short-description>
fix/<short-description>
```

---

# Commit Messages

Use clear commit messages.

Examples:

```text
Add Knowledge Architecture release 0.5
Update Enterprise Language glossary
Add Supplier Agent specification
Fix release index links
```

---

# Pull Request Checklist

Before submitting a pull request:

- The change has a clear purpose.
- Canonical terminology is used.
- Related ADRs are updated or created.
- Indexes are updated if new files were added.
- Diagrams are updated if architecture changed.
- Templates are used where applicable.
- No sensitive data is committed.
- `.DS_Store` and local environment files are not committed.

---

# Contribution Rule

A contribution is acceptable only if it strengthens SmartCoat's ability to transform Enterprise Knowledge into better Enterprise Decisions and Organizational Capability.
