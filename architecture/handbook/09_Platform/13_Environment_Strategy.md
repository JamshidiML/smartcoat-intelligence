# 13 Environment Strategy

Version: 1.0

Status: Draft

---

# Purpose

This chapter defines the environment strategy for SmartCoat.

---

# Environments

## Local

Developer workstation.

## Development

Shared engineering environment.

## Test

Automated and manual testing environment.

## Staging

Production-like validation environment.

## Production

Live enterprise system.

## Sandbox

Safe experimentation environment for AI, agents, and data ingestion.

---

# Environment Principles

- separation of environments
- no production data in unsafe environments without approval
- reproducible configuration
- controlled secrets
- migration testing
- monitoring in production
- restricted agent autonomy in lower maturity environments

---

# Environment Rule

Production knowledge and decisions require stronger governance than development experiments.
