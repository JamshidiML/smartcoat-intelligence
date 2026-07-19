import os
import re
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, delete, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from smartcoat.api.dependencies.database import get_db_session
from smartcoat.api.main import app
from smartcoat.domain.decision_objects import DecisionObject, DecisionType
from smartcoat.domain.events import EnterpriseEvent, EventType
from smartcoat.domain.knowledge_objects import KnowledgeObject, KnowledgeObjectType
from smartcoat.storage.database.base import Base
from smartcoat.storage.database.models import (
    DecisionObjectRecord,
    EnterpriseEventRecord,
    KnowledgeObjectRecord,
)

TEST_SCHEMA_PATTERN = re.compile(r"^smartcoat_test_[a-z0-9_]+$")
LIVE_POSTGRES_OPT_IN = "true"


@dataclass
class PostgresTestContext:
    client: TestClient
    created_ids: dict[type, list[str]]
    session_factory: sessionmaker[Session]


def _require_live_postgres_opt_in(value: str | None) -> None:
    if value != LIVE_POSTGRES_OPT_IN:
        raise RuntimeError(
            "Refusing live PostgreSQL integration: set "
            "SMARTCOAT_RUN_LIVE_POSTGRES_TESTS=true explicitly."
        )


def _require_test_target(database_url: str, schema_name: str | None) -> str:
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise RuntimeError("PostgreSQL integration tests require a PostgreSQL URL.")

    if schema_name is None:
        raise RuntimeError("Refusing integration execution: SMARTCOAT_TEST_SCHEMA is mandatory.")
    if not TEST_SCHEMA_PATTERN.fullmatch(schema_name):
        raise RuntimeError(
            "SMARTCOAT_TEST_SCHEMA must start with 'smartcoat_test_' and contain only "
            "lowercase letters, digits, and underscores."
        )
    return schema_name


def _drop_schema_and_assert_absent(admin_engine: Engine, schema_name: str) -> None:
    with admin_engine.begin() as connection:
        connection.execute(text(f'DROP SCHEMA "{schema_name}" CASCADE'))
    with admin_engine.connect() as connection:
        remaining = connection.scalar(
            text("SELECT COUNT(*) FROM pg_namespace WHERE nspname = :schema_name"),
            {"schema_name": schema_name},
        )
    assert remaining == 0


def _cleanup_created_objects(
    session_factory: sessionmaker[Session],
    created_ids: dict[type, list[str]],
) -> None:
    with session_factory() as session:
        for record_type, object_ids in created_ids.items():
            if object_ids:
                session.execute(delete(record_type).where(record_type.object_id.in_(object_ids)))
        session.commit()


def _register_created_object(
    context: PostgresTestContext,
    record_type: type,
    response: Any,
) -> dict[str, Any]:
    assert response.status_code == 200
    payload: dict[str, Any] = response.json()
    context.created_ids[record_type].append(payload["object_id"])
    return payload


def _listed_object(client: TestClient, path: str, object_id: str) -> dict[str, Any]:
    response = client.get(f"{path}?limit=500")
    assert response.status_code == 200
    matches = [item for item in response.json() if item["object_id"] == object_id]
    assert len(matches) == 1
    return matches[0]


@pytest.fixture()
def live_postgres_target() -> tuple[str, str]:
    database_url = os.getenv("SMARTCOAT_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set SMARTCOAT_TEST_DATABASE_URL to run PostgreSQL integration tests.")
    _require_live_postgres_opt_in(os.getenv("SMARTCOAT_RUN_LIVE_POSTGRES_TESTS"))
    schema_name = _require_test_target(database_url, os.getenv("SMARTCOAT_TEST_SCHEMA"))
    return database_url, schema_name


@pytest.fixture()
def postgres_context(
    live_postgres_target: tuple[str, str],
) -> Generator[PostgresTestContext, None, None]:
    database_url, schema_name = live_postgres_target
    admin_engine = create_engine(database_url, pool_pre_ping=True)
    test_engine: Engine = admin_engine
    schema_created = False
    session_factory: sessionmaker[Session] | None = None
    original_overrides = app.dependency_overrides.copy()
    created_ids: dict[type, list[str]] = {
        KnowledgeObjectRecord: [],
        DecisionObjectRecord: [],
        EnterpriseEventRecord: [],
    }

    try:
        with admin_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
        schema_created = True
        test_engine = create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={"options": f"-csearch_path={schema_name}"},
        )

        # This checks ORM/API compatibility only; it is not migration validation.
        Base.metadata.create_all(bind=test_engine)
        session_factory = sessionmaker(
            bind=test_engine,
            autoflush=False,
            autocommit=False,
        )

        def override_db_session() -> Generator[Session, None, None]:
            session = session_factory()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db_session] = override_db_session
        yield PostgresTestContext(
            client=TestClient(app),
            created_ids=created_ids,
            session_factory=session_factory,
        )
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
        try:
            if session_factory is not None:
                _cleanup_created_objects(session_factory, created_ids)
        finally:
            try:
                if test_engine is not admin_engine:
                    test_engine.dispose()
                if schema_created:
                    _drop_schema_and_assert_absent(admin_engine, schema_name)
            finally:
                admin_engine.dispose()


def test_live_postgres_requires_exact_opt_in() -> None:
    with pytest.raises(RuntimeError, match="SMARTCOAT_RUN_LIVE_POSTGRES_TESTS=true"):
        _require_live_postgres_opt_in(None)
    with pytest.raises(RuntimeError, match="SMARTCOAT_RUN_LIVE_POSTGRES_TESTS=true"):
        _require_live_postgres_opt_in("TRUE")


def test_postgres_target_requires_isolated_schema() -> None:
    with pytest.raises(RuntimeError, match="SMARTCOAT_TEST_SCHEMA is mandatory"):
        _require_test_target("postgresql+psycopg://localhost/smartcoat", None)
    with pytest.raises(RuntimeError, match="PostgreSQL URL"):
        _require_test_target("sqlite:///smartcoat.db", "smartcoat_test_t04")
    with pytest.raises(RuntimeError, match="lowercase letters"):
        _require_test_target(
            "postgresql+psycopg://localhost/smartcoat",
            "smartcoat_test_T04",
        )


def test_schema_drop_helper_removes_temporary_schema(
    live_postgres_target: tuple[str, str],
) -> None:
    database_url, base_schema_name = live_postgres_target
    schema_name = f"{base_schema_name[:45]}_teardown_probe"
    _require_test_target(database_url, schema_name)
    admin_engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with admin_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
        _drop_schema_and_assert_absent(admin_engine, schema_name)
    finally:
        admin_engine.dispose()


def test_http_to_postgres_round_trip_for_current_object_types(
    postgres_context: PostgresTestContext,
) -> None:
    knowledge_payload = KnowledgeObject(
        title="Synthetic persisted knowledge",
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        confidence=0.8,
    ).model_dump(mode="json")
    decision_payload = DecisionObject(
        title="Synthetic persisted decision",
        decision_type=DecisionType.ENGINEERING,
        confidence=0.7,
    ).model_dump(mode="json")
    event_payload = EnterpriseEvent(
        title="Synthetic persisted event",
        event_type=EventType.KNOWLEDGE_CREATED,
        actor="integration_test",
    ).model_dump(mode="json")

    knowledge = _register_created_object(
        postgres_context,
        KnowledgeObjectRecord,
        postgres_context.client.post("/knowledge", json=knowledge_payload),
    )
    decision = _register_created_object(
        postgres_context,
        DecisionObjectRecord,
        postgres_context.client.post("/decisions", json=decision_payload),
    )
    event = _register_created_object(
        postgres_context,
        EnterpriseEventRecord,
        postgres_context.client.post("/events", json=event_payload),
    )

    knowledge_get = postgres_context.client.get(f"/knowledge/{knowledge['object_id']}")
    decision_get = postgres_context.client.get(f"/decisions/{decision['object_id']}")
    event_get = postgres_context.client.get(f"/events/{event['object_id']}")

    assert knowledge_get.status_code == 200
    assert decision_get.status_code == 200
    assert event_get.status_code == 200
    assert knowledge_get.json()["title"] == "Synthetic persisted knowledge"
    assert decision_get.json()["title"] == "Synthetic persisted decision"
    assert event_get.json()["title"] == "Synthetic persisted event"

    listed_knowledge = _listed_object(
        postgres_context.client,
        "/knowledge",
        knowledge["object_id"],
    )
    listed_decision = _listed_object(
        postgres_context.client,
        "/decisions",
        decision["object_id"],
    )
    listed_event = _listed_object(
        postgres_context.client,
        "/events",
        event["object_id"],
    )

    assert listed_knowledge["title"] == "Synthetic persisted knowledge"
    assert listed_knowledge["knowledge_type"] == KnowledgeObjectType.OBSERVATION.value
    assert listed_decision["title"] == "Synthetic persisted decision"
    assert listed_decision["decision_type"] == DecisionType.ENGINEERING.value
    assert listed_event["title"] == "Synthetic persisted event"
    assert listed_event["event_type"] == EventType.KNOWLEDGE_CREATED.value
    assert listed_event["actor"] == "integration_test"


def test_cleanup_remains_effective_after_intermediate_failure(
    postgres_context: PostgresTestContext,
) -> None:
    payload = KnowledgeObject(
        title="Synthetic partial failure cleanup",
        knowledge_type=KnowledgeObjectType.LESSON_LEARNED,
    ).model_dump(mode="json")
    created = _register_created_object(
        postgres_context,
        KnowledgeObjectRecord,
        postgres_context.client.post("/knowledge", json=payload),
    )

    with pytest.raises(RuntimeError, match="synthetic intermediate failure"):
        try:
            raise RuntimeError("synthetic intermediate failure")
        finally:
            _cleanup_created_objects(
                postgres_context.session_factory,
                postgres_context.created_ids,
            )

    with postgres_context.session_factory() as session:
        assert session.get(KnowledgeObjectRecord, created["object_id"]) is None
