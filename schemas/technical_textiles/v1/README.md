# Technical Textiles Canonical Schema v1

Status: Controlled-pilot proposal

The JSON Schemas in this directory use JSON Schema Draft 2020-12:

- `platform-envelope.schema.json`: universal identity, tenancy, governance,
  provenance, evidence, review, lifecycle, relationship, timestamp, and
  measurement-state contract
- `material.schema.json`: technical-textile material extension
- `formulation.schema.json`: versioned formulation and ingredient extension
- `coating-trial.schema.json`: project, requirement, hypothesis, sample,
  process, machine, observation, failure, root-cause, lesson, and decision links
- `test-result.schema.json`: method, result, conditions, requirement, and
  assessment extension

Each schema embeds a synthetic `examples` array. No example represents a real
company, product, supplier, material, formulation, customer, process, price, or
test result.

## Validation

The schemas are validated with Python `jsonschema` Draft 2020-12 support. The
validator registers every schema by `$id`, checks each schema, and validates
every embedded example against its owning schema with format checking enabled.

## Compatibility

Version `1.0.0` is a pilot schema contract, not a database migration or complete
enterprise ontology. Additive optional fields may be proposed in compatible v1
revisions. Required-field, semantic, identifier, unit, or enum changes require
a new schema version and a documented migration/mapping decision.

## Boundary

The platform envelope is universal. Material, formulation, trial, and test
fields are Technical Textiles Industry Hub extensions. Application domain
models and persistence are not changed by this schema package.
