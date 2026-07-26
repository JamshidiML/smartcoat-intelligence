"""Dedicated append-only persistence records for canonical Knowledge audit."""

from datetime import datetime
from uuid import UUID as PythonUUID
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Identity,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from smartcoat.storage.database.base import Base


class KnowledgeAuditEventRecord(Base):
    """Release 1.8 canonical audit row, independent of legacy Enterprise Events."""

    __tablename__ = "knowledge_audit_events_v2"
    __table_args__ = (
        CheckConstraint(
            "schema_version = '1'",
            name="ck_knowledge_audit_events_v2_schema",
        ),
        CheckConstraint(
            "event_family = 'enterprise_event'",
            name="ck_knowledge_audit_events_v2_family",
        ),
        CheckConstraint(
            "event_type IN "
            "('create', 'update', 'draft_delete', 'transition', "
            "'correction_request', 'reject', 'reopen', 'approve', 'deprecate')",
            name="ck_knowledge_audit_events_v2_type",
        ),
        CheckConstraint(
            "previous_lifecycle IS NULL OR previous_lifecycle IN "
            "('draft', 'captured', 'reviewed', 'validated', 'approved', "
            "'deprecated', 'rejected')",
            name="ck_knowledge_audit_events_v2_previous_lifecycle",
        ),
        CheckConstraint(
            "resulting_lifecycle IS NULL OR resulting_lifecycle IN "
            "('draft', 'captured', 'reviewed', 'validated', 'approved', "
            "'deprecated', 'rejected')",
            name="ck_knowledge_audit_events_v2_resulting_lifecycle",
        ),
        CheckConstraint(
            "(event_type = 'create' AND previous_revision IS NULL "
            "AND resulting_revision = 1) OR "
            "(event_type = 'draft_delete' AND previous_revision >= 1 "
            "AND resulting_revision IS NULL) OR "
            "(event_type NOT IN ('create', 'draft_delete') "
            "AND previous_revision >= 1 "
            "AND resulting_revision = previous_revision + 1)",
            name="ck_knowledge_audit_events_v2_revisions",
        ),
        CheckConstraint(
            "recorded_at >= occurred_at",
            name="ck_knowledge_audit_events_v2_timestamp_order",
        ),
        UniqueConstraint(
            "audit_sequence",
            name="uq_knowledge_audit_events_v2_sequence",
        ),
        UniqueConstraint(
            "organization_id",
            "object_id",
            "correlation_id",
            name="uq_knowledge_audit_events_v2_atomic_action",
        ),
        Index(
            "ix_knowledge_audit_events_v2_org_object_sequence",
            "organization_id",
            "object_id",
            "audit_sequence",
        ),
    )

    event_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    schema_version: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="1",
        server_default=text("'1'"),
    )
    event_family: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="enterprise_event",
        server_default=text("'enterprise_event'"),
    )
    organization_id: Mapped[str] = mapped_column(String(512), nullable=False)
    object_id: Mapped[PythonUUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    lifecycle_action: Mapped[str | None] = mapped_column(String(64))
    actor_id: Mapped[str] = mapped_column(String(512), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(128), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("clock_timestamp()"),
    )
    correlation_id: Mapped[PythonUUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    previous_lifecycle: Mapped[str | None] = mapped_column(String(32))
    resulting_lifecycle: Mapped[str | None] = mapped_column(String(32))
    previous_revision: Mapped[int | None] = mapped_column(Integer)
    resulting_revision: Mapped[int | None] = mapped_column(Integer)
    reason_or_note: Mapped[str] = mapped_column(Text, nullable=False)
    changed_fields_json: Mapped[str] = mapped_column(Text, nullable=False)
    audit_sequence: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        nullable=False,
    )
