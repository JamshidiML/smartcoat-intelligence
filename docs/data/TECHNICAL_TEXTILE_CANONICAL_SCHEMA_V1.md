# Technical Textiles Canonical Schema v1

Status: Proposed controlled-pilot contract

Issue: #19

## Purpose and Boundary

This schema defines the minimum structured information needed to represent a
technical-textile coating R&D trial end to end while preserving SmartCoat's
industry-agnostic mother-platform architecture.

It is not a complete ontology, database migration, production API, ingestion
mapping, or authorization design. It contains no real company data.

## Platform Core vs Industry Extension

### Universal Platform Envelope

Every representative object carries:

- stable object ID and canonical type/name
- semantic schema version
- organization and optional site boundary
- accountable owner and role
- confidentiality and separate permitted uses
- lifecycle and human review status
- confidence without forced certainty
- source provenance and transformation history
- evidence and typed relationship references
- created/updated timestamps

These fields map to the canonical object structure in
`architecture/handbook/04_Information/02_Canonical_Data_Model.md`, provenance
requirements in `architecture/handbook/04_Information/09_Provenance_Model.md`,
and the current `EnterpriseBaseObject` concepts in
`src/smartcoat/domain/base.py`.

### Technical-Textile Extensions

The Industry Hub adds materials, supplier/manufacturer references, substrates,
formulation versions and ingredients, coating trials, samples, process/machine
conditions, test methods/results, observations, failure modes, hypotheses,
root-cause candidates, lessons, and decision/evidence links.

These extensions do not redefine platform Knowledge Object, Decision Object,
or Enterprise Event semantics.

## Entity Set

| Entity | Minimum role in pilot | Machine schema |
|---|---|---|
| Source/provenance envelope | Explains origin, transformation, ownership, review, confidence, and evidence. | `platform-envelope.schema.json` |
| Organization/Site | Establishes tenant and facility context. | Envelope fields. |
| Customer Requirement | Records property target, value state, unit, and priority. | Nested in trial. |
| Project | Groups requirements, trials, accountable owner, decisions, and learning. | Nested in trial. |
| Trial/Experiment | Records objective, hypotheses, samples, process, outcomes, and review. | `coating-trial.schema.json` |
| Sample | Binds substrate, fabric specification, formulation, and material batches. | Nested in trial. |
| Material/Raw Material | Represents material kind, producer/supplier references, specifications, properties, storage, and alternatives. | `material.schema.json` |
| Supplier/Manufacturer Reference | Stable reference only; commercial detail remains separately governed. | Material fields. |
| Fabric/Substrate | Material reference plus optional fabric specification. | Trial sample. |
| Formulation Version | Versioned ingredients, quantities, functions, targets, reasoning, and approval. | `formulation.schema.json` |
| Ingredient | Material reference, stateful quantity, function, and addition order. | Formulation item. |
| Process Condition | Named stateful measurement such as speed or temperature. | Trial item. |
| Machine/Line | Stable equipment references. | Trial fields. |
| Test Method/Standard | Method identity/version and optional standard reference. | `test-result.schema.json` |
| Test Result | Stateful result, units, conditions, requirement, assessment, and evidence. | `test-result.schema.json` |
| Observation | Evidence-backed statement from trial execution. | Trial item; maps to Knowledge Object. |
| Failure Mode | Described observed failure with severity. | Trial item; maps to Knowledge Object. |
| Hypothesis/Root-Cause Candidate | Explicit statement, confidence, and unresolved/supported/rejected state. | Trial items; map to Knowledge Object. |
| Lesson Learned | Reference to reviewed reusable knowledge. | Trial reference; maps to Knowledge Object. |
| Decision/Recommendation | Reference to rationale, approval, outcome, and learning in canonical Decision Object. | Trial reference. |
| Evidence Attachment | Metadata reference only; binary content is outside this schema. | Envelope evidence references. |

## Stable Identifiers

Pilot identifiers use a namespace-style form:

```text
<canonical_type>:<stable_local_identifier>
```

Examples are synthetic: `coating_trial:synthetic-trial-a` and
`material:synthetic-binder-a`.

Identifiers are immutable. Source-system IDs are provenance or mapping values,
not replacements for canonical IDs. Merges and aliases require a governed
master-data decision.

## Relationship Map

```text
Organization
  -> Site
  -> Project
       -> Customer Requirement
       -> Coating Trial
            -> Hypothesis
            -> Sample
                 -> Fabric/Substrate
                 -> Formulation Version
                      -> Ingredient -> Material -> Supplier/Manufacturer
            -> Process Condition -> Machine/Line
            -> Test Result -> Test Method/Standard
            -> Observation / Failure Mode / Root-Cause Candidate
            -> Lesson Learned / Decision / Evidence
```

Relationships must use stable target IDs and may include evidence and temporal
validity. A relationship must not imply causality unless the evidence and review
status support that claim.

## Required, Optional, and Conditional Fields

| Classification | Rule | Examples |
|---|---|---|
| Required | Object cannot support pilot traceability without it. | ID, type, schema version, organization, owner, confidentiality, use, lifecycle, review, provenance, timestamps. |
| Optional | Legitimately unavailable or irrelevant for some objects. | Site, description, confidence, manufacturer, standard, line. |
| Conditional | Required when a state or concept is used. | `value` when measurement state is `known`; at least two values when `conflicting`; approval reference under future model-training governance. |
| Reference | Target may be managed by another canonical object. | Supplier, machine, material batch, evidence, decision, lesson. |

## Information-State Semantics

Every measurement declares exactly one state:

| State | Meaning |
|---|---|
| `known` | A value is present; method and unit may still require review. |
| `unknown` | Value should exist but is not currently known. |
| `not_measured` | Measurement was not performed. |
| `not_applicable` | Concept does not apply to this case. |
| `conflicting` | Two or more source values disagree and are preserved for review. |

Null must not blur these states. A conflicting value must not be averaged or
selected without a reviewed resolution.

## Units and Normalization

- Every numeric engineering value records a source unit unless dimensionless.
- Unit symbols follow an approved unit vocabulary; free-text unit aliases must
  be mapped before canonical use.
- Source value/unit remain preserved.
- Optional normalized value/unit must identify the agreed canonical unit.
- Conversions require a deterministic method and transformation-history entry.
- Percentage bases (mass, volume, solids, wet, dry) must be explicit.
- Test conditions and method versions travel with results.

The schema validates structure, not physical dimensional compatibility. A
future unit service or semantic rule set must validate conversions.

## Data-Quality Rules

1. IDs are unique within their canonical namespace and immutable.
2. Organization ownership is mandatory; cross-company references are rejected
   unless separately authorized.
3. Provenance identifies source system/reference, creator, method, and capture
   time.
4. Review status is independent from lifecycle and confidence.
5. Confidence ranges from 0 to 1 or remains unknown; it is never invented.
6. Material and formulation versions are explicit and not overwritten.
7. Formulation ingredient quantities preserve units and value state.
8. Process and test measurements preserve method, conditions, and uncertainty
   where available.
9. Evidence attachments are references; binary content requires separate
   security and retention controls.
10. Failures and negative results are retained as first-class learning inputs.
11. Causal claims remain hypotheses/root-cause candidates until reviewed.
12. Conflicts are represented, not silently resolved.

## Synthetic End-to-End Example

The embedded examples represent a fictional project with a synthetic customer
requirement, material, two-component formulation, substrate/sample, controlled
coating trial, process measurements, test result, observation, unresolved
root-cause candidate, lesson reference, and decision reference.

The examples intentionally use `synthetic://` references and generalized names.
They are structurally realistic but scientifically and commercially meaningless.

## Mapping to Current Canonical Models

| Pilot concept | Current canonical mapping |
|---|---|
| Observation, hypothesis, failure mode, root cause, lesson | `KnowledgeObject` with corresponding `knowledge_type`, evidence, relationships, confidence, and lifecycle. |
| Recommendation or approved next step | `DecisionObject` with problem, context, evidence, alternatives, recommendation, rationale, risk, confidence, outcome, and learning. |
| Trial created/completed, decision executed, outcome observed | `EnterpriseEvent` with actor, related object, state transition, evidence, and impact. |
| Material/formulation/trial/test structures | Industry-extension objects linked to canonical knowledge, decisions, events, evidence, and provenance. |

No change to application models is approved by this document.

## Versioning and Extension

- Schema version is semantic and mandatory.
- Patch: clarification or validation fix that does not change accepted instances.
- Minor: additive optional fields or enums with reviewed compatibility.
- Major: required-field, meaning, identifier, relationship, unit, or governance
  changes that can invalidate existing instances.
- Company-specific fields use a governed extension namespace and must not
  redefine core or Hub fields.
- Future industry entities are added only when a validated use case requires
  them; v1 does not pre-model the whole enterprise ontology.

## Accepted v1 Decisions

- platform envelope and industry extension remain separate
- site is optional but organization is required
- provenance, confidentiality, permitted uses, review, lifecycle, confidence,
  evidence, and timestamps are universal
- unknown and conflicting states are explicit
- formulation reasoning is required, not composition alone
- binary evidence and commercial supplier details remain referenced and governed

## Open Design Decisions

1. Approved canonical unit vocabulary and conversion library.
2. Master-data ownership for materials, suppliers, machines, and standards.
3. Whether customer requirements become a standalone machine schema in v1.1.
4. Exact company-extension namespace and compatibility policy.
5. Persistence mapping and migration strategy after pilot review.
6. Retention and redaction behavior for evidence attachments.
