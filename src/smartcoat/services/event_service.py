from uuid import UUID

from smartcoat.domain.events import EnterpriseEvent
from smartcoat.storage.repositories.event_repository import EventRepository


class EventService:
    """Application service for Enterprise Events."""

    def __init__(self, repository: EventRepository | None = None) -> None:
        self.repository = repository
        self._objects: dict[UUID, EnterpriseEvent] = {}

    def create(self, event: EnterpriseEvent) -> EnterpriseEvent:
        if self.repository is not None:
            return self.repository.create(event)
        self._objects[event.object_id] = event
        return event

    def get(self, event_id: UUID) -> EnterpriseEvent | None:
        if self.repository is not None:
            return self.repository.get(event_id)
        return self._objects.get(event_id)

    def list(self, limit: int = 100) -> list[EnterpriseEvent]:
        if self.repository is not None:
            return self.repository.list(limit=limit)
        return list(self._objects.values())[:limit]
