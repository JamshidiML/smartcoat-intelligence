from uuid import UUID

from smartcoat.domain.knowledge_objects import KnowledgeObject
from smartcoat.storage.repositories.knowledge_repository import KnowledgeRepository


class KnowledgeService:
    """Application service for Knowledge Objects."""

    def __init__(self, repository: KnowledgeRepository | None = None) -> None:
        self.repository = repository
        self._objects: dict[UUID, KnowledgeObject] = {}

    def create(self, knowledge_object: KnowledgeObject) -> KnowledgeObject:
        if self.repository is not None:
            return self.repository.create(knowledge_object)
        self._objects[knowledge_object.object_id] = knowledge_object
        return knowledge_object

    def get(self, knowledge_id: UUID) -> KnowledgeObject | None:
        if self.repository is not None:
            return self.repository.get(knowledge_id)
        return self._objects.get(knowledge_id)

    def list(self, limit: int = 100) -> list[KnowledgeObject]:
        if self.repository is not None:
            return self.repository.list(limit=limit)
        return list(self._objects.values())[:limit]
