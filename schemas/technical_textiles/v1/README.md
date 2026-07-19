# Technical Textiles Canonical Schema v1

Status: Controlled-pilot proposal

The JSON Schemas in this directory use JSON Schema Draft 2020-12 and extend the
canonical platform envelope at
[`../../platform/v1/platform-envelope.schema.json`](../../platform/v1/platform-envelope.schema.json):

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
validator registers the platform schema and all four Hub schemas by `$id`,
checks all five schemas, and validates every embedded example against its owning
schema with format checking enabled.

## Compatibility

Version `1.1.0` is a pilot schema contract, not a database migration or complete
enterprise ontology. Additive optional fields may be proposed in compatible v1
revisions. Required-field, semantic, identifier, unit, or enum changes require
a new schema version and a documented migration/mapping decision.

## Boundary

The platform-owned envelope's object type is extensible and contains no textile
enum. This directory contains no duplicate envelope definition. Material,
formulation, trial, and test child schemas constrain their own object types as
Technical Textiles Industry Hub extensions. Application domain models and
persistence are not changed by this schema package.

Governance values align with T07 schema `smartcoat-governance-v1.1-draft`.
Purpose decisions are explicit for all six canonical purposes; schema presence
does not verify authorization or replace IAM.
