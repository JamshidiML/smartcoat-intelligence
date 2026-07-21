# ADR-0023 Cursor-Based Knowledge Pagination

Status: Accepted

Parent issue: #39

## Context

The current list endpoint accepts only a limit and returns a plain list. Release 1.8 needs filtering, stable traversal, and a contract that can scale beyond a small in-memory collection.

Offset pagination is easy to expose but can produce duplicates, omissions, and increasing query cost when records are inserted or changed while a client moves through pages.

## Decision

The canonical Release 1.8 Knowledge Object collection endpoint shall use opaque cursor-based pagination.

The fixed ordering is `updated_at DESC, object_id DESC`. Both fields are
non-null. `updated_at` is timezone-aware UTC and is serialized in normalized
RFC 3339 form at microsecond precision, for example
`2026-07-22T09:30:00.123456Z`. `object_id` is serialized as a lowercase,
hyphenated UUID.

The cursor shall be opaque to clients, URL-safe, validated, and free of secrets
or raw sensitive payloads. Its decoded contract contains exactly:

- cursor contract version;
- normalized position timestamp;
- normalized position UUID;
- fixed sort identifier; and
- SHA-256 fingerprint of the normalized effective semantic filters and sort.

Effective filters are normalized after documented defaults are applied. Their
fingerprint input is UTF-8 canonical JSON with lexicographically ordered field
names, canonical enum values, lowercase hyphenated UUIDs, UTC timestamps at
microsecond precision, and duplicate-free sorted values for filters whose
semantics are set-based. Omitted and null filters normalize to the documented
effective default. The fixed sort identifier is included in that input. The
cursor must match the exact effective semantic filters and sort of the request.
`page_size` may change within documented bounds and is not part of the cursor
position or filter fingerprint.

The response shall include:

- `items`;
- `next_cursor`, nullable when no further page exists;
- `page_size`;
- the effective sort contract;
- optional non-authoritative count only when explicitly implemented and documented.

Requirements:

- page size is bounded and defaults explicitly;
- combined filters use AND semantics;
- malformed encoding or shape returns `invalid_cursor_malformed`;
- an unsupported contract version returns `invalid_cursor_version`;
- a filter fingerprint mismatch returns `cursor_filter_mismatch`;
- a sort identifier mismatch returns `cursor_sort_mismatch`;
- an invalid position timestamp returns `invalid_cursor_timestamp`;
- an invalid position UUID returns `invalid_cursor_object_id`;
- unchanged datasets produce no duplicate or missing records across traversal;
- the next-page keyset predicate is
  `updated_at < cursor.updated_at OR (updated_at = cursor.updated_at AND object_id < cursor.object_id)`;
- records inserted, updated, or deleted between page requests may move, appear,
  or be omitted because Release 1.8 does not provide snapshot isolation across
  requests; clients requiring a stable snapshot must restart against an
  independently approved snapshot contract; and
- database queries use keyset predicates and supporting indexes when justified.

The SHA-256 filter fingerprint is unkeyed. It detects request-contract mismatch
but is not an authorization, authenticity, tamper-proofing, or security
boundary. Authentication, organization isolation, confidentiality, and
permission checks are reapplied independently on every page request.

Offset pagination may remain only as a temporary compatibility behavior if an explicit migration decision requires it. It shall not be presented as the canonical scalable contract.

## Rationale

Cursor pagination provides deterministic traversal and better long-term database behavior while keeping the API contract independent of internal row offsets.

## Consequences

- Query models and API responses change from a plain list to a page envelope.
- Repository queries need stable keyset ordering.
- Exact effective filters and the fixed sort identifier affect cursor validity.
- Tests must cover ties, boundaries, every deterministic cursor error, filter
  changes, sort mismatch, page-size changes, empty pages, mutation between
  pages, and complete traversal of an unchanged dataset.

## Rejected Alternatives

### Offset and limit as the canonical contract

Rejected because it is unstable under mutation and scales poorly for deep pages.

### Cursor containing raw JSON filter state

Rejected because it exposes implementation details and may leak sensitive metadata.

### Random or unspecified ordering

Rejected because pagination cannot be correct without deterministic order.

## Scope Boundary

This ADR does not add semantic relevance ranking, full-text search, vector search, or snapshot isolation across a long browsing session.
