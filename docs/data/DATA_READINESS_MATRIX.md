# Data Readiness Matrix

Status: Pilot preparation scoring model

Scoring model version: `smartcoat-readiness-v1.1-draft`

## Scoring Principle

Readiness measures whether an already authorized source can support a defined
pilot decision. It does not grant permission. Every dimension is rated 0-4 and
converted to weighted points:

```text
dimension points = weight × rating / 4
total readiness = sum(dimension points)
```

Round the total to one decimal place. Record evidence and reviewer for every
rating; unsupported ratings are zero.

The dimensions, weights, and score bands below are **pilot hypotheses**, not
validated predictors of value or ingestion safety. Preserve the model version
with every assessment. Recalibrate only from measured pilot outcomes, domain
review, and observed decision error; publish a new version and mapping instead
of silently changing historical scores.

## Dimensions

| Dimension | Weight | 0 | 2 | 4 |
|---|---:|---|---|---|
| Business value | 15 | No defined value | Plausible value | High measurable decision value |
| Pilot relevance | 15 | Outside pilot | Indirectly useful | Required for first demonstrator |
| Ownership clarity | 8 | No owner | Candidate owner | Accountable owner/steward confirmed |
| Permission readiness | 12 | Unknown/prohibited | Limited approval in review | Written approval for exact uses |
| Format/structure | 5 | Opaque/unreadable | Semi-structured | Documented stable structure |
| Volume/history | 4 | Unknown/inadequate | Partial | Representative bounded history |
| Completeness | 7 | Critical fields absent | Material gaps | Required fields consistently present |
| Consistency | 6 | Contradictory/uncontrolled | Known variation | Rules and controlled values applied |
| Identifier quality | 6 | No usable IDs | Partial links | Stable cross-source IDs |
| Timestamp quality | 4 | Missing/ambiguous | Partial | Reliable event/effective timestamps |
| Unit quality | 4 | Missing/ambiguous | Mixed but mappable | Explicit normalized units and bases |
| Provenance | 5 | Origin unknown | Partial source lineage | Source, actor, method, and transformations clear |
| Duplicate control | 3 | Unknown/high duplicate risk | Detectable | Deterministic duplicate identity/rules |
| Language readiness | 2 | Unknown/unhandled | Known mixed language | Language identified and supported |
| Extraction ease | 2 | Unsafe/manual/high difficulty | Feasible with review | Controlled structured extraction |
| Mapping ease | 2 | No target/major ambiguity | Partial mapping | Deterministic pilot-schema mapping |
| **Total** | **100** | | | |

Ratings 1 and 3 represent documented intermediate states. Difficulty dimensions
are phrased as readiness: easier and safer work receives the higher rating.

## Mandatory Governance Gate

Regardless of score, status is `blocked` when any is true:

- owner or steward is missing
- confidentiality or personal-data classification is incomplete
- legal/contractual permission is unknown, denied, expired, or mismatched to purpose
- cross-company boundary is unclear
- retention/deletion authority is undefined
- assessment would require copying unapproved raw content
- security, safety, employee-consent, or IP review is unresolved
- any intended purpose is not explicitly `approved`, including when its status
  is `not_requested`, `in_review`, `denied`, `expired`, or `revoked`

## Score Bands After Gate Passes

| Score | Readiness | Default action |
|---:|---|---|
| 85-100 | Pilot-ready candidate | Verify mapping and approve bounded package. |
| 70-84.9 | Prepare | Correct named gaps, then re-score. |
| 50-69.9 | Assess | Profile only an approved sanitized sample. |
| 25-49.9 | Discover | Clarify owner, purpose, and source shape. |
| 0-24.9 | Defer | No pilot work until fundamentals change. |

The readiness band cannot change a `blocked` governance gate.

These bands are prioritization hypotheses for the first controlled pilot. They
must be tested against measured preparation effort, correction rate, ingestion
defects, and user value before reuse as decision thresholds.

## Prioritization

Rank gate-passed sources using:

1. total readiness score
2. pilot relevance rating
3. measurable business value
4. lower confidentiality/consent complexity
5. lower extraction and mapping effort
6. stronger evidence/provenance

Do not aggregate away a critical risk. The matrix records a separate quality
risk summary and required mitigation for each source.

## Pilot Preparation Matrix

| Package component | Value | Typical readiness target | Gate evidence |
|---|---:|---:|---|
| Sanitized project/requirement register | High | >= 80 | Owner, customer de-identification, retrieval/human-review permission |
| Trial/sample index | High | >= 80 | Stable IDs, project links, confidentiality approval |
| Normalized test-result extract | High | >= 85 | Method/unit dictionary, evidence and quality owner |
| Reviewed lessons/decisions | High | >= 85 | Reviewer, evidence, lifecycle, reuse permission |
| Formulation reference index | Medium | >= 75 | No composition unless explicit trade-secret approval |
| Raw documents/images/voice | Variable | Not first package | Separate source, consent, extraction, retention, and content review |

A synthetic high-scoring row in the register deliberately remains `blocked`
because analytics is an intended purpose with status `in_review`. This proves
that a score near 100 cannot override a purpose-specific permission gate.

## Reassessment

Re-score when source structure, owner, permission, purpose, quality, mapping,
retention, or pilot scope changes. Every reassessment records a new assessment
ID, model version, timestamp, assessor role, evidence references, previous
assessment ID and score, reason, and immutable history reference. Never
overwrite prior rows or evidence silently.
