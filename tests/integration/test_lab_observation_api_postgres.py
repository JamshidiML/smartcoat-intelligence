from __future__ import annotations

import json
import os
import re
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from alembic import command
from smartcoat.api.dependencies.database import get_db_session
from smartcoat.api.main import app
from smartcoat.api.routes.lab_observations import (
    get_lab_observation_audit_service,
)
from smartcoat.domain.evidence_provenance import (
    CreationMethod,
    EvidenceCompleteness,
    EvidenceReference,
    EvidenceType,
    ProvenanceCompleteness,
    ProvenanceV2,
)
from smartcoat.services.knowledge_audit_service import KnowledgeAuditService
from smartcoat.storage.database.knowledge_audit_models import (
    KnowledgeAuditEventRecord,
)
from smartcoat.storage.database.knowledge_v2_models import (
    KnowledgeObjectV2ContextRecord,
    KnowledgeObjectV2EvidenceRecord,
    KnowledgeObjectV2ProvenanceRecord,
    KnowledgeObjectV2Record,
    KnowledgeObjectV2TagRecord,
)

LIVE_POSTGRES_OPT_IN = "true"
TEST_SCHEMA_PATTERN = re.compile(r"^smartcoat_test_lab_observation_[a-z0-9]+$")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PAYLOAD = {
    "project_id": "LAB-2026-001",
    "project_name": "Synthetic High-Temperature Coating Trial",
    "title": "Coating remained flexible after heat exposure",
    "observation": ("Synthetic sample remained flexible after the defined laboratory heat cycle."),
    "source_reference": "lab-notebook://synthetic/LAB-2026-001/observation-001",
    "observed_at": "2026-07-28T10:00:00+00:00",
    "actor_id": "synthetic-lab-engineer",
    "actor_role": "lab_engineer",
}
ORGANIZATION_ID = "synthetic-lab-org"


def _require_live_postgres(database_url: str | None, opt_in: str | None) -> str:
    if opt_in != LIVE_POSTGRES_OPT_IN:
        raise RuntimeError(
            "Refusing lab-observation live PostgreSQL execution without explicit "
            "SMARTCOAT_RUN_LIVE_POSTGRES_TESTS=true."
        )
    if not database_url:
        raise RuntimeError("SMARTCOAT_TEST_DATABASE_URL is required.")
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise RuntimeError("Lab-observation live tests require PostgreSQL.")
    if url.host not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("Lab-observation live tests accept only a localhost PostgreSQL target.")
    if not (url.database or "").startswith("smartcoat_test"):
        raise RuntimeError(
            "Lab-observation live tests require a database beginning with smartcoat_test."
        )
    return database_url


def _schema_name() -> str:
    return f"smartcoat_test_lab_observation_{uuid4().hex[:12]}"


def _assert_schema_name(schema_name: str) -> None:
    if TEST_SCHEMA_PATTERN.fullmatch(schema_name) is None:
        raise RuntimeError("unsafe lab-observation test schema name")


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


def _run_upgrade(database_url: str, schema_name: str) -> None:
    with _alembic_schema(schema_name):
        command.upgrade(_alembic_config(database_url), "head")


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
def isolated_schema(live_database_url: str) -> Generator[str, None, None]:
    schema_name = _schema_name()
    admin_engine = create_engine(live_database_url, poolclass=NullPool)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
    try:
        yield schema_name
    finally:
        _drop_schema_and_assert_absent(admin_engine, schema_name)
        admin_engine.dispose()


@pytest.fixture()
def migrated_store(
    live_database_url: str,
    isolated_schema: str,
) -> Generator[tuple[Engine, sessionmaker[Session]], None, None]:
    _run_upgrade(live_database_url, isolated_schema)
    engine = _schema_engine(live_database_url, isolated_schema)
    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    try:
        yield engine, factory
    finally:
        engine.dispose()


@pytest.fixture()
def live_client(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    _, factory = migrated_store
    original_overrides = app.dependency_overrides.copy()

    def override_db_session() -> Generator[Session, None, None]:
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_lab_observation_audit_service] = lambda: KnowledgeAuditService(
        factory
    )
    try:
        yield TestClient(app), factory
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)


def test_live_postgres_requires_exact_opt_in() -> None:
    database_url = "postgresql+psycopg://smartcoat:smartcoat@localhost:5432/smartcoat_test"
    for opt_in in (None, "", "TRUE", "True", "1", "yes", "false"):
        with pytest.raises(RuntimeError):
            _require_live_postgres(database_url, opt_in)


def test_lab_observation_http_postgres_round_trip(
    live_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, factory = live_client
    headers = {"X-SmartCoat-Organization-ID": ORGANIZATION_ID}

    post_response = client.post(
        "/api/v2/lab-observations",
        json=PAYLOAD,
        headers=headers,
    )

    assert post_response.status_code == 201, post_response.text
    created = post_response.json()
    view = created["observation"]
    assert view["lifecycle_state"] == "draft"
    assert view["revision"] == 1
    for field_name in (
        "project_id",
        "project_name",
        "title",
        "observation",
        "source_reference",
        "observed_at",
    ):
        assert view[field_name] == PAYLOAD[field_name].replace("+00:00", "Z")
    assert view["evidence_id"]
    assert created["audit_event_id"]
    assert created["audit_sequence"] > 0

    object_id = UUID(view["object_id"])
    get_response = client.get(
        f"/api/v2/lab-observations/{object_id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json() == view
    wrong_org = client.get(
        f"/api/v2/lab-observations/{object_id}",
        headers={"X-SmartCoat-Organization-ID": "another-synthetic-org"},
    )
    assert wrong_org.status_code == 404

    with factory() as session:
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
        assert root.confidentiality == "internal"
        assert json.loads(root.content_json) == {"observation": PAYLOAD["observation"]}
        original_updated_at = root.updated_at

        tags = session.scalars(
            select(KnowledgeObjectV2TagRecord).where(
                KnowledgeObjectV2TagRecord.organization_id == ORGANIZATION_ID,
                KnowledgeObjectV2TagRecord.object_id == object_id,
            )
        ).all()
        assert [tag.tag for tag in tags] == ["lab-observation"]

        contexts = session.scalars(
            select(KnowledgeObjectV2ContextRecord).where(
                KnowledgeObjectV2ContextRecord.organization_id == ORGANIZATION_ID,
                KnowledgeObjectV2ContextRecord.object_id == object_id,
            )
        ).all()
        assert len(contexts) == 1
        context = contexts[0]
        assert context.context_type == "project"
        assert context.reference_id == "LAB-2026-001"
        assert context.id_kind == "external"
        assert context.source_system == "smartcoat-lab"
        assert context.relationship_role == "project"

        evidence_rows = session.scalars(
            select(KnowledgeObjectV2EvidenceRecord).where(
                KnowledgeObjectV2EvidenceRecord.organization_id == ORGANIZATION_ID,
                KnowledgeObjectV2EvidenceRecord.object_id == object_id,
            )
        ).all()
        assert len(evidence_rows) == 1
        evidence = EvidenceReference.model_validate_json(evidence_rows[0].canonical_metadata_json)
        assert evidence.evidence_type is EvidenceType.OBSERVATION
        assert evidence.completeness is EvidenceCompleteness.COMPLETE
        assert evidence.source_reference == PAYLOAD["source_reference"]
        assert evidence.captured_by == PAYLOAD["actor_id"]

        provenance_rows = session.scalars(
            select(KnowledgeObjectV2ProvenanceRecord).where(
                KnowledgeObjectV2ProvenanceRecord.organization_id == ORGANIZATION_ID,
                KnowledgeObjectV2ProvenanceRecord.object_id == object_id,
            )
        ).all()
        assert len(provenance_rows) == 1
        provenance = ProvenanceV2.model_validate_json(provenance_rows[0].canonical_provenance_json)
        assert provenance.completeness is ProvenanceCompleteness.COMPLETE
        assert provenance.creation_method is CreationMethod.MANUAL
        assert provenance.source_system == "smartcoat-lab"

        audit_rows = session.scalars(
            select(KnowledgeAuditEventRecord).where(
                KnowledgeAuditEventRecord.organization_id == ORGANIZATION_ID,
                KnowledgeAuditEventRecord.object_id == object_id,
            )
        ).all()
        assert len(audit_rows) == 1
        audit = audit_rows[0]
        assert audit.event_type == "create"
        assert audit.resulting_lifecycle == "draft"
        assert audit.resulting_revision == 1
        assert audit.reason_or_note == "Manual lab observation capture"

    with factory() as session:
        assert (
            session.scalar(
                select(func.count())
                .select_from(KnowledgeAuditEventRecord)
                .where(
                    KnowledgeAuditEventRecord.organization_id == ORGANIZATION_ID,
                    KnowledgeAuditEventRecord.object_id == object_id,
                )
            )
            == 1
        )
        unchanged = session.scalar(
            select(KnowledgeObjectV2Record).where(
                KnowledgeObjectV2Record.organization_id == ORGANIZATION_ID,
                KnowledgeObjectV2Record.object_id == object_id,
            )
        )
        assert unchanged is not None
        assert unchanged.revision == 1
        assert unchanged.updated_at == original_updated_at


def test_randomized_schema_cleanup_leaves_zero_residual_schemas(
    live_database_url: str,
) -> None:
    schema_name = _schema_name()
    engine = create_engine(live_database_url, poolclass=NullPool)
    try:
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
        _drop_schema_and_assert_absent(engine, schema_name)
        with engine.connect() as connection:
            assert (
                connection.scalar(
                    text("SELECT count(*) FROM pg_namespace WHERE nspname = :schema_name"),
                    {"schema_name": schema_name},
                )
                == 0
            )
    finally:
        engine.dispose()
