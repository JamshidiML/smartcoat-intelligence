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


@dataclass
class PostgresTestContext:
    client: TestClient
    created_ids: dict[type, list[str]]
    session_factory: sessionmaker[Session]


def _require_test_target(database_url: str, schema_name: str | None) -> str | None:
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise RuntimeError("PostgreSQL integration tests require a PostgreSQL URL.")

    database_name = (url.database or "").lower()
    if schema_name is not None:
        normalized_schema = schema_name.lower()
        if not TEST_SCHEMA_PATTERN.fullmatch(normalized_schema):
            raise RuntimeError(
                "SMARTCOAT_TEST_SCHEMA must start with 'smartcoat_test_' and contain only "
                "lowercase letters, digits, and underscores."
            )
        return normalized_schema

    if not database_name.endswith("_test"):
        raise RuntimeError(
            "Refusing integration execution: use a database ending in '_test' or set an "
            "isolated SMARTCOAT_TEST_SCHEMA beginning with 'smartcoat_test_'."
        )
    return None


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
def postgres_context() -> Generator[PostgresTestContext, None, None]:
    database_url = os.getenv("SMARTCOAT_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set SMARTCOAT_TEST_DATABASE_URL to run PostgreSQL integration tests.")

    schema_name = _require_test_target(database_url, os.getenv("SMARTCOAT_TEST_SCHEMA"))
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
        if schema_name is not None:
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
            if test_engine is not admin_engine:
                test_engine.dispose()
            if schema_created and schema_name is not None:
                with admin_engine.begin() as connection:
                    connection.execute(text(f'DROP SCHEMA "{schema_name}" CASCADE'))
            admin_engine.dispose()


def test_non_test_database_without_schema_is_rejected() -> None:
    with pytest.raises(RuntimeError, match="Refusing integration execution"):
        _require_test_target("postgresql+psycopg://localhost/smartcoat", None)


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
