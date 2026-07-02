# Persistent API Layer

Version: 1.0 Draft

---

# Purpose

This document defines the persistent API layer introduced in Release 1.6.

---

# Architecture

HTTP Request

↓

FastAPI Route

↓

Database Session Dependency

↓

Repository

↓

Application Service

↓

Domain Object

↓

PostgreSQL

---

# API Objects

The first persistent API layer supports:

- Knowledge Objects
- Decision Objects
- Enterprise Events

---

# Design Principles

## Routes Are Thin

Routes validate requests, call services, and return responses.

## Services Own Application Behavior

Services coordinate application actions.

## Repositories Own Persistence

Repositories store and retrieve canonical objects.

## Domain Models Remain Canonical

API payloads use domain models to preserve enterprise language.

---

# Future Extensions

Later releases may add:

- authentication
- authorization
- pagination
- filtering
- audit logging
- event publishing
- graph synchronization
- semantic search
