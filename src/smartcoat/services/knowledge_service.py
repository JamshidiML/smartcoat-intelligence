from uuid import UUID

from smartcoat.domain.knowledge_objects import KnowledgeObject


class KnowledgeService:
    """In-memory Knowledge Object service for MVP scaffolding.

    This will later be replaced or backed by PostgreSQL and Knowledge Graph storage.
    """

    def __init__(self) -> None:
        self._objects: dict[UUID, KnowledgeObject] = {}

    def create(self, knowledge_object: KnowledgeObject) -> KnowledgeObject:
        self._objects[knowledge_object.object_id] = knowledge_object
        return knowledge_object

    def get(self, knowledge_id: UUID) -> KnowledgeObject | None:
        return self._objects.get(knowledge_id)

    def list(self) -> list[KnowledgeObject]:
        return list(self._objects.values())
