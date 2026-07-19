from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from smartcoat.api.dependencies.database import get_db_session
from smartcoat.domain.knowledge_objects import KnowledgeObject
from smartcoat.services.knowledge_service import KnowledgeService
from smartcoat.storage.repositories.knowledge_repository import KnowledgeRepository

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

SessionDependency = Annotated[Session, Depends(get_db_session)]
ListLimit = Annotated[int, Query(ge=1, le=500)]


def get_knowledge_service(
    session: SessionDependency,
) -> KnowledgeService:
    repository = KnowledgeRepository(session)
    return KnowledgeService(repository=repository)


KnowledgeServiceDependency = Annotated[KnowledgeService, Depends(get_knowledge_service)]


@router.post("", response_model=KnowledgeObject)
def create_knowledge_object(
    payload: KnowledgeObject,
    service: KnowledgeServiceDependency,
) -> KnowledgeObject:
    return service.create(payload)


@router.get("/{knowledge_id}", response_model=KnowledgeObject)
def get_knowledge_object(
    knowledge_id: UUID,
    service: KnowledgeServiceDependency,
) -> KnowledgeObject:
    item = service.get(knowledge_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Knowledge Object not found")
    return item


@router.get("", response_model=list[KnowledgeObject])
def list_knowledge_objects(
    service: KnowledgeServiceDependency,
    limit: ListLimit = 100,
) -> list[KnowledgeObject]:
    return service.list(limit=limit)
