# Ingestion Foundation V1

Status: Release 1.7 prototype

Issue: #22

## Purpose

The ingestion foundation defines a metadata-only entry point for controlled
source registration. It validates manifests, preserves provenance metadata, and
creates dry-run ingestion candidates without extracting raw enterprise content.

## Boundary

This prototype does:

- classify source type and format
- require organization and site boundary metadata
- require confidentiality and permitted-use metadata
- require checksum or content fingerprint support
- declare a schema target and version
- produce structured validation errors and warnings
- detect duplicate manifests deterministically
- support dry-run candidate creation

This prototype does not:

- perform OCR
- crawl email, ERP, file shares, or document systems
- parse raw PDFs, images, voice, spreadsheets, or ERP exports
- write to PostgreSQL
- create API routes
- map technical-textile fields into canonical schemas
- train models or create embeddings

## Pipeline Stages

1. Source discovery: identify a source family and owner.
2. Manifest registration: record metadata only.
3. Manifest validation: check required governance and provenance fields.
4. Duplicate screening: compare checksum or fingerprint keys.
5. Candidate creation: create a dry-run candidate for later review.
6. Human review: decide whether source content may be processed.
7. Canonical mapping: future industry-specific mapping after approval.
8. Persistence: future storage after mapping and review.

## Manifest Fields

| Field | Purpose |
|---|---|
| `source_type` | Broad source family such as spreadsheet, PDF, image, voice transcript, or ERP export. |
| `source_format` | File or payload format. |
| `source_system` | System or register where the source is known. |
| `source_reference` | Metadata-only reference, not raw content. |
| `organization_id` | Tenant or company boundary. |
| `site_id` | Optional site boundary. |
| `source_owner` | Steward responsible for permission and quality. |
| `confidentiality_level` | Access and handling classification. |
| `permitted_uses` | Approved purposes, separated by use. |
| `schema_target` | Intended canonical target and version. |
| `checksum_sha256` | Preferred duplicate and integrity key. |
| `content_fingerprint` | Fallback duplicate key when checksum is unavailable. |
| `dry_run` | Must remain true for metadata-only preparation. |

## Deterministic Duplicate Behavior

The duplicate key is:

```text
sha256:<checksum_sha256>
```

or, when no checksum is available:

```text
fingerprint:<content_fingerprint>
```

Reprocessing a manifest with the same key returns `duplicate` without creating a
new accepted registration.

## Security and Threat Notes

- Source references and metadata can still leak sensitive facts; keep examples
  synthetic until approval.
- Prompt-injection-like content inside documents is out of scope because the
  prototype does not read raw content.
- Future extractors must treat every source as untrusted input.
- Model-training use is blocked until explicit governance approval exists.
- Cross-company data isolation is represented by `organization_id` and must be
  enforced in future persistence and access-control layers.

## Extension Points

Technical-textile mappings can plug in after manifest validation by reading
`schema_target.name` and `schema_target.version`. They should remain separate
from source registration so each industry hub can define its own mapping rules
without changing the platform-core manifest contract.
