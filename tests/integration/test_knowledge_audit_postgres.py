from __future__ import annotations

import os
import re
import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import Engine, create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from alembic import command
from smartcoat.domain.base import LifecycleState
from smartcoat.domain.context_references import KnowledgeContext
from smartcoat.domain.events import EnterpriseEvent, EventType
from smartcoat.domain.evidence_provenance import (
    CreationMethod,
    EvidenceCompleteness,
    EvidenceReference,
    EvidenceType,
    ProvenanceCompleteness,
    ProvenanceTransformation,
    ProvenanceV2,
)
from smartcoat.domain.knowledge_audit import (
    GovernedKnowledgeCreateCommand,
    GovernedKnowledgeUpdateCommand,
    KnowledgeAuditChangedField,
    KnowledgeAuditEventType,
    audit_event_type_for_lifecycle_action,
)
from smartcoat.domain.knowledge_lifecycle import (
    ApproveValidatedCommand,
    CompleteReviewCommand,
    DeleteDraftCommand,
    DeprecateApprovedCommand,
    LifecycleAction,
    LifecycleActor,
    LifecycleTransitionCommand,
    RejectCapturedCommand,
    RejectReviewedCommand,
    RejectValidatedCommand,
    ReopenRejectedCommand,
    RequestCapturedCorrectionCommand,
    RequestReviewedCorrectionCommand,
    RequestValidatedCorrectionCommand,
    SubmitDraftCommand,
    ValidateReviewedCommand,
)
from smartcoat.domain.knowledge_objects import KnowledgeObjectType
from smartcoat.domain.knowledge_objects_v2 import (
    ConfidentialityLevel,
    KnowledgeObjectV2CreateCommand,
    KnowledgeObjectV2MutableState,
    KnowledgeObjectV2UpdateCommand,
    OwnerReference,
)
from smartcoat.services.knowledge_audit_service import KnowledgeAuditService
from smartcoat.storage.database.base import Base
from smartcoat.storage.database.knowledge_audit_models import (
    KnowledgeAuditEventRecord,
)
from smartcoat.storage.database.knowledge_v2_models import KnowledgeObjectV2Record
from smartcoat.storage.repositories.event_repository import EventRepository
from smartcoat.storage.repositories.knowledge_audit_repository import (
    KnowledgeAuditParticipant,
)
from smartcoat.storage.repositories.knowledge_v2_repository import (
    KnowledgeObjectV2RepositoryError,
)

LIVE_POSTGRES_OPT_IN = "true"
TEST_SCHEMA_PATTERN = re.compile(r"^smartcoat_test_[a-z0-9_]+$")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_REVISION = "0002_release_1_8_knowledge_v2"
HEAD_REVISION = "0003_release_1_8_knowledge_audit"
NOW = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)


class FixedClock:
    def now(self) -> datetime:
        return NOW


class DelayedSystemClock:
    def now(self) -> datetime:
        time.sleep(0.02)
        return datetime.now(UTC)


class FailingAuditParticipant(KnowledgeAuditParticipant):
    def flush(self, session: Session) -> None:
        assert session.in_transaction()
        raise RuntimeError("synthetic audit participant failure")


class AppendThenFailAuditParticipant(KnowledgeAuditParticipant):
    def flush(self, session: Session) -> None:
        super().flush(session)
        raise RuntimeError("synthetic post-append participant failure")


def _require_live_postgres(database_url: str | None, opt_in: str | None) -> str:
    if opt_in != LIVE_POSTGRES_OPT_IN:
        raise RuntimeError(
            "Refusing T07 live PostgreSQL execution without explicit opt-in: "
            "SMARTCOAT_RUN_LIVE_POSTGRES_TESTS=true."
        )
    if not database_url:
        raise RuntimeError("SMARTCOAT_TEST_DATABASE_URL is required.")
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise RuntimeError("T07 live tests require PostgreSQL.")
    if url.host not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("T07 live tests accept only a localhost PostgreSQL target.")
    if not (url.database or "").startswith("smartcoat_test"):
        raise RuntimeError("T07 live tests require a database name beginning with smartcoat_test.")
    return database_url


def _schema_name() -> str:
    return f"smartcoat_test_t07_{uuid4().hex[:12]}"


def _assert_schema_name(schema_name: str) -> None:
    if TEST_SCHEMA_PATTERN.fullmatch(schema_name) is None:
        raise RuntimeError("unsafe T07 test schema name")


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


def _run_upgrade(
    database_url: str,
    schema_name: str,
    revision: str = "head",
) -> None:
    with _alembic_schema(schema_name):
        command.upgrade(_alembic_config(database_url), revision)


def _run_downgrade(
    database_url: str,
    schema_name: str,
    revision: str,
) -> None:
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
        pytest.skip("Set SMARTCOAT_TEST_DATABASE_URL for T07 PostgreSQL tests.")
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


def _state(
    *,
    content: dict[str, object] | None = None,
) -> KnowledgeObjectV2MutableState:
    return KnowledgeObjectV2MutableState(
        title="Synthetic PostgreSQL audit observation",
        description="Synthetic metadata-only test.",
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        owner=OwnerReference(
            owner_id="synthetic-owner",
            role="knowledge_author",
        ),
        confidentiality=ConfidentialityLevel.INTERNAL,
        tags=("synthetic", "audit"),
        content=content or {"flag": True, "count": 1},
        context=KnowledgeContext(references=[]),
        evidence_ids=("synthetic-evidence-1",),
    )


def _evidence(*, title: str = "Synthetic audit evidence") -> tuple[EvidenceReference, ...]:
    return (
        EvidenceReference(
            evidence_id="synthetic-evidence-1",
            evidence_type=EvidenceType.OBSERVATION,
            completeness=EvidenceCompleteness.COMPLETE,
            title=title,
            source_reference="synthetic://audit/evidence/1",
            captured_by="synthetic-author",
            captured_at=NOW - timedelta(minutes=2),
        ),
    )


def _provenance(*, note: str = "Initial synthetic capture") -> ProvenanceV2:
    return ProvenanceV2(
        source_system="synthetic-test",
        source_reference="synthetic://audit/knowledge/1",
        created_by="synthetic-author",
        creation_method=CreationMethod.MANUAL,
        captured_at=NOW - timedelta(minutes=1),
        transformation_history=(
            ProvenanceTransformation(
                transformation_type="synthetic_normalization",
                performed_by="synthetic-author",
                performed_at=NOW - timedelta(seconds=30),
                note=note,
            ),
        ),
        completeness=ProvenanceCompleteness.COMPLETE,
    )


def _create_command() -> GovernedKnowledgeCreateCommand:
    return GovernedKnowledgeCreateCommand(
        create=KnowledgeObjectV2CreateCommand(
            organization_id="synthetic-org",
            mutable_state=_state(),
        ),
        evidence=_evidence(),
        provenance=_provenance(),
        actor=LifecycleActor(
            actor_id="synthetic-author",
            role="knowledge_author",
        ),
        reason_or_note="Create synthetic PostgreSQL draft.",
        correlation_id=uuid4(),
    )


def _service(
    factory: sessionmaker[Session],
    *,
    participant_factory: type[KnowledgeAuditParticipant] = KnowledgeAuditParticipant,
) -> KnowledgeAuditService:
    return KnowledgeAuditService(
        factory,
        clock=FixedClock(),
        participant_factory=participant_factory,
    )


def _created(
    service: KnowledgeAuditService,
) -> UUID:
    result = service.create(_create_command())
    assert result.knowledge is not None
    assert result.audit_event is not None
    assert result.audit_event.event_type is KnowledgeAuditEventType.CREATE
    return result.knowledge.core.object_id


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


def test_clean_0002_upgrade_downgrade_and_reupgrade(
    live_database_url: str,
    isolated_schema: str,
) -> None:
    engine = _schema_engine(live_database_url, isolated_schema)
    try:
        _run_upgrade(live_database_url, isolated_schema, PREVIOUS_REVISION)
        with engine.connect() as connection:
            assert "knowledge_objects_v2" in connection.dialect.get_table_names(connection)
            assert "knowledge_audit_events_v2" not in connection.dialect.get_table_names(connection)

        _run_upgrade(live_database_url, isolated_schema, HEAD_REVISION)
        with engine.connect() as connection:
            assert "knowledge_audit_events_v2" in connection.dialect.get_table_names(connection)
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                HEAD_REVISION
            )

        _run_downgrade(live_database_url, isolated_schema, PREVIOUS_REVISION)
        with engine.connect() as connection:
            assert "knowledge_objects_v2" in connection.dialect.get_table_names(connection)
            assert "knowledge_audit_events_v2" not in connection.dialect.get_table_names(connection)

        _run_upgrade(live_database_url, isolated_schema, HEAD_REVISION)
        with engine.connect() as connection:
            assert "knowledge_audit_events_v2" in connection.dialect.get_table_names(connection)
    finally:
        engine.dispose()


def test_clean_head_metadata_alignment_and_append_only_trigger(
    live_database_url: str,
    isolated_schema: str,
) -> None:
    _run_upgrade(live_database_url, isolated_schema)
    engine = _schema_engine(live_database_url, isolated_schema)
    try:
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                HEAD_REVISION
            )
            context = MigrationContext.configure(
                connection,
                opts={
                    "compare_type": True,
                    "compare_server_default": True,
                },
            )
            assert compare_metadata(context, Base.metadata) == []
            trigger_count = connection.scalar(
                text(
                    "SELECT count(*) FROM pg_trigger "
                    "WHERE tgname = 'trg_knowledge_audit_events_v2_append_only' "
                    "AND NOT tgisinternal"
                )
            )
            assert trigger_count == 1
    finally:
        engine.dispose()


def test_server_recording_time_uses_insert_time_not_transaction_start(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    service = KnowledgeAuditService(factory, clock=DelayedSystemClock())

    result = service.create(_create_command())

    assert result.audit_event is not None
    assert result.audit_event.recorded_at >= result.audit_event.occurred_at


def test_create_update_evidence_provenance_noop_and_stale_atomicity(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    service = _service(factory)
    object_id = _created(service)
    actor = LifecycleActor(
        actor_id="synthetic-author",
        role="knowledge_author",
    )

    material = service.update(
        GovernedKnowledgeUpdateCommand(
            organization_id="synthetic-org",
            update=KnowledgeObjectV2UpdateCommand(
                object_id=object_id,
                expected_revision=1,
                replacement=_state(content={"flag": False, "count": 1}),
            ),
            actor=actor,
            reason_or_note="Change synthetic content.",
            correlation_id=uuid4(),
        )
    )
    evidence_only = service.update(
        GovernedKnowledgeUpdateCommand(
            organization_id="synthetic-org",
            update=KnowledgeObjectV2UpdateCommand(
                object_id=object_id,
                expected_revision=2,
                replacement=_state(content={"flag": False, "count": 1}),
            ),
            evidence=_evidence(title="Changed synthetic evidence"),
            actor=actor,
            reason_or_note="Change synthetic evidence metadata.",
            correlation_id=uuid4(),
        )
    )
    provenance_only = service.update(
        GovernedKnowledgeUpdateCommand(
            organization_id="synthetic-org",
            update=KnowledgeObjectV2UpdateCommand(
                object_id=object_id,
                expected_revision=3,
                replacement=_state(content={"flag": False, "count": 1}),
            ),
            provenance=_provenance(note="Changed synthetic provenance"),
            actor=actor,
            reason_or_note="Change synthetic provenance metadata.",
            correlation_id=uuid4(),
        )
    )
    noop = service.update(
        GovernedKnowledgeUpdateCommand(
            organization_id="synthetic-org",
            update=KnowledgeObjectV2UpdateCommand(
                object_id=object_id,
                expected_revision=4,
                replacement=_state(content={"count": 1, "flag": False}),
            ),
            actor=actor,
            reason_or_note="Dictionary insertion order only.",
            correlation_id=uuid4(),
        )
    )
    with pytest.raises(KnowledgeObjectV2RepositoryError, match="stale_revision"):
        service.update(
            GovernedKnowledgeUpdateCommand(
                organization_id="synthetic-org",
                update=KnowledgeObjectV2UpdateCommand(
                    object_id=object_id,
                    expected_revision=3,
                    replacement=_state(content={"flag": False, "count": 1}),
                ),
                actor=actor,
                reason_or_note="Synthetic stale update.",
                correlation_id=uuid4(),
            )
        )

    history = service.history_for_object(
        organization_id="synthetic-org",
        object_id=object_id,
    )
    assert tuple(event.event_type for event in history) == (
        KnowledgeAuditEventType.CREATE,
        KnowledgeAuditEventType.UPDATE,
        KnowledgeAuditEventType.UPDATE,
        KnowledgeAuditEventType.UPDATE,
    )
    assert material.audit_event is not None
    assert material.audit_event.changed_fields == (KnowledgeAuditChangedField.CONTENT,)
    assert evidence_only.audit_event is not None
    assert evidence_only.audit_event.changed_fields == (KnowledgeAuditChangedField.EVIDENCE,)
    assert provenance_only.audit_event is not None
    assert provenance_only.audit_event.changed_fields == (KnowledgeAuditChangedField.PROVENANCE,)
    assert noop.audit_event is None
    assert tuple(event.audit_sequence for event in history) == tuple(
        sorted(event.audit_sequence for event in history)
    )


def _advance_to(
    service: KnowledgeAuditService,
    *,
    object_id: UUID,
    target: LifecycleState,
) -> None:
    if target is LifecycleState.DRAFT:
        return
    submit = service.transition(
        organization_id="synthetic-org",
        command=SubmitDraftCommand(
            object_id=object_id,
            expected_revision=1,
            actor=LifecycleActor(
                actor_id="synthetic-author",
                role="knowledge_author",
            ),
            submission_note="Submit synthetic draft.",
        ),
        correlation_id=uuid4(),
    )
    if target is LifecycleState.CAPTURED:
        return
    if target is LifecycleState.REJECTED:
        assert submit.knowledge is not None
        service.transition(
            organization_id="synthetic-org",
            command=RejectCapturedCommand(
                object_id=object_id,
                expected_revision=2,
                actor=LifecycleActor(
                    actor_id="synthetic-reviewer",
                    role="reviewer",
                ),
                rejection_reason="Synthetic rejection.",
            ),
            correlation_id=uuid4(),
        )
        return
    service.transition(
        organization_id="synthetic-org",
        command=CompleteReviewCommand(
            object_id=object_id,
            expected_revision=2,
            actor=LifecycleActor(
                actor_id="synthetic-reviewer",
                role="reviewer",
            ),
            review_note="Synthetic review.",
        ),
        correlation_id=uuid4(),
    )
    if target is LifecycleState.REVIEWED:
        return
    service.transition(
        organization_id="synthetic-org",
        command=ValidateReviewedCommand(
            object_id=object_id,
            expected_revision=3,
            actor=LifecycleActor(
                actor_id="synthetic-validator",
                role="validator",
            ),
            validation_note="Synthetic validation.",
        ),
        correlation_id=uuid4(),
    )
    if target is LifecycleState.VALIDATED:
        return
    service.transition(
        organization_id="synthetic-org",
        command=ApproveValidatedCommand(
            object_id=object_id,
            expected_revision=4,
            actor=LifecycleActor(
                actor_id="synthetic-approver",
                role="approver",
            ),
            approval_note="Synthetic approval.",
        ),
        correlation_id=uuid4(),
    )


def _transition_command(
    action: LifecycleAction,
    *,
    object_id: UUID,
    revision: int,
) -> LifecycleTransitionCommand:
    actor = LifecycleActor(
        actor_id="synthetic-steward",
        role="knowledge_steward",
    )
    if action is LifecycleAction.SUBMIT_DRAFT:
        return SubmitDraftCommand(
            object_id=object_id,
            expected_revision=revision,
            actor=actor,
            submission_note="Submit.",
        )
    if action is LifecycleAction.REQUEST_CAPTURED_CORRECTION:
        return RequestCapturedCorrectionCommand(
            object_id=object_id,
            expected_revision=revision,
            actor=LifecycleActor(actor_id="reviewer", role="reviewer"),
            correction_reason="Correct.",
        )
    if action is LifecycleAction.COMPLETE_REVIEW:
        return CompleteReviewCommand(
            object_id=object_id,
            expected_revision=revision,
            actor=LifecycleActor(actor_id="reviewer", role="reviewer"),
            review_note="Review.",
        )
    if action is LifecycleAction.REJECT_CAPTURED:
        return RejectCapturedCommand(
            object_id=object_id,
            expected_revision=revision,
            actor=LifecycleActor(actor_id="reviewer", role="reviewer"),
            rejection_reason="Reject.",
        )
    if action is LifecycleAction.REQUEST_REVIEWED_CORRECTION:
        return RequestReviewedCorrectionCommand(
            object_id=object_id,
            expected_revision=revision,
            actor=actor,
            correction_reason="Correct.",
        )
    if action is LifecycleAction.VALIDATE_REVIEWED:
        return ValidateReviewedCommand(
            object_id=object_id,
            expected_revision=revision,
            actor=LifecycleActor(actor_id="validator", role="validator"),
            validation_note="Validate.",
        )
    if action is LifecycleAction.REJECT_REVIEWED:
        return RejectReviewedCommand(
            object_id=object_id,
            expected_revision=revision,
            actor=actor,
            rejection_reason="Reject.",
        )
    if action is LifecycleAction.REQUEST_VALIDATED_CORRECTION:
        return RequestValidatedCorrectionCommand(
            object_id=object_id,
            expected_revision=revision,
            actor=actor,
            correction_reason="Correct.",
        )
    if action is LifecycleAction.APPROVE_VALIDATED:
        return ApproveValidatedCommand(
            object_id=object_id,
            expected_revision=revision,
            actor=LifecycleActor(actor_id="approver", role="approver"),
            approval_note="Approve.",
        )
    if action is LifecycleAction.REJECT_VALIDATED:
        return RejectValidatedCommand(
            object_id=object_id,
            expected_revision=revision,
            actor=actor,
            rejection_reason="Reject.",
        )
    if action is LifecycleAction.DEPRECATE_APPROVED:
        return DeprecateApprovedCommand(
            object_id=object_id,
            expected_revision=revision,
            actor=actor,
            deprecation_reason="Deprecate.",
        )
    if action is LifecycleAction.REOPEN_REJECTED:
        return ReopenRejectedCommand(
            object_id=object_id,
            expected_revision=revision,
            actor=actor,
            reopen_reason="Reopen.",
        )
    raise AssertionError(f"unsupported transition action {action}")


_LIFECYCLE_CASES = (
    (LifecycleAction.SUBMIT_DRAFT, LifecycleState.DRAFT, 1),
    (LifecycleAction.REQUEST_CAPTURED_CORRECTION, LifecycleState.CAPTURED, 2),
    (LifecycleAction.COMPLETE_REVIEW, LifecycleState.CAPTURED, 2),
    (LifecycleAction.REJECT_CAPTURED, LifecycleState.CAPTURED, 2),
    (LifecycleAction.REQUEST_REVIEWED_CORRECTION, LifecycleState.REVIEWED, 3),
    (LifecycleAction.VALIDATE_REVIEWED, LifecycleState.REVIEWED, 3),
    (LifecycleAction.REJECT_REVIEWED, LifecycleState.REVIEWED, 3),
    (
        LifecycleAction.REQUEST_VALIDATED_CORRECTION,
        LifecycleState.VALIDATED,
        4,
    ),
    (LifecycleAction.APPROVE_VALIDATED, LifecycleState.VALIDATED, 4),
    (LifecycleAction.REJECT_VALIDATED, LifecycleState.VALIDATED, 4),
    (LifecycleAction.DEPRECATE_APPROVED, LifecycleState.APPROVED, 5),
    (LifecycleAction.REOPEN_REJECTED, LifecycleState.REJECTED, 3),
)


@pytest.mark.parametrize(("action", "source", "revision"), _LIFECYCLE_CASES)
def test_every_lifecycle_transition_appends_exactly_one_mapped_event(
    migrated_store: tuple[Engine, sessionmaker[Session]],
    action: LifecycleAction,
    source: LifecycleState,
    revision: int,
) -> None:
    _, factory = migrated_store
    service = _service(factory)
    object_id = _created(service)
    _advance_to(service, object_id=object_id, target=source)
    before = service.history_for_object(
        organization_id="synthetic-org",
        object_id=object_id,
    )

    result = service.transition(
        organization_id="synthetic-org",
        command=_transition_command(
            action,
            object_id=object_id,
            revision=revision,
        ),
        correlation_id=uuid4(),
    )
    after = service.history_for_object(
        organization_id="synthetic-org",
        object_id=object_id,
    )

    assert result.audit_event is not None
    assert len(after) == len(before) + 1
    assert result.audit_event.lifecycle_action is action
    assert result.audit_event.event_type is audit_event_type_for_lifecycle_action(action)
    assert result.audit_event.changed_fields == (
        KnowledgeAuditChangedField.LIFECYCLE_STATE,
        KnowledgeAuditChangedField.REVISION,
    )


def test_draft_delete_retains_history_without_object_content(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    service = _service(factory)
    object_id = _created(service)

    result = service.delete_draft(
        organization_id="synthetic-org",
        command=DeleteDraftCommand(
            object_id=object_id,
            expected_revision=1,
            actor=LifecycleActor(
                actor_id="synthetic-author",
                role="knowledge_author",
            ),
            reason="Delete accidental synthetic draft.",
        ),
        correlation_id=uuid4(),
    )
    history = service.history_for_object(
        organization_id="synthetic-org",
        object_id=object_id,
    )

    assert result.knowledge is None
    assert tuple(event.event_type for event in history) == (
        KnowledgeAuditEventType.CREATE,
        KnowledgeAuditEventType.DRAFT_DELETE,
    )
    assert history[-1].changed_fields == ()
    assert "Synthetic PostgreSQL audit observation" not in history[-1].model_dump_json()
    with factory() as session:
        assert session.get(KnowledgeObjectV2Record, object_id) is None


def test_audit_failure_rolls_back_create_and_update(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    failing_service = _service(
        factory,
        participant_factory=FailingAuditParticipant,
    )
    with pytest.raises(RuntimeError, match="audit participant failure"):
        failing_service.create(_create_command())
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(KnowledgeObjectV2Record)) == 0
        assert session.scalar(select(func.count()).select_from(KnowledgeAuditEventRecord)) == 0

    working_service = _service(factory)
    object_id = _created(working_service)
    with pytest.raises(RuntimeError, match="audit participant failure"):
        failing_service.update(
            GovernedKnowledgeUpdateCommand(
                organization_id="synthetic-org",
                update=KnowledgeObjectV2UpdateCommand(
                    object_id=object_id,
                    expected_revision=1,
                    replacement=_state(content={"flag": False, "count": 1}),
                ),
                actor=LifecycleActor(
                    actor_id="synthetic-author",
                    role="knowledge_author",
                ),
                reason_or_note="Synthetic failing update.",
                correlation_id=uuid4(),
            )
        )
    with factory() as session:
        root = session.get(KnowledgeObjectV2Record, object_id)
        assert root is not None
        assert root.revision == 1
        count = session.scalar(
            select(func.count())
            .select_from(KnowledgeAuditEventRecord)
            .where(
                KnowledgeAuditEventRecord.organization_id == "synthetic-org",
                KnowledgeAuditEventRecord.object_id == object_id,
            )
        )
        assert count == 1


def test_post_append_failure_rolls_back_object_and_audit_row(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    _, factory = migrated_store
    command = _create_command()
    service = _service(
        factory,
        participant_factory=AppendThenFailAuditParticipant,
    )

    with pytest.raises(RuntimeError, match="post-append participant failure"):
        service.create(command)

    with factory() as session:
        object_count = session.scalar(select(func.count()).select_from(KnowledgeObjectV2Record))
        audit_count = session.scalar(
            select(func.count())
            .select_from(KnowledgeAuditEventRecord)
            .where(
                KnowledgeAuditEventRecord.organization_id == command.create.organization_id,
                KnowledgeAuditEventRecord.correlation_id == command.correlation_id,
            )
        )
    assert object_count == 0
    assert audit_count == 0


def test_database_guard_isolation_order_and_legacy_event_separation(
    migrated_store: tuple[Engine, sessionmaker[Session]],
) -> None:
    engine, factory = migrated_store
    service = _service(factory)
    object_id = _created(service)
    update = service.update(
        GovernedKnowledgeUpdateCommand(
            organization_id="synthetic-org",
            update=KnowledgeObjectV2UpdateCommand(
                object_id=object_id,
                expected_revision=1,
                replacement=_state(content={"flag": True, "count": 1.0}),
            ),
            actor=LifecycleActor(
                actor_id="synthetic-author",
                role="knowledge_author",
            ),
            reason_or_note="Preserve scalar type identity.",
            correlation_id=uuid4(),
        )
    )
    assert update.audit_event is not None
    assert update.audit_event.changed_fields == (KnowledgeAuditChangedField.CONTENT,)
    history = service.history_for_object(
        organization_id="synthetic-org",
        object_id=object_id,
    )
    assert len({event.occurred_at for event in history}) == 1
    assert tuple(event.audit_sequence for event in history) == tuple(
        sorted(event.audit_sequence for event in history)
    )
    assert (
        service.history_for_object(
            organization_id="other-synthetic-org",
            object_id=object_id,
        )
        == ()
    )
    assert (
        service.get_event(
            organization_id="other-synthetic-org",
            object_id=object_id,
            event_id=history[0].event_id,
        )
        is None
    )
    assert (
        service.get_event(
            organization_id="synthetic-org",
            object_id=object_id,
            event_id=history[0].event_id,
        )
        == history[0]
    )

    update_connection = engine.connect()
    update_transaction = update_connection.begin()
    try:
        with pytest.raises(DBAPIError, match="append-only"):
            update_connection.execute(
                text(
                    "UPDATE knowledge_audit_events_v2 "
                    "SET reason_or_note = 'forbidden' "
                    "WHERE event_id = :event_id"
                ),
                {"event_id": history[0].event_id},
            )
    finally:
        update_transaction.rollback()
        update_connection.close()

    delete_connection = engine.connect()
    delete_transaction = delete_connection.begin()
    try:
        with pytest.raises(DBAPIError, match="append-only"):
            delete_connection.execute(
                text("DELETE FROM knowledge_audit_events_v2 WHERE event_id = :event_id"),
                {"event_id": history[0].event_id},
            )
    finally:
        delete_transaction.rollback()
        delete_connection.close()

    with factory() as session:
        legacy = EventRepository(session).create(
            EnterpriseEvent(
                title="Synthetic caller-created legacy event",
                event_type=EventType.KNOWLEDGE_CREATED,
                actor="synthetic-caller",
                related_object_id=object_id,
                evidence=["synthetic://legacy/evidence"],
            )
        )
        assert EventRepository(session).get(legacy.object_id) is not None
    assert (
        len(
            service.history_for_object(
                organization_id="synthetic-org",
                object_id=object_id,
            )
        )
        == 2
    )


def test_cleanup_helper_leaves_zero_schema_objects(
    live_database_url: str,
) -> None:
    schema_name = _schema_name()
    admin_engine = create_engine(live_database_url, poolclass=NullPool)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
    _run_upgrade(live_database_url, schema_name)
    _drop_schema_and_assert_absent(admin_engine, schema_name)
    admin_engine.dispose()
