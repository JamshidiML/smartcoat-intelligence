from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from smartcoat.api.dependencies.database import get_db_session
from smartcoat.domain.decision_objects import DecisionObject
from smartcoat.services.decision_service import DecisionService
from smartcoat.storage.repositories.decision_repository import DecisionRepository

router = APIRouter(prefix="/decisions", tags=["decisions"])

SessionDependency = Annotated[Session, Depends(get_db_session)]
ListLimit = Annotated[int, Query(ge=1, le=500)]


def get_decision_service(
    session: SessionDependency,
) -> DecisionService:
    repository = DecisionRepository(session)
    return DecisionService(repository=repository)


DecisionServiceDependency = Annotated[DecisionService, Depends(get_decision_service)]


@router.post("", response_model=DecisionObject)
def create_decision_object(
    payload: DecisionObject,
    service: DecisionServiceDependency,
) -> DecisionObject:
    return service.create(payload)


@router.get("/{decision_id}", response_model=DecisionObject)
def get_decision_object(
    decision_id: UUID,
    service: DecisionServiceDependency,
) -> DecisionObject:
    item = service.get(decision_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Decision Object not found")
    return item


@router.get("", response_model=list[DecisionObject])
def list_decision_objects(
    service: DecisionServiceDependency,
    limit: ListLimit = 100,
) -> list[DecisionObject]:
    return service.list(limit=limit)
