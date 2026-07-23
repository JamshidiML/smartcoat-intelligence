"""Bounded Release 1.7 schema baseline for clean and unversioned databases.

This migration describes the repository's current legacy schema. It is not
evidence that historic deployments were managed by Alembic.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_release_1_7_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _ensure_index(table_name: str, index_name: str, columns: list[str]) -> None:
    existing = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}
    if index_name not in existing:
        op.create_index(index_name, table_name, columns, unique=False)


def upgrade() -> None:
    existing = _table_names()
    if "knowledge_objects" not in existing:
        op.create_table(
            "knowledge_objects",
            sa.Column("object_id", postgresql.UUID(as_uuid=False), nullable=False),
            sa.Column("knowledge_type", sa.String(length=100), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("domain", sa.String(length=255), nullable=True),
            sa.Column("owner", sa.String(length=255), nullable=True),
            sa.Column(
                "lifecycle_state",
                sa.String(length=100),
                server_default="draft",
                nullable=False,
            ),
            sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column(
                "related_entities",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
            ),
            sa.Column(
                "related_decisions",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
            ),
            sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=True),
            sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
            sa.PrimaryKeyConstraint("object_id"),
        )
    _ensure_index("knowledge_objects", "idx_knowledge_objects_type", ["knowledge_type"])
    _ensure_index("knowledge_objects", "idx_knowledge_objects_domain", ["domain"])
    _ensure_index(
        "knowledge_objects",
        "idx_knowledge_objects_lifecycle_state",
        ["lifecycle_state"],
    )

    if "decision_objects" not in existing:
        op.create_table(
            "decision_objects",
            sa.Column("object_id", postgresql.UUID(as_uuid=False), nullable=False),
            sa.Column("decision_type", sa.String(length=100), nullable=False),
            sa.Column("status", sa.String(length=100), server_default="draft", nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("domain", sa.String(length=255), nullable=True),
            sa.Column("owner", sa.String(length=255), nullable=True),
            sa.Column("problem", sa.Text(), nullable=True),
            sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("alternatives", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("recommendation", sa.Text(), nullable=True),
            sa.Column("rationale", sa.Text(), nullable=True),
            sa.Column("assumptions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("risks", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=True),
            sa.Column("outcome", sa.Text(), nullable=True),
            sa.Column("learning", sa.Text(), nullable=True),
            sa.Column(
                "related_knowledge",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
            ),
            sa.Column(
                "lifecycle_state",
                sa.String(length=100),
                server_default="draft",
                nullable=False,
            ),
            sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
            sa.PrimaryKeyConstraint("object_id"),
        )
    _ensure_index("decision_objects", "idx_decision_objects_type", ["decision_type"])
    _ensure_index("decision_objects", "idx_decision_objects_status", ["status"])
    _ensure_index("decision_objects", "idx_decision_objects_domain", ["domain"])

    if "enterprise_events" not in existing:
        op.create_table(
            "enterprise_events",
            sa.Column("object_id", postgresql.UUID(as_uuid=False), nullable=False),
            sa.Column("event_type", sa.String(length=100), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("domain", sa.String(length=255), nullable=True),
            sa.Column("owner", sa.String(length=255), nullable=True),
            sa.Column("actor", sa.String(length=255), nullable=True),
            sa.Column("related_object_id", postgresql.UUID(as_uuid=False), nullable=True),
            sa.Column("previous_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("new_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("impact", sa.Text(), nullable=True),
            sa.Column(
                "lifecycle_state",
                sa.String(length=100),
                server_default="draft",
                nullable=False,
            ),
            sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
            sa.PrimaryKeyConstraint("object_id"),
        )
    _ensure_index("enterprise_events", "idx_enterprise_events_type", ["event_type"])
    _ensure_index(
        "enterprise_events",
        "idx_enterprise_events_related_object_id",
        ["related_object_id"],
    )
    _ensure_index(
        "enterprise_events",
        "idx_enterprise_events_created_at",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_table("enterprise_events")
    op.drop_table("decision_objects")
    op.drop_table("knowledge_objects")
