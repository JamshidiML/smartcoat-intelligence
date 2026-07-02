from datetime import datetime, timezone
from uuid import UUID

from smartcoat.domain.base import LifecycleState, Provenance
from smartcoat.domain.decision_objects import DecisionObject, DecisionStatus, DecisionType
from smartcoat.domain.events import EnterpriseEvent, EventType
from smartcoat.domain.knowledge_objects import KnowledgeObject, KnowledgeObjectType
from smartcoat.storage.database.models import (
    DecisionObjectRecord,
    EnterpriseEventRecord,
    KnowledgeObjectRecord,
)


def _uuid_list(values: list) -> list[UUID]:
    return [UUID(str(value)) for value in values]


def _timestamp(value: datetime | None) -> datetime:
    return value if value is not None else datetime.now(timezone.utc)


def knowledge_to_record(obj: KnowledgeObject) -> KnowledgeObjectRecord:
    return KnowledgeObjectRecord(
        object_id=str(obj.object_id),
        knowledge_type=obj.knowledge_type.value,
        title=obj.title,
        description=obj.description,
        domain=obj.domain,
        owner=obj.owner,
        lifecycle_state=obj.lifecycle_state.value,
        evidence=obj.evidence,
        related_entities=[str(x) for x in obj.related_entities],
        related_decisions=[str(x) for x in obj.related_decisions],
        confidence=obj.confidence,
        tags=obj.tags,
        content=obj.content,
        provenance=obj.provenance.model_dump(),
        metadata_=obj.metadata,
    )


def record_to_knowledge(record: KnowledgeObjectRecord) -> KnowledgeObject:
    return KnowledgeObject(
        object_id=UUID(str(record.object_id)),
        knowledge_type=KnowledgeObjectType(record.knowledge_type),
        title=record.title,
        description=record.description,
        domain=record.domain,
        owner=record.owner,
        lifecycle_state=LifecycleState(record.lifecycle_state),
        evidence=record.evidence or [],
        related_entities=_uuid_list(record.related_entities or []),
        related_decisions=_uuid_list(record.related_decisions or []),
        confidence=float(record.confidence) if record.confidence is not None else None,
        tags=record.tags or [],
        content=record.content or {},
        provenance=Provenance(**(record.provenance or {})),
        metadata=record.metadata_ or {},
        created_at=_timestamp(record.created_at),
        updated_at=_timestamp(record.updated_at),
    )


def decision_to_record(obj: DecisionObject) -> DecisionObjectRecord:
    return DecisionObjectRecord(
        object_id=str(obj.object_id),
        decision_type=obj.decision_type.value,
        status=obj.status.value,
        title=obj.title,
        description=obj.description,
        domain=obj.domain,
        owner=obj.owner,
        problem=obj.problem,
        context=obj.context,
        evidence=obj.evidence,
        alternatives=obj.alternatives,
        recommendation=obj.recommendation,
        rationale=obj.rationale,
        assumptions=obj.assumptions,
        risks=obj.risks,
        confidence=obj.confidence,
        outcome=obj.outcome,
        learning=obj.learning,
        related_knowledge=[str(x) for x in obj.related_knowledge],
        lifecycle_state=obj.lifecycle_state.value,
        provenance=obj.provenance.model_dump(),
        metadata_=obj.metadata,
    )


def record_to_decision(record: DecisionObjectRecord) -> DecisionObject:
    return DecisionObject(
        object_id=UUID(str(record.object_id)),
        decision_type=DecisionType(record.decision_type),
        status=DecisionStatus(record.status),
        title=record.title,
        description=record.description,
        domain=record.domain,
        owner=record.owner,
        problem=record.problem,
        context=record.context or {},
        evidence=record.evidence or [],
        alternatives=record.alternatives or [],
        recommendation=record.recommendation,
        rationale=record.rationale,
        assumptions=record.assumptions or [],
        risks=record.risks or [],
        confidence=float(record.confidence) if record.confidence is not None else None,
        outcome=record.outcome,
        learning=record.learning,
        related_knowledge=_uuid_list(record.related_knowledge or []),
        lifecycle_state=LifecycleState(record.lifecycle_state),
        provenance=Provenance(**(record.provenance or {})),
        metadata=record.metadata_ or {},
        created_at=_timestamp(record.created_at),
        updated_at=_timestamp(record.updated_at),
    )


def event_to_record(obj: EnterpriseEvent) -> EnterpriseEventRecord:
    return EnterpriseEventRecord(
        object_id=str(obj.object_id),
        event_type=obj.event_type.value,
        title=obj.title,
        description=obj.description,
        domain=obj.domain,
        owner=obj.owner,
        actor=obj.actor,
        related_object_id=str(obj.related_object_id) if obj.related_object_id else None,
        previous_state=obj.previous_state,
        new_state=obj.new_state,
        evidence=obj.evidence,
        impact=obj.impact,
        lifecycle_state=obj.lifecycle_state.value,
        provenance=obj.provenance.model_dump(),
        metadata_=obj.metadata,
    )


def record_to_event(record: EnterpriseEventRecord) -> EnterpriseEvent:
    return EnterpriseEvent(
        object_id=UUID(str(record.object_id)),
        event_type=EventType(record.event_type),
        title=record.title,
        description=record.description,
        domain=record.domain,
        owner=record.owner,
        actor=record.actor,
        related_object_id=UUID(str(record.related_object_id)) if record.related_object_id else None,
        previous_state=record.previous_state,
        new_state=record.new_state,
        evidence=record.evidence or [],
        impact=record.impact,
        lifecycle_state=LifecycleState(record.lifecycle_state),
        provenance=Provenance(**(record.provenance or {})),
        metadata=record.metadata_ or {},
        created_at=_timestamp(record.created_at),
        updated_at=_timestamp(record.updated_at),
    )
