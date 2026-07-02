from uuid import UUID

from sqlalchemy.orm import Session

from smartcoat.domain.knowledge_objects import KnowledgeObject
from smartcoat.storage.database.models import KnowledgeObjectRecord
from smartcoat.storage.repositories.mappers import knowledge_to_record, record_to_knowledge


class KnowledgeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, obj: KnowledgeObject) -> KnowledgeObject:
        record = knowledge_to_record(obj)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record_to_knowledge(record)

    def get(self, object_id: UUID) -> KnowledgeObject | None:
        record = self.session.get(KnowledgeObjectRecord, str(object_id))
        return record_to_knowledge(record) if record else None

    def list(self, limit: int = 100) -> list[KnowledgeObject]:
        records = self.session.query(KnowledgeObjectRecord).limit(limit).all()
        return [record_to_knowledge(record) for record in records]
