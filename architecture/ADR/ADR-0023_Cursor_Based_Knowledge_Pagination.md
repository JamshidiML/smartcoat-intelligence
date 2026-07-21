# ADR-0023 Cursor-Based Knowledge Pagination

Status: Proposed

Parent issue: #39

## Context

The current list endpoint accepts only a limit and returns a plain list. Release 1.8 needs filtering, stable traversal, and a contract that can scale beyond a small in-memory collection.

Offset pagination is easy to expose but can produce duplicates, omissions, and increasing query cost when records are inserted or changed while a client moves through pages.

## Decision

The canonical Release 1.8 Knowledge Object collection endpoint shall use opaque cursor-based pagination.

The default ordering shall be:

1. `updated_at` descending;
2. `object_id` descending as a stable tie-breaker.

The cursor shall encode only the minimum normalized ordering position and contract version. It shall be opaque to clients, URL-safe, validated, and free of secrets or raw sensitive payloads.

The response shall include:

- `items`;
- `next_cursor`, nullable when no further page exists;
- `page_size`;
- the effective sort contract;
- optional non-authoritative count only when explicitly implemented and documented.

Requirements:

- page size is bounded and defaults explicitly;
- combined filters use AND semantics;
- invalid or unsupported cursors fail deterministically;
- a cursor is valid only for the compatible sort/filter contract version;
- unchanged datasets produce no duplicate or missing records across traversal;
- records changed between page requests may move position, and this limitation must be documented rather than hidden;
- database queries use keyset predicates and supporting indexes when justified.

Offset pagination may remain only as a temporary compatibility behavior if an explicit migration decision requires it. It shall not be presented as the canonical scalable contract.

## Rationale

Cursor pagination provides deterministic traversal and better long-term database behavior while keeping the API contract independent of internal row offsets.

## Consequences

- Query models and API responses change from a plain list to a page envelope.
- Repository queries need stable keyset ordering.
- Filters and sort version affect cursor validity.
- Tests must cover ties, boundaries, malformed cursors, filter changes, empty pages, and complete traversal.

## Rejected Alternatives

### Offset and limit as the canonical contract

Rejected because it is unstable under mutation and scales poorly for deep pages.

### Cursor containing raw JSON filter state

Rejected because it exposes implementation details and may leak sensitive metadata.

### Random or unspecified ordering

Rejected because pagination cannot be correct without deterministic order.

## Scope Boundary

This ADR does not add semantic relevance ranking, full-text search, vector search, or snapshot isolation across a long browsing session.
