from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from pydantic import ValidationError

from smartcoat.domain.base import LifecycleState
from smartcoat.domain.knowledge_objects import KnowledgeObjectType
from smartcoat.domain.knowledge_objects_v2 import ConfidentialityLevel
from smartcoat.domain.knowledge_query import (
    KnowledgeObjectV2CollectionItem,
    KnowledgeObjectV2CollectionOwner,
    KnowledgeObjectV2Query,
    KnowledgeObjectV2QueryRepositoryPage,
    KnowledgeQueryCursorError,
    KnowledgeQueryCursorPosition,
    KnowledgeQueryFilters,
    KnowledgeQuerySort,
)
from smartcoat.services.knowledge_query_service import KnowledgeObjectV2QueryService

SYNTHETIC_KEY = b"synthetic-t06-service-signing-key-0000000000000000"
NOW = datetime(2026, 7, 26, 14, 0, tzinfo=UTC)


def _item(
    object_id: str,
    *,
    created_at: datetime = NOW,
    updated_at: datetime = NOW,
) -> KnowledgeObjectV2CollectionItem:
    return KnowledgeObjectV2CollectionItem(
        object_id=UUID(object_id),
        revision=1,
        lifecycle_state=LifecycleState.DRAFT,
        title=f"Synthetic {object_id[-4:]}",
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        owner=KnowledgeObjectV2CollectionOwner(
            owner_id="synthetic-owner",
            role="knowledge_steward",
        ),
        confidentiality=ConfidentialityLevel.INTERNAL,
        created_at=created_at,
        updated_at=updated_at,
    )


ITEM_1 = _item("00000000-0000-0000-0000-000000000003")
ITEM_2 = _item("00000000-0000-0000-0000-000000000002")
ITEM_3 = _item("00000000-0000-0000-0000-000000000001")


def _result(
    items: tuple[KnowledgeObjectV2CollectionItem, ...],
    *,
    has_more: bool,
    sort: KnowledgeQuerySort = KnowledgeQuerySort.UPDATED_AT_DESC,
) -> KnowledgeObjectV2QueryRepositoryPage:
    last = items[-1] if items else None
    return KnowledgeObjectV2QueryRepositoryPage(
        items=items,
        has_more=has_more,
        final_position=(
            KnowledgeQueryCursorPosition(
                timestamp=getattr(last, sort.timestamp_field),
                object_id=last.object_id,
            )
            if last is not None
            else None
        ),
    )


class GuardedSession:
    def __init__(self) -> None:
        self.entered = False
        self.exited = False

    def __enter__(self) -> GuardedSession:
        self.entered = True
        return self

    def __exit__(self, *_args: object) -> None:
        self.exited = True

    def commit(self) -> None:
        raise AssertionError("query service must not commit")

    def flush(self) -> None:
        raise AssertionError("query service must not flush")

    def add(self, _value: object) -> None:
        raise AssertionError("query service must not add")

    def delete(self, _value: object) -> None:
        raise AssertionError("query service must not delete")


class SessionFactory:
    def __init__(self) -> None:
        self.calls = 0
        self.sessions: list[GuardedSession] = []

    def __call__(self) -> GuardedSession:
        self.calls += 1
        session = GuardedSession()
        self.sessions.append(session)
        return session


class StubRepository:
    def __init__(
        self,
        results: list[KnowledgeObjectV2QueryRepositoryPage],
    ) -> None:
        self.results = results
        self.calls: list[dict[str, Any]] = []

    def query_page(self, **kwargs: Any) -> KnowledgeObjectV2QueryRepositoryPage:
        self.calls.append(kwargs)
        return self.results.pop(0)


def _service(
    results: list[KnowledgeObjectV2QueryRepositoryPage],
) -> tuple[KnowledgeObjectV2QueryService, SessionFactory, StubRepository]:
    session_factory = SessionFactory()
    repository = StubRepository(results)
    service = KnowledgeObjectV2QueryService(
        session_factory,  # type: ignore[arg-type]
        cursor_signing_key=SYNTHETIC_KEY,
        repository_factory=lambda _session: repository,  # type: ignore[arg-type]
    )
    return service, session_factory, repository


def test_first_middle_and_final_pages_use_opaque_keyset_cursor() -> None:
    service, sessions, repository = _service(
        [
            _result((ITEM_1, ITEM_2), has_more=True),
            _result((ITEM_3,), has_more=False),
        ]
    )
    first = service.query(
        KnowledgeObjectV2Query(
            organization_id="synthetic-org",
            page_size=2,
        )
    )
    final = service.query(
        KnowledgeObjectV2Query(
            organization_id="synthetic-org",
            page_size=2,
            cursor=first.next_cursor,
        )
    )

    assert first.returned_count == 2
    assert first.has_more is True
    assert first.next_cursor is not None
    assert final.items == (ITEM_3,)
    assert final.has_more is False
    assert final.next_cursor is None
    assert sessions.calls == 2
    assert all(session.entered and session.exited for session in sessions.sessions)
    assert repository.calls[0]["position"] is None
    assert repository.calls[1]["position"] == KnowledgeQueryCursorPosition(
        timestamp=ITEM_2.updated_at,
        object_id=ITEM_2.object_id,
    )


def test_page_size_plus_one_detection_is_repository_owned_and_size_can_change() -> None:
    service, _, repository = _service(
        [
            _result((ITEM_1,), has_more=True),
            _result((ITEM_2, ITEM_3), has_more=False),
        ]
    )
    first = service.query(KnowledgeObjectV2Query(organization_id="synthetic-org", page_size=1))
    second = service.query(
        KnowledgeObjectV2Query(
            organization_id="synthetic-org",
            page_size=50,
            cursor=first.next_cursor,
        )
    )

    assert repository.calls[0]["page_size"] == 1
    assert repository.calls[1]["page_size"] == 50
    assert second.requested_page_size == 50
    assert second.returned_count == 2


@pytest.mark.parametrize("sort", list(KnowledgeQuerySort))
def test_all_sort_modes_reach_repository_and_bind_cursor(
    sort: KnowledgeQuerySort,
) -> None:
    timestamp = NOW + timedelta(minutes=1)
    item = _item(
        "00000000-0000-0000-0000-000000000010",
        created_at=NOW,
        updated_at=timestamp,
    )
    service, _, repository = _service([_result((item,), has_more=True, sort=sort)])
    page = service.query(
        KnowledgeObjectV2Query(
            organization_id="synthetic-org",
            sort=sort,
            page_size=1,
        )
    )

    assert repository.calls[0]["sort"] is sort
    assert page.applied_sort is sort
    assert page.next_cursor is not None


def test_repository_receives_normalized_filters() -> None:
    service, _, repository = _service([_result((), has_more=False)])
    service.query(
        KnowledgeObjectV2Query(
            organization_id=" synthetic-org ",
            filters={
                "owner_id": " synthetic-owner ",
                "tags_all": ["synthetic", "coating"],
            },
        )
    )

    assert repository.calls[0]["organization_id"] == "synthetic-org"
    assert repository.calls[0]["filters"] == KnowledgeQueryFilters(
        owner_id="synthetic-owner",
        tags_all=("synthetic", "coating"),
    )


def test_invalid_cursor_is_rejected_before_session_or_repository_creation() -> None:
    service, sessions, repository = _service([_result((), has_more=False)])
    with pytest.raises(KnowledgeQueryCursorError) as captured:
        service.query(
            KnowledgeObjectV2Query(
                organization_id="synthetic-org",
                cursor="malformed",
            )
        )

    assert captured.value.code == "knowledge_query_cursor_malformed"
    assert sessions.calls == 0
    assert repository.calls == []


def test_service_revalidates_bypass_constructed_command_before_opening_session() -> None:
    service, sessions, repository = _service([_result((), has_more=False)])
    bypassed = KnowledgeObjectV2Query.model_construct(
        organization_id=" ",
        filters=KnowledgeQueryFilters(),
        sort=KnowledgeQuerySort.UPDATED_AT_DESC,
        page_size=1000,
        cursor=None,
    )
    with pytest.raises(ValidationError):
        service.query(bypassed)

    assert sessions.calls == 0
    assert repository.calls == []


def test_cursor_is_bound_to_organization_filters_and_sort() -> None:
    service, sessions, repository = _service([_result((ITEM_1,), has_more=True)])
    first = service.query(
        KnowledgeObjectV2Query(
            organization_id="synthetic-org",
            filters=KnowledgeQueryFilters(tags_all=("synthetic",)),
            page_size=1,
        )
    )
    assert first.next_cursor is not None

    mismatches = (
        KnowledgeObjectV2Query(
            organization_id="other-org",
            filters=KnowledgeQueryFilters(tags_all=("synthetic",)),
            cursor=first.next_cursor,
        ),
        KnowledgeObjectV2Query(
            organization_id="synthetic-org",
            filters=KnowledgeQueryFilters(tags_all=("other",)),
            cursor=first.next_cursor,
        ),
        KnowledgeObjectV2Query(
            organization_id="synthetic-org",
            filters=KnowledgeQueryFilters(tags_all=("synthetic",)),
            sort=KnowledgeQuerySort.CREATED_AT_DESC,
            cursor=first.next_cursor,
        ),
    )
    for command in mismatches:
        with pytest.raises(KnowledgeQueryCursorError) as captured:
            service.query(command)
        assert captured.value.code == "knowledge_query_cursor_query_mismatch"

    assert sessions.calls == 1
    assert len(repository.calls) == 1


def test_true_empty_result_has_consistent_metadata() -> None:
    service, _, _ = _service([_result((), has_more=False)])
    page = service.query(KnowledgeObjectV2Query(organization_id="synthetic-org", page_size=100))
    assert page.items == ()
    assert page.returned_count == 0
    assert page.has_more is False
    assert page.next_cursor is None


def test_query_service_has_no_uow_audit_or_write_collaborator() -> None:
    service, sessions, repository = _service([_result((ITEM_1,), has_more=False)])
    page = service.query(KnowledgeObjectV2Query(organization_id="synthetic-org"))

    assert page.items == (ITEM_1,)
    assert set(vars(service)) == {
        "_session_factory",
        "_cursor_codec",
        "_repository_factory",
    }
    assert set(repository.calls[0]) == {
        "organization_id",
        "filters",
        "sort",
        "page_size",
        "position",
    }
    assert sessions.sessions[0].exited is True
