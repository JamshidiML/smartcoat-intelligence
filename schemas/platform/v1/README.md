# SmartCoat Platform Schema v1

Status: Controlled-pilot proposal

This directory owns industry-agnostic mother-platform schemas. It currently
contains one canonical source:

- `platform-envelope.schema.json`: identity, tenancy, governance, provenance,
  evidence, review, lifecycle, relationship, timestamp, and measurement-state
  contract for platform and Industry Hub objects

The canonical schema ID is
`urn:smartcoat:schema:platform:v1:envelope`. Industry Hub schemas register this
ID and extend it by reference; they must not copy or redefine the envelope.

The envelope contains no Technical Textiles object-type enumeration. Each Hub
owns its domain-specific type constraints and fields.
