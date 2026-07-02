from uuid import UUID

from sqlalchemy.orm import Session

from smartcoat.domain.decision_objects import DecisionObject
from smartcoat.storage.database.models import DecisionObjectRecord
from smartcoat.storage.repositories.mappers import decision_to_record, record_to_decision


class DecisionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, obj: DecisionObject) -> DecisionObject:
        record = decision_to_record(obj)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record_to_decision(record)

    def get(self, object_id: UUID) -> DecisionObject | None:
        record = self.session.get(DecisionObjectRecord, str(object_id))
        return record_to_decision(record) if record else None

    def list(self, limit: int = 100) -> list[DecisionObject]:
        records = self.session.query(DecisionObjectRecord).limit(limit).all()
        return [record_to_decision(record) for record in records]
