from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from smartcoat.storage.database.base import Base


class KnowledgeObjectRecord(Base):
    __tablename__ = "knowledge_objects"

    object_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    knowledge_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str | None] = mapped_column(String(255))
    owner: Mapped[str | None] = mapped_column(String(255))
    lifecycle_state: Mapped[str] = mapped_column(String(100), nullable=False, default="draft")
    evidence: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    related_entities: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    related_decisions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    provenance: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DecisionObjectRecord(Base):
    __tablename__ = "decision_objects"

    object_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    decision_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(100), nullable=False, default="draft")
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str | None] = mapped_column(String(255))
    owner: Mapped[str | None] = mapped_column(String(255))
    problem: Mapped[str | None] = mapped_column(Text)
    context: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    evidence: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    alternatives: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    recommendation: Mapped[str | None] = mapped_column(Text)
    rationale: Mapped[str | None] = mapped_column(Text)
    assumptions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    risks: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    outcome: Mapped[str | None] = mapped_column(Text)
    learning: Mapped[str | None] = mapped_column(Text)
    related_knowledge: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    lifecycle_state: Mapped[str] = mapped_column(String(100), nullable=False, default="draft")
    provenance: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EnterpriseEventRecord(Base):
    __tablename__ = "enterprise_events"

    object_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str | None] = mapped_column(String(255))
    owner: Mapped[str | None] = mapped_column(String(255))
    actor: Mapped[str | None] = mapped_column(String(255))
    related_object_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    previous_state: Mapped[dict | None] = mapped_column(JSONB)
    new_state: Mapped[dict | None] = mapped_column(JSONB)
    evidence: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    impact: Mapped[str | None] = mapped_column(Text)
    lifecycle_state: Mapped[str] = mapped_column(String(100), nullable=False, default="draft")
    provenance: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
