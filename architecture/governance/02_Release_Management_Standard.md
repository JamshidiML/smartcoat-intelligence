# 02 Release Management Standard

Version: 1.0

Status: Draft

---

# Purpose

This document defines how SmartCoat architecture releases are created, installed, reviewed, committed, and maintained.

---

# Release Philosophy

SmartCoat architecture evolves through releases rather than uncontrolled file changes.

Each release should represent a coherent architecture increment.

---

# Release Structure

Each release should include:

- release record
- architecture documents
- ADRs, when needed
- diagrams, when needed
- templates, when needed
- INSTALL.md
- clear commit message

---

# Release Naming

Release files should use:

`RELEASE_X_Y_Release_Name.md`

Example:

`RELEASE_1_1_Repository_Governance.md`

---

# Installation Rule

Release packages must be installed using merge-safe commands such as `rsync`.

Manual drag-and-drop folder replacement is not approved.

---

# Commit Message Standard

Use:

`Add <Release Name> release <version>`

Example:

`Add Repository Governance release 1.1`

---

# Release Rule

No release should introduce concepts that conflict with the Foundation, Reference Models, Enterprise Ontology, Enterprise Language, or accepted ADRs.
