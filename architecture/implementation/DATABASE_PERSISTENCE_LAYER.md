# Database Persistence Layer

Version: 1.0 Draft

---

# Purpose

This document defines the first SmartCoat database persistence layer.

---

# Persistence Strategy

Release 1.5 introduces PostgreSQL-compatible SQLAlchemy ORM models and repository classes.

---

# Architecture

API Routes

↓

Application Services

↓

Repositories

↓

SQLAlchemy ORM Models

↓

PostgreSQL

---

# Design Principle

Domain models remain separate from ORM models.

Domain models represent enterprise meaning.

ORM models represent database persistence.
