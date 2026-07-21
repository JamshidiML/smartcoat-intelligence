# ADR-0024 Minimum Domain Context References

Status: Proposed

Parent issue: #39

## Context

The Knowledge Capture MVP needs enough industrial context to make an observation, failure, result, lesson, or recommendation reusable. The existing Knowledge Object stores `related_entities` as UUIDs without entity type, label, version, or source meaning. The platform and Technical Textiles schemas are broader than the application needs for Release 1.8.

Implementing complete Project, Material, Formulation, Trial, Process, and Test bounded contexts now would expand the release into the full enterprise ontology and create unnecessary CRUD, migration, and governance obligations.

## Decision

Release 1.8 shall use typed minimum context references as embedded canonical value objects unless a thread proves that a standalone entity is required for the approved backend workflow.

The supported context types are:

- `project`
- `experiment_or_trial`
- `material`
- `fabric_or_substrate`
- `formulation_reference`
- `process_conditions`
- `test_result`

A minimum context reference shall preserve:

- `reference_id` as a stable UUID or governed external identifier;
- `context_type` from the canonical vocabulary;
- `display_name` or label;
- optional `version`;
- optional `source_system` and `source_reference`;
- optional relationship role;
- optional evidence reference;
- optional compact governed attributes only when needed for the first vertical slice.

The Knowledge Object may contain multiple typed context references. Duplicate identity and conflicting version behavior must be deterministic.

Standalone application entities and independent CRUD endpoints require:

1. a demonstrated Release 1.8 use case that cannot be satisfied by a reference;
2. an issue-level scope change;
3. migration, lifecycle, ownership, and API implications;
4. independent architecture approval.

Technical Textiles JSON Schemas remain an Industry Hub contract. Release 1.8 application models may map to them, but shall not duplicate the complete schema package into relational tables or domain classes.

## Rationale

Typed references improve meaning and retrieval over raw UUID lists while preserving the narrow MVP boundary and an expansion path to later domain services.

## Consequences

- `related_entities: list[UUID]` requires an explicit compatibility or migration strategy.
- Knowledge Object filtering may use context type and reference ID.
- Persistence may initially use deliberate JSONB for bounded reference value objects, with indexes justified by query requirements.
- Relationship integrity is application-enforced unless a standalone entity is later approved.
- Tests must cover types, identity, duplicates, versions, serialization, and compatibility.

## Rejected Alternatives

### Raw UUID list

Rejected because it does not preserve relationship meaning or context type.

### Complete domain entity implementation in Release 1.8

Rejected because it exceeds the first vertical slice and duplicates broad ontology work.

### Unstructured context dictionary

Rejected because it creates inconsistent language and weak validation.

## Scope Boundary

This ADR does not create master data, ERP synchronization, supplier/customer models, formulation optimization, or the complete Technical Textiles application domain.
