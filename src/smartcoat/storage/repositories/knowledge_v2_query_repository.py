"""Read-only root-summary query repository for Knowledge Object v2."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, and_, asc, desc, exists, or_, select
from sqlalchemy.orm import Session

from smartcoat.domain.knowledge_query import (
    MAX_PAGE_SIZE,
    MIN_PAGE_SIZE,
    KnowledgeObjectV2CollectionItem,
    KnowledgeObjectV2CollectionOwner,
    KnowledgeObjectV2QueryRepositoryPage,
    KnowledgeQueryCursorPosition,
    KnowledgeQueryFilters,
    KnowledgeQuerySort,
)
from smartcoat.storage.database.knowledge_v2_models import (
    KnowledgeObjectV2ContextRecord,
    KnowledgeObjectV2Record,
    KnowledgeObjectV2TagRecord,
)


class KnowledgeObjectV2QueryRepository:
    """Bounded collection reads; this class exposes no persistence operation."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def query_page(
        self,
        *,
        organization_id: str,
        filters: KnowledgeQueryFilters,
        sort: KnowledgeQuerySort,
        page_size: int,
        position: KnowledgeQueryCursorPosition | None = None,
    ) -> KnowledgeObjectV2QueryRepositoryPage:
        if (
            isinstance(page_size, bool)
            or not isinstance(page_size, int)
            or not MIN_PAGE_SIZE <= page_size <= MAX_PAGE_SIZE
        ):
            raise ValueError(
                f"page_size must be an integer from {MIN_PAGE_SIZE} through {MAX_PAGE_SIZE}"
            )
        statement = self._build_statement(
            organization_id=organization_id,
            filters=filters,
            sort=sort,
            page_size=page_size,
            position=position,
        )
        rows = self._session.execute(statement).mappings().all()
        has_more = len(rows) > page_size
        selected_rows = rows[:page_size]
        items = tuple(self._item_from_row(row) for row in selected_rows)
        final_position = (
            KnowledgeQueryCursorPosition(
                timestamp=getattr(items[-1], sort.timestamp_field),
                object_id=items[-1].object_id,
            )
            if items
            else None
        )
        return KnowledgeObjectV2QueryRepositoryPage(
            items=items,
            has_more=has_more,
            final_position=final_position,
        )

    @staticmethod
    def _build_statement(
        *,
        organization_id: str,
        filters: KnowledgeQueryFilters,
        sort: KnowledgeQuerySort,
        page_size: int,
        position: KnowledgeQueryCursorPosition | None,
    ) -> Select[tuple[Any, ...]]:
        root = KnowledgeObjectV2Record
        statement = select(
            root.object_id,
            root.revision,
            root.lifecycle_state,
            root.title,
            root.knowledge_type,
            root.owner_id,
            root.owner_role,
            root.confidentiality,
            root.created_at,
            root.updated_at,
        ).where(
            root.organization_id == organization_id,
            root.contract_version == "2",
        )

        predicates: list[Any] = []
        if filters.knowledge_type is not None:
            predicates.append(root.knowledge_type == filters.knowledge_type.value)
        if filters.lifecycle_state is not None:
            predicates.append(root.lifecycle_state == filters.lifecycle_state.value)
        if filters.owner_id is not None:
            predicates.append(root.owner_id == filters.owner_id)
        if filters.created_from is not None:
            predicates.append(root.created_at >= filters.created_from)
        if filters.created_before is not None:
            predicates.append(root.created_at < filters.created_before)
        if filters.updated_from is not None:
            predicates.append(root.updated_at >= filters.updated_from)
        if filters.updated_before is not None:
            predicates.append(root.updated_at < filters.updated_before)

        for tag in filters.tags_all:
            predicates.append(
                exists(
                    select(1).where(
                        KnowledgeObjectV2TagRecord.organization_id == organization_id,
                        KnowledgeObjectV2TagRecord.object_id == root.object_id,
                        KnowledgeObjectV2TagRecord.tag == tag,
                    )
                ).correlate(root)
            )

        if filters.context is not None:
            context = filters.context
            context_predicates = [
                KnowledgeObjectV2ContextRecord.organization_id == organization_id,
                KnowledgeObjectV2ContextRecord.object_id == root.object_id,
                KnowledgeObjectV2ContextRecord.context_type == context.context_type.value,
                KnowledgeObjectV2ContextRecord.id_kind == context.id_kind.value,
                KnowledgeObjectV2ContextRecord.reference_id == context.reference_id,
            ]
            if context.source_system is not None:
                context_predicates.append(
                    KnowledgeObjectV2ContextRecord.source_system == context.source_system
                )
            if context.relationship_role is not None:
                context_predicates.append(
                    KnowledgeObjectV2ContextRecord.relationship_role == context.relationship_role
                )
            predicates.append(exists(select(1).where(*context_predicates)).correlate(root))

        if predicates:
            statement = statement.where(and_(*predicates))

        timestamp_column = getattr(root, sort.timestamp_field)
        direction = desc if sort.descending else asc
        if position is not None:
            comparator = (
                or_(
                    timestamp_column < position.timestamp,
                    and_(
                        timestamp_column == position.timestamp,
                        root.object_id < position.object_id,
                    ),
                )
                if sort.descending
                else or_(
                    timestamp_column > position.timestamp,
                    and_(
                        timestamp_column == position.timestamp,
                        root.object_id > position.object_id,
                    ),
                )
            )
            statement = statement.where(comparator)

        return statement.order_by(
            direction(timestamp_column),
            direction(root.object_id),
        ).limit(page_size + 1)

    @staticmethod
    def _item_from_row(row: Any) -> KnowledgeObjectV2CollectionItem:
        return KnowledgeObjectV2CollectionItem(
            object_id=row["object_id"],
            revision=row["revision"],
            lifecycle_state=row["lifecycle_state"],
            title=row["title"],
            knowledge_type=row["knowledge_type"],
            owner=KnowledgeObjectV2CollectionOwner(
                owner_id=row["owner_id"],
                role=row["owner_role"],
            ),
            confidentiality=row["confidentiality"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
