import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
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


@pytest.fixture()
def postgres_client() -> Generator[TestClient, None, None]:
    database_url = os.getenv("SMARTCOAT_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set SMARTCOAT_TEST_DATABASE_URL to run PostgreSQL integration tests.")

    engine = create_engine(database_url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    created_ids: dict[type, list[str]] = {
        KnowledgeObjectRecord: [],
        DecisionObjectRecord: [],
        EnterpriseEventRecord: [],
    }

    def override_db_session() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_db_session
    try:
        client = TestClient(app)
        client.created_ids = created_ids  # type: ignore[attr-defined]
        yield client
    finally:
        app.dependency_overrides.clear()
        with Session(engine) as session:
            for record_type, object_ids in created_ids.items():
                if object_ids:
                    session.execute(delete(record_type).where(record_type.object_id.in_(object_ids)))
            session.commit()
        engine.dispose()


def test_http_to_postgres_round_trip_for_current_object_types(postgres_client: TestClient) -> None:
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

    knowledge_response = postgres_client.post("/knowledge", json=knowledge_payload)
    decision_response = postgres_client.post("/decisions", json=decision_payload)
    event_response = postgres_client.post("/events", json=event_payload)

    assert knowledge_response.status_code == 200
    assert decision_response.status_code == 200
    assert event_response.status_code == 200

    created_ids = postgres_client.created_ids  # type: ignore[attr-defined]
    created_ids[KnowledgeObjectRecord].append(knowledge_response.json()["object_id"])
    created_ids[DecisionObjectRecord].append(decision_response.json()["object_id"])
    created_ids[EnterpriseEventRecord].append(event_response.json()["object_id"])

    knowledge_get = postgres_client.get(f"/knowledge/{knowledge_response.json()['object_id']}")
    decision_get = postgres_client.get(f"/decisions/{decision_response.json()['object_id']}")
    event_get = postgres_client.get(f"/events/{event_response.json()['object_id']}")

    assert knowledge_get.status_code == 200
    assert decision_get.status_code == 200
    assert event_get.status_code == 200
    assert knowledge_get.json()["title"] == "Synthetic persisted knowledge"
    assert decision_get.json()["title"] == "Synthetic persisted decision"
    assert event_get.json()["title"] == "Synthetic persisted event"

    assert postgres_client.get("/knowledge?limit=1").status_code == 200
    assert postgres_client.get("/decisions?limit=1").status_code == 200
    assert postgres_client.get("/events?limit=1").status_code == 200
