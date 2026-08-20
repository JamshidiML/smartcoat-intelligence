from __future__ import annotations

import json
import os
import re
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from alembic import command
from smartcoat.api.dependencies.database import get_db_session
from smartcoat.api.routes.lab_project_captures import (
    CREATE_REASON,
    LAB_PROJECT_CAPTURE_SOURCE_SYSTEM,
    LAB_PROJECT_CAPTURE_TAG,
    get_lab_project_capture_audit_service,
    router,
)
from smartcoat.domain.evidence_provenance import (
    CreationMethod,
    EvidenceReference,
    EvidenceType,
    IntegrityAlgorithm,
    ProvenanceV2,
)
from smartcoat.services.knowledge_audit_service import KnowledgeAuditService
from smartcoat.storage.database.knowledge_audit_models import KnowledgeAuditEventRecord
from smartcoat.storage.database.knowledge_v2_models import (
    KnowledgeObjectV2ContextRecord,
    KnowledgeObjectV2EvidenceRecord,
    KnowledgeObjectV2ProvenanceRecord,
    KnowledgeObjectV2Record,
    KnowledgeObjectV2TagRecord,
)
from smartcoat.storage.repositories.knowledge_audit_repository import (
    KnowledgeAuditParticipant,
)

LIVE_POSTGRES_OPT_IN = "true"
TEST_SCHEMA_PATTERN = re.compile(r"^smartcoat_test_lab_project_capture_[a-z0-9]+$")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ORGANIZATION_ID = "synthetic-project-org"


def _payload(*, suffix: str = "001") -> dict[str, Any]:
    return {
        "capture_session_id": str(uuid4()),
        "source_kind": "excel",
        "source_language": "en",
        "extraction_model": "deterministic-import-mapper",
        "extraction_started_at": "2026-08-06T08:05:00Z",
        "extraction_completed_at": "2026-08-06T08:06:00Z",
        "project": {
            "project_id": f"P-PG-{suffix}",
            "project_name": f"Synthetic PostgreSQL project {suffix}",
            "customer_company": "Example Customer",
            "request_summary": "Validate a synthetic PostgreSQL capture.",
            "target_application": "Generalized laboratory validation",
            "success_criteria": ["Persist through the governed synthetic test path."],
            "project_status": "in_progress",
        },
        "substrate": {
            "substrate_id": "SUB-PG-01",
            "substrate_name": "Synthetic substrate",
            "reason_selected": "Selected only for a synthetic integration test.",
        },
        "approaches": [
            {
                "approach_id": "C-A-001",
                "outcome": "successful",
                "price_optimization_status": "assessed",
                "production_feasibility_status": "assessed",
                "reuse_potential": "Generalized reuse potential.",
            }
        ],
        "tests": [
            {
                "approach_id": "C-A-001",
                "test_name": "Synthetic persistence test",
                "method": "PostgreSQL round trip",
                "acceptance_criteria": "Canonical rows and audit event persist atomically.",
                "text_result": "Passed",
                "outcome": "passed",
            }
        ],
        "evidence": [
            {
                "evidence_id": f"EV-PG-{suffix}",
                "evidence_type": "excel",
                "filename": f"synthetic-{suffix}.xlsx",
                "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "source_reference": f"asset://synthetic/EV-PG-{suffix}",
                "sha256": "b" * 64,
                "captured_at": "2026-08-06T08:00:00Z",
                "description": "Synthetic workbook evidence.",
            }
        ],
        "current_next_action": "Review the synthetic draft.",
        "next_action_due_at": "2026-08-09T09:00:00Z",
        "unresolved_questions": ["Who owns the synthetic follow-up?"],
        "human_confirmed": True,
        "human_confirmed_by": "synthetic-postgres-reviewer",
        "human_confirmed_at": "2026-08-06T09:00:00Z",
    }


def _voice_payload() -> dict[str, Any]:
    payload = _payload(suffix="VOICE")
    payload.update(
        {
            "source_kind": "voice",
            "transcript": "Immutable synthetic PostgreSQL voice transcript.",
            "evidence": [
                {
                    "evidence_id": "EV-PG-VOICE-AUDIO",
                    "evidence_type": "audio",
                    "filename": "synthetic-voice.webm",
                    "media_type": "audio/webm",
                    "source_reference": "asset://synthetic/EV-PG-VOICE-AUDIO",
                    "sha256": "c" * 64,
                    "captured_at": "2026-08-06T08:00:00Z",
                    "description": "Synthetic audio evidence.",
                },
                {
                    "evidence_id": "EV-PG-VOICE-TRANSCRIPT",
                    "evidence_type": "transcript",
                    "filename": "capture-transcript.txt",
                    "media_type": "text/plain",
                    "source_reference": "asset://synthetic/EV-PG-VOICE-TRANSCRIPT",
                    "sha256": "d" * 64,
                    "captured_at": "2026-08-06T08:01:00Z",
                    "description": "Synthetic transcript evidence.",
                },
            ],
        }
    )
    return payload


def _require_live_postgres(database_url: str | None, opt_in: str | None) -> str:
    if opt_in != LIVE_POSTGRES_OPT_IN:
        raise RuntimeError(
            "Refusing lab-project-capture PostgreSQL execution without exact opt-in."
        )
    if not database_url:
        raise RuntimeError("SMARTCOAT_TEST_DATABASE_URL is required.")
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise RuntimeError("Lab-project-capture live tests require PostgreSQL.")
    if url.host not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("Live tests accept only a localhost PostgreSQL target.")
    if not (url.database or "").startswith("smartcoat_test"):
        raise RuntimeError("Live tests require a database beginning with smartcoat_test.")
    return database_url


def _schema_name() -> str:
    return f"smartcoat_test_lab_project_capture_{uuid4().hex[:12]}"


def _assert_schema_name(schema_name: str) -> None:
    if TEST_SCHEMA_PATTERN.fullmatch(schema_name) is None:
        raise RuntimeError("unsafe lab-project-capture test schema name")


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


def _alembic_config(database_url: str) -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


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
        pytest.skip("Set SMARTCOAT_TEST_DATABASE_URL for live PostgreSQL tests.")
    return _require_live_postgres(
        database_url,
        os.getenv("SMARTCOAT_RUN_LIVE_POSTGRES_TESTS"),
    )


@pytest.fixture()
def migrated_store(
    live_database_url: str,
) -> Generator[sessionmaker[Session], None, None]:
    schema_name = _schema_name()
    admin_engine = create_engine(live_database_url, poolclass=NullPool)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
    try:
        with _alembic_schema(schema_name):
            command.upgrade(_alembic_config(live_database_url), "head")
        engine = _schema_engine(live_database_url, schema_name)
        factory = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
        try:
            yield factory
        finally:
            engine.dispose()
    finally:
        _drop_schema_and_assert_absent(admin_engine, schema_name)
        admin_engine.dispose()


def _application(factory: sessionmaker[Session]) -> FastAPI:
    application = FastAPI()
    application.include_router(router)

    def override_db_session() -> Generator[Session, None, None]:
        session = factory()
        try:
            yield session
        finally:
            session.close()

    application.dependency_overrides[get_db_session] = override_db_session
    application.dependency_overrides[get_lab_project_capture_audit_service] = lambda: (
        KnowledgeAuditService(factory)
    )
    return application


def test_live_postgres_requires_exact_opt_in() -> None:
    database_url = "postgresql+psycopg://smartcoat:smartcoat@localhost:5432/smartcoat_test"
    for opt_in in (None, "", "TRUE", "True", "1", "yes", "false"):
        with pytest.raises(RuntimeError):
            _require_live_postgres(database_url, opt_in)


def test_postgres_round_trip_evidence_provenance_audit_and_reads(
    migrated_store: sessionmaker[Session],
) -> None:
    application = _application(migrated_store)
    client = TestClient(application)
    headers = {"X-SmartCoat-Organization-ID": ORGANIZATION_ID}

    response = client.post(
        "/api/v2/lab-project-captures",
        json=_payload(),
        headers=headers,
    )

    assert response.status_code == 201, response.text
    created = response.json()
    capture = created["capture"]
    object_id = UUID(capture["object_id"])
    assert capture["project_id"] == "P-PG-001"
    assert capture["current_status"] == "in_progress"
    assert capture["lifecycle"] == "draft"
    assert capture["revision"] == 1
    assert capture["observed_at"] == "2026-08-06T08:00:00Z"
    assert capture["captured_at"] == "2026-08-06T09:00:00Z"

    with migrated_store() as session:
        root = session.scalar(
            select(KnowledgeObjectV2Record).where(
                KnowledgeObjectV2Record.organization_id == ORGANIZATION_ID,
                KnowledgeObjectV2Record.object_id == object_id,
            )
        )
        assert root is not None
        assert root.contract_version == "2"
        assert root.lifecycle_state == "draft"
        assert root.revision == 1
        assert root.knowledge_type == "observation"
        assert root.confidentiality == "confidential"
        content = json.loads(root.content_json)
        assert content["project"][0]["project_id"] == "P-PG-001"
        assert content["quality_summary"][0]["human_confirmed"] is True

        tags = session.scalars(
            select(KnowledgeObjectV2TagRecord).where(
                KnowledgeObjectV2TagRecord.organization_id == ORGANIZATION_ID,
                KnowledgeObjectV2TagRecord.object_id == object_id,
            )
        ).all()
        assert [tag.tag for tag in tags] == [LAB_PROJECT_CAPTURE_TAG]

        contexts = session.scalars(
            select(KnowledgeObjectV2ContextRecord).where(
                KnowledgeObjectV2ContextRecord.organization_id == ORGANIZATION_ID,
                KnowledgeObjectV2ContextRecord.object_id == object_id,
            )
        ).all()
        assert len(contexts) == 1
        assert contexts[0].context_type == "project"
        assert contexts[0].reference_id == "P-PG-001"
        assert contexts[0].source_system == LAB_PROJECT_CAPTURE_SOURCE_SYSTEM

        evidence_rows = session.scalars(
            select(KnowledgeObjectV2EvidenceRecord).where(
                KnowledgeObjectV2EvidenceRecord.organization_id == ORGANIZATION_ID,
                KnowledgeObjectV2EvidenceRecord.object_id == object_id,
            )
        ).all()
        assert len(evidence_rows) == 1
        evidence = EvidenceReference.model_validate_json(evidence_rows[0].canonical_metadata_json)
        assert evidence.evidence_type is EvidenceType.DATASET
        assert evidence.source_reference == "asset://synthetic/EV-PG-001"
        assert evidence.integrity is not None
        assert evidence.integrity.algorithm is IntegrityAlgorithm.SHA256
        assert evidence.integrity.value == "b" * 64

        provenance_rows = session.scalars(
            select(KnowledgeObjectV2ProvenanceRecord).where(
                KnowledgeObjectV2ProvenanceRecord.organization_id == ORGANIZATION_ID,
                KnowledgeObjectV2ProvenanceRecord.object_id == object_id,
            )
        ).all()
        assert len(provenance_rows) == 1
        provenance = ProvenanceV2.model_validate_json(provenance_rows[0].canonical_provenance_json)
        assert provenance.source_system == LAB_PROJECT_CAPTURE_SOURCE_SYSTEM
        assert provenance.creation_method is CreationMethod.IMPORTED
        assert [item.transformation_type for item in provenance.transformation_history] == [
            "local_structured_extraction",
            "human_confirmation",
        ]

        audit_rows = session.scalars(
            select(KnowledgeAuditEventRecord).where(
                KnowledgeAuditEventRecord.organization_id == ORGANIZATION_ID,
                KnowledgeAuditEventRecord.object_id == object_id,
            )
        ).all()
        assert len(audit_rows) == 1
        audit = audit_rows[0]
        assert str(audit.event_id) == created["audit_event_id"]
        assert audit.event_type == "create"
        assert audit.resulting_lifecycle == "draft"
        assert audit.resulting_revision == 1
        assert audit.reason_or_note == CREATE_REASON

    list_response = client.get("/api/v2/lab-project-captures", headers=headers)
    detail_response = client.get(
        f"/api/v2/lab-project-captures/{object_id}",
        headers=headers,
    )
    wrong_org = client.get(
        f"/api/v2/lab-project-captures/{object_id}",
        headers={"X-SmartCoat-Organization-ID": "another-synthetic-org"},
    )
    assert list_response.status_code == 200
    assert list_response.json()["items"] == [capture]
    assert detail_response.status_code == 200
    assert detail_response.json() == capture
    assert wrong_org.status_code == 404


def test_postgres_voice_capture_persists_audio_transcript_provenance_and_audit(
    migrated_store: sessionmaker[Session],
) -> None:
    application = _application(migrated_store)
    response = TestClient(application).post(
        "/api/v2/lab-project-captures",
        json=_voice_payload(),
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )

    assert response.status_code == 201, response.text
    object_id = UUID(response.json()["capture"]["object_id"])
    with migrated_store() as session:
        evidence_rows = session.scalars(
            select(KnowledgeObjectV2EvidenceRecord).where(
                KnowledgeObjectV2EvidenceRecord.organization_id == ORGANIZATION_ID,
                KnowledgeObjectV2EvidenceRecord.object_id == object_id,
            )
        ).all()
        provenance_row = session.scalar(
            select(KnowledgeObjectV2ProvenanceRecord).where(
                KnowledgeObjectV2ProvenanceRecord.organization_id == ORGANIZATION_ID,
                KnowledgeObjectV2ProvenanceRecord.object_id == object_id,
            )
        )
        audit_count = session.scalar(
            select(func.count())
            .select_from(KnowledgeAuditEventRecord)
            .where(
                KnowledgeAuditEventRecord.organization_id == ORGANIZATION_ID,
                KnowledgeAuditEventRecord.object_id == object_id,
            )
        )

    assert len(evidence_rows) == 2
    evidence_types = {
        EvidenceReference.model_validate_json(row.canonical_metadata_json).evidence_type
        for row in evidence_rows
    }
    assert evidence_types == {EvidenceType.OBSERVATION, EvidenceType.DOCUMENT}
    assert provenance_row is not None
    provenance = ProvenanceV2.model_validate_json(provenance_row.canonical_provenance_json)
    assert provenance.creation_method is CreationMethod.IMPORTED
    assert [item.transformation_type for item in provenance.transformation_history] == [
        "local_structured_extraction",
        "human_confirmation",
    ]
    assert audit_count == 1


def test_postgres_rejects_cross_organization_local_evidence_before_persistence(
    migrated_store: sessionmaker[Session],
) -> None:
    application = _application(migrated_store)
    client = TestClient(application)
    digest = "e" * 64

    with migrated_store() as session:
        knowledge_before = session.scalar(select(func.count()).select_from(KnowledgeObjectV2Record))
        audit_before = session.scalar(select(func.count()).select_from(KnowledgeAuditEventRecord))

    cross_organization = _payload(suffix="CROSS-ORG")
    cross_organization["evidence"][0].update(
        {
            "source_reference": f"smartcoat-asset://synthetic-org-a/{digest}",
            "sha256": digest,
        }
    )
    rejected = client.post(
        "/api/v2/lab-project-captures",
        json=cross_organization,
        headers={"X-SmartCoat-Organization-ID": "synthetic-org-b"},
    )

    assert rejected.status_code == 422
    assert rejected.json()["detail"]["code"] == "evidence_organization_mismatch"
    with migrated_store() as session:
        knowledge_after_rejection = session.scalar(
            select(func.count()).select_from(KnowledgeObjectV2Record)
        )
        audit_after_rejection = session.scalar(
            select(func.count()).select_from(KnowledgeAuditEventRecord)
        )
    assert knowledge_after_rejection == knowledge_before
    assert audit_after_rejection == audit_before

    same_organization = _payload(suffix="SAME-ORG")
    same_organization["evidence"][0].update(
        {
            "source_reference": f"smartcoat-asset://synthetic-org-a/{digest}",
            "sha256": digest,
        }
    )
    created = client.post(
        "/api/v2/lab-project-captures",
        json=same_organization,
        headers={"X-SmartCoat-Organization-ID": "synthetic-org-a"},
    )

    assert created.status_code == 201, created.text
    with migrated_store() as session:
        knowledge_after_create = session.scalar(
            select(func.count()).select_from(KnowledgeObjectV2Record)
        )
        audit_after_create = session.scalar(
            select(func.count()).select_from(KnowledgeAuditEventRecord)
        )
    assert knowledge_after_create == knowledge_before + 1
    assert audit_after_create == audit_before + 1


class FailingAuditParticipant(KnowledgeAuditParticipant):
    def flush(self, session: Session) -> None:
        raise RuntimeError("synthetic audit persistence failure")


def test_postgres_rolls_back_knowledge_when_audit_fails(
    migrated_store: sessionmaker[Session],
) -> None:
    application = _application(migrated_store)
    application.dependency_overrides[get_lab_project_capture_audit_service] = lambda: (
        KnowledgeAuditService(
            migrated_store,
            participant_factory=FailingAuditParticipant,
        )
    )

    response = TestClient(application, raise_server_exceptions=False).post(
        "/api/v2/lab-project-captures",
        json=_payload(suffix="ROLLBACK"),
        headers={"X-SmartCoat-Organization-ID": ORGANIZATION_ID},
    )

    assert response.status_code == 500
    with migrated_store() as session:
        knowledge_count = session.scalar(
            select(func.count())
            .select_from(KnowledgeObjectV2Record)
            .where(KnowledgeObjectV2Record.organization_id == ORGANIZATION_ID)
        )
        audit_count = session.scalar(
            select(func.count())
            .select_from(KnowledgeAuditEventRecord)
            .where(KnowledgeAuditEventRecord.organization_id == ORGANIZATION_ID)
        )
    assert knowledge_count == 0
    assert audit_count == 0
