from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from smartcoat.api.dependencies.database import get_db_session
from smartcoat.domain.events import EnterpriseEvent
from smartcoat.services.event_service import EventService
from smartcoat.storage.repositories.event_repository import EventRepository

router = APIRouter(prefix="/events", tags=["events"])


def get_event_service(
    session: Session = Depends(get_db_session),
) -> EventService:
    repository = EventRepository(session)
    return EventService(repository=repository)


@router.post("", response_model=EnterpriseEvent)
def create_enterprise_event(
    payload: EnterpriseEvent,
    service: EventService = Depends(get_event_service),
) -> EnterpriseEvent:
    return service.create(payload)


@router.get("/{event_id}", response_model=EnterpriseEvent)
def get_enterprise_event(
    event_id: UUID,
    service: EventService = Depends(get_event_service),
) -> EnterpriseEvent:
    item = service.get(event_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Enterprise Event not found")
    return item


@router.get("", response_model=list[EnterpriseEvent])
def list_enterprise_events(
    limit: int = 100,
    service: EventService = Depends(get_event_service),
) -> list[EnterpriseEvent]:
    return service.list(limit=limit)
