# ADR-0025 Structured Evidence and Provenance Compatibility

Status: Proposed

Parent issue: #39

## Context

The current Knowledge Object stores evidence as `list[str]` and provenance as a small object containing optional source system, source reference, creator, and method. The current platform envelope is a controlled-pilot proposal with richer provenance metadata and string evidence references. Release 1.8 needs auditability, migration compatibility, and future file or test-result linkage without ingesting unrestricted raw content.

Replacing existing fields without a compatibility decision could break Release 1.7 API payloads and persisted synthetic records. Keeping strings as the permanent contract would make evidence type, identity, source, actor, time, and integrity ambiguous.

## Decision

The Release 1.8 application domain is canonical for this backend. It shall
introduce structured evidence references and expanded provenance as canonical
domain value objects. The current platform envelope remains a proposal and an
adapter target; it is not an Accepted ADR or a second application source of
truth.

### Structured EvidenceReference

Canonical fields include:

- stable `evidence_id`;
- canonical `evidence_type`;
- `title` or `description`;
- `source_reference`;
- optional `source_system`;
- `captured_by`;
- `captured_at`;
- optional `source_created_at`;
- optional `checksum` or `content_fingerprint` declaration;
- optional `media_type`;
- optional `confidentiality`; and
- optional `context_reference`.

Evidence references contain metadata and governed links. They do not contain unrestricted raw file bytes or a general document-ingestion payload.

### Expanded Provenance

The canonical provenance field names are:

- `source_system`;
- `source_reference`;
- `created_by`;
- `creation_method`;
- `captured_at`;
- `source_created_at`;
- `transformation_history`;
- `derived_from_object_id`; and
- `derived_from_revision`.

New canonical records shall follow the required-field and validation rules
implemented and reviewed in T03. That contract must preserve source, actor,
method, and capture time and may keep `source_created_at`, derivation fields, or
other facts nullable where the source does not supply them. Unknown values
remain explicit and are never fabricated.

### Compatibility

Release 1.7 evidence strings shall use an explicit compatibility path:

- existing strings are accepted only through a documented legacy input adapter or migration layer;
- each legacy string becomes a structured evidence reference with a
  deterministic stable evidence ID, `legacy_reference` type, the original
  string preserved as `source_reference`, and explicit incomplete migration
  provenance;
- new canonical domain objects and responses use structured evidence;
- legacy output compatibility, if retained, is versioned and must not become the source of truth.

Existing provenance fields map directly where possible. Missing legacy facts
remain null and are explicitly marked incomplete. Migrations shall not invent
actor names, organizations, owners, confidentiality values, or historical
timestamps. An incomplete legacy record shall not be falsely projected as
conformant with an envelope whose required fields it cannot satisfy. Exact
migration mechanics belong to T05.

Evidence identity and collision handling are deterministic. An identical
normalized `EvidenceReference` repeated under the same `evidence_id` is rejected
as a duplicate. Reuse of an `evidence_id` with different normalized metadata is
rejected as `evidence_id_conflict`. Neither case silently overwrites, merges, or
selects a record.

### Platform-envelope adapter boundary

Projection to the current platform envelope emits only ordered, unique
`evidence_id` values in `evidence_references`. Structured EvidenceReference
objects remain canonical in the application. T01 authorizes no change to the
platform-envelope schema. Any future envelope that carries structured evidence
requires a separately reviewed and versioned schema rather than silent mutation
of the current proposal.

The application keeps `object_id` as its canonical UUID. Envelope projection
derives `knowledge_object:<uuid>` and does not store a second identity. New v2
records require `organization_id`, structured owner fields `owner_id` and
`role`, and exactly one confidentiality value: `public`, `internal`,
`confidential`, `restricted`, or `strategic`. Creator identity remains
`provenance.created_by`. Legacy gaps use fail-closed, explicitly marked
compatibility behavior and never infer real governance facts.

## Rationale

This gives the backend one canonical application model, defines an explicit
adapter to the proposed platform envelope, enables reliable audit and
retrieval, preserves migration honesty, and avoids premature raw-document
ingestion.

## Consequences

- Knowledge Object v2 changes its evidence type.
- Pydantic models, mappers, persistence, API schemas, and tests require coordinated changes.
- Release 1.7 synthetic records need a migration or adapter.
- Future file storage, OCR, approval verification, or external evidence services remain separate capabilities.

## Rejected Alternatives

### Keep evidence as permanent strings

Rejected because strings cannot represent provenance, identity, type, time, integrity, or confidentiality consistently.

### Store raw files directly in the Knowledge Object JSON

Rejected because it bypasses ingestion, security, storage, retention, and authorization boundaries.

### Populate missing historical metadata with defaults presented as facts

Rejected because it creates false provenance.

## Scope Boundary

This ADR does not authorize real file ingestion, prove IAM authorization, verify external evidence authenticity, or define production retention and deletion policy.
