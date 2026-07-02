from uuid import UUID

from fastapi import APIRouter, HTTPException

from smartcoat.domain.decision_objects import DecisionObject
from smartcoat.services.decision_service import DecisionService

router = APIRouter(prefix="/decisions", tags=["decisions"])

_service = DecisionService()


@router.post("", response_model=DecisionObject)
def create_decision_object(payload: DecisionObject) -> DecisionObject:
    return _service.create(payload)


@router.get("/{decision_id}", response_model=DecisionObject)
def get_decision_object(decision_id: UUID) -> DecisionObject:
    item = _service.get(decision_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Decision Object not found")
    return item


@router.get("", response_model=list[DecisionObject])
def list_decision_objects() -> list[DecisionObject]:
    return _service.list()
