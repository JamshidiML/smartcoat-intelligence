from __future__ import annotations

import os
import re
import threading
import time
from collections.abc import Generator, Sequence
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
HEAD_REVISION = "0002_release_1_8_knowledge_v2"
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
        tags=("synthetic", "coating"),
        content={
            "marker": content_marker,
            "boolean_true": True,
            "boolean_false": False,
            "integer_one": 1,
            "float_one": 1.0,
            "ordered": [True, 1, 1.0, False, None],
        },
        context=KnowledgeContext(references=_context_references()),
        evidence_ids=("evidence-synthetic-1",),
        knowledge_relationships=tuple(knowledge_relationships),
        decision_relationships=tuple(decision_relationships),
    )


def _evidence() -> tuple[EvidenceReference, ...]:
    return (
        EvidenceReference(
            evidence_id="evidence-synthetic-1",
            evidence_type=EvidenceType.MEASUREMENT,
            completeness=EvidenceCompleteness.COMPLETE,
            title="Synthetic measurement reference",
            source_reference="synthetic://measurement/1",
            source_system="synthetic-test-catalog",
            captured_by="synthetic-operator",
            captured_at=NOW,
            source_created_at=None,
            integrity=None,
            media_type="application/json",
            confidentiality=ConfidentialityLevel.INTERNAL,
            context_reference=_context_references()[0],
        ),
    )


def _provenance() -> ProvenanceV2:
    return ProvenanceV2(
        source_system="synthetic-test-catalog",
        source_reference="synthetic://knowledge/1",
        created_by="synthetic-operator",
        creation_method=CreationMethod.MANUAL,
        captured_at=NOW,
        source_created_at=None,
        transformation_history=(
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
    organization_id: str = "synthetic-org",
) -> UUID:
    with KnowledgeUnitOfWork(factory) as unit:
        created = unit.knowledge_objects.stage_create(
            KnowledgeObjectV2CreateCommand(
                organization_id=organization_id,
                mutable_state=state or _mutable_state(),
            ),
            evidence=_evidence(),
            provenance=_provenance(),
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
