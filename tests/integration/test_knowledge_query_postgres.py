from __future__ import annotations

import base64
import hmac
import json
import os
import re
from collections.abc import Generator, Iterable, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from sqlalchemy import Engine, create_engine, event, inspect, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from alembic import command
from smartcoat.domain.base import LifecycleState
from smartcoat.domain.context_references import ContextIdKind, ContextType
from smartcoat.domain.knowledge_objects import KnowledgeObjectType
from smartcoat.domain.knowledge_objects_v2 import ConfidentialityLevel
from smartcoat.domain.knowledge_query import (
    KnowledgeContextIdentityFilter,
    KnowledgeObjectV2Query,
    KnowledgeQueryCursorError,
    KnowledgeQueryFilters,
    KnowledgeQuerySort,
)
from smartcoat.services.knowledge_query_service import KnowledgeObjectV2QueryService
from smartcoat.storage.database.knowledge_v2_models import (
    KnowledgeObjectV2ContextRecord,
    KnowledgeObjectV2Record,
    KnowledgeObjectV2TagRecord,
)
from smartcoat.storage.database.models import EnterpriseEventRecord, KnowledgeObjectRecord
from smartcoat.storage.repositories.knowledge_v2_query_repository import (
    KnowledgeObjectV2QueryRepository,
)

LIVE_POSTGRES_OPT_IN = "true"
TEST_SCHEMA_PATTERN = re.compile(r"^smartcoat_test_[a-z0-9_]+$")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_KEY = b"synthetic-t06-live-signing-key-000000000000000000"
BASE_TIME = datetime(2026, 7, 26, 10, 0, tzinfo=UTC)


def _require_live_postgres(database_url: str | None, opt_in: str | None) -> str:
    if opt_in != LIVE_POSTGRES_OPT_IN:
        raise RuntimeError(
            "Refusing T06 live PostgreSQL execution without explicit opt-in: "
            "SMARTCOAT_RUN_LIVE_POSTGRES_TESTS=true."
        )
    if not database_url:
        raise RuntimeError("SMARTCOAT_TEST_DATABASE_URL is required.")
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise RuntimeError("T06 live tests require PostgreSQL.")
    if url.host not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("T06 live tests accept only a localhost PostgreSQL target.")
    if not (url.database or "").startswith("smartcoat_test"):
        raise RuntimeError("T06 live tests require a database name beginning with smartcoat_test.")
    return database_url


def _schema_name() -> str:
    return f"smartcoat_test_t06_{uuid4().hex[:12]}"


def _assert_schema_name(schema_name: str) -> None:
    if TEST_SCHEMA_PATTERN.fullmatch(schema_name) is None:
        raise RuntimeError("unsafe T06 test schema name")


def _drop_schema_and_assert_absent(engine: Engine, schema_name: str) -> None:
    _assert_schema_name(schema_name)
    with engine.begin() as connection:
        connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
    with engine.connect() as connection:
        remaining = connection.scalar(
            text("SELECT count(*) FROM pg_namespace WHERE nspname = :schema_name"),
            {"schema_name": schema_name},
        )
    assert remaining == 0


@contextmanager
def _alembic_schema(schema_name: str) -> Generator[None, None, None]:
    original = os.environ.get("SMARTCOAT_ALEMBIC_SCHEMA")
    os.environ["SMARTCOAT_ALEMBIC_SCHEMA"] = schema_name
    try:
        yield
    finally:
        if original is None:
            os.environ.pop("SMARTCOAT_ALEMBIC_SCHEMA", None)
        else:
            os.environ["SMARTCOAT_ALEMBIC_SCHEMA"] = original


def _alembic_config(database_url: str) -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _run_upgrade(database_url: str, schema_name: str) -> None:
    with _alembic_schema(schema_name):
        command.upgrade(_alembic_config(database_url), "head")


def _schema_engine(database_url: str, schema_name: str) -> Engine:
    return create_engine(
        database_url,
        poolclass=NullPool,
        connect_args={"options": f"-csearch_path={schema_name}"},
    )


@pytest.fixture(scope="session")
def live_database_url() -> str:
    database_url = os.getenv("SMARTCOAT_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set SMARTCOAT_TEST_DATABASE_URL for T06 PostgreSQL tests.")
    return _require_live_postgres(
        database_url,
        os.getenv("SMARTCOAT_RUN_LIVE_POSTGRES_TESTS"),
    )


@pytest.fixture(scope="module")
def migrated_store(
    live_database_url: str,
) -> Generator[tuple[Engine, sessionmaker[Session]], None, None]:
    schema_name = _schema_name()
    admin_engine = create_engine(live_database_url, poolclass=NullPool)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
    _run_upgrade(live_database_url, schema_name)
    engine = _schema_engine(live_database_url, schema_name)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    try:
        yield engine, factory
    finally:
        engine.dispose()
        _drop_schema_and_assert_absent(admin_engine, schema_name)
        admin_engine.dispose()


def _uuid(value: int) -> UUID:
    return UUID(int=value)


def _insert_object(
    factory: sessionmaker[Session],
    *,
    object_id: UUID,
    organization_id: str,
    created_at: datetime,
    updated_at: datetime | None = None,
    knowledge_type: KnowledgeObjectType = KnowledgeObjectType.OBSERVATION,
    lifecycle_state: LifecycleState = LifecycleState.DRAFT,
    owner_id: str = "synthetic-owner",
    tags: Sequence[str] = (),
    context_reference_id: str | None = None,
    context_role: str | None = None,
) -> None:
    root = KnowledgeObjectV2Record(
        object_id=object_id,
        organization_id=organization_id,
        contract_version="2",
        revision=1,
        lifecycle_state=lifecycle_state.value,
        has_ever_left_draft=lifecycle_state is not LifecycleState.DRAFT,
        last_pre_deprecation_lifecycle=None,
        title=f"Synthetic object {object_id}",
        description=None,
        knowledge_type=knowledge_type.value,
        owner_id=owner_id,
        owner_role="knowledge_steward",
        confidentiality=ConfidentialityLevel.INTERNAL.value,
        uncertainty_json=None,
        content_json="{}",
        created_at=created_at,
        updated_at=updated_at or created_at,
    )
    with factory() as session:
        session.add(root)
        session.flush()
        session.add_all(
            [
                KnowledgeObjectV2TagRecord(
                    organization_id=organization_id,
                    object_id=object_id,
                    position=position,
                    tag=tag,
                )
                for position, tag in enumerate(tags)
            ]
        )
        if context_reference_id is not None:
            session.add(
                KnowledgeObjectV2ContextRecord(
                    organization_id=organization_id,
                    object_id=object_id,
                    position=0,
                    context_type=ContextType.MATERIAL.value,
                    reference_id=context_reference_id,
                    id_kind=ContextIdKind.EXTERNAL.value,
                    source_system="synthetic-catalog",
                    display_name="Synthetic material",
                    version=None,
                    relationship_role=context_role,
                    source_reference=None,
                    evidence_reference=None,
                    attributes_json="{}",
                )
            )
        session.commit()


def _service(factory: sessionmaker[Session]) -> KnowledgeObjectV2QueryService:
    return KnowledgeObjectV2QueryService(
        factory,
        cursor_signing_key=SYNTHETIC_KEY,
    )


def _query_ids(
    service: KnowledgeObjectV2QueryService,
    *,
    organization_id: str,
    filters: KnowledgeQueryFilters | None = None,
    sort: KnowledgeQuerySort = KnowledgeQuerySort.UPDATED_AT_DESC,
) -> tuple[UUID, ...]:
    page = service.query(
        KnowledgeObjectV2Query(
            organization_id=organization_id,
            filters=filters or KnowledgeQueryFilters(),
            sort=sort,
            page_size=100,
        )
    )
    assert page.next_cursor is None
    return tuple(item.object_id for item in page.items)


def _traverse(
    service: KnowledgeObjectV2QueryService,
    *,
    organization_id: str,
    sort: KnowledgeQuerySort,
    page_sizes: Sequence[int],
) -> tuple[tuple[UUID, ...], str | None]:
    cursor: str | None = None
    collected: list[UUID] = []
    page_index = 0
    while True:
        page = service.query(
            KnowledgeObjectV2Query(
                organization_id=organization_id,
                sort=sort,
                page_size=page_sizes[page_index % len(page_sizes)],
                cursor=cursor,
            )
        )
        collected.extend(item.object_id for item in page.items)
        cursor = page.next_cursor
        page_index += 1
        if cursor is None:
            return tuple(collected), cursor


def _sorted_ids(
    rows: Iterable[tuple[UUID, datetime, datetime]],
    sort: KnowledgeQuerySort,
) -> tuple[UUID, ...]:
    timestamp_index = 2 if sort.timestamp_field == "updated_at" else 1
    ordered = sorted(
        rows,
        key=lambda row: (row[timestamp_index], row[0]),
        reverse=sort.descending,
    )
    return tuple(row[0] for row in ordered)


def test_live_target_guardrails_reject_unsafe_inputs() -> None:
    with pytest.raises(RuntimeError, match="opt-in"):
        _require_live_postgres("postgresql+psycopg://localhost/smartcoat_test", None)
    with pytest.raises(RuntimeError, match="localhost"):
        _require_live_postgres(
            "postgresql+psycopg://example.com/smartcoat_test",
            LIVE_POSTGRES_OPT_IN,
        )
    with pytest.raises(RuntimeError, match="beginning with smartcoat_test"):
        _require_live_postgres(
            "postgresql+psycopg://localhost/smartcoat",
            LIVE_POSTGRES_OPT_IN,
        )


def test_unchanged_traversal_all_sorts_equal_timestamps_and_page_size_changes(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    organization_id = "synthetic-traversal-org"
    rows: list[tuple[UUID, datetime, datetime]] = []
    for offset in range(13):
        object_id = _uuid(1000 + offset)
        created_at = BASE_TIME + timedelta(minutes=offset // 2)
        updated_at = BASE_TIME + timedelta(hours=1, minutes=(12 - offset) // 2)
        rows.append((object_id, created_at, updated_at))
        _insert_object(
            factory,
            object_id=object_id,
            organization_id=organization_id,
            created_at=created_at,
            updated_at=updated_at,
        )

    service = _service(factory)
    for sort in KnowledgeQuerySort:
        traversed, final_cursor = _traverse(
            service,
            organization_id=organization_id,
            sort=sort,
            page_sizes=(2, 4, 3),
        )
        assert final_cursor is None
        assert len(traversed) == 13
        assert len(set(traversed)) == 13
        assert traversed == _sorted_ids(rows, sort)


def test_individual_filters_and_half_open_time_boundaries(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    organization_id = "synthetic-filter-org"
    first, second, third = _uuid(2001), _uuid(2002), _uuid(2003)
    _insert_object(
        factory,
        object_id=first,
        organization_id=organization_id,
        created_at=BASE_TIME,
        updated_at=BASE_TIME + timedelta(days=3),
        knowledge_type=KnowledgeObjectType.FINDING,
        lifecycle_state=LifecycleState.CAPTURED,
        owner_id="owner-a",
        tags=("red", "blue"),
        context_reference_id="material-42",
        context_role="primary",
    )
    _insert_object(
        factory,
        object_id=second,
        organization_id=organization_id,
        created_at=BASE_TIME + timedelta(days=1),
        updated_at=BASE_TIME + timedelta(days=2),
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        lifecycle_state=LifecycleState.DRAFT,
        owner_id="owner-b",
        tags=("red",),
        context_reference_id="material-42",
        context_role=None,
    )
    _insert_object(
        factory,
        object_id=third,
        organization_id=organization_id,
        created_at=BASE_TIME + timedelta(days=2),
        updated_at=BASE_TIME + timedelta(days=4),
        knowledge_type=KnowledgeObjectType.FINDING,
        lifecycle_state=LifecycleState.REVIEWED,
        owner_id="owner-a",
        tags=("blue",),
        context_reference_id="material-99",
        context_role="secondary",
    )
    service = _service(factory)

    cases = (
        (KnowledgeQueryFilters(knowledge_type=KnowledgeObjectType.FINDING), {first, third}),
        (KnowledgeQueryFilters(lifecycle_state=LifecycleState.CAPTURED), {first}),
        (KnowledgeQueryFilters(owner_id="owner-b"), {second}),
        (KnowledgeQueryFilters(tags_all=("red",)), {first, second}),
        (
            KnowledgeQueryFilters(
                context=KnowledgeContextIdentityFilter(
                    context_type=ContextType.MATERIAL,
                    id_kind=ContextIdKind.EXTERNAL,
                    reference_id="material-42",
                    source_system="synthetic-catalog",
                )
            ),
            {first, second},
        ),
        (KnowledgeQueryFilters(created_from=BASE_TIME + timedelta(days=1)), {second, third}),
        (KnowledgeQueryFilters(created_before=BASE_TIME + timedelta(days=1)), {first}),
        (KnowledgeQueryFilters(updated_from=BASE_TIME + timedelta(days=3)), {first, third}),
        (KnowledgeQueryFilters(updated_before=BASE_TIME + timedelta(days=3)), {second}),
    )
    for filters, expected in cases:
        assert (
            set(
                _query_ids(
                    service,
                    organization_id=organization_id,
                    filters=filters,
                )
            )
            == expected
        )


def test_combined_filters_have_and_all_tag_and_exact_context_semantics(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    organization_id = "synthetic-combined-org"
    one, two, three = _uuid(3001), _uuid(3002), _uuid(3003)
    for object_id, lifecycle, owner, tags, reference, role, offset in (
        (
            one,
            LifecycleState.CAPTURED,
            "owner-a",
            ("red", "blue"),
            "material-42",
            "primary",
            0,
        ),
        (
            two,
            LifecycleState.CAPTURED,
            "owner-b",
            ("red",),
            "material-42",
            None,
            1,
        ),
        (
            three,
            LifecycleState.REVIEWED,
            "owner-a",
            ("blue", "green"),
            "material-99",
            "secondary",
            2,
        ),
    ):
        _insert_object(
            factory,
            object_id=object_id,
            organization_id=organization_id,
            created_at=BASE_TIME + timedelta(days=offset),
            updated_at=BASE_TIME + timedelta(days=offset, hours=1),
            knowledge_type=KnowledgeObjectType.FINDING,
            lifecycle_state=lifecycle,
            owner_id=owner,
            tags=tags,
            context_reference_id=reference,
            context_role=role,
        )
    service = _service(factory)
    context_any_role = KnowledgeContextIdentityFilter(
        context_type=ContextType.MATERIAL,
        id_kind=ContextIdKind.EXTERNAL,
        reference_id="material-42",
        source_system="synthetic-catalog",
    )

    cases = (
        (
            KnowledgeQueryFilters(
                knowledge_type=KnowledgeObjectType.FINDING,
                lifecycle_state=LifecycleState.CAPTURED,
            ),
            {one, two},
        ),
        (KnowledgeQueryFilters(owner_id="owner-a", tags_all=("blue",)), {one, three}),
        (KnowledgeQueryFilters(tags_all=("red", "blue")), {one}),
        (
            KnowledgeQueryFilters(
                context=context_any_role,
                lifecycle_state=LifecycleState.CAPTURED,
            ),
            {one, two},
        ),
        (
            KnowledgeQueryFilters(
                knowledge_type=KnowledgeObjectType.FINDING,
                tags_all=("red",),
                created_from=BASE_TIME,
                created_before=BASE_TIME + timedelta(days=1),
            ),
            {one},
        ),
        (KnowledgeQueryFilters(owner_id="nobody", tags_all=("absent",)), set()),
    )
    for filters, expected in cases:
        assert (
            set(
                _query_ids(
                    service,
                    organization_id=organization_id,
                    filters=filters,
                )
            )
            == expected
        )

    role_specific = KnowledgeQueryFilters(
        context=context_any_role.model_copy(update={"relationship_role": "primary"})
    )
    assert _query_ids(
        service,
        organization_id=organization_id,
        filters=role_specific,
    ) == (one,)


def test_organization_isolation_no_audit_no_write_and_legacy_exclusion(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    engine, factory = migrated_store
    organization_id = "synthetic-isolation-org"
    own_ids = (_uuid(4001), _uuid(4002))
    foreign_id = _uuid(4003)
    for offset, object_id in enumerate(own_ids):
        _insert_object(
            factory,
            object_id=object_id,
            organization_id=organization_id,
            created_at=BASE_TIME + timedelta(minutes=offset),
            tags=("synthetic",),
            context_reference_id="material-isolation",
        )
    _insert_object(
        factory,
        object_id=foreign_id,
        organization_id="synthetic-other-org",
        created_at=BASE_TIME + timedelta(days=1),
        tags=("synthetic",),
    )
    legacy_id, event_id = _uuid(4010), _uuid(4011)
    with factory() as session:
        session.add(
            KnowledgeObjectRecord(
                object_id=str(legacy_id),
                knowledge_type=KnowledgeObjectType.OBSERVATION.value,
                title="Synthetic legacy row",
                evidence=[],
                related_entities=[],
                related_decisions=[],
                tags=[],
                content={},
                provenance={},
                metadata_={},
            )
        )
        session.add(
            EnterpriseEventRecord(
                object_id=str(event_id),
                event_type="synthetic",
                title="Synthetic legacy event",
                evidence=[],
                provenance={},
                metadata_={},
            )
        )
        session.commit()

    with factory() as session:
        before_root = tuple(
            session.execute(
                text(
                    "SELECT object_id, revision, xmin::text "
                    "FROM knowledge_objects_v2 WHERE organization_id = :organization_id "
                    "ORDER BY object_id"
                ),
                {"organization_id": organization_id},
            ).all()
        )
        before_children = tuple(
            session.execute(
                text(
                    "SELECT object_id, position, xmin::text "
                    "FROM knowledge_object_v2_tags WHERE organization_id = :organization_id "
                    "ORDER BY object_id, position"
                ),
                {"organization_id": organization_id},
            ).all()
        )
        before_audits = session.scalar(text("SELECT count(*) FROM knowledge_audit_events_v2"))

    captured_sql: list[tuple[str, object]] = []

    def capture_statement(
        _connection: object,
        _cursor: object,
        statement: str,
        parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        if "knowledge_objects_v2" in statement:
            captured_sql.append((statement, parameters))

    event.listen(engine, "before_cursor_execute", capture_statement)
    try:
        service = _service(factory)
        first_page = service.query(
            KnowledgeObjectV2Query(
                organization_id=organization_id,
                page_size=1,
            )
        )
        all_ids = _query_ids(service, organization_id=organization_id)
    finally:
        event.remove(engine, "before_cursor_execute", capture_statement)

    assert set(all_ids) == set(own_ids)
    assert foreign_id not in all_ids
    assert legacy_id not in all_ids
    assert event_id not in all_ids
    assert first_page.next_cursor is not None
    assert captured_sql
    assert all(" LIMIT " in statement.upper() for statement, _ in captured_sql)
    assert all(
        not any(keyword in statement.upper() for keyword in ("INSERT ", "UPDATE ", "DELETE "))
        for statement, _ in captured_sql
    )

    with pytest.raises(KnowledgeQueryCursorError) as captured:
        service.query(
            KnowledgeObjectV2Query(
                organization_id="synthetic-other-org",
                page_size=1,
                cursor=first_page.next_cursor,
            )
        )
    assert captured.value.code == "knowledge_query_cursor_query_mismatch"

    with factory() as session:
        after_root = tuple(
            session.execute(
                text(
                    "SELECT object_id, revision, xmin::text "
                    "FROM knowledge_objects_v2 WHERE organization_id = :organization_id "
                    "ORDER BY object_id"
                ),
                {"organization_id": organization_id},
            ).all()
        )
        after_children = tuple(
            session.execute(
                text(
                    "SELECT object_id, position, xmin::text "
                    "FROM knowledge_object_v2_tags WHERE organization_id = :organization_id "
                    "ORDER BY object_id, position"
                ),
                {"organization_id": organization_id},
            ).all()
        )
        after_audits = session.scalar(text("SELECT count(*) FROM knowledge_audit_events_v2"))
    assert after_root == before_root
    assert after_children == before_children
    assert after_audits == before_audits


def test_created_sort_live_insert_and_delete_match_keyset_contract(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    organization_id = "synthetic-created-change-org"
    original_ids = tuple(_uuid(5000 + offset) for offset in range(6))
    for offset, object_id in enumerate(original_ids):
        _insert_object(
            factory,
            object_id=object_id,
            organization_id=organization_id,
            created_at=BASE_TIME + timedelta(minutes=offset),
        )
    service = _service(factory)
    first = service.query(
        KnowledgeObjectV2Query(
            organization_id=organization_id,
            sort=KnowledgeQuerySort.CREATED_AT_DESC,
            page_size=2,
        )
    )
    assert first.next_cursor is not None
    returned = tuple(item.object_id for item in first.items)

    inserted_before_cursor = _uuid(5099)
    _insert_object(
        factory,
        object_id=inserted_before_cursor,
        organization_id=organization_id,
        created_at=BASE_TIME + timedelta(hours=1),
    )
    deleted_after_cursor = original_ids[2]
    with factory() as session:
        session.execute(
            text(
                "DELETE FROM knowledge_objects_v2 "
                "WHERE organization_id = :organization_id AND object_id = :object_id"
            ),
            {
                "organization_id": organization_id,
                "object_id": deleted_after_cursor,
            },
        )
        session.commit()

    cursor = first.next_cursor
    while cursor is not None:
        page = service.query(
            KnowledgeObjectV2Query(
                organization_id=organization_id,
                sort=KnowledgeQuerySort.CREATED_AT_DESC,
                page_size=2,
                cursor=cursor,
            )
        )
        returned += tuple(item.object_id for item in page.items)
        cursor = page.next_cursor

    assert len(returned) == len(set(returned))
    assert inserted_before_cursor not in returned
    assert deleted_after_cursor not in returned
    assert set(returned) == set(original_ids) - {deleted_after_cursor}


def test_updated_sort_move_before_cursor_can_omit_and_never_repeats_returned_row(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    organization_id = "synthetic-updated-change-org"
    original_ids = tuple(_uuid(6000 + offset) for offset in range(6))
    for offset, object_id in enumerate(original_ids):
        _insert_object(
            factory,
            object_id=object_id,
            organization_id=organization_id,
            created_at=BASE_TIME,
            updated_at=BASE_TIME + timedelta(minutes=offset),
        )
    service = _service(factory)
    first = service.query(
        KnowledgeObjectV2Query(
            organization_id=organization_id,
            sort=KnowledgeQuerySort.UPDATED_AT_DESC,
            page_size=2,
        )
    )
    returned = tuple(item.object_id for item in first.items)
    assert first.next_cursor is not None
    not_yet_returned = original_ids[2]
    already_returned = returned[0]
    with factory() as session:
        session.execute(
            text(
                "UPDATE knowledge_objects_v2 SET updated_at = :updated_at "
                "WHERE organization_id = :organization_id AND object_id = :object_id"
            ),
            {
                "updated_at": BASE_TIME + timedelta(hours=2),
                "organization_id": organization_id,
                "object_id": not_yet_returned,
            },
        )
        session.execute(
            text(
                "UPDATE knowledge_objects_v2 SET updated_at = :updated_at "
                "WHERE organization_id = :organization_id AND object_id = :object_id"
            ),
            {
                "updated_at": BASE_TIME + timedelta(hours=3),
                "organization_id": organization_id,
                "object_id": already_returned,
            },
        )
        session.commit()

    cursor = first.next_cursor
    while cursor is not None:
        page = service.query(
            KnowledgeObjectV2Query(
                organization_id=organization_id,
                sort=KnowledgeQuerySort.UPDATED_AT_DESC,
                page_size=2,
                cursor=cursor,
            )
        )
        returned += tuple(item.object_id for item in page.items)
        cursor = page.next_cursor

    assert len(returned) == len(set(returned))
    assert returned.count(already_returned) == 1
    assert not_yet_returned not in returned
    assert set(returned) == set(original_ids) - {not_yet_returned}


def _signed_invalid_position_cursor(valid_cursor: str) -> str:
    payload_text = valid_cursor.split(".")[0]
    padded = payload_text + "=" * (-len(payload_text) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded))
    payload["timestamp"] = "invalid-position"
    serialized = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    signature = hmac.digest(SYNTHETIC_KEY, serialized, "sha256")
    return (
        f"{base64.urlsafe_b64encode(serialized).rstrip(b'=').decode()}."
        f"{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"
    )


def test_cursor_errors_fail_before_query_execution(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    engine, factory = migrated_store
    organization_id = "synthetic-cursor-error-org"
    for offset in range(2):
        _insert_object(
            factory,
            object_id=_uuid(7000 + offset),
            organization_id=organization_id,
            created_at=BASE_TIME + timedelta(minutes=offset),
            tags=("synthetic",),
        )
    service = _service(factory)
    first = service.query(
        KnowledgeObjectV2Query(
            organization_id=organization_id,
            page_size=1,
        )
    )
    assert first.next_cursor is not None
    query_count = 0

    def count_query(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        nonlocal query_count
        if statement.lstrip().upper().startswith("SELECT") and "knowledge_objects_v2" in statement:
            query_count += 1

    event.listen(engine, "before_cursor_execute", count_query)
    try:
        invalid_signature = f"{first.next_cursor.rsplit('.', 1)[0]}.{'eA' * 16}"
        commands = (
            KnowledgeObjectV2Query(
                organization_id=organization_id,
                cursor=invalid_signature,
            ),
            KnowledgeObjectV2Query(
                organization_id=organization_id,
                filters=KnowledgeQueryFilters(tags_all=("synthetic",)),
                cursor=first.next_cursor,
            ),
            KnowledgeObjectV2Query(
                organization_id=organization_id,
                sort=KnowledgeQuerySort.CREATED_AT_DESC,
                cursor=first.next_cursor,
            ),
            KnowledgeObjectV2Query(
                organization_id=organization_id,
                cursor=_signed_invalid_position_cursor(first.next_cursor),
            ),
        )
        expected = (
            "knowledge_query_cursor_signature_invalid",
            "knowledge_query_cursor_query_mismatch",
            "knowledge_query_cursor_query_mismatch",
            "knowledge_query_cursor_position_invalid",
        )
        for command_value, error_code in zip(commands, expected, strict=True):
            with pytest.raises(KnowledgeQueryCursorError) as captured:
                service.query(command_value)
            assert captured.value.code == error_code
    finally:
        event.remove(engine, "before_cursor_execute", count_query)
    assert query_count == 0


def _compiled_query_sql(
    *,
    organization_id: str,
    filters: KnowledgeQueryFilters,
    sort: KnowledgeQuerySort,
) -> str:
    statement = KnowledgeObjectV2QueryRepository._build_statement(
        organization_id=organization_id,
        filters=filters,
        sort=sort,
        page_size=25,
        position=None,
    )
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


def test_index_inventory_and_representative_explain_json(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    engine, factory = migrated_store
    organization_id = "synthetic-explain-org"
    for offset in range(40):
        _insert_object(
            factory,
            object_id=_uuid(8000 + offset),
            organization_id=organization_id,
            created_at=BASE_TIME + timedelta(minutes=offset),
            updated_at=BASE_TIME + timedelta(hours=1, minutes=offset),
            knowledge_type=(
                KnowledgeObjectType.FINDING if offset % 2 else KnowledgeObjectType.OBSERVATION
            ),
            lifecycle_state=(LifecycleState.CAPTURED if offset % 3 else LifecycleState.DRAFT),
            owner_id=f"owner-{offset % 4}",
            tags=("synthetic", f"group-{offset % 3}"),
            context_reference_id=f"material-{offset % 5}",
            context_role="primary" if offset % 2 else None,
        )

    with engine.connect() as connection:
        inspector = inspect(connection)
        index_names = {
            index["name"]
            for table_name in (
                "knowledge_objects_v2",
                "knowledge_object_v2_tags",
                "knowledge_object_v2_context",
            )
            for index in inspector.get_indexes(table_name)
        }
        expected_indexes = {
            "ix_knowledge_objects_v2_org_revision",
            "ix_knowledge_objects_v2_org_type",
            "ix_knowledge_objects_v2_org_lifecycle",
            "ix_knowledge_objects_v2_org_owner",
            "ix_knowledge_objects_v2_org_created",
            "ix_knowledge_objects_v2_org_updated",
            "ix_knowledge_object_v2_tags_org_tag",
            "ix_knowledge_object_v2_context_lookup",
        }
        assert expected_indexes <= index_names

        context = KnowledgeContextIdentityFilter(
            context_type=ContextType.MATERIAL,
            id_kind=ContextIdKind.EXTERNAL,
            reference_id="material-1",
            source_system="synthetic-catalog",
        )
        cases = {
            "updated_default": (KnowledgeQueryFilters(), KnowledgeQuerySort.UPDATED_AT_DESC),
            "created_desc": (KnowledgeQueryFilters(), KnowledgeQuerySort.CREATED_AT_DESC),
            "knowledge_type": (
                KnowledgeQueryFilters(knowledge_type=KnowledgeObjectType.FINDING),
                KnowledgeQuerySort.UPDATED_AT_DESC,
            ),
            "lifecycle": (
                KnowledgeQueryFilters(lifecycle_state=LifecycleState.CAPTURED),
                KnowledgeQuerySort.UPDATED_AT_DESC,
            ),
            "owner": (
                KnowledgeQueryFilters(owner_id="owner-1"),
                KnowledgeQuerySort.UPDATED_AT_DESC,
            ),
            "all_tags": (
                KnowledgeQueryFilters(tags_all=("synthetic", "group-1")),
                KnowledgeQuerySort.UPDATED_AT_DESC,
            ),
            "context": (
                KnowledgeQueryFilters(context=context),
                KnowledgeQuerySort.UPDATED_AT_DESC,
            ),
            "combined": (
                KnowledgeQueryFilters(
                    knowledge_type=KnowledgeObjectType.FINDING,
                    lifecycle_state=LifecycleState.CAPTURED,
                    owner_id="owner-1",
                    tags_all=("synthetic",),
                    context=context,
                ),
                KnowledgeQuerySort.CREATED_AT_DESC,
            ),
        }
        plan_summaries: dict[str, dict[str, object]] = {}
        for name, (filters, sort) in cases.items():
            query_sql = _compiled_query_sql(
                organization_id=organization_id,
                filters=filters,
                sort=sort,
            )
            assert " LIMIT 26" in query_sql
            plan_document = connection.execute(
                text(f"EXPLAIN (FORMAT JSON) {query_sql}")
            ).scalar_one()
            assert isinstance(plan_document, list)
            assert isinstance(plan_document[0], dict)
            assert isinstance(plan_document[0].get("Plan"), dict)
            plan = plan_document[0]["Plan"]
            plan_summaries[name] = {
                "node": plan.get("Node Type"),
                "rows": plan.get("Plan Rows"),
                "cost": plan.get("Total Cost"),
            }

    assert set(plan_summaries) == {
        "updated_default",
        "created_desc",
        "knowledge_type",
        "lifecycle",
        "owner",
        "all_tags",
        "context",
        "combined",
    }
