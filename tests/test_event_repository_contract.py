from unittest.mock import MagicMock

from smartcoat.domain.events import EnterpriseEvent, EventType
from smartcoat.storage.repositories.event_repository import EventRepository
from smartcoat.storage.repositories.mappers import event_to_record


def test_event_repository_returns_domain_objects_after_persistence() -> None:
    event = EnterpriseEvent(
        title="Synthetic event persisted",
        event_type=EventType.KNOWLEDGE_CREATED,
        actor="test_runner",
        evidence=["synthetic-evidence-ref"],
    )
    record = event_to_record(event)
    session = MagicMock()
    session.get.return_value = record
    session.query.return_value.limit.return_value.all.return_value = [record]

    repository = EventRepository(session)
    created = repository.create(event)
    loaded = repository.get(created.object_id)
    listed = repository.list(limit=10)

    session.add.assert_called_once()
    session.commit.assert_called_once()
    session.refresh.assert_called_once()

    assert isinstance(created, EnterpriseEvent)
    assert isinstance(loaded, EnterpriseEvent)
    assert all(isinstance(item, EnterpriseEvent) for item in listed)
    assert loaded is not None
    assert loaded.object_id == created.object_id
    assert loaded.evidence == ["synthetic-evidence-ref"]
