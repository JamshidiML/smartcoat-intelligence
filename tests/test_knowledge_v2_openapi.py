from __future__ import annotations

import json
from typing import Any

from smartcoat.api.main import create_app

V2_PATHS = {
    "/api/v2/knowledge": {"get", "post"},
    "/api/v2/knowledge/{object_id}": {"get", "put", "delete"},
    "/api/v2/knowledge/{object_id}/lifecycle-actions": {"post"},
    "/api/v2/knowledge/{object_id}/audit-history": {"get"},
}


def _schema() -> dict[str, Any]:
    return create_app().openapi()


def _operations(schema: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        operation
        for path, methods in V2_PATHS.items()
        for method, operation in schema["paths"][path].items()
        if method in methods
    ]


def _referenced_schema(schema: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    name = reference["$ref"].rsplit("/", maxsplit=1)[-1]
    return schema["components"]["schemas"][name]


def test_openapi_contains_exact_v2_operations_and_unique_ids() -> None:
    schema = _schema()
    actual = {
        path: {
            method for method in schema["paths"][path] if method in {"get", "post", "put", "delete"}
        }
        for path in schema["paths"]
        if path.startswith("/api/v2")
    }
    operation_ids = [operation["operationId"] for operation in _operations(schema)]

    assert actual == V2_PATHS
    assert len(operation_ids) == 7
    assert len(operation_ids) == len(set(operation_ids))


def test_every_v2_operation_documents_context_headers_and_error_envelope() -> None:
    schema = _schema()

    for operation in _operations(schema):
        parameters = {parameter["name"]: parameter for parameter in operation["parameters"]}
        assert parameters["X-SmartCoat-Organization-ID"]["required"] is True
        assert parameters["X-SmartCoat-Organization-ID"]["in"] == "header"
        assert parameters["X-Correlation-ID"]["required"] is False
        assert parameters["X-Correlation-ID"]["in"] == "header"
        for status_code in ("400", "404", "409", "422", "500"):
            response = operation["responses"][status_code]
            response_schema = response["content"]["application/json"]["schema"]
            assert response_schema["$ref"].endswith("/SmartCoatAPIErrorResponse")


def test_create_and_update_requests_exclude_server_owned_fields() -> None:
    schema = _schema()
    create_ref = schema["paths"]["/api/v2/knowledge"]["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"]
    update_ref = schema["paths"]["/api/v2/knowledge/{object_id}"]["put"]["requestBody"]["content"][
        "application/json"
    ]["schema"]
    create = _referenced_schema(schema, create_ref)
    update = _referenced_schema(schema, update_ref)
    forbidden = {
        "object_id",
        "organization_id",
        "lifecycle_state",
        "revision",
        "created_at",
        "updated_at",
        "audit_sequence",
        "event_id",
        "recorded_at",
        "audit_payload",
    }

    assert set(create["properties"]) == {
        "mutable_state",
        "evidence",
        "provenance",
        "actor",
        "reason_or_note",
    }
    assert set(update["properties"]) == {
        "expected_revision",
        "replacement",
        "evidence",
        "provenance",
        "actor",
        "reason_or_note",
    }
    assert forbidden.isdisjoint(create["properties"])
    assert forbidden.isdisjoint(update["properties"])


def test_lifecycle_discriminator_has_exact_twelve_actions() -> None:
    schema = _schema()
    body = schema["paths"]["/api/v2/knowledge/{object_id}/lifecycle-actions"]["post"][
        "requestBody"
    ]["content"]["application/json"]["schema"]
    mapping = body["discriminator"]["mapping"]
    expected = {
        "submit_draft",
        "request_captured_correction",
        "complete_review",
        "reject_captured",
        "request_reviewed_correction",
        "validate_reviewed",
        "reject_reviewed",
        "request_validated_correction",
        "approve_validated",
        "reject_validated",
        "deprecate_approved",
        "reopen_rejected",
    }

    assert body["discriminator"]["propertyName"] == "action"
    assert set(mapping) == expected
    assert len(body["oneOf"]) == 12
    assert "delete_draft" not in mapping


def test_replacement_object_id_appears_only_on_deprecation_action() -> None:
    schema = _schema()
    action_names = {
        name for name in schema["components"]["schemas"] if name.endswith("ActionRequest")
    }

    for name in action_names:
        properties = schema["components"]["schemas"][name]["properties"]
        assert ("replacement_object_id" in properties) is (name == "DeprecateApprovedActionRequest")


def test_response_contracts_are_explicit_and_storage_free() -> None:
    schema = _schema()
    serialized = json.dumps(schema, sort_keys=True)
    required_models = {
        "KnowledgeObjectV2Response",
        "KnowledgeMutationResponse",
        "KnowledgeDraftDeleteResponse",
        "KnowledgeObjectV2CollectionItemResponse",
        "KnowledgeObjectV2PageResponse",
        "KnowledgeAuditEventResponse",
        "KnowledgeAuditHistoryResponse",
        "SmartCoatAPIErrorResponse",
    }

    assert required_models <= set(schema["components"]["schemas"])
    assert "canonical_state_json" not in serialized
    assert "canonical_metadata_json" not in serialized
    assert "KnowledgeAuditAppendRequest" not in serialized
    assert "xmin" not in serialized
    assert "knowledge_cursor_signing_key" not in serialized
    assert "SMARTCOAT_KNOWLEDGE_CURSOR_SIGNING_KEY" not in serialized


def test_legacy_routes_and_schemas_remain_present_without_v2_fields() -> None:
    schema = _schema()

    assert {"/knowledge", "/knowledge/{knowledge_id}", "/events", "/decisions"} <= set(
        schema["paths"]
    )
    legacy_create = schema["paths"]["/knowledge"]["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"]
    legacy_schema = _referenced_schema(schema, legacy_create)
    assert "context_references" not in legacy_schema["properties"]
    assert "revision" not in legacy_schema["properties"]
    assert "organization_id" not in legacy_schema["properties"]


def test_openapi_has_no_unapproved_public_surface_or_security_claim() -> None:
    schema = _schema()
    paths = "\n".join(schema["paths"])

    assert "/semantic" not in paths
    assert "/search" not in paths
    assert "/audit-append" not in paths
    assert "/bulk" not in paths
    assert "/ui" not in paths
    assert "securitySchemes" not in schema.get("components", {})
