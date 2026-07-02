from uuid import UUID

from sqlalchemy.orm import Session

from smartcoat.domain.events import EnterpriseEvent
from smartcoat.storage.database.models import EnterpriseEventRecord
from smartcoat.storage.repositories.mappers import event_to_record


class EventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, obj: EnterpriseEvent) -> EnterpriseEvent:
        record = event_to_record(obj)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return obj

    def get(self, object_id: UUID) -> EnterpriseEventRecord | None:
        return self.session.get(EnterpriseEventRecord, str(object_id))

    def list(self, limit: int = 100) -> list[EnterpriseEventRecord]:
        return self.session.query(EnterpriseEventRecord).limit(limit).all()
