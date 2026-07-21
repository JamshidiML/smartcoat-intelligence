# ADR-0025 Structured Evidence and Provenance Compatibility

Status: Proposed

Parent issue: #39

## Context

The current Knowledge Object stores evidence as `list[str]` and provenance as a small object containing optional source system, source reference, creator, and method. The accepted platform envelope already requires richer provenance metadata and evidence references, while Release 1.8 needs auditability, migration compatibility, and future file or test-result linkage without ingesting unrestricted raw content.

Replacing existing fields without a compatibility decision could break Release 1.7 API payloads and persisted synthetic records. Keeping strings as the permanent contract would make evidence type, identity, source, actor, time, and integrity ambiguous.

## Decision

Release 1.8 shall introduce structured evidence references and expanded provenance as canonical domain value objects.

### Structured EvidenceReference

Minimum fields:

- stable `evidence_id`;
- canonical `evidence_type`;
- title or description;
- source reference;
- optional source system;
- captured by;
- captured at;
- optional source or event timestamp;
- optional checksum or content fingerprint declaration;
- optional media type;
- optional confidentiality classification;
- optional context reference.

Evidence references contain metadata and governed links. They do not contain unrestricted raw file bytes or a general document-ingestion payload.

### Expanded Provenance

Minimum fields:

- source system;
- source reference;
- actor or creator;
- capture method;
- recorded timestamp;
- optional source timestamp;
- optional transformation history;
- optional prior object or revision reference when derived.

Unknown values remain explicit and are not fabricated.

### Compatibility

Release 1.7 evidence strings shall use an explicit compatibility path:

- existing strings are accepted only through a documented legacy input adapter or migration layer;
- each legacy string becomes a structured evidence reference with a generated stable evidence ID, `legacy_reference` type, the original string preserved as source reference, and explicit migration provenance;
- new canonical domain objects and responses use structured evidence;
- legacy output compatibility, if retained, is versioned and must not become the source of truth.

Existing provenance fields map directly where possible. Missing timestamps or actors remain `unknown` or nullable according to the accepted domain contract; migrations shall not invent historical facts.

Evidence identity and duplicate handling shall be deterministic. A matching evidence ID cannot silently represent different normalized metadata.

## Rationale

This aligns application behavior with the platform envelope, enables reliable audit and retrieval, preserves migration honesty, and avoids premature raw-document ingestion.

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
