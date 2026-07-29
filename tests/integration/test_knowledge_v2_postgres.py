from __future__ import annotations

import os
import re
import threading
import time
from collections.abc import Callable, Generator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from queue import Queue
from uuid import UUID, uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from alembic import command
from smartcoat.domain.base import LifecycleState
from smartcoat.domain.context_references import (
    ContextIdKind,
    ContextReference,
    ContextType,
    KnowledgeContext,
)
from smartcoat.domain.decision_objects import DecisionObject, DecisionType
from smartcoat.domain.evidence_provenance import (
    CreationMethod,
    EvidenceCompleteness,
    EvidenceReference,
    EvidenceType,
    KnowledgeObjectV2EvidenceComposition,
    ProvenanceCompleteness,
    ProvenanceTransformation,
    ProvenanceV2,
)
from smartcoat.domain.knowledge_lifecycle import (
    DeleteDraftCommand,
    DraftDeletionAuditTombstoneRequest,
    DraftDeletionFacts,
    DraftDeletionPlan,
    LifecycleActor,
    LifecycleHistoryFacts,
    RequestCapturedCorrectionCommand,
    SubmitDraftCommand,
)
from smartcoat.domain.knowledge_objects import KnowledgeObjectType
from smartcoat.domain.knowledge_objects_v2 import (
    ConfidentialityLevel,
    DecisionObjectRelationship,
    KnowledgeObjectRelationship,
    KnowledgeObjectV2CreateCommand,
    KnowledgeObjectV2MutableState,
    KnowledgeObjectV2UpdateCommand,
    OwnerReference,
    UncertaintyDeclaration,
    UncertaintyKind,
)
from smartcoat.services.knowledge_lifecycle_service import KnowledgeLifecyclePlanner
from smartcoat.storage.database.base import Base
from smartcoat.storage.database.knowledge_v2_models import KnowledgeObjectV2Record
from smartcoat.storage.database.models import KnowledgeObjectRecord
from smartcoat.storage.repositories.decision_repository import DecisionRepository
from smartcoat.storage.repositories.knowledge_repository import KnowledgeRepository
from smartcoat.storage.repositories.knowledge_v2_mappers import (
    assess_legacy_persistence_record,
)
from smartcoat.storage.repositories.knowledge_v2_repository import (
    KnowledgeObjectV2Repository,
    KnowledgeObjectV2RepositoryError,
)
from smartcoat.storage.unit_of_work import KnowledgeUnitOfWork

LIVE_POSTGRES_OPT_IN = "true"
TEST_SCHEMA_PATTERN = re.compile(r"^smartcoat_test_[a-z0-9_]+$")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASELINE_REVISION = "0001_release_1_7_baseline"
HEAD_REVISION = "0003_release_1_8_knowledge_audit"
NOW = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)


class FixedClock:
    def now(self) -> datetime:
        return NOW + timedelta(minutes=10)


class FailingParticipant:
    def flush(self, session: Session) -> None:
        assert session.in_transaction()
        raise RuntimeError("synthetic participant failure")


def _require_live_postgres(database_url: str | None, opt_in: str | None) -> str:
    if opt_in != LIVE_POSTGRES_OPT_IN:
        raise RuntimeError(
            "Refusing T05 live PostgreSQL execution without explicit opt-in: "
            "SMARTCOAT_RUN_LIVE_POSTGRES_TESTS=true."
        )
    if not database_url:
        raise RuntimeError("SMARTCOAT_TEST_DATABASE_URL is required.")
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise RuntimeError("T05 live tests require PostgreSQL.")
    if url.host not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("T05 live tests accept only a localhost PostgreSQL target.")
    if not (url.database or "").startswith("smartcoat_test"):
        raise RuntimeError("T05 live tests require a database name beginning with smartcoat_test.")
    return database_url


def _schema_name() -> str:
    return f"smartcoat_test_t05_{uuid4().hex[:12]}"


def _assert_schema_name(schema_name: str) -> None:
    if TEST_SCHEMA_PATTERN.fullmatch(schema_name) is None:
        raise RuntimeError("unsafe T05 test schema name")


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


def _run_upgrade(database_url: str, schema_name: str, revision: str = "head") -> None:
    with _alembic_schema(schema_name):
        command.upgrade(_alembic_config(database_url), revision)


def _run_downgrade(database_url: str, schema_name: str, revision: str) -> None:
    with _alembic_schema(schema_name):
        command.downgrade(_alembic_config(database_url), revision)


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
        pytest.skip("Set SMARTCOAT_TEST_DATABASE_URL for T05 PostgreSQL tests.")
    return _require_live_postgres(
        database_url,
        os.getenv("SMARTCOAT_RUN_LIVE_POSTGRES_TESTS"),
    )


@pytest.fixture()
def isolated_schema(live_database_url: str) -> Generator[str, None, None]:
    schema_name = _schema_name()
    admin_engine = create_engine(live_database_url, poolclass=NullPool)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
    try:
        yield schema_name
    finally:
        _drop_schema_and_assert_absent(admin_engine, schema_name)
        admin_engine.dispose()


@pytest.fixture()
def migrated_store(
    live_database_url: str,
    isolated_schema: str,
) -> Generator[tuple[Engine, sessionmaker[Session]], None, None]:
    _run_upgrade(live_database_url, isolated_schema)
    engine = _schema_engine(live_database_url, isolated_schema)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    try:
        yield engine, factory
    finally:
        engine.dispose()


def _context_references() -> list[ContextReference]:
    return [
        ContextReference(
            context_type=context_type,
            reference_id=f"synthetic-{position}",
            id_kind=ContextIdKind.EXTERNAL,
            source_system="synthetic-test-catalog",
            display_name=f"Synthetic {context_type.value}",
            version=None if position % 2 else "v1",
            relationship_role=f"role-{position}",
            source_reference=f"synthetic://context/{position}",
            evidence_reference="evidence-synthetic-1",
            attributes={
                "boolean_true": True,
                "boolean_false": False,
                "integer_one": 1,
                "float_one": 1.0,
                "nullable": None,
                "ordered": [True, 1, 1.0, False],
            },
        )
        for position, context_type in enumerate(ContextType)
    ]


def _mutable_state(
    *,
    title: str = "Synthetic persisted coating observation",
    content_marker: str = "initial",
    tags: Sequence[str] = ("synthetic", "coating"),
    evidence_ids: Sequence[str] = ("evidence-synthetic-1",),
    knowledge_relationships: Sequence[KnowledgeObjectRelationship] = (),
    decision_relationships: Sequence[DecisionObjectRelationship] = (),
) -> KnowledgeObjectV2MutableState:
    return KnowledgeObjectV2MutableState(
        title=title,
        description=None,
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        owner=OwnerReference(owner_id="synthetic-owner", role="knowledge_steward"),
        confidentiality=ConfidentialityLevel.INTERNAL,
        uncertainty=UncertaintyDeclaration(
            kind=UncertaintyKind.ESTIMATE,
            confidence=0.75,
            note="Synthetic bounded uncertainty.",
        ),
        tags=tuple(tags),
        content={
            "marker": content_marker,
            "boolean_true": True,
            "boolean_false": False,
            "integer_one": 1,
            "float_one": 1.0,
            "ordered": [True, 1, 1.0, False, None],
        },
        context=KnowledgeContext(references=_context_references()),
        evidence_ids=tuple(evidence_ids),
        knowledge_relationships=tuple(knowledge_relationships),
        decision_relationships=tuple(decision_relationships),
    )


def _evidence_reference(
    *,
    evidence_id: str = "evidence-synthetic-1",
    title: str = "Synthetic measurement reference",
    source_reference: str = "synthetic://measurement/1",
    source_system: str = "synthetic-test-catalog",
    context_reference: ContextReference | None = None,
) -> EvidenceReference:
    return EvidenceReference(
        evidence_id=evidence_id,
        evidence_type=EvidenceType.MEASUREMENT,
        completeness=EvidenceCompleteness.COMPLETE,
        title=title,
        source_reference=source_reference,
        source_system=source_system,
        captured_by="synthetic-operator",
        captured_at=NOW,
        source_created_at=None,
        integrity=None,
        media_type="application/json",
        confidentiality=ConfidentialityLevel.INTERNAL,
        context_reference=(
            _context_references()[0] if context_reference is None else context_reference
        ),
    )


def _evidence() -> tuple[EvidenceReference, ...]:
    return (_evidence_reference(),)


def _provenance(
    *,
    source_reference: str = "synthetic://knowledge/1",
    transformations: Sequence[ProvenanceTransformation] | None = None,
) -> ProvenanceV2:
    return ProvenanceV2(
        source_system="synthetic-test-catalog",
        source_reference=source_reference,
        created_by="synthetic-operator",
        creation_method=CreationMethod.MANUAL,
        captured_at=NOW,
        source_created_at=None,
        transformation_history=tuple(transformations)
        if transformations is not None
        else (
            ProvenanceTransformation(
                transformation_type="synthetic_normalization",
                performed_by="synthetic-pipeline",
                performed_at=NOW,
                note=None,
                source_reference="synthetic://measurement/1",
            ),
        ),
        derived_from_object_id=None,
        derived_from_revision=None,
        completeness=ProvenanceCompleteness.COMPLETE,
    )


def _create(
    factory: sessionmaker[Session],
    *,
    state: KnowledgeObjectV2MutableState | None = None,
    evidence: Sequence[EvidenceReference] | None = None,
    provenance: ProvenanceV2 | None = None,
    organization_id: str = "synthetic-org",
) -> UUID:
    with KnowledgeUnitOfWork(factory) as unit:
        created = unit.knowledge_objects.stage_create(
            KnowledgeObjectV2CreateCommand(
                organization_id=organization_id,
                mutable_state=state or _mutable_state(),
            ),
            evidence=tuple(evidence) if evidence is not None else _evidence(),
            provenance=provenance if provenance is not None else _provenance(),
        )
        object_id = created.core.object_id
        unit.commit()
    return object_id


def _eligible_deletion_plan(
    repository: KnowledgeObjectV2Repository,
    *,
    object_id: UUID,
    organization_id: str = "synthetic-org",
) -> DraftDeletionPlan:
    current = repository.load_for_controlled_mutation(
        object_id=object_id,
        organization_id=organization_id,
    )
    return KnowledgeLifecyclePlanner(FixedClock()).plan_draft_deletion(
        current.core,
        DeleteDraftCommand(
            object_id=object_id,
            expected_revision=current.core.revision,
            actor=LifecycleActor(actor_id="synthetic-actor", role="knowledge_steward"),
            reason="Synthetic draft cleanup.",
        ),
        LifecycleHistoryFacts(has_ever_left_draft=False),
        DraftDeletionFacts(has_inbound_governed_references=False),
    )


def _replace_evidence(
    reference: EvidenceReference,
    **changes: object,
) -> EvidenceReference:
    payload = reference.model_dump(mode="python")
    payload.update(changes)
    return EvidenceReference.model_validate(payload)


def _replace_provenance(
    provenance: ProvenanceV2,
    **changes: object,
) -> ProvenanceV2:
    payload = provenance.model_dump(mode="python")
    payload.update(changes)
    return ProvenanceV2.model_validate(payload)


def _aggregate_xmins(session: Session, object_id: UUID) -> dict[str, tuple[str, ...]]:
    statements = {
        "root": text(
            "SELECT xmin::text FROM knowledge_objects_v2 "
            "WHERE object_id = :object_id ORDER BY object_id"
        ),
        "tags": text(
            "SELECT xmin::text FROM knowledge_object_v2_tags "
            "WHERE object_id = :object_id ORDER BY position"
        ),
        "evidence": text(
            "SELECT xmin::text FROM knowledge_object_v2_evidence "
            "WHERE object_id = :object_id ORDER BY position"
        ),
        "provenance": text(
            "SELECT xmin::text FROM knowledge_object_v2_provenance "
            "WHERE object_id = :object_id ORDER BY object_id"
        ),
        "context": text(
            "SELECT xmin::text FROM knowledge_object_v2_context "
            "WHERE object_id = :object_id ORDER BY position"
        ),
        "knowledge_relationships": text(
            "SELECT xmin::text FROM knowledge_object_v2_knowledge_relationships "
            "WHERE source_object_id = :object_id ORDER BY position"
        ),
        "decision_relationships": text(
            "SELECT xmin::text FROM knowledge_object_v2_decision_relationships "
            "WHERE source_object_id = :object_id ORDER BY position"
        ),
    }
    return {
        name: tuple(session.scalars(statement, {"object_id": object_id}).all())
        for name, statement in statements.items()
    }


def _is_full_root_select(statement: str) -> bool:
    normalized = " ".join(statement.split())
    return (
        normalized.startswith(
            "SELECT knowledge_objects_v2.object_id, knowledge_objects_v2.organization_id"
        )
        and "knowledge_objects_v2.contract_version" in normalized
    )


def _read_with_root_interleaving(
    engine: Engine,
    *,
    object_id: UUID,
    writer: Callable[[int], None],
    trigger_limit: int = 1,
) -> tuple[KnowledgeObjectV2EvidenceComposition | None, int]:
    trigger_count = 0
    connection = engine.connect()

    def commit_after_root(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        nonlocal trigger_count
        if trigger_count >= trigger_limit or not _is_full_root_select(statement):
            return
        trigger_count += 1
        writer(trigger_count)

    event.listen(connection, "after_cursor_execute", commit_after_root)
    try:
        with Session(bind=connection, autoflush=False, expire_on_commit=False) as session:
            result = KnowledgeObjectV2Repository(session).get(
                object_id=object_id,
                organization_id="synthetic-org",
            )
    finally:
        event.remove(connection, "after_cursor_execute", commit_after_root)
        connection.close()
    return result, trigger_count


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


def test_clean_upgrade_metadata_alignment_downgrade_and_reupgrade(
    live_database_url: str,
    isolated_schema: str,
) -> None:
    _run_upgrade(live_database_url, isolated_schema)
    engine = _schema_engine(live_database_url, isolated_schema)
    try:
        with engine.connect() as connection:
            table_names = set(connection.dialect.get_table_names(connection))
            assert table_names == set(Base.metadata.tables) | {"alembic_version"}
            version = connection.scalar(text("SELECT version_num FROM alembic_version"))
            assert version == HEAD_REVISION
            context = MigrationContext.configure(
                connection,
                opts={
                    "compare_type": True,
                    "compare_server_default": True,
                },
            )
            assert compare_metadata(context, Base.metadata) == []

        _run_downgrade(live_database_url, isolated_schema, BASELINE_REVISION)
        with engine.connect() as connection:
            tables = set(connection.dialect.get_table_names(connection))
            assert "knowledge_objects_v2" not in tables
            assert "knowledge_objects" in tables
            columns = {
                column["name"]
                for column in connection.dialect.get_columns(connection, "knowledge_objects")
            }
            assert "contract_version" not in columns

        _run_upgrade(live_database_url, isolated_schema)
        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        object_id = _create(factory)
        with factory() as session:
            loaded = KnowledgeObjectV2Repository(session).get(
                object_id=object_id,
                organization_id="synthetic-org",
            )
        assert loaded is not None
        assert loaded.core.revision == 1
    finally:
        engine.dispose()


def test_existing_release_1_7_schema_upgrades_without_fabricating_v2_facts(
    live_database_url: str,
    isolated_schema: str,
) -> None:
    engine = _schema_engine(live_database_url, isolated_schema)
    historical_sql = (PROJECT_ROOT / "database/migrations/0001_initial.sql").read_text()
    historical_sql = historical_sql.replace(
        'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";',
        "",
    ).replace(" DEFAULT uuid_generate_v4()", "")
    legacy_id = uuid4()
    try:
        with engine.begin() as connection:
            connection.execute(text(historical_sql))
            connection.execute(
                text(
                    "INSERT INTO knowledge_objects "
                    "(object_id, knowledge_type, title, evidence, content, provenance, metadata) "
                    "VALUES (:object_id, :knowledge_type, :title, "
                    "CAST(:evidence AS jsonb), CAST(:content AS jsonb), "
                    "CAST(:provenance AS jsonb), CAST(:metadata AS jsonb))"
                ),
                {
                    "object_id": legacy_id,
                    "knowledge_type": KnowledgeObjectType.OBSERVATION.value,
                    "title": "Synthetic legacy observation",
                    "evidence": '["synthetic://legacy/evidence/1"]',
                    "content": '{"synthetic":true}',
                    "provenance": "{}",
                    "metadata": "{}",
                },
            )

        _run_upgrade(live_database_url, isolated_schema)
        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            legacy = KnowledgeRepository(session).get(legacy_id)
            record = session.get(KnowledgeObjectRecord, str(legacy_id))
            assert legacy is not None
            assert record is not None
            assessment = assess_legacy_persistence_record(record)
            assert assessment.contract_version == "legacy_v1_table"
            assert assessment.core.is_v2_complete is False
            assert assessment.evidence_and_provenance.is_canonical_complete is False
            assert assessment.evidence_and_provenance.provenance.provenance.created_by is None
            assert assessment.evidence_and_provenance.provenance.provenance.captured_at is None
            assert session.get(KnowledgeObjectV2Record, legacy_id) is None
    finally:
        engine.dispose()


def test_complete_round_trip_preserves_composition_order_and_scalar_identity(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    target_id = _create(factory, state=_mutable_state(title="Synthetic target"))
    with factory() as session:
        decision = DecisionRepository(session).create(
            DecisionObject(
                title="Synthetic related decision",
                decision_type=DecisionType.ENGINEERING,
            )
        )
    source_state = _mutable_state(
        knowledge_relationships=(
            KnowledgeObjectRelationship(
                target_object_id=target_id,
                relationship_type="supports",
                target_revision=1,
            ),
        ),
        decision_relationships=(
            DecisionObjectRelationship(
                target_decision_id=decision.object_id,
                relationship_type="informs",
                target_revision=None,
            ),
        ),
    )
    source_id = _create(factory, state=source_state)

    with factory() as session:
        loaded = KnowledgeObjectV2Repository(session).get(
            object_id=source_id,
            organization_id="synthetic-org",
        )

    assert loaded is not None
    state = loaded.core.mutable_state
    assert loaded.core.revision == 1
    assert loaded.core.lifecycle_state is LifecycleState.DRAFT
    assert loaded.core.created_at.tzinfo is not None
    assert loaded.core.updated_at.tzinfo is not None
    assert tuple(item.context_type for item in state.context.references) == tuple(ContextType)
    assert state.tags == ("synthetic", "coating")
    assert state.evidence_ids == ("evidence-synthetic-1",)
    assert state.knowledge_relationships[0].target_revision == 1
    assert state.decision_relationships[0].target_revision is None
    assert state.content["boolean_true"] is True
    assert state.content["boolean_false"] is False
    assert type(state.content["integer_one"]) is int
    assert type(state.content["float_one"]) is float
    assert state.content["ordered"] == [True, 1, 1.0, False, None]


def test_create_alignment_organization_boundary_and_flush_without_commit(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    session = factory()
    try:
        repository = KnowledgeObjectV2Repository(session)
        with pytest.raises(ValueError, match="evidence"):
            repository.stage_create(
                KnowledgeObjectV2CreateCommand(
                    organization_id="synthetic-org",
                    mutable_state=_mutable_state(),
                ),
                evidence=(),
                provenance=_provenance(),
            )
        session.rollback()

        created = repository.stage_create(
            KnowledgeObjectV2CreateCommand(
                organization_id="synthetic-org",
                mutable_state=_mutable_state(),
            ),
            evidence=_evidence(),
            provenance=_provenance(),
        )
        with factory() as observer:
            assert observer.get(KnowledgeObjectV2Record, created.core.object_id) is None
        session.commit()
        with factory() as observer:
            assert observer.get(KnowledgeObjectV2Record, created.core.object_id) is not None
            other_org = KnowledgeObjectV2Repository(observer).get(
                object_id=created.core.object_id,
                organization_id="synthetic-org-other",
            )
            assert other_org is None
    finally:
        session.close()


def test_noop_material_stale_target_and_atomic_two_session_race(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    engine, factory = migrated_store
    object_id = _create(factory)
    with factory() as session:
        before = KnowledgeObjectV2Repository(session).load_for_controlled_mutation(
            object_id=object_id,
            organization_id="synthetic-org",
        )
        before_xmin = session.scalar(
            text("SELECT xmin::text FROM knowledge_objects_v2 WHERE object_id = :object_id"),
            {"object_id": object_id},
        )
        no_op = KnowledgeObjectV2Repository(session).stage_material_update(
            organization_id="synthetic-org",
            object_id=object_id,
            command=KnowledgeObjectV2UpdateCommand(
                object_id=object_id,
                expected_revision=1,
                replacement=before.core.mutable_state.to_mutable_state(),
            ),
        )
        session.commit()
    with factory() as session:
        after_xmin = session.scalar(
            text("SELECT xmin::text FROM knowledge_objects_v2 WHERE object_id = :object_id"),
            {"object_id": object_id},
        )
    assert no_op.core.revision == 1
    assert no_op.core.updated_at == before.core.updated_at
    assert after_xmin == before_xmin

    session_one = factory()
    try:
        winner = KnowledgeObjectV2Repository(session_one).stage_material_update(
            organization_id="synthetic-org",
            object_id=object_id,
            command=KnowledgeObjectV2UpdateCommand(
                object_id=object_id,
                expected_revision=1,
                replacement=_mutable_state(content_marker="winner"),
            ),
        )
        assert winner.core.revision == 2

        outcome: Queue[str] = Queue()

        def competing_update() -> None:
            with factory() as session_two:
                try:
                    KnowledgeObjectV2Repository(session_two).stage_material_update(
                        organization_id="synthetic-org",
                        object_id=object_id,
                        command=KnowledgeObjectV2UpdateCommand(
                            object_id=object_id,
                            expected_revision=1,
                            replacement=_mutable_state(content_marker="loser"),
                        ),
                    )
                    session_two.commit()
                except KnowledgeObjectV2RepositoryError as error:
                    session_two.rollback()
                    outcome.put(error.code)

        thread = threading.Thread(target=competing_update)
        thread.start()
        time.sleep(0.2)
        assert thread.is_alive()
        session_one.commit()
        thread.join(timeout=5)
        assert not thread.is_alive()
        assert outcome.get_nowait() == "stale_revision"
    finally:
        session_one.close()

    with factory() as session:
        current = KnowledgeObjectV2Repository(session).load_for_controlled_mutation(
            object_id=object_id,
            organization_id="synthetic-org",
        )
        assert current.core.revision == 2
        assert current.core.mutable_state.content["marker"] == "winner"
        with pytest.raises(KnowledgeObjectV2RepositoryError) as stale_no_op:
            KnowledgeObjectV2Repository(session).stage_material_update(
                organization_id="synthetic-org",
                object_id=object_id,
                command=KnowledgeObjectV2UpdateCommand(
                    object_id=object_id,
                    expected_revision=1,
                    replacement=current.core.mutable_state.to_mutable_state(),
                ),
            )
        assert stale_no_op.value.code == "stale_revision"
        with pytest.raises(KnowledgeObjectV2RepositoryError) as target_mismatch:
            KnowledgeObjectV2Repository(session).stage_material_update(
                organization_id="synthetic-org",
                object_id=object_id,
                command=KnowledgeObjectV2UpdateCommand(
                    object_id=uuid4(),
                    expected_revision=2,
                    replacement=current.core.mutable_state.to_mutable_state(),
                ),
            )
        assert target_mismatch.value.code == "knowledge_object_target_mismatch"

    assert engine.pool.status()


@pytest.mark.parametrize(
    "change",
    (
        "title",
        "source_reference",
        "source_system",
        "context_attributes",
        "context_scalar_identity",
    ),
)
def test_evidence_only_material_changes_increment_revision(
    migrated_store: tuple[Engine, sessionmaker[Session]],
    change: str,
) -> None:
    _, factory = migrated_store
    object_id = _create(factory)
    original = _evidence()[0]
    if change == "title":
        replacement = _replace_evidence(original, title="Changed synthetic title")
    elif change == "source_reference":
        replacement = _replace_evidence(
            original,
            source_reference="synthetic://measurement/changed",
        )
    elif change == "source_system":
        replacement = _replace_evidence(
            original,
            source_system="synthetic-alternate-catalog",
        )
    else:
        context = original.context_reference
        assert context is not None
        context_payload = context.model_dump(mode="python")
        attributes = dict(context.attributes)
        if change == "context_attributes":
            attributes["synthetic_added"] = "changed"
        else:
            attributes["boolean_true"] = 1
        context_payload["attributes"] = attributes
        replacement = _replace_evidence(
            original,
            context_reference=ContextReference.model_validate(context_payload),
        )
    assert replacement.canonical_metadata_json != original.canonical_metadata_json

    with factory() as session:
        repository = KnowledgeObjectV2Repository(session)
        before = repository.load_for_controlled_mutation(
            object_id=object_id,
            organization_id="synthetic-org",
        )
        updated = repository.stage_material_update(
            organization_id="synthetic-org",
            object_id=object_id,
            command=KnowledgeObjectV2UpdateCommand(
                object_id=object_id,
                expected_revision=1,
                replacement=before.core.mutable_state.to_mutable_state(),
            ),
            evidence=(replacement,),
        )
        session.commit()

    assert updated.core.revision == 2
    assert updated.core.updated_at > before.core.updated_at
    assert (
        updated.core.mutable_state.canonical_state_json
        == before.core.mutable_state.canonical_state_json
    )
    assert updated.evidence[0].canonical_metadata_json == replacement.canonical_metadata_json
    if change == "context_scalar_identity":
        loaded_context = updated.evidence[0].context_reference
        assert loaded_context is not None
        assert type(loaded_context.attributes["boolean_true"]) is int


def test_provenance_only_and_ordered_composition_changes_are_material(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    provenance_id = _create(factory)
    with factory() as session:
        repository = KnowledgeObjectV2Repository(session)
        current = repository.load_for_controlled_mutation(
            object_id=provenance_id,
            organization_id="synthetic-org",
        )
        changed_provenance = _replace_provenance(
            current.provenance,
            source_reference="synthetic://knowledge/changed",
        )
        provenance_updated = repository.stage_material_update(
            organization_id="synthetic-org",
            object_id=provenance_id,
            command=KnowledgeObjectV2UpdateCommand(
                object_id=provenance_id,
                expected_revision=1,
                replacement=current.core.mutable_state.to_mutable_state(),
            ),
            provenance=changed_provenance,
        )
        session.commit()
    assert provenance_updated.core.revision == 2
    assert (
        provenance_updated.core.mutable_state.canonical_state_json
        == current.core.mutable_state.canonical_state_json
    )
    assert provenance_updated.provenance.source_reference == "synthetic://knowledge/changed"

    first_transformation = ProvenanceTransformation(
        transformation_type="synthetic_first",
        performed_by="synthetic-pipeline",
        performed_at=NOW,
        source_reference="synthetic://measurement/1",
    )
    second_transformation = ProvenanceTransformation(
        transformation_type="synthetic_second",
        performed_by="synthetic-pipeline",
        performed_at=NOW + timedelta(seconds=1),
        source_reference="synthetic://measurement/2",
    )
    ordered_provenance = _provenance(transformations=(first_transformation, second_transformation))
    transformation_id = _create(factory, provenance=ordered_provenance)
    with factory() as session:
        repository = KnowledgeObjectV2Repository(session)
        current = repository.load_for_controlled_mutation(
            object_id=transformation_id,
            organization_id="synthetic-org",
        )
        reordered_provenance = _replace_provenance(
            current.provenance,
            transformation_history=(second_transformation, first_transformation),
        )
        reordered = repository.stage_material_update(
            organization_id="synthetic-org",
            object_id=transformation_id,
            command=KnowledgeObjectV2UpdateCommand(
                object_id=transformation_id,
                expected_revision=1,
                replacement=current.core.mutable_state.to_mutable_state(),
            ),
            provenance=reordered_provenance,
        )
        session.commit()
    assert reordered.core.revision == 2
    assert tuple(
        item.transformation_type for item in reordered.provenance.transformation_history
    ) == ("synthetic_second", "synthetic_first")

    first_evidence = _evidence_reference()
    second_evidence = _evidence_reference(
        evidence_id="evidence-synthetic-2",
        title="Synthetic second measurement",
        source_reference="synthetic://measurement/2",
        context_reference=_context_references()[1],
    )
    evidence_id = _create(
        factory,
        state=_mutable_state(evidence_ids=("evidence-synthetic-1", "evidence-synthetic-2")),
        evidence=(first_evidence, second_evidence),
    )
    with factory() as session:
        repository = KnowledgeObjectV2Repository(session)
        reordered = repository.stage_material_update(
            organization_id="synthetic-org",
            object_id=evidence_id,
            command=KnowledgeObjectV2UpdateCommand(
                object_id=evidence_id,
                expected_revision=1,
                replacement=_mutable_state(
                    evidence_ids=("evidence-synthetic-2", "evidence-synthetic-1")
                ),
            ),
            evidence=(second_evidence, first_evidence),
        )
        session.commit()
    assert reordered.core.revision == 2
    assert tuple(item.evidence_id for item in reordered.evidence) == (
        "evidence-synthetic-2",
        "evidence-synthetic-1",
    )


def test_identical_complete_composition_is_a_strict_noop(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    object_id = _create(factory)
    with factory() as session:
        repository = KnowledgeObjectV2Repository(session)
        before = repository.load_for_controlled_mutation(
            object_id=object_id,
            organization_id="synthetic-org",
        )
        before_xmins = _aggregate_xmins(session, object_id)

        state_payload = before.core.mutable_state.to_mutable_state().model_dump(mode="python")
        state_payload["content"] = dict(reversed(state_payload["content"].items()))
        reordered_state = KnowledgeObjectV2MutableState.model_validate(state_payload)

        evidence_payload = before.evidence[0].model_dump(mode="python")
        context = before.evidence[0].context_reference
        assert context is not None
        context_payload = context.model_dump(mode="python")
        context_payload["attributes"] = dict(reversed(context.attributes.items()))
        evidence_payload["context_reference"] = context_payload
        reordered_evidence = EvidenceReference.model_validate(evidence_payload)
        supplied_provenance = ProvenanceV2.model_validate(
            before.provenance.model_dump(mode="python")
        )

        no_op = repository.stage_material_update(
            organization_id="synthetic-org",
            object_id=object_id,
            command=KnowledgeObjectV2UpdateCommand(
                object_id=object_id,
                expected_revision=1,
                replacement=reordered_state,
            ),
            evidence=(reordered_evidence,),
            provenance=supplied_provenance,
        )
        session.commit()

    with factory() as session:
        after = KnowledgeObjectV2Repository(session).load_for_controlled_mutation(
            object_id=object_id,
            organization_id="synthetic-org",
        )
        after_xmins = _aggregate_xmins(session, object_id)

    assert no_op.core.revision == 1
    assert no_op.core.updated_at == before.core.updated_at
    assert after.core.revision == 1
    assert after.core.updated_at == before.core.updated_at
    assert after_xmins == before_xmins


def test_complete_composition_precedence_and_validation_failures_remain_deterministic(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    object_id = _create(factory)
    changed_evidence = _replace_evidence(_evidence()[0], title="Changed once")
    changed_provenance = _provenance(source_reference="synthetic://knowledge/stale-replacement")
    with factory() as session:
        repository = KnowledgeObjectV2Repository(session)
        current = repository.load_for_controlled_mutation(
            object_id=object_id,
            organization_id="synthetic-org",
        )
        repository.stage_material_update(
            organization_id="synthetic-org",
            object_id=object_id,
            command=KnowledgeObjectV2UpdateCommand(
                object_id=object_id,
                expected_revision=1,
                replacement=current.core.mutable_state.to_mutable_state(),
            ),
            evidence=(changed_evidence,),
        )
        session.commit()

    with factory() as session:
        repository = KnowledgeObjectV2Repository(session)
        current = repository.load_for_controlled_mutation(
            object_id=object_id,
            organization_id="synthetic-org",
        )
        with pytest.raises(KnowledgeObjectV2RepositoryError) as stale:
            repository.stage_material_update(
                organization_id="synthetic-org",
                object_id=object_id,
                command=KnowledgeObjectV2UpdateCommand(
                    object_id=object_id,
                    expected_revision=1,
                    replacement=current.core.mutable_state.to_mutable_state(),
                ),
                evidence=(_replace_evidence(changed_evidence, title="Changed twice"),),
            )
        assert stale.value.code == "stale_revision"

        with pytest.raises(KnowledgeObjectV2RepositoryError) as stale_provenance:
            repository.stage_material_update(
                organization_id="synthetic-org",
                object_id=object_id,
                command=KnowledgeObjectV2UpdateCommand(
                    object_id=object_id,
                    expected_revision=1,
                    replacement=current.core.mutable_state.to_mutable_state(),
                ),
                provenance=changed_provenance,
            )
        assert stale_provenance.value.code == "stale_revision"

        with pytest.raises(KnowledgeObjectV2RepositoryError) as target_mismatch:
            repository.stage_material_update(
                organization_id="synthetic-org",
                object_id=object_id,
                command=KnowledgeObjectV2UpdateCommand(
                    object_id=uuid4(),
                    expected_revision=1,
                    replacement=current.core.mutable_state.to_mutable_state(),
                ),
                evidence=(_replace_evidence(changed_evidence, title="Changed twice"),),
                provenance=changed_provenance,
            )
        assert target_mismatch.value.code == "knowledge_object_target_mismatch"

        replacement_payload = current.core.mutable_state.to_mutable_state().model_dump(
            mode="python"
        )
        replacement_payload["evidence_ids"] = ("evidence-synthetic-2",)
        with pytest.raises(KnowledgeObjectV2RepositoryError) as missing_evidence:
            repository.stage_material_update(
                organization_id="synthetic-org",
                object_id=object_id,
                command=KnowledgeObjectV2UpdateCommand(
                    object_id=object_id,
                    expected_revision=2,
                    replacement=KnowledgeObjectV2MutableState.model_validate(replacement_payload),
                ),
            )
        assert missing_evidence.value.code == "replacement_evidence_required"

        incomplete_provenance = ProvenanceV2(
            transformation_history=(),
            completeness=ProvenanceCompleteness.LEGACY_INCOMPLETE,
        )
        with pytest.raises(ValueError, match="canonical_provenance_incomplete"):
            repository.stage_material_update(
                organization_id="synthetic-org",
                object_id=object_id,
                command=KnowledgeObjectV2UpdateCommand(
                    object_id=object_id,
                    expected_revision=2,
                    replacement=current.core.mutable_state.to_mutable_state(),
                ),
                provenance=incomplete_provenance,
            )


@pytest.mark.parametrize("material_dimension", ("evidence", "provenance"))
def test_evidence_and_provenance_updates_roll_back_with_uow_failure(
    migrated_store: tuple[Engine, sessionmaker[Session]],
    material_dimension: str,
) -> None:
    _, factory = migrated_store
    object_id = _create(factory)
    with factory() as session:
        before = KnowledgeObjectV2Repository(session).load_for_controlled_mutation(
            object_id=object_id,
            organization_id="synthetic-org",
        )

    with pytest.raises(RuntimeError, match="synthetic participant failure"):
        with KnowledgeUnitOfWork(
            factory,
            participants=(FailingParticipant(),),
        ) as unit:
            current = unit.knowledge_objects.load_for_controlled_mutation(
                object_id=object_id,
                organization_id="synthetic-org",
            )
            replacement_evidence = (
                (_replace_evidence(current.evidence[0], title="Rolled back title"),)
                if material_dimension == "evidence"
                else None
            )
            replacement_provenance = (
                _replace_provenance(
                    current.provenance,
                    source_reference="synthetic://knowledge/rolled-back",
                )
                if material_dimension == "provenance"
                else None
            )
            unit.knowledge_objects.stage_material_update(
                organization_id="synthetic-org",
                object_id=object_id,
                command=KnowledgeObjectV2UpdateCommand(
                    object_id=object_id,
                    expected_revision=1,
                    replacement=current.core.mutable_state.to_mutable_state(),
                ),
                evidence=replacement_evidence,
                provenance=replacement_provenance,
            )
            unit.commit()

    with factory() as session:
        after = KnowledgeObjectV2Repository(session).load_for_controlled_mutation(
            object_id=object_id,
            organization_id="synthetic-org",
        )
    assert after.core.revision == 1
    assert after.core.updated_at == before.core.updated_at
    assert after.evidence[0].canonical_metadata_json == before.evidence[0].canonical_metadata_json
    assert after.provenance.model_dump_json() == before.provenance.model_dump_json()


def test_revision_verified_read_retries_root_and_multiple_child_update(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    engine, factory = migrated_store
    object_id = _create(factory)

    def writer(_attempt: int) -> None:
        with factory() as session:
            repository = KnowledgeObjectV2Repository(session)
            current = repository.load_for_controlled_mutation(
                object_id=object_id,
                organization_id="synthetic-org",
            )
            repository.stage_material_update(
                organization_id="synthetic-org",
                object_id=object_id,
                command=KnowledgeObjectV2UpdateCommand(
                    object_id=object_id,
                    expected_revision=current.core.revision,
                    replacement=_mutable_state(
                        title="Concurrent complete title",
                        content_marker="concurrent-complete",
                        tags=("replacement", "coherent"),
                    ),
                ),
                evidence=(
                    _replace_evidence(
                        current.evidence[0],
                        title="Concurrent replacement evidence",
                    ),
                ),
                provenance=_replace_provenance(
                    current.provenance,
                    source_reference="synthetic://knowledge/concurrent-complete",
                ),
            )
            session.commit()

    loaded, trigger_count = _read_with_root_interleaving(
        engine,
        object_id=object_id,
        writer=writer,
    )

    assert trigger_count == 1
    assert loaded is not None
    assert loaded.core.revision == 2
    assert loaded.core.mutable_state.title == "Concurrent complete title"
    assert loaded.core.mutable_state.content["marker"] == "concurrent-complete"
    assert loaded.core.mutable_state.tags == ("replacement", "coherent")
    assert loaded.evidence[0].title == "Concurrent replacement evidence"
    assert loaded.provenance.source_reference == "synthetic://knowledge/concurrent-complete"


def test_revision_verified_read_retries_evidence_and_provenance_only_update(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    engine, factory = migrated_store
    object_id = _create(factory)

    def writer(_attempt: int) -> None:
        with factory() as session:
            repository = KnowledgeObjectV2Repository(session)
            current = repository.load_for_controlled_mutation(
                object_id=object_id,
                organization_id="synthetic-org",
            )
            repository.stage_material_update(
                organization_id="synthetic-org",
                object_id=object_id,
                command=KnowledgeObjectV2UpdateCommand(
                    object_id=object_id,
                    expected_revision=current.core.revision,
                    replacement=current.core.mutable_state.to_mutable_state(),
                ),
                evidence=(
                    _replace_evidence(
                        current.evidence[0],
                        source_reference="synthetic://measurement/concurrent",
                    ),
                ),
                provenance=_replace_provenance(
                    current.provenance,
                    source_reference="synthetic://knowledge/concurrent",
                ),
            )
            session.commit()

    loaded, trigger_count = _read_with_root_interleaving(
        engine,
        object_id=object_id,
        writer=writer,
    )

    assert trigger_count == 1
    assert loaded is not None
    assert loaded.core.revision == 2
    assert loaded.core.mutable_state.content["marker"] == "initial"
    assert loaded.evidence[0].source_reference == "synthetic://measurement/concurrent"
    assert loaded.provenance.source_reference == "synthetic://knowledge/concurrent"


def test_revision_verified_read_retries_lifecycle_only_update(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    engine, factory = migrated_store
    object_id = _create(factory)

    def writer(_attempt: int) -> None:
        with factory() as session:
            repository = KnowledgeObjectV2Repository(session)
            current = repository.load_for_controlled_mutation(
                object_id=object_id,
                organization_id="synthetic-org",
            )
            plan = KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
                current.core,
                SubmitDraftCommand(
                    object_id=object_id,
                    expected_revision=current.core.revision,
                    actor=LifecycleActor(
                        actor_id="synthetic-concurrent-actor",
                        role="knowledge_steward",
                    ),
                    submission_note="Synthetic concurrent capture submission.",
                ),
                LifecycleHistoryFacts(has_ever_left_draft=False),
            )
            repository.stage_lifecycle_transition(
                organization_id="synthetic-org",
                plan=plan,
            )
            session.commit()

    loaded, trigger_count = _read_with_root_interleaving(
        engine,
        object_id=object_id,
        writer=writer,
    )

    assert trigger_count == 1
    assert loaded is not None
    assert loaded.core.revision == 2
    assert loaded.core.lifecycle_state is LifecycleState.CAPTURED
    assert loaded.core.mutable_state.content["marker"] == "initial"


def test_revision_verified_read_retries_concurrent_deletion(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    engine, factory = migrated_store
    object_id = _create(factory)

    def writer(_attempt: int) -> None:
        with factory() as session:
            repository = KnowledgeObjectV2Repository(session)
            plan = _eligible_deletion_plan(repository, object_id=object_id)
            repository.stage_eligible_draft_deletion(
                organization_id="synthetic-org",
                plan=plan,
            )
            session.commit()

    loaded, trigger_count = _read_with_root_interleaving(
        engine,
        object_id=object_id,
        writer=writer,
    )

    assert trigger_count == 1
    assert loaded is None


def test_revision_verified_read_retry_exhaustion_is_bounded_and_releases_connection(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    engine, factory = migrated_store
    object_id = _create(factory)
    writer_attempts: list[int] = []

    def writer(attempt: int) -> None:
        writer_attempts.append(attempt)
        with factory() as session:
            repository = KnowledgeObjectV2Repository(session)
            current = repository.load_for_controlled_mutation(
                object_id=object_id,
                organization_id="synthetic-org",
            )
            repository.stage_material_update(
                organization_id="synthetic-org",
                object_id=object_id,
                command=KnowledgeObjectV2UpdateCommand(
                    object_id=object_id,
                    expected_revision=current.core.revision,
                    replacement=_mutable_state(content_marker=f"retry-{attempt}"),
                ),
            )
            session.commit()

    with pytest.raises(KnowledgeObjectV2RepositoryError) as exhausted:
        _read_with_root_interleaving(
            engine,
            object_id=object_id,
            writer=writer,
            trigger_limit=3,
        )

    assert exhausted.value.code == "aggregate_read_retry_exhausted"
    assert writer_attempts == [1, 2, 3]
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT 1")) == 1
    with factory() as session:
        final = KnowledgeObjectV2Repository(session).load_for_controlled_mutation(
            object_id=object_id,
            organization_id="synthetic-org",
        )
    assert final.core.revision == 4
    assert final.core.mutable_state.content["marker"] == "retry-3"


def test_valid_lifecycle_plan_persists_exactly_and_stale_plan_fails(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    object_id = _create(factory)
    with factory() as session:
        repository = KnowledgeObjectV2Repository(session)
        source = repository.load_for_controlled_mutation(
            object_id=object_id,
            organization_id="synthetic-org",
        )
        plan = KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
            source.core,
            SubmitDraftCommand(
                object_id=object_id,
                expected_revision=1,
                actor=LifecycleActor(
                    actor_id="synthetic-actor",
                    role="knowledge_steward",
                ),
                submission_note="Synthetic capture submission.",
            ),
            LifecycleHistoryFacts(has_ever_left_draft=False),
        )
        persisted = repository.stage_lifecycle_transition(
            organization_id="synthetic-org",
            plan=plan,
        )
        session.commit()

    assert source.core.lifecycle_state is LifecycleState.DRAFT
    assert source.core.revision == 1
    assert persisted.core.lifecycle_state is plan.to_lifecycle
    assert persisted.core.revision == plan.resulting_revision
    assert persisted.core.updated_at >= source.core.updated_at

    with factory() as session:
        repository = KnowledgeObjectV2Repository(session)
        history = repository.lifecycle_history_facts(
            object_id=object_id,
            organization_id="synthetic-org",
        )
        assert history.has_ever_left_draft is True
        with pytest.raises(KnowledgeObjectV2RepositoryError) as stale:
            repository.stage_lifecycle_transition(
                organization_id="synthetic-org",
                plan=plan,
            )
        assert stale.value.code == "stale_revision"


def test_draft_delete_eligibility_and_inbound_reference_guards(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    eligible_id = _create(factory, state=_mutable_state(title="Synthetic eligible draft"))
    with factory() as session:
        repository = KnowledgeObjectV2Repository(session)
        plan = _eligible_deletion_plan(repository, object_id=eligible_id)
        repository.stage_eligible_draft_deletion(
            organization_id="synthetic-org",
            plan=plan,
        )
        session.commit()
    with factory() as session:
        assert session.get(KnowledgeObjectV2Record, eligible_id) is None

    target_id = _create(factory, state=_mutable_state(title="Synthetic inbound target"))
    with factory() as session:
        target_plan = _eligible_deletion_plan(
            KnowledgeObjectV2Repository(session),
            object_id=target_id,
        )
    _create(
        factory,
        state=_mutable_state(
            title="Synthetic inbound source",
            knowledge_relationships=(
                KnowledgeObjectRelationship(
                    target_object_id=target_id,
                    relationship_type="supports",
                    target_revision=1,
                ),
            ),
        ),
    )
    with factory() as session:
        repository = KnowledgeObjectV2Repository(session)
        facts = repository.compute_inbound_governed_reference_facts(
            object_id=target_id,
            organization_id="synthetic-org",
        )
        assert facts.has_inbound_governed_references is True
        with pytest.raises(KnowledgeObjectV2RepositoryError) as inbound:
            repository.stage_eligible_draft_deletion(
                organization_id="synthetic-org",
                plan=target_plan,
            )
        assert inbound.value.code == "inbound_reference_blocks_deletion"

    decision_target_id = _create(
        factory,
        state=_mutable_state(title="Synthetic decision inbound target"),
    )
    with factory() as session:
        decision_plan = _eligible_deletion_plan(
            KnowledgeObjectV2Repository(session),
            object_id=decision_target_id,
        )
        DecisionRepository(session).create(
            DecisionObject(
                title="Synthetic inbound decision",
                decision_type=DecisionType.ENGINEERING,
                related_knowledge=[decision_target_id],
            )
        )
    with factory() as session:
        repository = KnowledgeObjectV2Repository(session)
        with pytest.raises(KnowledgeObjectV2RepositoryError) as inbound_decision:
            repository.stage_eligible_draft_deletion(
                organization_id="synthetic-org",
                plan=decision_plan,
            )
        assert inbound_decision.value.code == "inbound_reference_blocks_deletion"


def test_non_draft_correction_draft_revision_and_uow_rollback_guards(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    object_id = _create(factory)
    with factory() as session:
        repository = KnowledgeObjectV2Repository(session)
        current = repository.load_for_controlled_mutation(
            object_id=object_id,
            organization_id="synthetic-org",
        )
        plan = KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
            current.core,
            SubmitDraftCommand(
                object_id=object_id,
                expected_revision=1,
                actor=LifecycleActor(
                    actor_id="synthetic-actor",
                    role="knowledge_steward",
                ),
                submission_note="Synthetic capture submission.",
            ),
            LifecycleHistoryFacts(has_ever_left_draft=False),
        )
        repository.stage_lifecycle_transition(
            organization_id="synthetic-org",
            plan=plan,
        )
        session.commit()

    actor = LifecycleActor(actor_id="synthetic-actor", role="knowledge_steward")
    tombstone = DraftDeletionAuditTombstoneRequest(
        object_id=object_id,
        object_revision=2,
        actor=actor,
        reason="Synthetic invalid deletion.",
        occurred_at=NOW,
    )
    invalid_plan = DraftDeletionPlan(
        object_id=object_id,
        expected_revision=2,
        actor=actor,
        reason="Synthetic invalid deletion.",
        occurred_at=NOW,
        tombstone_request=tombstone,
    )
    with factory() as session:
        with pytest.raises(KnowledgeObjectV2RepositoryError) as non_draft:
            KnowledgeObjectV2Repository(session).stage_eligible_draft_deletion(
                organization_id="synthetic-org",
                plan=invalid_plan,
            )
        assert non_draft.value.code == "trusted_record_hard_delete_forbidden"

    with factory() as session:
        repository = KnowledgeObjectV2Repository(session)
        captured = repository.load_for_controlled_mutation(
            object_id=object_id,
            organization_id="synthetic-org",
        )
        correction_plan = KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
            captured.core,
            RequestCapturedCorrectionCommand(
                object_id=object_id,
                expected_revision=2,
                actor=LifecycleActor(
                    actor_id="synthetic-reviewer",
                    role="reviewer",
                ),
                correction_reason="Synthetic correction request.",
            ),
            LifecycleHistoryFacts(has_ever_left_draft=True),
        )
        corrected = repository.stage_lifecycle_transition(
            organization_id="synthetic-org",
            plan=correction_plan,
        )
        session.commit()
    assert corrected.core.lifecycle_state is LifecycleState.DRAFT
    assert corrected.core.revision == 3

    correction_tombstone = DraftDeletionAuditTombstoneRequest(
        object_id=object_id,
        object_revision=3,
        actor=actor,
        reason="Synthetic correction draft deletion attempt.",
        occurred_at=NOW,
    )
    correction_delete_plan = DraftDeletionPlan(
        object_id=object_id,
        expected_revision=3,
        actor=actor,
        reason="Synthetic correction draft deletion attempt.",
        occurred_at=NOW,
        tombstone_request=correction_tombstone,
    )
    assert "content" not in correction_tombstone.model_dump()
    with factory() as session:
        repository = KnowledgeObjectV2Repository(session)
        with pytest.raises(KnowledgeObjectV2RepositoryError) as correction_draft:
            repository.stage_eligible_draft_deletion(
                organization_id="synthetic-org",
                plan=correction_delete_plan,
            )
        assert correction_draft.value.code == "draft_delete_ineligible"
        with pytest.raises(KnowledgeObjectV2RepositoryError) as revision_conflict:
            repository.stage_eligible_draft_deletion(
                organization_id="synthetic-org",
                plan=invalid_plan,
            )
        assert revision_conflict.value.code == "stale_revision"

    rollback_id: UUID | None = None
    with pytest.raises(RuntimeError, match="synthetic participant failure"):
        with KnowledgeUnitOfWork(
            factory,
            participants=(FailingParticipant(),),
        ) as unit:
            created = unit.knowledge_objects.stage_create(
                KnowledgeObjectV2CreateCommand(
                    organization_id="synthetic-org",
                    mutable_state=_mutable_state(title="Synthetic rollback object"),
                ),
                evidence=_evidence(),
                provenance=_provenance(),
            )
            rollback_id = created.core.object_id
            unit.commit()
    assert rollback_id is not None
    with factory() as session:
        assert session.get(KnowledgeObjectV2Record, rollback_id) is None

    commit_id: UUID | None = None
    commits = 0

    def count_commit(session: Session) -> None:
        nonlocal commits
        commits += 1

    with KnowledgeUnitOfWork(factory) as unit:
        event.listen(unit.session, "after_commit", count_commit)
        created = unit.knowledge_objects.stage_create(
            KnowledgeObjectV2CreateCommand(
                organization_id="synthetic-org",
                mutable_state=_mutable_state(title="Synthetic single commit"),
            ),
            evidence=_evidence(),
            provenance=_provenance(),
        )
        commit_id = created.core.object_id
        unit.commit()
    assert commits == 1
    assert commit_id is not None
    with factory() as session:
        assert session.get(KnowledgeObjectV2Record, commit_id) is not None

    with KnowledgeUnitOfWork(factory) as unit:
        current = unit.knowledge_objects.load_for_controlled_mutation(
            object_id=commit_id,
            organization_id="synthetic-org",
        )
        unit.knowledge_objects.stage_material_update(
            organization_id="synthetic-org",
            object_id=commit_id,
            command=KnowledgeObjectV2UpdateCommand(
                object_id=commit_id,
                expected_revision=1,
                replacement=_mutable_state(content_marker="rolled-back"),
            ),
        )
        assert current.core.revision == 1
    with factory() as session:
        persisted = KnowledgeObjectV2Repository(session).load_for_controlled_mutation(
            object_id=commit_id,
            organization_id="synthetic-org",
        )
        assert persisted.core.revision == 1
        assert persisted.core.mutable_state.content["marker"] == "initial"


def test_cleanup_helper_leaves_zero_schema_objects(live_database_url: str) -> None:
    schema_name = _schema_name()
    admin_engine = create_engine(live_database_url, poolclass=NullPool)
    try:
        with admin_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
            connection.execute(text(f'CREATE TABLE "{schema_name}".synthetic_probe (id integer)'))
        _drop_schema_and_assert_absent(admin_engine, schema_name)
    finally:
        admin_engine.dispose()
