# Release Readiness Checklist

Version: 1.0

Status: Draft

---

# Purpose

This checklist determines whether a release package is ready to install, commit, and push.

---

# Checklist

## Package

- ZIP file exists.
- INSTALL.md exists.
- Release record exists.
- Files are under correct paths.
- No unwanted root folder nesting exists.

## Architecture

- Release aligns with Foundation.
- Release aligns with Reference Models.
- Release does not introduce conflicting terminology.
- Related ADR exists if required.

## Repository

- Install uses rsync.
- git status reviewed.
- git diff --stat reviewed.
- No sensitive data included.
- .DS_Store removed.
- Commit message follows standard.

## Post-Commit

- git status is clean.
- GitHub shows files in expected paths.
- Release index updated if needed.
