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
- detect accepted duplicates within an organization boundary
- create stable UUIDv5 dry-run candidates only through validated processing

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
4. Governance screening: reject non-dry-run input and block unapproved
   model-training use.
5. Duplicate screening: compare organization-scoped checksum or fingerprint
   identities.
6. Candidate creation: create a dry-run candidate only after `validated`.
7. Human review: decide whether source content may be processed.
8. Canonical mapping: future industry-specific mapping after approval.
9. Persistence: future storage after mapping and review.

The approved package-level workflow is:

```python
result = ManifestRegistry().process(manifest)
```

`result.candidate` is populated only when the internally produced validation
status is `validated`. `blocked`, `rejected`, and `duplicate` outcomes return no
candidate. There is no package-level `create_candidate(manifest)` function.

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
| `model_training_approval_reference` | Required governance reference when model training is permitted. |
| `schema_target` | Intended canonical target and version. |
| `checksum_sha256` | Preferred duplicate and integrity key. |
| `content_fingerprint` | Normalized fallback key: 16-256 supported characters with at least four distinct alphanumeric characters. |
| `dry_run` | Must remain true for metadata-only preparation. |

`dry_run` is modeled as literal `true`. Input containing `false` is rejected
during parsing, and candidate construction repeats the guard defensively.

## Organization-Scoped Duplicate Behavior

The duplicate key is:

```text
organization:<organization-id-length>:<organization_id>|checksum_sha256:<digest>
```

or, when no checksum is available:

```text
organization:<organization-id-length>:<organization_id>|content_fingerprint:<fingerprint>
```

`site_id` is deliberately not part of duplicate identity. It remains preserved
as provenance, but identical content at two sites in one organization is still
a duplicate. The same content in two organizations is not a duplicate, which
prevents cross-tenant collisions.

Reprocessing an accepted manifest with the same organization-scoped key returns
`duplicate` without a candidate. Blocked keys are tracked separately: repeated
blocked submissions remain `blocked`, do not become accepted duplicates, and
include a `blocked_manifest_repeated` warning.

Duplicate warnings identify the actual source field, either `checksum_sha256`
or `content_fingerprint`.

## Stable Candidate Identity

Candidate IDs use UUIDv5 under the namespace derived from:

```text
urn:smartcoat:ingestion-candidate:v1
```

The UUIDv5 name combines the organization-scoped duplicate key with the schema
target name and version. Manifest ID, ingestion job ID, and site ID are not part
of candidate identity; they remain provenance. Two independent registries
therefore derive the same candidate ID for the same organization, content, and
schema target.

Candidates preserve:

- manifest ID and ingestion job ID
- source system, reference, owner, and source timestamp
- manifest timestamp
- organization and site boundaries
- confidentiality and permitted uses
- model-training approval reference when present
- checksum or fingerprint
- schema target name and version

## Security and Threat Notes

- Source references and metadata can still leak sensitive facts; keep examples
  synthetic until approval.
- Prompt-injection-like content inside documents is out of scope because the
  prototype does not read raw content.
- Future extractors must treat every source as untrusted input.
- Model-training use is blocked until an explicit approval reference exists.
  The reference is governance metadata, not proof of IAM authorization.
- In-memory duplicate isolation is organization-scoped in this prototype;
  persistence and access-control enforcement remain future work.

## Extension Points

Technical-textile mappings can plug in after manifest validation by reading
`schema_target.name` and `schema_target.version`. They should remain separate
from source registration so each industry hub can define its own mapping rules
without changing the platform-core manifest contract.
