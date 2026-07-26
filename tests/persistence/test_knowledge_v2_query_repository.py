from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from smartcoat.domain.base import LifecycleState
from smartcoat.domain.context_references import ContextIdKind, ContextType
from smartcoat.domain.knowledge_objects import KnowledgeObjectType
from smartcoat.domain.knowledge_objects_v2 import ConfidentialityLevel
from smartcoat.domain.knowledge_query import (
    KnowledgeContextIdentityFilter,
    KnowledgeQueryCursorPosition,
    KnowledgeQueryFilters,
    KnowledgeQuerySort,
)
from smartcoat.storage.repositories.knowledge_v2_query_repository import (
    KnowledgeObjectV2QueryRepository,
)

NOW = datetime(2026, 7, 26, 15, 0, tzinfo=UTC)
OBJECT_ID = UUID("00000000-0000-0000-0000-000000000123")


class FakeMappingResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def mappings(self) -> FakeMappingResult:
        return self

    def all(self) -> list[dict[str, Any]]:
        return self._rows


class RecordingReadSession:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.statement: Any = None
        self.rows = rows or []

    def execute(self, statement: Any) -> FakeMappingResult:
        self.statement = statement
        return FakeMappingResult(self.rows)

    def commit(self) -> None:
        raise AssertionError("query repository must not commit")

    def flush(self) -> None:
        raise AssertionError("query repository must not flush")

    def add(self, _value: object) -> None:
        raise AssertionError("query repository must not add")

    def delete(self, _value: object) -> None:
        raise AssertionError("query repository must not delete")


def _row(
    object_id: UUID = OBJECT_ID,
    *,
    created_at: datetime = NOW,
    updated_at: datetime = NOW,
) -> dict[str, Any]:
    return {
        "object_id": object_id,
        "revision": 2,
        "lifecycle_state": LifecycleState.CAPTURED.value,
        "title": "Synthetic query row",
        "knowledge_type": KnowledgeObjectType.FINDING.value,
        "owner_id": "synthetic-owner",
        "owner_role": "reviewer",
        "confidentiality": ConfidentialityLevel.INTERNAL.value,
        "created_at": created_at,
        "updated_at": updated_at,
    }


def _capture(
    *,
    filters: KnowledgeQueryFilters | None = None,
    sort: KnowledgeQuerySort = KnowledgeQuerySort.UPDATED_AT_DESC,
    page_size: int = 7,
    position: KnowledgeQueryCursorPosition | None = None,
    rows: list[dict[str, Any]] | None = None,
) -> tuple[str, RecordingReadSession, object]:
    session = RecordingReadSession(rows)
    result = KnowledgeObjectV2QueryRepository(cast(Session, session)).query_page(
        organization_id="synthetic-org",
        filters=filters or KnowledgeQueryFilters(),
        sort=sort,
        page_size=page_size,
        position=position,
    )
    compiled = str(
        session.statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )
    return " ".join(compiled.split()), session, result


def test_repository_surface_is_read_only_and_single_purpose() -> None:
    public_methods = {
        name
        for name, value in vars(KnowledgeObjectV2QueryRepository).items()
        if not name.startswith("_") and callable(value)
    }
    assert public_methods == {"query_page"}


def test_every_query_is_organization_and_v2_scoped_with_bounded_limit() -> None:
    sql, _, _ = _capture(page_size=7)
    assert "knowledge_objects_v2.organization_id = 'synthetic-org'" in sql
    assert "knowledge_objects_v2.contract_version = '2'" in sql
    assert "LIMIT 8" in sql
    assert " OFFSET " not in f" {sql} "


@pytest.mark.parametrize("page_size", [False, 0, 101, 1.0])
def test_repository_defensively_rejects_out_of_contract_page_size(
    page_size: object,
) -> None:
    session = RecordingReadSession()
    with pytest.raises(ValueError, match="page_size"):
        KnowledgeObjectV2QueryRepository(cast(Session, session)).query_page(
            organization_id="synthetic-org",
            filters=KnowledgeQueryFilters(),
            sort=KnowledgeQuerySort.UPDATED_AT_DESC,
            page_size=page_size,  # type: ignore[arg-type]
        )
    assert session.statement is None


@pytest.mark.parametrize(
    ("sort", "expected_order"),
    [
        (
            KnowledgeQuerySort.UPDATED_AT_DESC,
            "ORDER BY knowledge_objects_v2.updated_at DESC, knowledge_objects_v2.object_id DESC",
        ),
        (
            KnowledgeQuerySort.UPDATED_AT_ASC,
            "ORDER BY knowledge_objects_v2.updated_at ASC, knowledge_objects_v2.object_id ASC",
        ),
        (
            KnowledgeQuerySort.CREATED_AT_DESC,
            "ORDER BY knowledge_objects_v2.created_at DESC, knowledge_objects_v2.object_id DESC",
        ),
        (
            KnowledgeQuerySort.CREATED_AT_ASC,
            "ORDER BY knowledge_objects_v2.created_at ASC, knowledge_objects_v2.object_id ASC",
        ),
    ],
)
def test_all_sorts_use_same_direction_uuid_tie_break(
    sort: KnowledgeQuerySort,
    expected_order: str,
) -> None:
    sql, _, _ = _capture(sort=sort)
    assert expected_order in sql


@pytest.mark.parametrize(
    ("sort", "timestamp_operator", "uuid_operator"),
    [
        (KnowledgeQuerySort.UPDATED_AT_DESC, "<", "<"),
        (KnowledgeQuerySort.CREATED_AT_DESC, "<", "<"),
        (KnowledgeQuerySort.UPDATED_AT_ASC, ">", ">"),
        (KnowledgeQuerySort.CREATED_AT_ASC, ">", ">"),
    ],
)
def test_keyset_predicate_matches_sort_direction(
    sort: KnowledgeQuerySort,
    timestamp_operator: str,
    uuid_operator: str,
) -> None:
    sql, _, _ = _capture(
        sort=sort,
        position=KnowledgeQueryCursorPosition(timestamp=NOW, object_id=OBJECT_ID),
    )
    field = sort.timestamp_field
    assert f"knowledge_objects_v2.{field} {timestamp_operator}" in sql
    assert f"knowledge_objects_v2.object_id {uuid_operator}" in sql
    assert f"knowledge_objects_v2.{field} =" in sql


def test_every_scalar_and_time_filter_is_combined_with_and() -> None:
    sql, _, _ = _capture(
        filters=KnowledgeQueryFilters(
            knowledge_type=KnowledgeObjectType.FINDING,
            lifecycle_state=LifecycleState.CAPTURED,
            owner_id="synthetic-owner",
            created_from=NOW - timedelta(days=2),
            created_before=NOW + timedelta(days=2),
            updated_from=NOW - timedelta(days=1),
            updated_before=NOW + timedelta(days=1),
        )
    )
    assert "knowledge_objects_v2.knowledge_type = 'finding'" in sql
    assert "knowledge_objects_v2.lifecycle_state = 'captured'" in sql
    assert "knowledge_objects_v2.owner_id = 'synthetic-owner'" in sql
    assert "knowledge_objects_v2.created_at >=" in sql
    assert "knowledge_objects_v2.created_at <" in sql
    assert "knowledge_objects_v2.updated_at >=" in sql
    assert "knowledge_objects_v2.updated_at <" in sql
    assert sql.count(" AND ") >= 8


def test_tags_all_uses_one_correlated_exists_per_tag_without_join() -> None:
    sql, _, _ = _capture(filters=KnowledgeQueryFilters(tags_all=("synthetic", "coating")))
    assert sql.count("EXISTS (SELECT 1") == 2
    assert "knowledge_object_v2_tags.tag = 'synthetic'" in sql
    assert "knowledge_object_v2_tags.tag = 'coating'" in sql
    assert sql.count("knowledge_object_v2_tags.organization_id = 'synthetic-org'") == 2
    assert " JOIN " not in f" {sql} "


def test_context_filter_uses_correlated_exists_and_omitted_role_means_any_role() -> None:
    sql, _, _ = _capture(
        filters=KnowledgeQueryFilters(
            context=KnowledgeContextIdentityFilter(
                context_type=ContextType.MATERIAL,
                id_kind=ContextIdKind.EXTERNAL,
                reference_id="material-42",
                source_system="synthetic-catalog",
            )
        )
    )
    assert "EXISTS (SELECT 1" in sql
    assert "knowledge_object_v2_context.organization_id = 'synthetic-org'" in sql
    assert "knowledge_object_v2_context.context_type = 'material'" in sql
    assert "knowledge_object_v2_context.id_kind = 'external'" in sql
    assert "knowledge_object_v2_context.reference_id = 'material-42'" in sql
    assert "knowledge_object_v2_context.source_system = 'synthetic-catalog'" in sql
    assert "relationship_role" not in sql
    assert " JOIN " not in f" {sql} "


def test_context_role_is_exact_after_domain_casefolding() -> None:
    sql, _, _ = _capture(
        filters=KnowledgeQueryFilters(
            context=KnowledgeContextIdentityFilter(
                context_type=ContextType.MATERIAL,
                id_kind=ContextIdKind.EXTERNAL,
                reference_id="material-42",
                source_system="synthetic-catalog",
                relationship_role=" Primary ",
            )
        )
    )
    assert "knowledge_object_v2_context.relationship_role = 'primary'" in sql


def test_only_approved_root_summary_columns_are_selected() -> None:
    _, session, _ = _capture()
    assert tuple(session.statement.selected_columns.keys()) == (
        "object_id",
        "revision",
        "lifecycle_state",
        "title",
        "knowledge_type",
        "owner_id",
        "owner_role",
        "confidentiality",
        "created_at",
        "updated_at",
    )


def test_page_size_plus_one_is_trimmed_and_position_uses_last_returned_item() -> None:
    rows = [_row(UUID(f"00000000-0000-0000-0000-{index:012d}")) for index in (3, 2, 1)]
    _, _, result = _capture(page_size=2, rows=rows)

    assert result.has_more is True
    assert tuple(item.object_id for item in result.items) == (
        rows[0]["object_id"],
        rows[1]["object_id"],
    )
    assert result.final_position.object_id == rows[1]["object_id"]
    assert result.final_position.timestamp == NOW


def test_empty_page_has_no_cursor_position() -> None:
    _, _, result = _capture(rows=[])
    assert result.items == ()
    assert result.has_more is False
    assert result.final_position is None


def test_repository_returns_detached_frozen_summaries_and_performs_no_write() -> None:
    sql, session, result = _capture(rows=[_row()])
    assert result.items[0].object_id == OBJECT_ID
    assert result.items[0].owner.owner_id == "synthetic-owner"
    assert "INSERT " not in sql
    assert "UPDATE " not in sql
    assert "DELETE " not in sql
    with pytest.raises(ValidationError):
        result.items[0].title = "mutated"

    assert session.statement is not None
