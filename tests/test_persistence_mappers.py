from smartcoat.domain.decision_objects import DecisionObject, DecisionType
from smartcoat.domain.events import EnterpriseEvent, EventType
from smartcoat.domain.knowledge_objects import KnowledgeObject, KnowledgeObjectType
from smartcoat.storage.repositories.mappers import (
    decision_to_record,
    event_to_record,
    knowledge_to_record,
    record_to_decision,
    record_to_event,
    record_to_knowledge,
)


def test_knowledge_mapper_round_trip() -> None:
    obj = KnowledgeObject(
        title="Captured coating observation",
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        confidence=0.8,
    )

    record = knowledge_to_record(obj)
    restored = record_to_knowledge(record)

    assert restored.title == "Captured coating observation"
    assert restored.knowledge_type == KnowledgeObjectType.OBSERVATION
    assert restored.confidence == 0.8
    assert restored.created_at is not None
    assert restored.updated_at is not None


def test_decision_mapper_round_trip() -> None:
    obj = DecisionObject(
        title="Use alternative supplier",
        decision_type=DecisionType.SUPPLIER,
        confidence=0.7,
    )

    record = decision_to_record(obj)
    restored = record_to_decision(record)

    assert restored.title == "Use alternative supplier"
    assert restored.decision_type == DecisionType.SUPPLIER
    assert restored.confidence == 0.7
    assert restored.created_at is not None
    assert restored.updated_at is not None


def test_event_mapper_round_trip() -> None:
    obj = EnterpriseEvent(
        title="Knowledge object created",
        event_type=EventType.KNOWLEDGE_CREATED,
        actor="memory_agent",
    )

    record = event_to_record(obj)
    restored = record_to_event(record)

    assert restored.title == "Knowledge object created"
    assert restored.event_type == EventType.KNOWLEDGE_CREATED
    assert restored.actor == "memory_agent"
    assert restored.created_at is not None
    assert restored.updated_at is not None
