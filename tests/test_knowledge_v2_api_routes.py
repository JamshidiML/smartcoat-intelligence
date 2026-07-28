from __future__ import annotations

from datetime import UTC, datetime, timedelta
from inspect import getsource
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from smartcoat.api.dependencies.knowledge_v2 import (
    get_knowledge_audit_service,
    get_knowledge_query_service,
    get_knowledge_v2_read_service,
)
from smartcoat.api.main import create_app
from smartcoat.api.routes import knowledge_v2
from smartcoat.domain.base import LifecycleState
from smartcoat.domain.evidence_provenance import (
    CreationMethod,
    EvidenceCompleteness,
    EvidenceReference,
    EvidenceType,
    KnowledgeObjectV2EvidenceComposition,
    ProvenanceCompleteness,
    ProvenanceV2,
)
from smartcoat.domain.knowledge_audit import (
    KnowledgeAuditChangedField,
    KnowledgeAuditEvent,
    KnowledgeAuditEventType,
)
from smartcoat.domain.knowledge_lifecycle import LifecycleAction
from smartcoat.domain.knowledge_objects import KnowledgeObjectType
from smartcoat.domain.knowledge_objects_v2 import (
    ConfidentialityLevel,
    KnowledgeObjectV2CoreRecord,
    KnowledgeObjectV2MutableState,
    KnowledgeObjectV2PersistedStateSnapshot,
    OwnerReference,
)
from smartcoat.domain.knowledge_query import (
    KnowledgeObjectV2CollectionItem,
    KnowledgeObjectV2CollectionOwner,
    KnowledgeObjectV2Page,
    KnowledgeQueryCursorError,
    KnowledgeQuerySort,
)
from smartcoat.services.knowledge_audit_service import (
    KnowledgeAuditMutationResult,
    KnowledgeAuditServiceError,
)
from smartcoat.storage.repositories.knowledge_v2_repository import (
    KnowledgeObjectV2RepositoryError,
)

NOW = datetime(2026, 7, 27, 12, 0, tzinfo=UTC)
OBJECT_ID = UUID("00000000-0000-0000-0000-000000000911")
DELETED_ID = UUID("00000000-0000-0000-0000-000000000912")
CORRELATION_ID = UUID("00000000-0000-0000-0000-000000000913")
HEADERS = {
    "X-SmartCoat-Organization-ID": "synthetic-org",
    "X-Correlation-ID": str(CORRELATION_ID),
}


def _state(*, title: str = "Synthetic API object") -> KnowledgeObjectV2MutableState:
    return KnowledgeObjectV2MutableState(
        title=title,
        description="Generalized metadata-only route fixture.",
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        owner=OwnerReference(
            owner_id="synthetic-owner",
            role="knowledge_author",
        ),
        confidentiality=ConfidentialityLevel.INTERNAL,
        tags=("synthetic",),
        content={"result": True, "sample_count": 3},
        evidence_ids=("synthetic-evidence-1",),
    )


def _evidence() -> tuple[EvidenceReference, ...]:
    return (
        EvidenceReference(
            evidence_id="synthetic-evidence-1",
            evidence_type=EvidenceType.OBSERVATION,
            completeness=EvidenceCompleteness.COMPLETE,
            title="Synthetic evidence",
            source_reference="synthetic://evidence/1",
            captured_by="synthetic-author",
            captured_at=NOW - timedelta(minutes=2),
        ),
    )


def _provenance() -> ProvenanceV2:
    return ProvenanceV2(
        source_system="synthetic-test",
        source_reference="synthetic://knowledge/1",
        created_by="synthetic-author",
        creation_method=CreationMethod.MANUAL,
        captured_at=NOW - timedelta(minutes=1),
        completeness=ProvenanceCompleteness.COMPLETE,
    )


def _composition(
    *,
    object_id: UUID = OBJECT_ID,
    organization_id: str = "synthetic-org",
    revision: int = 1,
    lifecycle: LifecycleState = LifecycleState.DRAFT,
    title: str = "Synthetic API object",
) -> KnowledgeObjectV2EvidenceComposition:
    return KnowledgeObjectV2EvidenceComposition(
        core=KnowledgeObjectV2CoreRecord(
            object_id=object_id,
            organization_id=organization_id,
            revision=revision,
            lifecycle_state=lifecycle,
            created_at=NOW,
            updated_at=NOW + timedelta(seconds=revision),
            mutable_state=KnowledgeObjectV2PersistedStateSnapshot.from_mutable_state(
                _state(title=title)
            ),
        ),
        evidence=_evidence(),
        provenance=_provenance(),
    )


def _event(
    *,
    object_id: UUID = OBJECT_ID,
    event_type: KnowledgeAuditEventType = KnowledgeAuditEventType.CREATE,
    audit_sequence: int = 1,
) -> KnowledgeAuditEvent:
    if event_type is KnowledgeAuditEventType.CREATE:
        lifecycle_action = None
        previous_lifecycle = None
        resulting_lifecycle = LifecycleState.DRAFT
        previous_revision = None
        resulting_revision = 1
        changed_fields = (
            KnowledgeAuditChangedField.TITLE,
            KnowledgeAuditChangedField.REVISION,
        )
    elif event_type is KnowledgeAuditEventType.DRAFT_DELETE:
        lifecycle_action = LifecycleAction.DELETE_DRAFT
        previous_lifecycle = LifecycleState.DRAFT
        resulting_lifecycle = None
        previous_revision = 1
        resulting_revision = None
        changed_fields = ()
    else:
        lifecycle_action = None
        previous_lifecycle = LifecycleState.DRAFT
        resulting_lifecycle = LifecycleState.DRAFT
        previous_revision = 1
        resulting_revision = 2
        changed_fields = (KnowledgeAuditChangedField.TITLE,)
    return KnowledgeAuditEvent(
        event_id=UUID(f"00000000-0000-0000-0000-{audit_sequence:012d}"),
        organization_id="synthetic-org",
        object_id=object_id,
        event_type=event_type,
        lifecycle_action=lifecycle_action,
        actor_id="synthetic-author",
        actor_role="knowledge_author",
        occurred_at=NOW,
        recorded_at=NOW + timedelta(seconds=1),
        audit_sequence=audit_sequence,
        correlation_id=CORRELATION_ID,
        previous_lifecycle=previous_lifecycle,
        resulting_lifecycle=resulting_lifecycle,
        previous_revision=previous_revision,
        resulting_revision=resulting_revision,
        reason_or_note="Synthetic route event.",
        changed_fields=changed_fields,
    )


def _create_payload() -> dict[str, Any]:
    return {
        "mutable_state": _state().model_dump(mode="json"),
        "evidence": [_evidence()[0].model_dump(mode="json")],
        "provenance": _provenance().model_dump(mode="json"),
        "actor": {
            "actor_id": "synthetic-author",
            "actor_role": "knowledge_author",
        },
        "reason_or_note": "Create synthetic draft.",
    }


def _update_payload(*, reason: str = "Update synthetic draft.") -> dict[str, Any]:
    return {
        "expected_revision": 1,
        "replacement": _state(title="Updated synthetic object").model_dump(mode="json"),
        "actor": {
            "actor_id": "synthetic-author",
            "actor_role": "knowledge_author",
        },
        "reason_or_note": reason,
    }


class FakeAuditService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []
        self.history: dict[UUID, tuple[KnowledgeAuditEvent, ...]] = {
            OBJECT_ID: (_event(),),
            DELETED_ID: (
                _event(object_id=DELETED_ID),
                _event(
                    object_id=DELETED_ID,
                    event_type=KnowledgeAuditEventType.DRAFT_DELETE,
                    audit_sequence=2,
                ),
            ),
        }

    def create(self, command: Any) -> KnowledgeAuditMutationResult:
        self.calls.append(("create", command))
        return KnowledgeAuditMutationResult(
            knowledge=_composition(),
            audit_event=_event(),
        )

    def update(self, command: Any) -> KnowledgeAuditMutationResult:
        self.calls.append(("update", command))
        reason = command.reason_or_note
        if reason == "stale":
            raise KnowledgeObjectV2RepositoryError("stale_revision", "internal revision detail")
        if reason == "non-draft":
            raise KnowledgeAuditServiceError(
                "knowledge_update_lifecycle_forbidden",
                "internal lifecycle detail",
            )
        if reason == "unexpected":
            raise RuntimeError("postgresql://secret@localhost/private_table")
        return KnowledgeAuditMutationResult(
            knowledge=_composition(
                revision=(1 if reason == "no-op" else 2),
                title=("Synthetic API object" if reason == "no-op" else "Updated"),
            ),
            audit_event=(
                None if reason == "no-op" else _event(event_type=KnowledgeAuditEventType.UPDATE)
            ),
        )

    def transition(
        self,
        *,
        organization_id: str,
        command: Any,
        correlation_id: UUID,
    ) -> KnowledgeAuditMutationResult:
        self.calls.append(
            (
                "transition",
                {
                    "organization_id": organization_id,
                    "command": command,
                    "correlation_id": correlation_id,
                },
            )
        )
        if command.actor.actor_id == "invalid-transition":
            raise KnowledgeObjectV2RepositoryError(
                "invalid_lifecycle_transition",
                "internal transition detail",
            )
        return KnowledgeAuditMutationResult(
            knowledge=_composition(revision=2, lifecycle=LifecycleState.CAPTURED),
            audit_event=_event(),
        )

    def delete_draft(
        self,
        *,
        organization_id: str,
        command: Any,
        correlation_id: UUID,
    ) -> KnowledgeAuditMutationResult:
        self.calls.append(
            (
                "delete",
                {
                    "organization_id": organization_id,
                    "command": command,
                    "correlation_id": correlation_id,
                },
            )
        )
        if command.reason == "ineligible":
            raise KnowledgeObjectV2RepositoryError(
                "draft_delete_ineligible",
                "internal deletion detail",
            )
        return KnowledgeAuditMutationResult(
            knowledge=None,
            audit_event=_event(
                object_id=command.object_id,
                event_type=KnowledgeAuditEventType.DRAFT_DELETE,
            ),
        )

    def history_for_object(
        self,
        *,
        organization_id: str,
        object_id: UUID,
    ) -> tuple[KnowledgeAuditEvent, ...]:
        self.calls.append(("history", (organization_id, object_id)))
        return self.history.get(object_id, ())


class FakeReadService:
    def __init__(self) -> None:
        self.deleted = {DELETED_ID}
        self.calls: list[dict[str, Any]] = []

    def get(
        self,
        *,
        object_id: UUID,
        organization_id: str,
    ) -> KnowledgeObjectV2EvidenceComposition | None:
        self.calls.append(
            {
                "object_id": object_id,
                "organization_id": organization_id,
            }
        )
        if (
            organization_id != "synthetic-org"
            or object_id != OBJECT_ID
            or object_id in self.deleted
        ):
            return None
        return _composition(object_id=object_id)


class FakeQueryService:
    def __init__(self) -> None:
        self.calls: list[Any] = []

    def query(self, command: Any) -> KnowledgeObjectV2Page:
        self.calls.append(command)
        if command.cursor == "invalid":
            raise KnowledgeQueryCursorError(
                "knowledge_query_cursor_signature_invalid",
                "internal cursor payload",
            )
        item = KnowledgeObjectV2CollectionItem(
            object_id=OBJECT_ID,
            revision=1,
            lifecycle_state=LifecycleState.DRAFT,
            title="Synthetic API object",
            knowledge_type=KnowledgeObjectType.OBSERVATION,
            owner=KnowledgeObjectV2CollectionOwner(
                owner_id="synthetic-owner",
                role="knowledge_author",
            ),
            confidentiality=ConfidentialityLevel.INTERNAL,
            created_at=NOW,
            updated_at=NOW,
        )
        has_more = command.page_size == 1 and command.cursor is None
        return KnowledgeObjectV2Page(
            items=(item,),
            returned_count=1,
            requested_page_size=command.page_size,
            has_more=has_more,
            next_cursor=("opaque-next" if has_more else None),
            applied_sort=command.sort,
        )


@pytest.fixture()
def api() -> tuple[TestClient, FakeAuditService, FakeReadService, FakeQueryService]:
    application = create_app()
    application.openapi()
    audit = FakeAuditService()
    read = FakeReadService()
    query = FakeQueryService()
    application.dependency_overrides[get_knowledge_audit_service] = lambda: audit
    application.dependency_overrides[get_knowledge_v2_read_service] = lambda: read
    application.dependency_overrides[get_knowledge_query_service] = lambda: query
    return TestClient(application, raise_server_exceptions=False), audit, read, query


def test_create_returns_201_exact_correlation_and_audit(
    api: tuple[TestClient, FakeAuditService, FakeReadService, FakeQueryService],
) -> None:
    client, audit, _, _ = api

    response = client.post("/api/v2/knowledge", headers=HEADERS, json=_create_payload())

    assert response.status_code == 201
    assert response.headers["X-Correlation-ID"] == str(CORRELATION_ID)
    assert response.json()["knowledge"]["lifecycle_state"] == "draft"
    assert response.json()["knowledge"]["revision"] == 1
    assert response.json()["audit_event"]["event_type"] == "create"
    command = audit.calls[0][1]
    assert command.correlation_id == CORRELATION_ID
    assert command.create.organization_id == "synthetic-org"


def test_get_found_missing_cross_organization_and_deleted(
    api: tuple[TestClient, FakeAuditService, FakeReadService, FakeQueryService],
) -> None:
    client, _, read, _ = api

    found = client.get(f"/api/v2/knowledge/{OBJECT_ID}", headers=HEADERS)
    missing = client.get(
        "/api/v2/knowledge/00000000-0000-0000-0000-000000000999",
        headers=HEADERS,
    )
    cross_org = client.get(
        f"/api/v2/knowledge/{OBJECT_ID}",
        headers={**HEADERS, "X-SmartCoat-Organization-ID": "other-org"},
    )
    deleted = client.get(f"/api/v2/knowledge/{DELETED_ID}", headers=HEADERS)

    assert found.status_code == 200
    assert found.json()["evidence"][0]["evidence_id"] == "synthetic-evidence-1"
    for response in (missing, cross_org, deleted):
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "knowledge_object_not_found"
    assert read.calls[-2]["organization_id"] == "other-org"


@pytest.mark.parametrize(
    ("reason", "status_code", "audit_event", "error_code"),
    [
        ("Update synthetic draft.", 200, True, None),
        ("no-op", 200, False, None),
        ("stale", 409, None, "stale_revision"),
        (
            "non-draft",
            409,
            None,
            "knowledge_update_lifecycle_forbidden",
        ),
    ],
)
def test_update_material_noop_stale_and_non_draft(
    api: tuple[TestClient, FakeAuditService, FakeReadService, FakeQueryService],
    reason: str,
    status_code: int,
    audit_event: bool | None,
    error_code: str | None,
) -> None:
    client, _, _, _ = api

    response = client.put(
        f"/api/v2/knowledge/{OBJECT_ID}",
        headers=HEADERS,
        json=_update_payload(reason=reason),
    )

    assert response.status_code == status_code
    if error_code is None:
        assert (response.json()["audit_event"] is not None) is audit_event
    else:
        assert response.json()["error"]["code"] == error_code
        assert "internal" not in response.text


_LIFECYCLE_PAYLOADS = (
    {"action": "submit_draft", "submission_note": "Submit."},
    {
        "action": "request_captured_correction",
        "correction_reason": "Correct.",
    },
    {"action": "complete_review", "review_note": "Review."},
    {"action": "reject_captured", "rejection_reason": "Reject."},
    {
        "action": "request_reviewed_correction",
        "correction_reason": "Correct.",
    },
    {"action": "validate_reviewed", "validation_note": "Validate."},
    {"action": "reject_reviewed", "rejection_reason": "Reject."},
    {
        "action": "request_validated_correction",
        "correction_reason": "Correct.",
    },
    {"action": "approve_validated", "approval_note": "Approve."},
    {"action": "reject_validated", "rejection_reason": "Reject."},
    {
        "action": "deprecate_approved",
        "deprecation_reason": "Superseded.",
        "replacement_object_id": "00000000-0000-0000-0000-000000000914",
    },
    {"action": "reopen_rejected", "reopen_reason": "Reopen."},
)


@pytest.mark.parametrize("specific", _LIFECYCLE_PAYLOADS)
def test_all_twelve_lifecycle_actions_reach_transition_service(
    api: tuple[TestClient, FakeAuditService, FakeReadService, FakeQueryService],
    specific: dict[str, object],
) -> None:
    client, audit, _, _ = api
    payload = {
        **specific,
        "expected_revision": 1,
        "actor": {
            "actor_id": "synthetic-actor",
            "actor_role": "reviewer",
        },
    }

    response = client.post(
        f"/api/v2/knowledge/{OBJECT_ID}/lifecycle-actions",
        headers=HEADERS,
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["audit_event"] is not None
    transition = audit.calls[-1][1]
    assert transition["command"].object_id == OBJECT_ID
    assert transition["correlation_id"] == CORRELATION_ID


def test_invalid_transition_uses_conflict_envelope(
    api: tuple[TestClient, FakeAuditService, FakeReadService, FakeQueryService],
) -> None:
    client, _, _, _ = api
    payload = {
        "action": "submit_draft",
        "expected_revision": 1,
        "actor": {
            "actor_id": "invalid-transition",
            "actor_role": "knowledge_author",
        },
        "submission_note": "Submit.",
    }

    response = client.post(
        f"/api/v2/knowledge/{OBJECT_ID}/lifecycle-actions",
        headers=HEADERS,
        json=payload,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "invalid_lifecycle_transition"
    assert response.json()["error"]["correlation_id"] == str(CORRELATION_ID)


def test_delete_and_ineligible_delete_are_content_free(
    api: tuple[TestClient, FakeAuditService, FakeReadService, FakeQueryService],
) -> None:
    client, _, _, _ = api
    payload = {
        "expected_revision": 1,
        "actor": {
            "actor_id": "synthetic-author",
            "actor_role": "knowledge_author",
        },
        "reason": "Delete synthetic draft.",
    }

    deleted = client.request(
        "DELETE",
        f"/api/v2/knowledge/{DELETED_ID}",
        headers=HEADERS,
        json=payload,
    )
    payload["reason"] = "ineligible"
    ineligible = client.request(
        "DELETE",
        f"/api/v2/knowledge/{OBJECT_ID}",
        headers=HEADERS,
        json=payload,
    )

    assert deleted.status_code == 200
    assert set(deleted.json()) == {"deleted_object_id", "deleted", "audit_event"}
    assert deleted.json()["deleted"] is True
    assert "content" not in deleted.text
    assert ineligible.status_code == 409
    assert ineligible.json()["error"]["code"] == "draft_delete_ineligible"


def test_deleted_history_is_retained_and_unknown_history_is_404(
    api: tuple[TestClient, FakeAuditService, FakeReadService, FakeQueryService],
) -> None:
    client, _, _, _ = api

    retained = client.get(
        f"/api/v2/knowledge/{DELETED_ID}/audit-history",
        headers=HEADERS,
    )
    missing = client.get(
        "/api/v2/knowledge/00000000-0000-0000-0000-000000000999/audit-history",
        headers=HEADERS,
    )

    assert retained.status_code == 200
    assert [event["audit_sequence"] for event in retained.json()["events"]] == [1, 2]
    assert retained.json()["events"][-1]["event_type"] == "draft_delete"
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "knowledge_history_not_found"


def test_list_maps_all_filters_and_page_metadata(
    api: tuple[TestClient, FakeAuditService, FakeReadService, FakeQueryService],
) -> None:
    client, _, _, query = api
    query_string = (
        "?knowledge_type=observation&lifecycle_state=draft&owner_id=synthetic-owner"
        "&tags_all=synthetic&tags_all=coating&context_type=project&context_id_kind=uuid"
        "&context_reference_id=00000000-0000-0000-0000-000000000903"
        "&context_relationship_role=source"
        "&created_from=2026-07-01T00:00:00Z&created_before=2026-08-01T00:00:00Z"
        "&updated_from=2026-07-01T00:00:00Z&updated_before=2026-08-01T00:00:00Z"
        "&sort=created_at_asc&page_size=1"
    )

    first = client.get(f"/api/v2/knowledge{query_string}", headers=HEADERS)
    final = client.get(
        f"/api/v2/knowledge{query_string}&cursor=opaque-next",
        headers=HEADERS,
    )

    assert first.status_code == 200
    assert first.json()["has_more"] is True
    assert first.json()["next_cursor"] == "opaque-next"
    assert final.status_code == 200
    assert final.json()["has_more"] is False
    command = query.calls[0]
    assert command.filters.tags_all == ("synthetic", "coating")
    assert command.filters.context is not None
    assert command.filters.context.relationship_role == "source"
    assert command.sort is KnowledgeQuerySort.CREATED_AT_ASC


def test_invalid_cursor_and_cross_organization_cursor_use_400(
    api: tuple[TestClient, FakeAuditService, FakeReadService, FakeQueryService],
) -> None:
    client, _, _, _ = api

    invalid = client.get(
        "/api/v2/knowledge?cursor=invalid",
        headers=HEADERS,
    )

    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "knowledge_query_cursor_signature_invalid"
    assert "payload" not in invalid.text


def test_correlation_generation_preservation_and_malformed_header(
    api: tuple[TestClient, FakeAuditService, FakeReadService, FakeQueryService],
) -> None:
    client, _, _, _ = api
    generated = client.get(
        f"/api/v2/knowledge/{OBJECT_ID}",
        headers={"X-SmartCoat-Organization-ID": "synthetic-org"},
    )
    malformed = client.get(
        f"/api/v2/knowledge/{OBJECT_ID}",
        headers={
            "X-SmartCoat-Organization-ID": "synthetic-org",
            "X-Correlation-ID": "not-a-uuid",
        },
    )

    assert generated.status_code == 200
    UUID(generated.headers["X-Correlation-ID"])
    assert malformed.status_code == 400
    UUID(malformed.headers["X-Correlation-ID"])
    assert malformed.json()["error"]["code"] == "correlation_id_invalid"
    assert malformed.json()["error"]["correlation_id"] == malformed.headers["X-Correlation-ID"]


def test_safe_422_never_echoes_input_values(
    api: tuple[TestClient, FakeAuditService, FakeReadService, FakeQueryService],
) -> None:
    client, _, _, _ = api
    payload = _create_payload()
    payload["mutable_state"]["content"] = {"secret_value": "must-not-echo"}
    payload["unexpected"] = "private-value"

    response = client.post("/api/v2/knowledge", headers=HEADERS, json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_error"
    assert "must-not-echo" not in response.text
    assert "private-value" not in response.text


def test_safe_500_sanitizes_unexpected_service_error(
    api: tuple[TestClient, FakeAuditService, FakeReadService, FakeQueryService],
) -> None:
    client, _, _, _ = api

    response = client.put(
        f"/api/v2/knowledge/{OBJECT_ID}",
        headers=HEADERS,
        json=_update_payload(reason="unexpected"),
    )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_server_error"
    assert "postgresql" not in response.text
    assert "private_table" not in response.text


def test_missing_cursor_key_fails_closed_with_safe_500() -> None:
    application = create_app()
    client = TestClient(application, raise_server_exceptions=False)

    response = client.get("/api/v2/knowledge", headers=HEADERS)

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "server_configuration_error"


def test_partial_context_filter_is_deterministic_400(
    api: tuple[TestClient, FakeAuditService, FakeReadService, FakeQueryService],
) -> None:
    client, _, _, _ = api

    response = client.get(
        "/api/v2/knowledge?context_type=project",
        headers=HEADERS,
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "context_filter_incomplete"


def test_routes_do_not_construct_repositories_or_unit_of_work() -> None:
    source = getsource(knowledge_v2)

    assert "KnowledgeObjectV2Repository(" not in source
    assert "KnowledgeObjectV2QueryRepository(" not in source
    assert "KnowledgeAuditRepository(" not in source
    assert "KnowledgeUnitOfWork(" not in source
