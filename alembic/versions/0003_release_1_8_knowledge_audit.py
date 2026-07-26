"""Add the Release 1.8 append-only Knowledge audit store."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003_release_1_8_knowledge_audit"
down_revision: str | None = "0002_release_1_8_knowledge_v2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_audit_events_v2",
        sa.Column(
            "event_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "schema_version",
            sa.String(length=16),
            server_default=sa.text("'1'"),
            nullable=False,
        ),
        sa.Column(
            "event_family",
            sa.String(length=64),
            server_default=sa.text("'enterprise_event'"),
            nullable=False,
        ),
        sa.Column("organization_id", sa.String(length=512), nullable=False),
        sa.Column(
            "object_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("lifecycle_action", sa.String(length=64), nullable=True),
        sa.Column("actor_id", sa.String(length=512), nullable=False),
        sa.Column("actor_role", sa.String(length=128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.Column(
            "correlation_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "replacement_object_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("previous_lifecycle", sa.String(length=32), nullable=True),
        sa.Column("resulting_lifecycle", sa.String(length=32), nullable=True),
        sa.Column("previous_revision", sa.Integer(), nullable=True),
        sa.Column("resulting_revision", sa.Integer(), nullable=True),
        sa.Column("reason_or_note", sa.Text(), nullable=False),
        sa.Column("changed_fields_json", sa.Text(), nullable=False),
        sa.Column(
            "audit_sequence",
            sa.BigInteger(),
            sa.Identity(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "schema_version = '1'",
            name="ck_knowledge_audit_events_v2_schema",
        ),
        sa.CheckConstraint(
            "event_family = 'enterprise_event'",
            name="ck_knowledge_audit_events_v2_family",
        ),
        sa.CheckConstraint(
            "event_type IN "
            "('create', 'update', 'draft_delete', 'transition', "
            "'correction_request', 'reject', 'reopen', 'approve', 'deprecate')",
            name="ck_knowledge_audit_events_v2_type",
        ),
        sa.CheckConstraint(
            "previous_lifecycle IS NULL OR previous_lifecycle IN "
            "('draft', 'captured', 'reviewed', 'validated', 'approved', "
            "'deprecated', 'rejected')",
            name="ck_knowledge_audit_events_v2_previous_lifecycle",
        ),
        sa.CheckConstraint(
            "resulting_lifecycle IS NULL OR resulting_lifecycle IN "
            "('draft', 'captured', 'reviewed', 'validated', 'approved', "
            "'deprecated', 'rejected')",
            name="ck_knowledge_audit_events_v2_resulting_lifecycle",
        ),
        sa.CheckConstraint(
            "(event_type = 'create' AND previous_revision IS NULL "
            "AND resulting_revision = 1) OR "
            "(event_type = 'draft_delete' AND previous_revision >= 1 "
            "AND resulting_revision IS NULL) OR "
            "(event_type NOT IN ('create', 'draft_delete') "
            "AND previous_revision >= 1 "
            "AND resulting_revision = previous_revision + 1)",
            name="ck_knowledge_audit_events_v2_revisions",
        ),
        sa.CheckConstraint(
            "recorded_at >= occurred_at",
            name="ck_knowledge_audit_events_v2_timestamp_order",
        ),
        sa.CheckConstraint(
            "replacement_object_id IS NULL OR "
            "(event_type = 'deprecate' "
            "AND lifecycle_action = 'deprecate_approved')",
            name="ck_knowledge_audit_events_v2_replacement",
        ),
        sa.PrimaryKeyConstraint("event_id"),
        sa.UniqueConstraint(
            "audit_sequence",
            name="uq_knowledge_audit_events_v2_sequence",
        ),
        sa.UniqueConstraint(
            "organization_id",
            "object_id",
            "correlation_id",
            name="uq_knowledge_audit_events_v2_atomic_action",
        ),
    )
    op.create_index(
        "ix_knowledge_audit_events_v2_org_object_sequence",
        "knowledge_audit_events_v2",
        ["organization_id", "object_id", "audit_sequence"],
    )
    op.execute(
        """
        CREATE FUNCTION reject_knowledge_audit_mutation_v2()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION
                'knowledge_audit_events_v2 is append-only: % is forbidden',
                TG_OP
                USING ERRCODE = '55000';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_knowledge_audit_events_v2_append_only
        BEFORE UPDATE OR DELETE ON knowledge_audit_events_v2
        FOR EACH ROW
        EXECUTE FUNCTION reject_knowledge_audit_mutation_v2()
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_knowledge_audit_events_v2_append_only
        ON knowledge_audit_events_v2
        """
    )
    op.drop_table("knowledge_audit_events_v2")
    op.execute("DROP FUNCTION IF EXISTS reject_knowledge_audit_mutation_v2()")
