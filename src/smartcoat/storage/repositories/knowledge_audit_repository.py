"""Append-only repository and same-session participant for Knowledge audit."""

from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from smartcoat.domain.base import LifecycleState
from smartcoat.domain.knowledge_audit import (
    KNOWLEDGE_AUDIT_EVENT_FAMILY,
    KNOWLEDGE_AUDIT_SCHEMA_VERSION,
    KnowledgeAuditAppendRequest,
    KnowledgeAuditChangedField,
    KnowledgeAuditEvent,
    KnowledgeAuditEventType,
)
from smartcoat.domain.knowledge_lifecycle import LifecycleAction
from smartcoat.storage.database.knowledge_audit_models import (
    KnowledgeAuditEventRecord,
)


class KnowledgeAuditRepositoryError(ValueError):
    """Typed deterministic canonical audit persistence failure."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _changed_fields_json(
    changed_fields: tuple[KnowledgeAuditChangedField, ...],
) -> str:
    return json.dumps(
        [field.value for field in changed_fields],
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _event_from_record(record: KnowledgeAuditEventRecord) -> KnowledgeAuditEvent:
    if (
        record.schema_version != KNOWLEDGE_AUDIT_SCHEMA_VERSION
        or record.event_family != KNOWLEDGE_AUDIT_EVENT_FAMILY
    ):
        raise KnowledgeAuditRepositoryError(
            "knowledge_audit_contract_invalid",
            "persisted audit schema version and event family must be canonical",
        )
    changed_fields_payload = json.loads(record.changed_fields_json)
    if not isinstance(changed_fields_payload, list):
        raise KnowledgeAuditRepositoryError(
            "knowledge_audit_changed_fields_invalid",
            "persisted changed_fields_json must contain a JSON list",
        )
    return KnowledgeAuditEvent(
        event_id=record.event_id,
        organization_id=record.organization_id,
        object_id=record.object_id,
        event_type=KnowledgeAuditEventType(record.event_type),
        lifecycle_action=(
            LifecycleAction(record.lifecycle_action)
            if record.lifecycle_action is not None
            else None
        ),
        actor_id=record.actor_id,
        actor_role=record.actor_role,
        occurred_at=record.occurred_at,
        recorded_at=record.recorded_at,
        correlation_id=record.correlation_id,
        previous_lifecycle=(
            LifecycleState(record.previous_lifecycle)
            if record.previous_lifecycle is not None
            else None
        ),
        resulting_lifecycle=(
            LifecycleState(record.resulting_lifecycle)
            if record.resulting_lifecycle is not None
            else None
        ),
        previous_revision=record.previous_revision,
        resulting_revision=record.resulting_revision,
        reason_or_note=record.reason_or_note,
        changed_fields=tuple(changed_fields_payload),
        audit_sequence=record.audit_sequence,
    )


class KnowledgeAuditRepository:
    """No-commit append and organization-scoped history primitives."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def stage_append(
        self,
        request: KnowledgeAuditAppendRequest,
    ) -> KnowledgeAuditEvent:
        duplicate = self._session.scalar(
            select(KnowledgeAuditEventRecord.event_id).where(
                KnowledgeAuditEventRecord.organization_id == request.organization_id,
                KnowledgeAuditEventRecord.object_id == request.object_id,
                KnowledgeAuditEventRecord.correlation_id == request.correlation_id,
            )
        )
        if duplicate is not None:
            raise KnowledgeAuditRepositoryError(
                "duplicate_audit_action",
                "the organization, object, and correlation ID already identify an audit event",
            )

        record = KnowledgeAuditEventRecord(
            organization_id=request.organization_id,
            object_id=request.object_id,
            event_type=request.event_type.value,
            lifecycle_action=(
                request.lifecycle_action.value if request.lifecycle_action is not None else None
            ),
            actor_id=request.actor_id,
            actor_role=request.actor_role,
            occurred_at=request.occurred_at,
            correlation_id=request.correlation_id,
            previous_lifecycle=(
                request.previous_lifecycle.value if request.previous_lifecycle is not None else None
            ),
            resulting_lifecycle=(
                request.resulting_lifecycle.value
                if request.resulting_lifecycle is not None
                else None
            ),
            previous_revision=request.previous_revision,
            resulting_revision=request.resulting_revision,
            reason_or_note=request.reason_or_note,
            changed_fields_json=_changed_fields_json(request.changed_fields),
        )
        self._session.add(record)
        self._session.flush()
        self._session.refresh(record)
        return _event_from_record(record)

    def get_event(
        self,
        *,
        organization_id: str,
        object_id: UUID,
        event_id: UUID,
    ) -> KnowledgeAuditEvent | None:
        record = self._session.scalar(
            select(KnowledgeAuditEventRecord).where(
                KnowledgeAuditEventRecord.organization_id == organization_id,
                KnowledgeAuditEventRecord.object_id == object_id,
                KnowledgeAuditEventRecord.event_id == event_id,
            )
        )
        return _event_from_record(record) if record is not None else None

    def history_for_object(
        self,
        *,
        organization_id: str,
        object_id: UUID,
    ) -> tuple[KnowledgeAuditEvent, ...]:
        records = self._session.scalars(
            select(KnowledgeAuditEventRecord)
            .where(
                KnowledgeAuditEventRecord.organization_id == organization_id,
                KnowledgeAuditEventRecord.object_id == object_id,
            )
            .order_by(KnowledgeAuditEventRecord.audit_sequence.asc())
        ).all()
        return tuple(_event_from_record(record) for record in records)


class KnowledgeAuditParticipantError(RuntimeError):
    """Invalid queue or flush lifecycle for one internal audit participant."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class KnowledgeAuditParticipant:
    """Queue canonical requests and flush them through the UoW Session."""

    def __init__(self) -> None:
        self._requests: list[KnowledgeAuditAppendRequest] = []
        self._appended_events: tuple[KnowledgeAuditEvent, ...] = ()
        self._flushed = False

    def queue(self, request: KnowledgeAuditAppendRequest) -> None:
        if self._flushed:
            raise KnowledgeAuditParticipantError(
                "audit_participant_already_flushed",
                "audit work cannot be queued after participant flush",
            )
        key = (
            request.organization_id,
            request.object_id,
            request.correlation_id,
        )
        if any(
            (
                queued.organization_id,
                queued.object_id,
                queued.correlation_id,
            )
            == key
            for queued in self._requests
        ):
            raise KnowledgeAuditParticipantError(
                "duplicate_audit_queue",
                "one atomic action may queue only one canonical audit request",
            )
        self._requests.append(request)

    def flush(self, session: Session) -> None:
        if self._flushed:
            raise KnowledgeAuditParticipantError(
                "audit_participant_already_flushed",
                "the audit participant may be flushed only once",
            )
        repository = KnowledgeAuditRepository(session)
        appended = tuple(repository.stage_append(request) for request in self._requests)
        self._appended_events = appended
        self._flushed = True

    @property
    def appended_events(self) -> tuple[KnowledgeAuditEvent, ...]:
        if not self._flushed:
            raise KnowledgeAuditParticipantError(
                "audit_participant_not_flushed",
                "audit events are unavailable before successful participant flush",
            )
        return self._appended_events

    def single_appended_event(self) -> KnowledgeAuditEvent:
        events = self.appended_events
        if len(events) != 1:
            raise KnowledgeAuditParticipantError(
                "audit_participant_event_count",
                f"expected exactly one appended event, found {len(events)}",
            )
        return events[0]
