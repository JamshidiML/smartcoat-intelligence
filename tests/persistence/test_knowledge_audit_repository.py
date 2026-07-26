from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from smartcoat.domain.base import LifecycleState
from smartcoat.domain.knowledge_audit import (
    KnowledgeAuditAppendRequest,
    KnowledgeAuditChangedField,
    KnowledgeAuditEventType,
)
from smartcoat.storage.database.knowledge_audit_models import (
    KnowledgeAuditEventRecord,
)
from smartcoat.storage.repositories.knowledge_audit_repository import (
    KnowledgeAuditParticipant,
    KnowledgeAuditParticipantError,
    KnowledgeAuditRepository,
)

NOW = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
OBJECT_ID = uuid4()
CORRELATION_ID = uuid4()


def _request(
    *,
    object_id: UUID = OBJECT_ID,
    correlation_id: UUID = CORRELATION_ID,
) -> KnowledgeAuditAppendRequest:
    return KnowledgeAuditAppendRequest(
        organization_id="synthetic-org",
        object_id=object_id,
        event_type=KnowledgeAuditEventType.UPDATE,
        lifecycle_action=None,
        actor_id="synthetic-actor",
        actor_role="knowledge_author",
        occurred_at=NOW,
        correlation_id=correlation_id,
        previous_lifecycle=LifecycleState.DRAFT,
        resulting_lifecycle=LifecycleState.DRAFT,
        previous_revision=1,
        resulting_revision=2,
        reason_or_note="Synthetic update.",
        changed_fields=[KnowledgeAuditChangedField.CONTENT],
    )


def _record(
    *,
    sequence: int,
    event_id: UUID | None = None,
) -> KnowledgeAuditEventRecord:
    return KnowledgeAuditEventRecord(
        event_id=event_id or uuid4(),
        schema_version="1",
        event_family="enterprise_event",
        organization_id="synthetic-org",
        object_id=OBJECT_ID,
        event_type="update",
        lifecycle_action=None,
        actor_id="synthetic-actor",
        actor_role="knowledge_author",
        occurred_at=NOW,
        recorded_at=NOW + timedelta(seconds=1),
        correlation_id=uuid4(),
        previous_lifecycle="draft",
        resulting_lifecycle="draft",
        previous_revision=sequence,
        resulting_revision=sequence + 1,
        reason_or_note="Synthetic update.",
        changed_fields_json='["content"]',
        audit_sequence=sequence,
    )


def _compiled(statement: object) -> str:
    return str(
        statement.compile(  # type: ignore[attr-defined]
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
    )


def test_stage_append_flushes_without_committing_and_returns_domain_event() -> None:
    session = MagicMock(spec=Session)
    session.scalar.return_value = None

    def assign_server_fields() -> None:
        record = session.add.call_args.args[0]
        record.event_id = uuid4()
        record.schema_version = "1"
        record.event_family = "enterprise_event"
        record.recorded_at = NOW + timedelta(seconds=1)
        record.audit_sequence = 7

    session.flush.side_effect = assign_server_fields
    repository = KnowledgeAuditRepository(session)

    event = repository.stage_append(_request())

    session.add.assert_called_once()
    session.flush.assert_called_once()
    session.refresh.assert_called_once()
    session.commit.assert_not_called()
    assert event.audit_sequence == 7
    assert event.changed_fields == (KnowledgeAuditChangedField.CONTENT,)


def test_every_query_contains_organization_and_object_predicates() -> None:
    session = MagicMock(spec=Session)
    session.scalar.return_value = None
    session.scalars.return_value.all.return_value = []
    repository = KnowledgeAuditRepository(session)

    assert (
        repository.get_event(
            organization_id="synthetic-org",
            object_id=OBJECT_ID,
            event_id=uuid4(),
        )
        is None
    )
    repository.history_for_object(
        organization_id="synthetic-org",
        object_id=OBJECT_ID,
    )

    get_sql = _compiled(session.scalar.call_args.args[0])
    history_sql = _compiled(session.scalars.call_args.args[0])
    for statement in (get_sql, history_sql):
        assert "organization_id" in statement
        assert "object_id" in statement
    assert "ORDER BY knowledge_audit_events_v2.audit_sequence ASC" in history_sql


def test_history_returns_frozen_domain_events_in_repository_order() -> None:
    session = MagicMock(spec=Session)
    session.scalars.return_value.all.return_value = [
        _record(sequence=4),
        _record(sequence=9),
    ]
    repository = KnowledgeAuditRepository(session)

    events = repository.history_for_object(
        organization_id="synthetic-org",
        object_id=OBJECT_ID,
    )

    assert tuple(event.audit_sequence for event in events) == (4, 9)
    with pytest.raises(Exception, match="frozen"):
        events[0].actor_id = "changed"  # type: ignore[misc]


def test_repository_surface_is_append_only_and_has_no_commit_method() -> None:
    public_methods = {name for name in dir(KnowledgeAuditRepository) if not name.startswith("_")}
    assert public_methods == {"get_event", "history_for_object", "stage_append"}
    assert not hasattr(KnowledgeAuditRepository, "commit")
    assert not hasattr(KnowledgeAuditRepository, "save")
    assert not hasattr(KnowledgeAuditRepository, "update")
    assert not hasattr(KnowledgeAuditRepository, "delete")


def test_participant_rejects_duplicate_queue_and_second_flush() -> None:
    participant = KnowledgeAuditParticipant()
    request = _request()
    participant.queue(request)

    with pytest.raises(
        KnowledgeAuditParticipantError,
        match="duplicate_audit_queue",
    ):
        participant.queue(request)

    session = MagicMock(spec=Session)
    record = _record(sequence=3)
    session.scalar.side_effect = [None]

    def assign_server_fields() -> None:
        staged = session.add.call_args.args[0]
        staged.event_id = record.event_id
        staged.schema_version = "1"
        staged.event_family = "enterprise_event"
        staged.recorded_at = record.recorded_at
        staged.audit_sequence = record.audit_sequence

    session.flush.side_effect = assign_server_fields
    participant.flush(session)

    assert participant.single_appended_event().audit_sequence == 3
    with pytest.raises(
        KnowledgeAuditParticipantError,
        match="already_flushed",
    ):
        participant.flush(session)


def test_participant_does_not_expose_events_before_flush() -> None:
    participant = KnowledgeAuditParticipant()
    participant.queue(_request())

    with pytest.raises(
        KnowledgeAuditParticipantError,
        match="not_flushed",
    ):
        _ = participant.appended_events
