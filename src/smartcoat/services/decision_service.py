from uuid import UUID

from smartcoat.domain.decision_objects import DecisionObject


class DecisionService:
    """In-memory Decision Object service for MVP scaffolding."""

    def __init__(self) -> None:
        self._objects: dict[UUID, DecisionObject] = {}

    def create(self, decision_object: DecisionObject) -> DecisionObject:
        self._objects[decision_object.object_id] = decision_object
        return decision_object

    def get(self, decision_id: UUID) -> DecisionObject | None:
        return self._objects.get(decision_id)

    def list(self) -> list[DecisionObject]:
        return list(self._objects.values())
