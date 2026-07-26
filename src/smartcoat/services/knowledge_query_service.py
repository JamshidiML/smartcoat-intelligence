"""Read-only Knowledge Object v2 collection orchestration."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from smartcoat.domain.knowledge_query import (
    KnowledgeObjectV2Page,
    KnowledgeObjectV2Query,
    KnowledgeQueryCursorCodec,
    knowledge_query_fingerprint,
)
from smartcoat.storage.repositories.knowledge_v2_query_repository import (
    KnowledgeObjectV2QueryRepository,
)

type QueryRepositoryFactory = Callable[[Session], KnowledgeObjectV2QueryRepository]


class KnowledgeObjectV2QueryService:
    """Validate, bind, and execute one bounded collection read."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        *,
        cursor_signing_key: bytes,
        repository_factory: QueryRepositoryFactory = KnowledgeObjectV2QueryRepository,
    ) -> None:
        self._session_factory = session_factory
        self._cursor_codec = KnowledgeQueryCursorCodec(cursor_signing_key)
        self._repository_factory = repository_factory

    def query(self, command: KnowledgeObjectV2Query) -> KnowledgeObjectV2Page:
        command = KnowledgeObjectV2Query.model_validate(command.model_dump(mode="python"))
        fingerprint = knowledge_query_fingerprint(
            organization_id=command.organization_id,
            filters=command.filters,
            sort=command.sort,
        )
        position = (
            self._cursor_codec.decode(
                command.cursor,
                expected_sort=command.sort,
                expected_query_fingerprint=fingerprint,
            )
            if command.cursor is not None
            else None
        )

        with self._session_factory() as session:
            result = self._repository_factory(session).query_page(
                organization_id=command.organization_id,
                filters=command.filters,
                sort=command.sort,
                page_size=command.page_size,
                position=position,
            )

        next_cursor = (
            self._cursor_codec.encode(
                sort=command.sort,
                position=result.final_position,
                query_fingerprint=fingerprint,
            )
            if result.has_more and result.final_position is not None
            else None
        )
        return KnowledgeObjectV2Page(
            items=result.items,
            returned_count=len(result.items),
            requested_page_size=command.page_size,
            has_more=result.has_more,
            next_cursor=next_cursor,
            applied_sort=command.sort,
        )
