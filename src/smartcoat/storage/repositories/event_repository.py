from uuid import UUID

from sqlalchemy.orm import Session

from smartcoat.domain.events import EnterpriseEvent
from smartcoat.storage.database.models import EnterpriseEventRecord
from smartcoat.storage.repositories.mappers import event_to_record, record_to_event


class EventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, obj: EnterpriseEvent) -> EnterpriseEvent:
        record = event_to_record(obj)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record_to_event(record)

    def get(self, object_id: UUID) -> EnterpriseEvent | None:
        record = self.session.get(EnterpriseEventRecord, str(object_id))
        return record_to_event(record) if record else None

    def list(self, limit: int = 100) -> list[EnterpriseEvent]:
        records = self.session.query(EnterpriseEventRecord).limit(limit).all()
        return [record_to_event(record) for record in records]
