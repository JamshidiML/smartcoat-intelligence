from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from smartcoat.api.dependencies.database import get_db_session
from smartcoat.domain.decision_objects import DecisionObject
from smartcoat.services.decision_service import DecisionService
from smartcoat.storage.repositories.decision_repository import DecisionRepository

router = APIRouter(prefix="/decisions", tags=["decisions"])


def get_decision_service(
    session: Session = Depends(get_db_session),
) -> DecisionService:
    repository = DecisionRepository(session)
    return DecisionService(repository=repository)


@router.post("", response_model=DecisionObject)
def create_decision_object(
    payload: DecisionObject,
    service: DecisionService = Depends(get_decision_service),
) -> DecisionObject:
    return service.create(payload)


@router.get("/{decision_id}", response_model=DecisionObject)
def get_decision_object(
    decision_id: UUID,
    service: DecisionService = Depends(get_decision_service),
) -> DecisionObject:
    item = service.get(decision_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Decision Object not found")
    return item


@router.get("", response_model=list[DecisionObject])
def list_decision_objects(
    limit: int = 100,
    service: DecisionService = Depends(get_decision_service),
) -> list[DecisionObject]:
    return service.list(limit=limit)
