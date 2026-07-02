from uuid import UUID

from fastapi import APIRouter, HTTPException

from smartcoat.domain.knowledge_objects import KnowledgeObject
from smartcoat.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

_service = KnowledgeService()


@router.post("", response_model=KnowledgeObject)
def create_knowledge_object(payload: KnowledgeObject) -> KnowledgeObject:
    return _service.create(payload)


@router.get("/{knowledge_id}", response_model=KnowledgeObject)
def get_knowledge_object(knowledge_id: UUID) -> KnowledgeObject:
    item = _service.get(knowledge_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Knowledge Object not found")
    return item


@router.get("", response_model=list[KnowledgeObject])
def list_knowledge_objects() -> list[KnowledgeObject]:
    return _service.list()
