from __future__ import annotations

import os
import re
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from alembic import command
from smartcoat.api.dependencies.database import get_db_session
from smartcoat.api.dependencies.knowledge_v2 import (
    get_knowledge_audit_service,
    get_knowledge_v2_session_factory,
)
from smartcoat.api.main import create_app
from smartcoat.core.config import Settings, get_settings
from smartcoat.services.knowledge_audit_service import KnowledgeAuditService
from smartcoat.storage.repositories.knowledge_audit_repository import (
    KnowledgeAuditParticipant,
)

LIVE_POSTGRES_OPT_IN = "true"
TEST_SCHEMA_PATTERN = re.compile(r"^smartcoat_test_[a-z0-9_]+$")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_CURSOR_KEY = "synthetic-t09-live-cursor-signing-key-000000000000"
ORGANIZATION_ID = "synthetic-org-t09"
OTHER_ORGANIZATION_ID = "synthetic-org-t09-other"
NOW = datetime(2026, 7, 27, 14, 0, tzinfo=UTC)


@dataclass(frozen=True)
class LiveAPIContext:
    app: FastAPI
    client: TestClient
    session_factory: sessionmaker[Session]
    engine: Engine
    schema_name: str


class FailingAuditParticipant(KnowledgeAuditParticipant):
    def flush(self, session: Session) -> None:
        assert session.in_transaction()
        raise RuntimeError("synthetic T09 audit participant failure")


def _require_live_postgres(database_url: str | None, opt_in: str | None) -> str:
    if opt_in != LIVE_POSTGRES_OPT_IN:
        raise RuntimeError(
            "Refusing T09 live PostgreSQL execution without explicit opt-in: "
            "SMARTCOAT_RUN_LIVE_POSTGRES_TESTS=true."
        )
    if not database_url:
        raise RuntimeError("SMARTCOAT_TEST_DATABASE_URL is required.")
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise RuntimeError("T09 live tests require PostgreSQL.")
    if url.host not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("T09 live tests accept only a localhost PostgreSQL target.")
    if not (url.database or "").startswith("smartcoat_test"):
        raise RuntimeError("T09 live tests require a database beginning with smartcoat_test.")
    return database_url


def _schema_name() -> str:
    return f"smartcoat_test_t09_{uuid4().hex[:12]}"


def _assert_schema_name(schema_name: str) -> None:
    if TEST_SCHEMA_PATTERN.fullmatch(schema_name) is None:
        raise RuntimeError("unsafe T09 test schema name")


def _drop_schema_and_assert_absent(engine: Engine, schema_name: str) -> None:
    _assert_schema_name(schema_name)
    with engine.begin() as connection:
        connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
    with engine.connect() as connection:
        remaining = connection.scalar(
            text("SELECT count(*) FROM pg_namespace WHERE nspname = :schema_name"),
            {"schema_name": schema_name},
        )
    assert remaining == 0


@contextmanager
def _alembic_schema(schema_name: str) -> Generator[None, None, None]:
    original = os.environ.get("SMARTCOAT_ALEMBIC_SCHEMA")
    os.environ["SMARTCOAT_ALEMBIC_SCHEMA"] = schema_name
    try:
        yield
    finally:
        if original is None:
            os.environ.pop("SMARTCOAT_ALEMBIC_SCHEMA", None)
        else:
            os.environ["SMARTCOAT_ALEMBIC_SCHEMA"] = original


def _run_upgrade(database_url: str, schema_name: str) -> None:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    with _alembic_schema(schema_name):
        command.upgrade(config, "head")


def _schema_engine(database_url: str, schema_name: str) -> Engine:
    return create_engine(
        database_url,
        poolclass=NullPool,
        connect_args={"options": f"-csearch_path={schema_name}"},
    )


@pytest.fixture(scope="session")
def live_database_url() -> str:
    database_url = os.getenv("SMARTCOAT_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set SMARTCOAT_TEST_DATABASE_URL for T09 PostgreSQL tests.")
    return _require_live_postgres(
        database_url,
        os.getenv("SMARTCOAT_RUN_LIVE_POSTGRES_TESTS"),
    )


@pytest.fixture(scope="module")
def live_api(live_database_url: str) -> Generator[LiveAPIContext, None, None]:
    schema_name = _schema_name()
    admin_engine = create_engine(live_database_url, poolclass=NullPool)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
    _run_upgrade(live_database_url, schema_name)
    engine = _schema_engine(live_database_url, schema_name)
    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    application = create_app()
    application.openapi()
    audit_service = KnowledgeAuditService(factory)
    settings = Settings(
        _env_file=None,
        knowledge_cursor_signing_key=SecretStr(SYNTHETIC_CURSOR_KEY),
    )

    def override_session_factory() -> sessionmaker[Session]:
        return factory

    def override_db_session() -> Generator[Session, None, None]:
        with factory() as session:
            yield session

    application.dependency_overrides[get_knowledge_v2_session_factory] = override_session_factory
    application.dependency_overrides[get_knowledge_audit_service] = lambda: audit_service
    application.dependency_overrides[get_settings] = lambda: settings
    application.dependency_overrides[get_db_session] = override_db_session

    try:
        with TestClient(application, raise_server_exceptions=False) as client:
            yield LiveAPIContext(
                app=application,
                client=client,
                session_factory=factory,
                engine=engine,
                schema_name=schema_name,
            )
    finally:
        application.dependency_overrides.clear()
        engine.dispose()
        _drop_schema_and_assert_absent(admin_engine, schema_name)
        admin_engine.dispose()


def _headers(
    *,
    organization_id: str = ORGANIZATION_ID,
    correlation_id: UUID | None = None,
) -> dict[str, str]:
    return {
        "X-SmartCoat-Organization-ID": organization_id,
        "X-Correlation-ID": str(correlation_id or uuid4()),
    }


def _actor(role: str = "knowledge_author") -> dict[str, str]:
    return {
        "actor_id": f"synthetic-{role}",
        "actor_role": role,
    }


def _create_payload(
    *,
    marker: str,
    include_full_context: bool = False,
) -> dict[str, Any]:
    context = []
    if include_full_context:
        context = [
            {
                "context_type": "project",
                "id_kind": "uuid",
                "reference_id": str(uuid4()),
                "display_name": "Synthetic project",
                "relationship_role": "scope",
                "attributes": {"phase": "pilot"},
            },
            {
                "context_type": "material",
                "id_kind": "external",
                "reference_id": f"MAT-{marker}",
                "source_system": "synthetic-catalog",
                "display_name": "Synthetic material",
                "relationship_role": "subject",
                "attributes": {"family": "generalized"},
            },
            {
                "context_type": "formulation_reference",
                "id_kind": "external",
                "reference_id": f"FORM-{marker}",
                "source_system": "synthetic-catalog",
                "display_name": "Synthetic formulation reference",
                "relationship_role": "input",
                "attributes": {"version_label": "v1"},
            },
            {
                "context_type": "test_result",
                "id_kind": "external",
                "reference_id": f"TEST-{marker}",
                "source_system": "synthetic-lab",
                "display_name": "Synthetic test result",
                "relationship_role": "evidence",
                "attributes": {"outcome": "pass"},
            },
        ]
    evidence_id = f"synthetic-evidence-{marker}"
    return {
        "mutable_state": {
            "title": f"Synthetic coating knowledge {marker}",
            "description": "Generalized metadata-only live API fixture.",
            "knowledge_type": "observation",
            "owner": {
                "owner_id": "synthetic-owner",
                "role": "knowledge_author",
            },
            "confidentiality": "internal",
            "tags": ["synthetic", "coating", marker],
            "content": {
                "result": True,
                "sample_count": 3,
                "method": "generalized",
            },
            "context": {"references": context},
            "evidence_ids": [evidence_id],
            "knowledge_relationships": [],
            "decision_relationships": [],
        },
        "evidence": [
            {
                "evidence_id": evidence_id,
                "evidence_type": "observation",
                "completeness": "complete",
                "title": f"Synthetic evidence {marker}",
                "source_reference": f"synthetic://evidence/{marker}",
                "source_system": "synthetic-test",
                "captured_by": "synthetic-author",
                "captured_at": NOW.isoformat(),
                "media_type": "application/json",
                "confidentiality": "internal",
            }
        ],
        "provenance": {
            "source_system": "synthetic-test",
            "source_reference": f"synthetic://knowledge/{marker}",
            "created_by": "synthetic-author",
            "creation_method": "manual",
            "captured_at": NOW.isoformat(),
            "transformation_history": [],
            "completeness": "complete",
        },
        "actor": _actor(),
        "reason_or_note": f"Create synthetic draft {marker}.",
    }


def _create(
    context: LiveAPIContext,
    *,
    marker: str,
    include_full_context: bool = False,
) -> dict[str, Any]:
    response = context.client.post(
        "/api/v2/knowledge",
        headers=_headers(),
        json=_create_payload(marker=marker, include_full_context=include_full_context),
    )
    assert response.status_code == 201, response.text
    payload: dict[str, Any] = response.json()
    assert payload["knowledge"]["revision"] == 1
    assert payload["knowledge"]["lifecycle_state"] == "draft"
    assert payload["audit_event"]["event_type"] == "create"
    return payload


def _transition(
    context: LiveAPIContext,
    object_id: str,
    *,
    expected_revision: int,
    action: str,
    field: str,
    value: str,
    role: str = "knowledge_author",
    replacement_object_id: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "action": action,
        "expected_revision": expected_revision,
        "actor": _actor(role),
        field: value,
    }
    if replacement_object_id is not None:
        payload["replacement_object_id"] = replacement_object_id
    response = context.client.post(
        f"/api/v2/knowledge/{object_id}/lifecycle-actions",
        headers=_headers(),
        json=payload,
    )
    assert response.status_code == 200, response.text
    result: dict[str, Any] = response.json()
    assert result["audit_event"]["lifecycle_action"] == action
    return result


def _storage_snapshot(context: LiveAPIContext, object_id: str) -> dict[str, Any]:
    child_tables = (
        "knowledge_object_v2_tags",
        "knowledge_object_v2_evidence",
        "knowledge_object_v2_provenance",
        "knowledge_object_v2_context",
    )
    with context.engine.connect() as connection:
        root = connection.execute(
            text(
                "SELECT revision, xmin::text FROM knowledge_objects_v2 WHERE object_id = :object_id"
            ),
            {"object_id": object_id},
        ).one()
        child_xmins = {
            table: tuple(
                connection.scalars(
                    text(
                        f"SELECT xmin::text FROM {table} "
                        "WHERE object_id = :object_id ORDER BY xmin::text"
                    ),
                    {"object_id": object_id},
                )
            )
            for table in child_tables
        }
        audit_count = connection.scalar(
            text("SELECT count(*) FROM knowledge_audit_events_v2 WHERE object_id = :object_id"),
            {"object_id": object_id},
        )
    return {
        "revision": root.revision,
        "root_xmin": root.xmin,
        "child_xmins": child_xmins,
        "audit_count": audit_count,
    }


def test_live_postgres_guardrails() -> None:
    with pytest.raises(RuntimeError, match="explicit opt-in"):
        _require_live_postgres(
            "postgresql+psycopg://synthetic:synthetic@localhost/smartcoat_test",
            None,
        )
    with pytest.raises(RuntimeError, match="localhost"):
        _require_live_postgres(
            "postgresql+psycopg://synthetic:synthetic@example.com/smartcoat_test",
            LIVE_POSTGRES_OPT_IN,
        )
    with pytest.raises(RuntimeError, match="beginning with smartcoat_test"):
        _require_live_postgres(
            "postgresql+psycopg://synthetic:synthetic@localhost/production",
            LIVE_POSTGRES_OPT_IN,
        )


def test_http_create_get_list_update_lifecycle_history_and_read_only(
    live_api: LiveAPIContext,
) -> None:
    created = _create(live_api, marker="primary", include_full_context=True)
    object_id = created["knowledge"]["object_id"]
    detail = live_api.client.get(
        f"/api/v2/knowledge/{object_id}",
        headers=_headers(),
    )
    assert detail.status_code == 200
    assert len(detail.json()["mutable_state"]["context_references"]) == 4
    assert detail.json()["evidence"][0]["source_reference"].startswith("synthetic://")
    assert detail.json()["provenance"]["completeness"] == "complete"

    listed = live_api.client.get(
        "/api/v2/knowledge?knowledge_type=observation&lifecycle_state=draft"
        "&owner_id=synthetic-owner&tags_all=synthetic&tags_all=coating"
        "&context_type=material&context_id_kind=external"
        "&context_reference_id=MAT-primary&context_source_system=synthetic-catalog"
        "&sort=created_at_asc&page_size=10",
        headers=_headers(),
    )
    assert listed.status_code == 200
    assert [item["object_id"] for item in listed.json()["items"]] == [object_id]

    before_reads = _storage_snapshot(live_api, object_id)
    history_read = live_api.client.get(
        f"/api/v2/knowledge/{object_id}/audit-history",
        headers=_headers(),
    )
    assert history_read.status_code == 200
    after_reads = _storage_snapshot(live_api, object_id)
    assert after_reads == before_reads

    replacement = created["knowledge"]["mutable_state"]
    replacement["title"] = "Updated synthetic coating knowledge"
    replacement["context"] = {
        "references": replacement.pop("context_references"),
    }
    update = live_api.client.put(
        f"/api/v2/knowledge/{object_id}",
        headers=_headers(),
        json={
            "expected_revision": 1,
            "replacement": replacement,
            "actor": _actor(),
            "reason_or_note": "Update synthetic draft through CAS.",
        },
    )
    assert update.status_code == 200, update.text
    assert update.json()["knowledge"]["revision"] == 2
    assert update.json()["audit_event"]["event_type"] == "update"

    stale = live_api.client.put(
        f"/api/v2/knowledge/{object_id}",
        headers=_headers(),
        json={
            "expected_revision": 1,
            "replacement": replacement,
            "actor": _actor(),
            "reason_or_note": "Stale synthetic update.",
        },
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "stale_revision"

    no_op = live_api.client.put(
        f"/api/v2/knowledge/{object_id}",
        headers=_headers(),
        json={
            "expected_revision": 2,
            "replacement": replacement,
            "actor": _actor(),
            "reason_or_note": "Confirm exact synthetic no-op.",
        },
    )
    assert no_op.status_code == 200
    assert no_op.json()["knowledge"]["revision"] == 2
    assert no_op.json()["audit_event"] is None

    submitted = _transition(
        live_api,
        object_id,
        expected_revision=2,
        action="submit_draft",
        field="submission_note",
        value="Submit synthetic draft.",
    )
    reviewed = _transition(
        live_api,
        object_id,
        expected_revision=3,
        action="complete_review",
        field="review_note",
        value="Complete synthetic review.",
        role="reviewer",
    )
    validated = _transition(
        live_api,
        object_id,
        expected_revision=4,
        action="validate_reviewed",
        field="validation_note",
        value="Validate synthetic review.",
        role="validator",
    )
    approved = _transition(
        live_api,
        object_id,
        expected_revision=5,
        action="approve_validated",
        field="approval_note",
        value="Approve synthetic knowledge.",
        role="approver",
    )
    replacement_id = str(uuid4())
    deprecated = _transition(
        live_api,
        object_id,
        expected_revision=6,
        action="deprecate_approved",
        field="deprecation_reason",
        value="Superseded by synthetic replacement.",
        replacement_object_id=replacement_id,
    )
    assert submitted["knowledge"]["lifecycle_state"] == "captured"
    assert reviewed["knowledge"]["lifecycle_state"] == "reviewed"
    assert validated["knowledge"]["lifecycle_state"] == "validated"
    assert approved["knowledge"]["lifecycle_state"] == "approved"
    assert deprecated["knowledge"]["lifecycle_state"] == "deprecated"
    assert deprecated["audit_event"]["replacement_object_id"] == replacement_id

    invalid_transition = live_api.client.post(
        f"/api/v2/knowledge/{object_id}/lifecycle-actions",
        headers=_headers(),
        json={
            "action": "submit_draft",
            "expected_revision": 7,
            "actor": _actor(),
            "submission_note": "Invalid from deprecated.",
        },
    )
    non_draft_update = live_api.client.put(
        f"/api/v2/knowledge/{object_id}",
        headers=_headers(),
        json={
            "expected_revision": 7,
            "replacement": replacement,
            "actor": _actor(),
            "reason_or_note": "Forbidden non-draft update.",
        },
    )
    assert invalid_transition.status_code == 409
    assert invalid_transition.json()["error"]["code"] == "invalid_lifecycle_transition"
    assert non_draft_update.status_code == 409
    assert non_draft_update.json()["error"]["code"] == "knowledge_update_lifecycle_forbidden"
    cross_org = live_api.client.get(
        f"/api/v2/knowledge/{object_id}",
        headers=_headers(organization_id=OTHER_ORGANIZATION_ID),
    )
    assert cross_org.status_code == 404
    assert cross_org.json()["error"]["code"] == "knowledge_object_not_found"

    history = live_api.client.get(
        f"/api/v2/knowledge/{object_id}/audit-history",
        headers=_headers(),
    )
    assert history.status_code == 200
    events = history.json()["events"]
    assert [event["audit_sequence"] for event in events] == list(range(1, 8))
    assert events[-1]["replacement_object_id"] == replacement_id
    assert _storage_snapshot(live_api, object_id)["audit_count"] == 7


def test_complete_twelve_action_http_matrix(live_api: LiveAPIContext) -> None:
    captured = _create(live_api, marker="captured-branch")
    captured_id = captured["knowledge"]["object_id"]
    _transition(
        live_api,
        captured_id,
        expected_revision=1,
        action="submit_draft",
        field="submission_note",
        value="Submit captured branch.",
    )
    corrected = _transition(
        live_api,
        captured_id,
        expected_revision=2,
        action="request_captured_correction",
        field="correction_reason",
        value="Correct captured branch.",
        role="reviewer",
    )
    assert corrected["knowledge"]["lifecycle_state"] == "draft"
    _transition(
        live_api,
        captured_id,
        expected_revision=3,
        action="submit_draft",
        field="submission_note",
        value="Resubmit captured branch.",
    )
    rejected_captured = _transition(
        live_api,
        captured_id,
        expected_revision=4,
        action="reject_captured",
        field="rejection_reason",
        value="Reject captured branch.",
        role="reviewer",
    )
    reopened = _transition(
        live_api,
        captured_id,
        expected_revision=5,
        action="reopen_rejected",
        field="reopen_reason",
        value="Reopen captured branch.",
    )
    assert rejected_captured["knowledge"]["lifecycle_state"] == "rejected"
    assert reopened["knowledge"]["lifecycle_state"] == "draft"

    reviewed = _create(live_api, marker="reviewed-branch")
    reviewed_id = reviewed["knowledge"]["object_id"]
    _transition(
        live_api,
        reviewed_id,
        expected_revision=1,
        action="submit_draft",
        field="submission_note",
        value="Submit reviewed branch.",
    )
    _transition(
        live_api,
        reviewed_id,
        expected_revision=2,
        action="complete_review",
        field="review_note",
        value="Complete reviewed branch.",
        role="reviewer",
    )
    reviewed_correction = _transition(
        live_api,
        reviewed_id,
        expected_revision=3,
        action="request_reviewed_correction",
        field="correction_reason",
        value="Correct reviewed branch.",
    )
    assert reviewed_correction["knowledge"]["lifecycle_state"] == "draft"
    _transition(
        live_api,
        reviewed_id,
        expected_revision=4,
        action="submit_draft",
        field="submission_note",
        value="Resubmit reviewed branch.",
    )
    _transition(
        live_api,
        reviewed_id,
        expected_revision=5,
        action="complete_review",
        field="review_note",
        value="Complete second review.",
        role="reviewer",
    )
    rejected_reviewed = _transition(
        live_api,
        reviewed_id,
        expected_revision=6,
        action="reject_reviewed",
        field="rejection_reason",
        value="Reject reviewed branch.",
    )
    assert rejected_reviewed["knowledge"]["lifecycle_state"] == "rejected"

    validated = _create(live_api, marker="validated-branch")
    validated_id = validated["knowledge"]["object_id"]
    _transition(
        live_api,
        validated_id,
        expected_revision=1,
        action="submit_draft",
        field="submission_note",
        value="Submit validated branch.",
    )
    _transition(
        live_api,
        validated_id,
        expected_revision=2,
        action="complete_review",
        field="review_note",
        value="Review validated branch.",
        role="reviewer",
    )
    _transition(
        live_api,
        validated_id,
        expected_revision=3,
        action="validate_reviewed",
        field="validation_note",
        value="Validate branch.",
        role="validator",
    )
    validated_correction = _transition(
        live_api,
        validated_id,
        expected_revision=4,
        action="request_validated_correction",
        field="correction_reason",
        value="Correct validated branch.",
    )
    assert validated_correction["knowledge"]["lifecycle_state"] == "draft"
    _transition(
        live_api,
        validated_id,
        expected_revision=5,
        action="submit_draft",
        field="submission_note",
        value="Resubmit validated branch.",
    )
    _transition(
        live_api,
        validated_id,
        expected_revision=6,
        action="complete_review",
        field="review_note",
        value="Review corrected branch.",
        role="reviewer",
    )
    _transition(
        live_api,
        validated_id,
        expected_revision=7,
        action="validate_reviewed",
        field="validation_note",
        value="Revalidate branch.",
        role="validator",
    )
    rejected_validated = _transition(
        live_api,
        validated_id,
        expected_revision=8,
        action="reject_validated",
        field="rejection_reason",
        value="Reject validated branch.",
    )
    assert rejected_validated["knowledge"]["lifecycle_state"] == "rejected"

    seen_actions: set[str] = set()
    for object_id in (captured_id, reviewed_id, validated_id):
        history = live_api.client.get(
            f"/api/v2/knowledge/{object_id}/audit-history",
            headers=_headers(),
        )
        assert history.status_code == 200
        seen_actions.update(
            event["lifecycle_action"]
            for event in history.json()["events"]
            if event["lifecycle_action"] is not None
        )
    assert {
        "request_captured_correction",
        "reject_captured",
        "reopen_rejected",
        "request_reviewed_correction",
        "reject_reviewed",
        "request_validated_correction",
        "reject_validated",
    } <= seen_actions
    with live_api.engine.connect() as connection:
        all_actions = set(
            connection.scalars(
                text(
                    "SELECT DISTINCT lifecycle_action FROM knowledge_audit_events_v2 "
                    "WHERE lifecycle_action IS NOT NULL "
                    "AND lifecycle_action <> 'delete_draft'"
                )
            )
        )
    assert all_actions == {
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


def test_delete_retained_history_cross_org_and_atomic_rollback(
    live_api: LiveAPIContext,
) -> None:
    deletable = _create(live_api, marker="delete")
    deleted_id = deletable["knowledge"]["object_id"]
    delete = live_api.client.request(
        "DELETE",
        f"/api/v2/knowledge/{deleted_id}",
        headers=_headers(),
        json={
            "expected_revision": 1,
            "actor": _actor(),
            "reason": "Delete eligible synthetic draft.",
        },
    )
    assert delete.status_code == 200
    assert delete.json()["deleted"] is True
    assert "content" not in delete.text
    assert (
        live_api.client.get(
            f"/api/v2/knowledge/{deleted_id}",
            headers=_headers(),
        ).status_code
        == 404
    )
    retained = live_api.client.get(
        f"/api/v2/knowledge/{deleted_id}/audit-history",
        headers=_headers(),
    )
    assert retained.status_code == 200
    assert [event["event_type"] for event in retained.json()["events"]] == [
        "create",
        "draft_delete",
    ]
    cross_org = live_api.client.get(
        f"/api/v2/knowledge/{deleted_id}/audit-history",
        headers=_headers(organization_id=OTHER_ORGANIZATION_ID),
    )
    assert cross_org.status_code == 404

    rollback = _create(live_api, marker="rollback")
    rollback_id = rollback["knowledge"]["object_id"]
    before = _storage_snapshot(live_api, rollback_id)
    replacement = rollback["knowledge"]["mutable_state"]
    replacement["title"] = "Must roll back"
    replacement["context"] = {
        "references": replacement.pop("context_references"),
    }
    failing_service = KnowledgeAuditService(
        live_api.session_factory,
        participant_factory=FailingAuditParticipant,
    )
    live_api.app.dependency_overrides[get_knowledge_audit_service] = lambda: failing_service
    try:
        failed = live_api.client.put(
            f"/api/v2/knowledge/{rollback_id}",
            headers=_headers(),
            json={
                "expected_revision": 1,
                "replacement": replacement,
                "actor": _actor(),
                "reason_or_note": "Synthetic rollback probe.",
            },
        )
    finally:
        live_api.app.dependency_overrides[get_knowledge_audit_service] = lambda: (
            KnowledgeAuditService(live_api.session_factory)
        )
    assert failed.status_code == 500
    assert failed.json()["error"]["code"] == "internal_server_error"
    assert _storage_snapshot(live_api, rollback_id) == before


def test_cursor_binding_pagination_and_legacy_isolation(live_api: LiveAPIContext) -> None:
    created_ids = {
        _create(live_api, marker=f"page-{index}")["knowledge"]["object_id"] for index in range(3)
    }
    first = live_api.client.get(
        "/api/v2/knowledge?sort=created_at_asc&page_size=1",
        headers=_headers(),
    )
    assert first.status_code == 200
    assert first.json()["has_more"] is True
    cursor = first.json()["next_cursor"]
    second = live_api.client.get(
        f"/api/v2/knowledge?sort=created_at_asc&page_size=2&cursor={cursor}",
        headers=_headers(),
    )
    assert second.status_code == 200
    assert not (
        {first.json()["items"][0]["object_id"]}
        & {item["object_id"] for item in second.json()["items"]}
    )
    cross_org_cursor = live_api.client.get(
        f"/api/v2/knowledge?sort=created_at_asc&page_size=2&cursor={cursor}",
        headers=_headers(organization_id=OTHER_ORGANIZATION_ID),
    )
    assert cross_org_cursor.status_code == 400
    assert cross_org_cursor.json()["error"]["code"] == "knowledge_query_cursor_query_mismatch"

    legacy = live_api.client.post(
        "/knowledge",
        json={
            "title": "Synthetic legacy knowledge",
            "knowledge_type": "observation",
            "content": {"legacy": True},
        },
    )
    assert legacy.status_code == 200, legacy.text
    legacy_id = legacy.json()["object_id"]
    legacy_detail = live_api.client.get(f"/knowledge/{legacy_id}")
    assert legacy_detail.status_code == 200
    v2_list = live_api.client.get(
        "/api/v2/knowledge?page_size=100",
        headers=_headers(),
    )
    assert v2_list.status_code == 200
    v2_ids = {item["object_id"] for item in v2_list.json()["items"]}
    assert legacy_id not in v2_ids
    assert created_ids <= v2_ids
