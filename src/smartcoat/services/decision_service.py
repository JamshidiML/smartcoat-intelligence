from uuid import UUID

from smartcoat.domain.decision_objects import DecisionObject
from smartcoat.storage.repositories.decision_repository import DecisionRepository


class DecisionService:
    """Application service for Decision Objects."""

    def __init__(self, repository: DecisionRepository | None = None) -> None:
        self.repository = repository
        self._objects: dict[UUID, DecisionObject] = {}

    def create(self, decision_object: DecisionObject) -> DecisionObject:
        if self.repository is not None:
            return self.repository.create(decision_object)
        self._objects[decision_object.object_id] = decision_object
        return decision_object

    def get(self, decision_id: UUID) -> DecisionObject | None:
        if self.repository is not None:
            return self.repository.get(decision_id)
        return self._objects.get(decision_id)

    def list(self, limit: int = 100) -> list[DecisionObject]:
        if self.repository is not None:
            return self.repository.list(limit=limit)
        return list(self._objects.values())[:limit]
