"""Add Release 1.8 Knowledge Object v2 persistence contracts."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_release_1_8_knowledge_v2"
down_revision: str | None = "0001_release_1_7_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_objects_v2",
        sa.Column("object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.String(length=512), nullable=False),
        sa.Column(
            "contract_version",
            sa.String(length=16),
            server_default="2",
            nullable=False,
        ),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column(
            "lifecycle_state",
            sa.String(length=32),
            server_default="draft",
            nullable=False,
        ),
        sa.Column(
            "has_ever_left_draft",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("last_pre_deprecation_lifecycle", sa.String(length=32), nullable=True),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("knowledge_type", sa.String(length=100), nullable=False),
        sa.Column("owner_id", sa.String(length=512), nullable=False),
        sa.Column("owner_role", sa.String(length=128), nullable=False),
        sa.Column("confidentiality", sa.String(length=32), nullable=False),
        sa.Column("uncertainty_json", sa.Text(), nullable=True),
        sa.Column("content_json", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("contract_version = '2'", name="ck_knowledge_objects_v2_contract"),
        sa.CheckConstraint("revision >= 1", name="ck_knowledge_objects_v2_revision"),
        sa.CheckConstraint(
            "lifecycle_state IN "
            "('draft', 'captured', 'reviewed', 'validated', 'approved', 'deprecated', 'rejected')",
            name="ck_knowledge_objects_v2_lifecycle",
        ),
        sa.CheckConstraint(
            "updated_at >= created_at",
            name="ck_knowledge_objects_v2_timestamp_order",
        ),
        sa.PrimaryKeyConstraint("object_id"),
        sa.UniqueConstraint(
            "organization_id",
            "object_id",
            name="uq_knowledge_objects_v2_org_object",
        ),
    )
    op.create_index(
        "ix_knowledge_objects_v2_org_revision",
        "knowledge_objects_v2",
        ["organization_id", "object_id", "revision"],
    )
    op.create_index(
        "ix_knowledge_objects_v2_org_type",
        "knowledge_objects_v2",
        ["organization_id", "knowledge_type"],
    )
    op.create_index(
        "ix_knowledge_objects_v2_org_lifecycle",
        "knowledge_objects_v2",
        ["organization_id", "lifecycle_state"],
    )
    op.create_index(
        "ix_knowledge_objects_v2_org_owner",
        "knowledge_objects_v2",
        ["organization_id", "owner_id"],
    )
    op.create_index(
        "ix_knowledge_objects_v2_org_created",
        "knowledge_objects_v2",
        ["organization_id", sa.text("created_at DESC"), sa.text("object_id DESC")],
    )
    op.create_index(
        "ix_knowledge_objects_v2_org_updated",
        "knowledge_objects_v2",
        ["organization_id", sa.text("updated_at DESC"), sa.text("object_id DESC")],
    )

    source_fk = ["organization_id", "object_id"]
    source_target = [
        "knowledge_objects_v2.organization_id",
        "knowledge_objects_v2.object_id",
    ]
    op.create_table(
        "knowledge_object_v2_tags",
        sa.Column("organization_id", sa.String(length=512), nullable=False),
        sa.Column("object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("tag", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(
            source_fk,
            source_target,
            name="fk_knowledge_object_v2_tags_source",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("organization_id", "object_id", "position"),
        sa.UniqueConstraint(
            "organization_id",
            "object_id",
            "tag",
            name="uq_knowledge_object_v2_tags_value",
        ),
    )
    op.create_index(
        "ix_knowledge_object_v2_tags_org_tag",
        "knowledge_object_v2_tags",
        ["organization_id", "tag"],
    )

    op.create_table(
        "knowledge_object_v2_evidence",
        sa.Column("organization_id", sa.String(length=512), nullable=False),
        sa.Column("object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("evidence_id", sa.String(length=512), nullable=False),
        sa.Column("canonical_metadata_json", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            source_fk,
            source_target,
            name="fk_knowledge_object_v2_evidence_source",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("organization_id", "object_id", "position"),
        sa.UniqueConstraint(
            "organization_id",
            "object_id",
            "evidence_id",
            name="uq_knowledge_object_v2_evidence_id",
        ),
    )
    op.create_index(
        "ix_knowledge_object_v2_evidence_identity",
        "knowledge_object_v2_evidence",
        ["organization_id", "evidence_id"],
    )

    op.create_table(
        "knowledge_object_v2_provenance",
        sa.Column("organization_id", sa.String(length=512), nullable=False),
        sa.Column("object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("canonical_provenance_json", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            source_fk,
            source_target,
            name="fk_knowledge_object_v2_provenance_source",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("organization_id", "object_id"),
    )

    op.create_table(
        "knowledge_object_v2_context",
        sa.Column("organization_id", sa.String(length=512), nullable=False),
        sa.Column("object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("context_type", sa.String(length=64), nullable=False),
        sa.Column("reference_id", sa.String(length=512), nullable=False),
        sa.Column("id_kind", sa.String(length=32), nullable=False),
        sa.Column("source_system", sa.String(length=128), nullable=True),
        sa.Column("display_name", sa.String(length=256), nullable=False),
        sa.Column("version", sa.String(length=128), nullable=True),
        sa.Column("relationship_role", sa.String(length=128), nullable=True),
        sa.Column("source_reference", sa.String(length=512), nullable=True),
        sa.Column("evidence_reference", sa.String(length=512), nullable=True),
        sa.Column("attributes_json", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            source_fk,
            source_target,
            name="fk_knowledge_object_v2_context_source",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("organization_id", "object_id", "position"),
        sa.UniqueConstraint(
            "organization_id",
            "object_id",
            "context_type",
            "reference_id",
            "relationship_role",
            name="uq_knowledge_object_v2_context_link",
            postgresql_nulls_not_distinct=True,
        ),
    )
    op.create_index(
        "ix_knowledge_object_v2_context_lookup",
        "knowledge_object_v2_context",
        ["organization_id", "context_type", "reference_id"],
    )

    op.create_table(
        "knowledge_object_v2_knowledge_relationships",
        sa.Column("organization_id", sa.String(length=512), nullable=False),
        sa.Column("source_object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("target_object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", sa.String(length=128), nullable=False),
        sa.Column("target_revision", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id", "source_object_id"],
            source_target,
            name="fk_knowledge_object_v2_knowledge_rel_source",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "target_object_id"],
            source_target,
            name="fk_knowledge_object_v2_knowledge_rel_target",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("organization_id", "source_object_id", "position"),
        sa.UniqueConstraint(
            "organization_id",
            "source_object_id",
            "target_object_id",
            "relationship_type",
            name="uq_knowledge_object_v2_knowledge_rel_identity",
        ),
    )
    op.create_index(
        "ix_knowledge_object_v2_knowledge_rel_inbound",
        "knowledge_object_v2_knowledge_relationships",
        ["organization_id", "target_object_id"],
    )

    op.create_table(
        "knowledge_object_v2_decision_relationships",
        sa.Column("organization_id", sa.String(length=512), nullable=False),
        sa.Column("source_object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("target_decision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", sa.String(length=128), nullable=False),
        sa.Column("target_revision", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id", "source_object_id"],
            source_target,
            name="fk_knowledge_object_v2_decision_rel_source",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_decision_id"],
            ["decision_objects.object_id"],
            name="fk_knowledge_object_v2_decision_rel_target",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("organization_id", "source_object_id", "position"),
        sa.UniqueConstraint(
            "organization_id",
            "source_object_id",
            "target_decision_id",
            "relationship_type",
            name="uq_knowledge_object_v2_decision_rel_identity",
        ),
    )
    op.create_index(
        "ix_knowledge_object_v2_decision_rel_target",
        "knowledge_object_v2_decision_relationships",
        ["target_decision_id"],
    )


def downgrade() -> None:
    op.drop_table("knowledge_object_v2_decision_relationships")
    op.drop_table("knowledge_object_v2_knowledge_relationships")
    op.drop_table("knowledge_object_v2_context")
    op.drop_table("knowledge_object_v2_provenance")
    op.drop_table("knowledge_object_v2_evidence")
    op.drop_table("knowledge_object_v2_tags")
    op.drop_table("knowledge_objects_v2")
