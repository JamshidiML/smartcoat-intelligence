from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from smartcoat.api.dependencies.database import get_db_session
from smartcoat.domain.knowledge_objects import KnowledgeObject
from smartcoat.services.knowledge_service import KnowledgeService
from smartcoat.storage.repositories.knowledge_repository import KnowledgeRepository

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def get_knowledge_service(
    session: Session = Depends(get_db_session),
) -> KnowledgeService:
    repository = KnowledgeRepository(session)
    return KnowledgeService(repository=repository)


@router.post("", response_model=KnowledgeObject)
def create_knowledge_object(
    payload: KnowledgeObject,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeObject:
    return service.create(payload)


@router.get("/{knowledge_id}", response_model=KnowledgeObject)
def get_knowledge_object(
    knowledge_id: UUID,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeObject:
    item = service.get(knowledge_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Knowledge Object not found")
    return item


@router.get("", response_model=list[KnowledgeObject])
def list_knowledge_objects(
    limit: int = 100,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> list[KnowledgeObject]:
    return service.list(limit=limit)
