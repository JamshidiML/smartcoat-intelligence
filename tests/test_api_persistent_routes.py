from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from smartcoat.api.main import app
from smartcoat.api.routes.decisions import get_decision_service
from smartcoat.api.routes.events import get_event_service
from smartcoat.api.routes.knowledge import get_knowledge_service
from smartcoat.domain.decision_objects import DecisionObject, DecisionType
from smartcoat.domain.events import EnterpriseEvent, EventType
from smartcoat.domain.knowledge_objects import KnowledgeObject, KnowledgeObjectType
from smartcoat.services.decision_service import DecisionService
from smartcoat.services.event_service import EventService
from smartcoat.services.knowledge_service import KnowledgeService


def override_knowledge_service() -> KnowledgeService:
    return KnowledgeService()


def override_decision_service() -> DecisionService:
    return DecisionService()


def override_event_service() -> EventService:
    return EventService()


client = TestClient(app)


@pytest.fixture(autouse=True)
def service_overrides() -> None:
    app.dependency_overrides[get_knowledge_service] = override_knowledge_service
    app.dependency_overrides[get_decision_service] = override_decision_service
    app.dependency_overrides[get_event_service] = override_event_service
    yield
    app.dependency_overrides.clear()


def test_health_route() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_knowledge_route() -> None:
    payload = KnowledgeObject(
        title="API knowledge object",
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        confidence=0.8,
    ).model_dump(mode="json")

    response = client.post("/knowledge", json=payload)

    assert response.status_code == 200
    assert response.json()["title"] == "API knowledge object"


def test_list_knowledge_route_rejects_zero_limit() -> None:
    response = client.get("/knowledge?limit=0")

    assert response.status_code == 422


def test_get_missing_knowledge_route() -> None:
    response = client.get(f"/knowledge/{uuid4()}")

    assert response.status_code == 404


def test_create_decision_route() -> None:
    payload = DecisionObject(
        title="API decision object",
        decision_type=DecisionType.ENGINEERING,
        confidence=0.7,
    ).model_dump(mode="json")

    response = client.post("/decisions", json=payload)

    assert response.status_code == 200
    assert response.json()["title"] == "API decision object"


def test_list_decision_route_rejects_excessive_limit() -> None:
    response = client.get("/decisions?limit=501")

    assert response.status_code == 422


def test_create_event_route() -> None:
    payload = EnterpriseEvent(
        title="API event object",
        event_type=EventType.KNOWLEDGE_CREATED,
        actor="test",
    ).model_dump(mode="json")

    response = client.post("/events", json=payload)

    assert response.status_code == 200
    assert response.json()["title"] == "API event object"


def test_list_event_route_rejects_zero_limit() -> None:
    response = client.get("/events?limit=0")

    assert response.status_code == 422
