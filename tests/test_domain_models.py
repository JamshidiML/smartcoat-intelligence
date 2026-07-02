from smartcoat.domain.decision_objects import DecisionObject, DecisionType
from smartcoat.domain.knowledge_objects import KnowledgeObject, KnowledgeObjectType


def test_knowledge_object_creation() -> None:
    obj = KnowledgeObject(
        title="Adhesion failure lesson",
        knowledge_type=KnowledgeObjectType.LESSON_LEARNED,
        description="Initial test knowledge object.",
        confidence=0.7,
    )

    assert obj.title == "Adhesion failure lesson"
    assert obj.knowledge_type == KnowledgeObjectType.LESSON_LEARNED


def test_decision_object_creation() -> None:
    obj = DecisionObject(
        title="Select alternative supplier",
        decision_type=DecisionType.SUPPLIER,
        problem="Material unavailable from primary supplier.",
        confidence=0.6,
    )

    assert obj.title == "Select alternative supplier"
    assert obj.decision_type == DecisionType.SUPPLIER
