from smartcoat.domain.decision_objects import DecisionObject, DecisionType
from smartcoat.domain.events import EnterpriseEvent, EventType
from smartcoat.domain.knowledge_objects import KnowledgeObject, KnowledgeObjectType
from smartcoat.storage.repositories.mappers import decision_to_record, event_to_record, knowledge_to_record


def test_knowledge_to_record_mapper() -> None:
    obj = KnowledgeObject(
        title="Captured coating observation",
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        confidence=0.8,
    )

    record = knowledge_to_record(obj)

    assert record.title == "Captured coating observation"
    assert record.knowledge_type == "observation"
    assert record.confidence == 0.8


def test_decision_to_record_mapper() -> None:
    obj = DecisionObject(
        title="Use alternative supplier",
        decision_type=DecisionType.SUPPLIER,
        confidence=0.7,
    )

    record = decision_to_record(obj)

    assert record.title == "Use alternative supplier"
    assert record.decision_type == "supplier"
    assert record.confidence == 0.7


def test_event_to_record_mapper() -> None:
    obj = EnterpriseEvent(
        title="Knowledge object created",
        event_type=EventType.KNOWLEDGE_CREATED,
        actor="memory_agent",
    )

    record = event_to_record(obj)

    assert record.title == "Knowledge object created"
    assert record.event_type == "knowledge_created"
    assert record.actor == "memory_agent"
