# ADR-0013 Root Repository Documentation As Project Entry Point

Status: Accepted

---

# Context

SmartCoat has evolved into a multi-volume enterprise architecture repository.

Without strong root-level documentation, contributors and reviewers may not understand the project purpose, navigation structure, release model, governance model, or security expectations.

---

# Decision

SmartCoat shall use root-level repository documentation as the official entry point for project understanding.

The root README shall guide users into the architecture portal, roadmap, release index, governance documents, and repository structure.

---

# Consequences

- README.md must remain high-level and navigational.
- Detailed architecture belongs under `architecture/`.
- Root documents must not redefine concepts that belong to Foundation, Reference Models, or Glossary.
- Root documents should be updated when repository organization changes.
