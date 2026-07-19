from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from smartcoat.api.dependencies.database import get_db_session
from smartcoat.domain.events import EnterpriseEvent
from smartcoat.services.event_service import EventService
from smartcoat.storage.repositories.event_repository import EventRepository

router = APIRouter(prefix="/events", tags=["events"])

SessionDependency = Annotated[Session, Depends(get_db_session)]
ListLimit = Annotated[int, Query(ge=1, le=500)]


def get_event_service(
    session: SessionDependency,
) -> EventService:
    repository = EventRepository(session)
    return EventService(repository=repository)


EventServiceDependency = Annotated[EventService, Depends(get_event_service)]


@router.post("", response_model=EnterpriseEvent)
def create_enterprise_event(
    payload: EnterpriseEvent,
    service: EventServiceDependency,
) -> EnterpriseEvent:
    return service.create(payload)


@router.get("/{event_id}", response_model=EnterpriseEvent)
def get_enterprise_event(
    event_id: UUID,
    service: EventServiceDependency,
) -> EnterpriseEvent:
    item = service.get(event_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Enterprise Event not found")
    return item


@router.get("", response_model=list[EnterpriseEvent])
def list_enterprise_events(
    service: EventServiceDependency,
    limit: ListLimit = 100,
) -> list[EnterpriseEvent]:
    return service.list(limit=limit)
