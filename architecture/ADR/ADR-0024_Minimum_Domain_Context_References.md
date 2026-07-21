# ADR-0024 Minimum Domain Context References

Status: Accepted

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

A `ContextReference` shall contain:

- `context_type` from the canonical vocabulary;
- `reference_id` as a normalized string;
- `id_kind`, either `uuid` or `external`;
- `source_system`, required when `id_kind=external` and otherwise optional;
- `display_name`;
- optional `version`;
- optional `relationship_role`;
- optional `source_reference`;
- optional `evidence_reference`; and
- optional bounded `attributes` needed for the first vertical slice.

When `id_kind=uuid`, `reference_id` is validated and normalized to lowercase
hyphenated UUID text. External identifiers preserve their governed canonical
form and require `source_system` so their identity boundary is explicit.

Within one Knowledge Object, the unique link key is
`(context_type, reference_id, relationship_role)`. Repeating the same normalized
reference is rejected as an exact duplicate. Supplying a different `version`
for the same unique key is rejected as a conflicting version. No input path may
silently merge, replace, or select one of those references.

When two references share that unique link key but differ in any
identity-bearing normalized field, including `id_kind`, required
`source_system`, or `version`, the result is a deterministic conflict. No input
path may silently merge, replace, or select one of the conflicting references.

Every reference inherits `organization_id` from its Knowledge Object. Release
1.8 prohibits a reference to a target known to belong to another organization.
An absent or unverifiable organization boundary fails closed rather than being
treated as cross-organization permission.

Standalone application entities and independent CRUD endpoints shall not be
introduced without:

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
- Tests must cover types, identity normalization, exact duplicates, version
  conflicts, organization isolation, serialization, and compatibility.

## Rejected Alternatives

### Raw UUID list

Rejected because it does not preserve relationship meaning or context type.

### Complete domain entity implementation in Release 1.8

Rejected because it exceeds the first vertical slice and duplicates broad ontology work.

### Unstructured context dictionary

Rejected because it creates inconsistent language and weak validation.

## Scope Boundary

This ADR does not create master data, ERP synchronization, supplier/customer models, formulation optimization, or the complete Technical Textiles application domain.
