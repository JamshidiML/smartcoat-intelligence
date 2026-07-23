from datetime import datetime
from uuid import UUID as PythonUUID
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from smartcoat.storage.database.base import Base


class KnowledgeObjectV2Record(Base):
    """Release 1.8 aggregate root; canonical domain objects stay outside the ORM."""

    __tablename__ = "knowledge_objects_v2"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "object_id",
            name="uq_knowledge_objects_v2_org_object",
        ),
        CheckConstraint("contract_version = '2'", name="ck_knowledge_objects_v2_contract"),
        CheckConstraint("revision >= 1", name="ck_knowledge_objects_v2_revision"),
        CheckConstraint(
            "lifecycle_state IN "
            "('draft', 'captured', 'reviewed', 'validated', 'approved', 'deprecated', 'rejected')",
            name="ck_knowledge_objects_v2_lifecycle",
        ),
        CheckConstraint(
            "updated_at >= created_at",
            name="ck_knowledge_objects_v2_timestamp_order",
        ),
        Index(
            "ix_knowledge_objects_v2_org_revision",
            "organization_id",
            "object_id",
            "revision",
        ),
        Index(
            "ix_knowledge_objects_v2_org_type",
            "organization_id",
            "knowledge_type",
        ),
        Index(
            "ix_knowledge_objects_v2_org_lifecycle",
            "organization_id",
            "lifecycle_state",
        ),
        Index(
            "ix_knowledge_objects_v2_org_owner",
            "organization_id",
            "owner_id",
        ),
        Index(
            "ix_knowledge_objects_v2_org_created",
            "organization_id",
            text("created_at DESC"),
            text("object_id DESC"),
        ),
        Index(
            "ix_knowledge_objects_v2_org_updated",
            "organization_id",
            text("updated_at DESC"),
            text("object_id DESC"),
        ),
    )

    object_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    organization_id: Mapped[str] = mapped_column(String(512), nullable=False)
    contract_version: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="2",
        server_default=text("'2'"),
    )
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    lifecycle_state: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="draft",
        server_default=text("'draft'"),
    )
    has_ever_left_draft: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    last_pre_deprecation_lifecycle: Mapped[str | None] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    knowledge_type: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(512), nullable=False)
    owner_role: Mapped[str] = mapped_column(String(128), nullable=False)
    confidentiality: Mapped[str] = mapped_column(String(32), nullable=False)
    uncertainty_json: Mapped[str | None] = mapped_column(Text)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class KnowledgeObjectV2TagRecord(Base):
    __tablename__ = "knowledge_object_v2_tags"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "object_id"],
            ["knowledge_objects_v2.organization_id", "knowledge_objects_v2.object_id"],
            name="fk_knowledge_object_v2_tags_source",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "organization_id",
            "object_id",
            "tag",
            name="uq_knowledge_object_v2_tags_value",
        ),
        Index("ix_knowledge_object_v2_tags_org_tag", "organization_id", "tag"),
    )

    organization_id: Mapped[str] = mapped_column(String(512), primary_key=True)
    object_id: Mapped[PythonUUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    tag: Mapped[str] = mapped_column(String(128), nullable=False)


class KnowledgeObjectV2EvidenceRecord(Base):
    __tablename__ = "knowledge_object_v2_evidence"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "object_id"],
            ["knowledge_objects_v2.organization_id", "knowledge_objects_v2.object_id"],
            name="fk_knowledge_object_v2_evidence_source",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "organization_id",
            "object_id",
            "evidence_id",
            name="uq_knowledge_object_v2_evidence_id",
        ),
        Index(
            "ix_knowledge_object_v2_evidence_identity",
            "organization_id",
            "evidence_id",
        ),
    )

    organization_id: Mapped[str] = mapped_column(String(512), primary_key=True)
    object_id: Mapped[PythonUUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    evidence_id: Mapped[str] = mapped_column(String(512), nullable=False)
    canonical_metadata_json: Mapped[str] = mapped_column(Text, nullable=False)


class KnowledgeObjectV2ProvenanceRecord(Base):
    __tablename__ = "knowledge_object_v2_provenance"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "object_id"],
            ["knowledge_objects_v2.organization_id", "knowledge_objects_v2.object_id"],
            name="fk_knowledge_object_v2_provenance_source",
            ondelete="CASCADE",
        ),
    )

    organization_id: Mapped[str] = mapped_column(String(512), primary_key=True)
    object_id: Mapped[PythonUUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    canonical_provenance_json: Mapped[str] = mapped_column(Text, nullable=False)


class KnowledgeObjectV2ContextRecord(Base):
    __tablename__ = "knowledge_object_v2_context"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "object_id"],
            ["knowledge_objects_v2.organization_id", "knowledge_objects_v2.object_id"],
            name="fk_knowledge_object_v2_context_source",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "organization_id",
            "object_id",
            "context_type",
            "reference_id",
            "relationship_role",
            name="uq_knowledge_object_v2_context_link",
            postgresql_nulls_not_distinct=True,
        ),
        Index(
            "ix_knowledge_object_v2_context_lookup",
            "organization_id",
            "context_type",
            "reference_id",
        ),
    )

    organization_id: Mapped[str] = mapped_column(String(512), primary_key=True)
    object_id: Mapped[PythonUUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    context_type: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(512), nullable=False)
    id_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    source_system: Mapped[str | None] = mapped_column(String(128))
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    version: Mapped[str | None] = mapped_column(String(128))
    relationship_role: Mapped[str | None] = mapped_column(String(128))
    source_reference: Mapped[str | None] = mapped_column(String(512))
    evidence_reference: Mapped[str | None] = mapped_column(String(512))
    attributes_json: Mapped[str] = mapped_column(Text, nullable=False)


class KnowledgeObjectV2KnowledgeRelationshipRecord(Base):
    __tablename__ = "knowledge_object_v2_knowledge_relationships"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "source_object_id"],
            ["knowledge_objects_v2.organization_id", "knowledge_objects_v2.object_id"],
            name="fk_knowledge_object_v2_knowledge_rel_source",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["organization_id", "target_object_id"],
            ["knowledge_objects_v2.organization_id", "knowledge_objects_v2.object_id"],
            name="fk_knowledge_object_v2_knowledge_rel_target",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "source_object_id",
            "target_object_id",
            "relationship_type",
            name="uq_knowledge_object_v2_knowledge_rel_identity",
        ),
        Index(
            "ix_knowledge_object_v2_knowledge_rel_inbound",
            "organization_id",
            "target_object_id",
        ),
    )

    organization_id: Mapped[str] = mapped_column(String(512), primary_key=True)
    source_object_id: Mapped[PythonUUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_object_id: Mapped[PythonUUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(128), nullable=False)
    target_revision: Mapped[int | None] = mapped_column(Integer)


class KnowledgeObjectV2DecisionRelationshipRecord(Base):
    __tablename__ = "knowledge_object_v2_decision_relationships"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "source_object_id"],
            ["knowledge_objects_v2.organization_id", "knowledge_objects_v2.object_id"],
            name="fk_knowledge_object_v2_decision_rel_source",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["target_decision_id"],
            ["decision_objects.object_id"],
            name="fk_knowledge_object_v2_decision_rel_target",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "organization_id",
            "source_object_id",
            "target_decision_id",
            "relationship_type",
            name="uq_knowledge_object_v2_decision_rel_identity",
        ),
        Index(
            "ix_knowledge_object_v2_decision_rel_target",
            "target_decision_id",
        ),
    )

    organization_id: Mapped[str] = mapped_column(String(512), primary_key=True)
    source_object_id: Mapped[PythonUUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_decision_id: Mapped[PythonUUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(128), nullable=False)
    target_revision: Mapped[int | None] = mapped_column(Integer)
