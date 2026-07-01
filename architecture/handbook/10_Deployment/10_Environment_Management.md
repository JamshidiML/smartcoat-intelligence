# 10 Environment Management

Version: 1.0

Status: Draft

---

# Purpose

This chapter defines environment management for SmartCoat.

---

# Environment Types

## Local

Developer workstation.

## Development

Shared environment for feature development.

## Test

Automated and manual validation environment.

## Staging

Production-like validation environment.

## Production

Operational enterprise environment.

## Sandbox

Controlled experimentation environment for AI, agents, data ingestion, and integration trials.

---

# Environment Rules

- production data must not be used in unsafe environments without approval
- secrets must be separated by environment
- environment configuration must be versioned
- migrations must be tested before production
- agent autonomy must be restricted in non-production environments
- AI experiments must not affect production knowledge without approval

---

# Environment Management Rule

Each environment must have a clear purpose, owner, access model, data policy, and lifecycle.
