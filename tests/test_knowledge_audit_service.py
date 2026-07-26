from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from smartcoat.domain.base import LifecycleState
from smartcoat.domain.context_references import KnowledgeContext
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
from smartcoat.domain.knowledge_audit import (
    GovernedKnowledgeCreateCommand,
    GovernedKnowledgeUpdateCommand,
    KnowledgeAuditAppendRequest,
    KnowledgeAuditChangedField,
    KnowledgeAuditEvent,
    KnowledgeAuditEventType,
)
from smartcoat.domain.knowledge_lifecycle import (
    ApproveValidatedCommand,
    CompleteReviewCommand,
    DeleteDraftCommand,
    DeprecateApprovedCommand,
    DraftDeletionFacts,
    DraftDeletionPlan,
    LifecycleAction,
    LifecycleActor,
    LifecycleHistoryFacts,
    LifecycleMutationPlan,
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
    KnowledgeObjectUpdateError,
    KnowledgeObjectV2CoreRecord,
    KnowledgeObjectV2CreateCommand,
    KnowledgeObjectV2MutableState,
    KnowledgeObjectV2PersistedStateSnapshot,
    KnowledgeObjectV2UpdateCommand,
    OwnerReference,
    evaluate_knowledge_object_update,
)
from smartcoat.services.knowledge_audit_service import (
    KnowledgeAuditService,
    KnowledgeAuditServiceError,
)
from smartcoat.storage.repositories.knowledge_audit_repository import (
    KnowledgeAuditParticipant,
)
from smartcoat.storage.repositories.knowledge_v2_repository import (
    KnowledgeObjectV2RepositoryError,
)

NOW = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)


class FixedClock:
    def now(self) -> datetime:
        return NOW


def _state(
    *,
    content: dict[str, object] | None = None,
) -> KnowledgeObjectV2MutableState:
    return KnowledgeObjectV2MutableState(
        title="Synthetic audit observation",
        description="Synthetic metadata-only test.",
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        owner=OwnerReference(
            owner_id="synthetic-owner",
            role="knowledge_author",
        ),
        confidentiality=ConfidentialityLevel.INTERNAL,
        tags=("synthetic",),
        content=content or {"result": True, "sample_count": 3},
        context=KnowledgeContext(references=[]),
        evidence_ids=("synthetic-evidence-1",),
    )


def _evidence(*, title: str = "Synthetic evidence") -> tuple[EvidenceReference, ...]:
    return (
        EvidenceReference(
            evidence_id="synthetic-evidence-1",
            evidence_type=EvidenceType.OBSERVATION,
            completeness=EvidenceCompleteness.COMPLETE,
            title=title,
            source_reference="synthetic://evidence/1",
            captured_by="synthetic-author",
            captured_at=NOW - timedelta(minutes=2),
        ),
    )


def _provenance(*, note: str = "Initial synthetic capture") -> ProvenanceV2:
    return ProvenanceV2(
        source_system="synthetic-test",
        source_reference="synthetic://knowledge/1",
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
        reason_or_note="Create synthetic draft.",
        correlation_id=uuid4(),
    )


def _composition(
    *,
    object_id: UUID,
    revision: int,
    lifecycle: LifecycleState,
    state: KnowledgeObjectV2MutableState,
    evidence: Sequence[EvidenceReference],
    provenance: ProvenanceV2,
) -> KnowledgeObjectV2EvidenceComposition:
    return KnowledgeObjectV2EvidenceComposition(
        core=KnowledgeObjectV2CoreRecord(
            object_id=object_id,
            organization_id="synthetic-org",
            revision=revision,
            lifecycle_state=lifecycle,
            created_at=NOW - timedelta(hours=1),
            updated_at=NOW + timedelta(seconds=revision),
            mutable_state=KnowledgeObjectV2PersistedStateSnapshot.from_mutable_state(state),
        ),
        evidence=tuple(evidence),
        provenance=provenance,
    )


class FakeKnowledgeRepository:
    def __init__(self) -> None:
        self.objects: dict[UUID, KnowledgeObjectV2EvidenceComposition] = {}
        self.history: dict[UUID, LifecycleHistoryFacts] = {}

    def stage_create(
        self,
        command: KnowledgeObjectV2CreateCommand,
        *,
        evidence: Sequence[EvidenceReference],
        provenance: ProvenanceV2,
    ) -> KnowledgeObjectV2EvidenceComposition:
        object_id = uuid4()
        created = _composition(
            object_id=object_id,
            revision=1,
            lifecycle=LifecycleState.DRAFT,
            state=command.mutable_state,
            evidence=evidence,
            provenance=provenance,
        )
        self.objects[object_id] = created
        self.history[object_id] = LifecycleHistoryFacts(
            has_ever_left_draft=False,
        )
        return created

    def load_for_controlled_mutation(
        self,
        *,
        object_id: UUID,
        organization_id: str,
    ) -> KnowledgeObjectV2EvidenceComposition:
        current = self.objects.get(object_id)
        if current is None or current.core.organization_id != organization_id:
            raise KnowledgeObjectV2RepositoryError(
                "knowledge_object_not_found",
                "synthetic object not found",
            )
        return current

    def stage_material_update(
        self,
        *,
        organization_id: str,
        object_id: UUID,
        command: KnowledgeObjectV2UpdateCommand,
        evidence: Sequence[EvidenceReference] | None = None,
        provenance: ProvenanceV2 | None = None,
    ) -> KnowledgeObjectV2EvidenceComposition:
        current = self.load_for_controlled_mutation(
            object_id=object_id,
            organization_id=organization_id,
        )
        try:
            evaluate_knowledge_object_update(current.core, command)
        except KnowledgeObjectUpdateError as error:
            raise KnowledgeObjectV2RepositoryError(error.code, str(error)) from error
        replacement_evidence = tuple(evidence) if evidence is not None else current.evidence
        replacement_provenance = provenance or current.provenance
        desired = _composition(
            object_id=object_id,
            revision=current.core.revision,
            lifecycle=current.core.lifecycle_state,
            state=command.replacement,
            evidence=replacement_evidence,
            provenance=replacement_provenance,
        )
        if (
            desired.core.mutable_state.canonical_state_json
            == current.core.mutable_state.canonical_state_json
            and tuple(item.canonical_metadata_json for item in desired.evidence)
            == tuple(item.canonical_metadata_json for item in current.evidence)
            and desired.provenance.model_dump_json() == current.provenance.model_dump_json()
        ):
            return current
        updated = _composition(
            object_id=object_id,
            revision=current.core.revision + 1,
            lifecycle=current.core.lifecycle_state,
            state=command.replacement,
            evidence=replacement_evidence,
            provenance=replacement_provenance,
        )
        self.objects[object_id] = updated
        return updated

    def lifecycle_history_facts(
        self,
        *,
        object_id: UUID,
        organization_id: str,
    ) -> LifecycleHistoryFacts:
        self.load_for_controlled_mutation(
            object_id=object_id,
            organization_id=organization_id,
        )
        return self.history[object_id]

    def stage_lifecycle_transition(
        self,
        *,
        organization_id: str,
        plan: LifecycleMutationPlan,
    ) -> KnowledgeObjectV2EvidenceComposition:
        current = self.load_for_controlled_mutation(
            object_id=plan.object_id,
            organization_id=organization_id,
        )
        updated = _composition(
            object_id=plan.object_id,
            revision=plan.resulting_revision,
            lifecycle=plan.to_lifecycle,
            state=current.core.mutable_state.to_mutable_state(),
            evidence=current.evidence,
            provenance=current.provenance,
        )
        self.objects[plan.object_id] = updated
        self.history[plan.object_id] = LifecycleHistoryFacts(
            has_ever_left_draft=True,
            last_pre_deprecation_lifecycle=(
                plan.from_lifecycle if plan.to_lifecycle is LifecycleState.DEPRECATED else None
            ),
        )
        return updated

    def compute_inbound_governed_reference_facts(
        self,
        *,
        object_id: UUID,
        organization_id: str,
    ) -> DraftDeletionFacts:
        self.load_for_controlled_mutation(
            object_id=object_id,
            organization_id=organization_id,
        )
        return DraftDeletionFacts(has_inbound_governed_references=False)

    def stage_eligible_draft_deletion(
        self,
        *,
        organization_id: str,
        plan: DraftDeletionPlan,
    ) -> DraftDeletionPlan:
        self.load_for_controlled_mutation(
            object_id=plan.object_id,
            organization_id=organization_id,
        )
        del self.objects[plan.object_id]
        del self.history[plan.object_id]
        return plan

    def force_lifecycle(
        self,
        *,
        object_id: UUID,
        lifecycle: LifecycleState,
        revision: int,
    ) -> None:
        current = self.objects[object_id]
        self.objects[object_id] = _composition(
            object_id=object_id,
            revision=revision,
            lifecycle=lifecycle,
            state=current.core.mutable_state.to_mutable_state(),
            evidence=current.evidence,
            provenance=current.provenance,
        )
        self.history[object_id] = LifecycleHistoryFacts(
            has_ever_left_draft=lifecycle is not LifecycleState.DRAFT,
        )


class FailingMutationRepository(FakeKnowledgeRepository):
    def stage_create(
        self,
        command: KnowledgeObjectV2CreateCommand,
        *,
        evidence: Sequence[EvidenceReference],
        provenance: ProvenanceV2,
    ) -> KnowledgeObjectV2EvidenceComposition:
        del command, evidence, provenance
        raise RuntimeError("synthetic object mutation failure")


class CapturingParticipant(KnowledgeAuditParticipant):
    def __init__(self, sink: list[KnowledgeAuditEvent]) -> None:
        self._sink = sink
        self._request: KnowledgeAuditAppendRequest | None = None
        self._event: KnowledgeAuditEvent | None = None

    def queue(self, request: KnowledgeAuditAppendRequest) -> None:
        if self._request is not None:
            raise RuntimeError("duplicate_audit_queue")
        self._request = request

    def flush(self, session: Session) -> None:
        assert session is not None
        if self._request is None:
            return
        request = self._request
        event = KnowledgeAuditEvent(
            **request.model_dump(),
            event_id=uuid4(),
            recorded_at=request.occurred_at + timedelta(seconds=1),
            audit_sequence=len(self._sink) + 1,
        )
        self._sink.append(event)
        self._event = event

    def single_appended_event(self) -> KnowledgeAuditEvent:
        if self._event is None:
            raise RuntimeError("no appended event")
        return self._event


class FailingParticipant(CapturingParticipant):
    def flush(self, session: Session) -> None:
        raise RuntimeError("synthetic audit flush failure")


class FakeUnitOfWork:
    def __init__(
        self,
        repository: FakeKnowledgeRepository,
        participants: Sequence[KnowledgeAuditParticipant],
    ) -> None:
        self.knowledge_objects = repository
        self._participants = participants
        self._snapshot: dict[UUID, KnowledgeObjectV2EvidenceComposition] = {}
        self._history_snapshot: dict[UUID, LifecycleHistoryFacts] = {}
        self._finished = False

    def __enter__(self) -> FakeUnitOfWork:
        self._snapshot = dict(self.knowledge_objects.objects)
        self._history_snapshot = dict(self.knowledge_objects.history)
        return self

    def __exit__(self, *args: object) -> None:
        if not self._finished:
            self._restore()

    def _restore(self) -> None:
        self.knowledge_objects.objects = dict(self._snapshot)
        self.knowledge_objects.history = dict(self._history_snapshot)

    def commit(self) -> None:
        try:
            for participant in self._participants:
                participant.flush(MagicMock(spec=Session))
        except Exception:
            self._restore()
            self._finished = True
            raise
        self._finished = True


class FakeUnitOfWorkFactory:
    def __init__(self, repository: FakeKnowledgeRepository) -> None:
        self.repository = repository

    def __call__(
        self,
        session_factory: Callable[[], Session],
        *,
        participants: Sequence[KnowledgeAuditParticipant],
    ) -> Any:
        del session_factory
        return FakeUnitOfWork(self.repository, participants)


def _service(
    *,
    repository: FakeKnowledgeRepository | None = None,
    sink: list[KnowledgeAuditEvent] | None = None,
    failing_audit: bool = False,
) -> tuple[KnowledgeAuditService, FakeKnowledgeRepository, list[KnowledgeAuditEvent]]:
    repository = repository or FakeKnowledgeRepository()
    sink = sink if sink is not None else []

    def participant_factory() -> KnowledgeAuditParticipant:
        if failing_audit:
            return FailingParticipant(sink)
        return CapturingParticipant(sink)

    service = KnowledgeAuditService(
        lambda: MagicMock(spec=Session),
        clock=FixedClock(),
        participant_factory=participant_factory,
        unit_of_work_factory=FakeUnitOfWorkFactory(repository),
    )
    return service, repository, sink


def _created(
    service: KnowledgeAuditService,
) -> tuple[UUID, KnowledgeAuditEvent]:
    result = service.create(_create_command())
    assert result.knowledge is not None
    assert result.audit_event is not None
    return result.knowledge.core.object_id, result.audit_event


def test_create_and_material_update_each_create_exactly_one_event() -> None:
    service, _, events = _service()
    object_id, created_event = _created(service)
    replacement = _state(content={"result": False})

    result = service.update(
        GovernedKnowledgeUpdateCommand(
            organization_id="synthetic-org",
            update=KnowledgeObjectV2UpdateCommand(
                object_id=object_id,
                expected_revision=1,
                replacement=replacement,
            ),
            actor=LifecycleActor(
                actor_id="synthetic-author",
                role="knowledge_author",
            ),
            reason_or_note="Correct synthetic result.",
            correlation_id=uuid4(),
        )
    )

    assert created_event.event_type is KnowledgeAuditEventType.CREATE
    assert result.audit_event is not None
    assert result.audit_event.event_type is KnowledgeAuditEventType.UPDATE
    assert result.audit_event.changed_fields == (KnowledgeAuditChangedField.CONTENT,)
    assert len(events) == 2


def test_evidence_only_and_provenance_only_updates_are_material() -> None:
    service, _, events = _service()
    object_id, _ = _created(service)
    actor = LifecycleActor(
        actor_id="synthetic-author",
        role="knowledge_author",
    )
    evidence_result = service.update(
        GovernedKnowledgeUpdateCommand(
            organization_id="synthetic-org",
            update=KnowledgeObjectV2UpdateCommand(
                object_id=object_id,
                expected_revision=1,
                replacement=_state(),
            ),
            evidence=_evidence(title="Changed synthetic evidence"),
            actor=actor,
            reason_or_note="Update evidence metadata.",
            correlation_id=uuid4(),
        )
    )
    provenance_result = service.update(
        GovernedKnowledgeUpdateCommand(
            organization_id="synthetic-org",
            update=KnowledgeObjectV2UpdateCommand(
                object_id=object_id,
                expected_revision=2,
                replacement=_state(),
            ),
            provenance=_provenance(note="Changed synthetic transformation"),
            actor=actor,
            reason_or_note="Update provenance metadata.",
            correlation_id=uuid4(),
        )
    )

    assert evidence_result.audit_event is not None
    assert evidence_result.audit_event.changed_fields == (KnowledgeAuditChangedField.EVIDENCE,)
    assert provenance_result.audit_event is not None
    assert provenance_result.audit_event.changed_fields == (KnowledgeAuditChangedField.PROVENANCE,)
    assert len(events) == 3


def test_dictionary_order_noop_creates_zero_events_and_stale_fails_first() -> None:
    service, repository, events = _service()
    object_id, _ = _created(service)
    actor = LifecycleActor(
        actor_id="synthetic-author",
        role="knowledge_author",
    )
    reordered = _state(content={"sample_count": 3, "result": True})
    noop = service.update(
        GovernedKnowledgeUpdateCommand(
            organization_id="synthetic-org",
            update=KnowledgeObjectV2UpdateCommand(
                object_id=object_id,
                expected_revision=1,
                replacement=reordered,
            ),
            actor=actor,
            reason_or_note="No material change.",
            correlation_id=uuid4(),
        )
    )
    before = repository.objects[object_id]

    with pytest.raises(KnowledgeObjectV2RepositoryError, match="stale_revision"):
        service.update(
            GovernedKnowledgeUpdateCommand(
                organization_id="synthetic-org",
                update=KnowledgeObjectV2UpdateCommand(
                    object_id=object_id,
                    expected_revision=99,
                    replacement=reordered,
                ),
                actor=actor,
                reason_or_note="Stale request.",
                correlation_id=uuid4(),
            )
        )

    assert noop.audit_event is None
    assert repository.objects[object_id] == before
    assert len(events) == 1


_EDITABILITY_CASES = (
    (LifecycleState.DRAFT, 1, True),
    (LifecycleState.CAPTURED, 2, False),
    (LifecycleState.REVIEWED, 3, False),
    (LifecycleState.VALIDATED, 4, False),
    (LifecycleState.APPROVED, 5, False),
    (LifecycleState.REJECTED, 3, False),
    (LifecycleState.DEPRECATED, 6, False),
)


def _update_command(
    *,
    object_id: UUID,
    expected_revision: int,
    replacement: KnowledgeObjectV2MutableState,
    organization_id: str = "synthetic-org",
) -> GovernedKnowledgeUpdateCommand:
    return GovernedKnowledgeUpdateCommand(
        organization_id=organization_id,
        update=KnowledgeObjectV2UpdateCommand(
            object_id=object_id,
            expected_revision=expected_revision,
            replacement=replacement,
        ),
        actor=LifecycleActor(
            actor_id="synthetic-author",
            role="knowledge_author",
        ),
        reason_or_note="Synthetic governed update.",
        correlation_id=uuid4(),
    )


@pytest.mark.parametrize(
    ("lifecycle", "revision", "editable"),
    _EDITABILITY_CASES,
)
def test_ir_c01_seven_state_material_update_matrix(
    lifecycle: LifecycleState,
    revision: int,
    editable: bool,
) -> None:
    service, repository, events = _service()
    object_id, _ = _created(service)
    repository.force_lifecycle(
        object_id=object_id,
        lifecycle=lifecycle,
        revision=revision,
    )
    before = repository.objects[object_id]
    before_events = tuple(events)
    command = _update_command(
        object_id=object_id,
        expected_revision=revision,
        replacement=_state(content={"result": False, "sample_count": 3}),
    )

    if editable:
        result = service.update(command)
        assert result.knowledge is not None
        assert result.knowledge.core.revision == revision + 1
        assert result.audit_event is not None
        assert result.audit_event.event_type is KnowledgeAuditEventType.UPDATE
        return

    with pytest.raises(KnowledgeAuditServiceError) as error:
        service.update(command)

    assert error.value.code == "knowledge_update_lifecycle_forbidden"
    assert repository.objects[object_id] == before
    assert tuple(events) == before_events


@pytest.mark.parametrize(
    ("lifecycle", "revision", "editable"),
    _EDITABILITY_CASES,
)
def test_ir_c01_seven_state_noop_update_matrix(
    lifecycle: LifecycleState,
    revision: int,
    editable: bool,
) -> None:
    service, repository, events = _service()
    object_id, _ = _created(service)
    repository.force_lifecycle(
        object_id=object_id,
        lifecycle=lifecycle,
        revision=revision,
    )
    before = repository.objects[object_id]
    before_events = tuple(events)
    command = _update_command(
        object_id=object_id,
        expected_revision=revision,
        replacement=_state(),
    )

    if editable:
        result = service.update(command)
        assert result.knowledge == before
        assert result.audit_event is None
        assert tuple(events) == before_events
        return

    with pytest.raises(KnowledgeAuditServiceError) as error:
        service.update(command)

    assert error.value.code == "knowledge_update_lifecycle_forbidden"
    assert repository.objects[object_id] == before
    assert tuple(events) == before_events


def test_ir_c01_stale_and_organization_precedence_remain_fail_closed() -> None:
    service, repository, events = _service()
    object_id, _ = _created(service)
    repository.force_lifecycle(
        object_id=object_id,
        lifecycle=LifecycleState.APPROVED,
        revision=5,
    )
    before = repository.objects[object_id]
    before_events = tuple(events)

    with pytest.raises(KnowledgeObjectV2RepositoryError) as stale_error:
        service.update(
            _update_command(
                object_id=object_id,
                expected_revision=4,
                replacement=_state(content={"result": False}),
            )
        )
    with pytest.raises(KnowledgeObjectV2RepositoryError) as missing_error:
        service.update(
            _update_command(
                object_id=object_id,
                expected_revision=5,
                replacement=_state(content={"result": False}),
                organization_id="other-synthetic-org",
            )
        )

    assert stale_error.value.code == "stale_revision"
    assert missing_error.value.code == "knowledge_object_not_found"
    assert repository.objects[object_id] == before
    assert tuple(events) == before_events


_RETURN_TO_DRAFT_CASES: tuple[
    tuple[LifecycleState, int, LifecycleTransitionCommand],
    ...,
] = (
    (
        LifecycleState.CAPTURED,
        2,
        RequestCapturedCorrectionCommand(
            object_id=uuid4(),
            expected_revision=2,
            actor=LifecycleActor(actor_id="reviewer", role="reviewer"),
            correction_reason="Return captured knowledge to draft.",
        ),
    ),
    (
        LifecycleState.REVIEWED,
        3,
        RequestReviewedCorrectionCommand(
            object_id=uuid4(),
            expected_revision=3,
            actor=LifecycleActor(actor_id="reviewer", role="reviewer"),
            correction_reason="Return reviewed knowledge to draft.",
        ),
    ),
    (
        LifecycleState.VALIDATED,
        4,
        RequestValidatedCorrectionCommand(
            object_id=uuid4(),
            expected_revision=4,
            actor=LifecycleActor(actor_id="validator", role="validator"),
            correction_reason="Return validated knowledge to draft.",
        ),
    ),
    (
        LifecycleState.REJECTED,
        3,
        ReopenRejectedCommand(
            object_id=uuid4(),
            expected_revision=3,
            actor=LifecycleActor(
                actor_id="synthetic-author",
                role="knowledge_author",
            ),
            reopen_reason="Reopen rejected knowledge as draft.",
        ),
    ),
)


@pytest.mark.parametrize(
    ("source", "revision", "template"),
    _RETURN_TO_DRAFT_CASES,
)
def test_ir_c01_correction_or_reopen_then_draft_update_succeeds(
    source: LifecycleState,
    revision: int,
    template: LifecycleTransitionCommand,
) -> None:
    service, repository, events = _service()
    object_id, _ = _created(service)
    repository.force_lifecycle(
        object_id=object_id,
        lifecycle=source,
        revision=revision,
    )

    transition = service.transition(
        organization_id="synthetic-org",
        command=template.model_copy(update={"object_id": object_id}),
        correlation_id=uuid4(),
    )
    updated = service.update(
        _update_command(
            object_id=object_id,
            expected_revision=revision + 1,
            replacement=_state(content={"result": False}),
        )
    )

    assert transition.knowledge is not None
    assert transition.knowledge.core.lifecycle_state is LifecycleState.DRAFT
    assert updated.knowledge is not None
    assert updated.knowledge.core.lifecycle_state is LifecycleState.DRAFT
    assert updated.knowledge.core.revision == revision + 2
    assert updated.audit_event is not None
    assert tuple(event.event_type for event in events[-2:]) == (
        KnowledgeAuditEventType.CORRECTION_REQUEST
        if source is not LifecycleState.REJECTED
        else KnowledgeAuditEventType.REOPEN,
        KnowledgeAuditEventType.UPDATE,
    )


_TRANSITION_CASES: tuple[
    tuple[
        LifecycleAction,
        LifecycleState,
        LifecycleTransitionCommand,
        KnowledgeAuditEventType,
    ],
    ...,
] = (
    (
        LifecycleAction.SUBMIT_DRAFT,
        LifecycleState.DRAFT,
        SubmitDraftCommand(
            object_id=uuid4(),
            expected_revision=1,
            actor=LifecycleActor(actor_id="author", role="knowledge_author"),
            submission_note="Submit.",
        ),
        KnowledgeAuditEventType.TRANSITION,
    ),
    (
        LifecycleAction.REQUEST_CAPTURED_CORRECTION,
        LifecycleState.CAPTURED,
        RequestCapturedCorrectionCommand(
            object_id=uuid4(),
            expected_revision=2,
            actor=LifecycleActor(actor_id="reviewer", role="reviewer"),
            correction_reason="Correct.",
        ),
        KnowledgeAuditEventType.CORRECTION_REQUEST,
    ),
    (
        LifecycleAction.COMPLETE_REVIEW,
        LifecycleState.CAPTURED,
        CompleteReviewCommand(
            object_id=uuid4(),
            expected_revision=2,
            actor=LifecycleActor(actor_id="reviewer", role="reviewer"),
            review_note="Reviewed.",
        ),
        KnowledgeAuditEventType.TRANSITION,
    ),
    (
        LifecycleAction.REJECT_CAPTURED,
        LifecycleState.CAPTURED,
        RejectCapturedCommand(
            object_id=uuid4(),
            expected_revision=2,
            actor=LifecycleActor(actor_id="reviewer", role="reviewer"),
            rejection_reason="Reject.",
        ),
        KnowledgeAuditEventType.REJECT,
    ),
    (
        LifecycleAction.REQUEST_REVIEWED_CORRECTION,
        LifecycleState.REVIEWED,
        RequestReviewedCorrectionCommand(
            object_id=uuid4(),
            expected_revision=3,
            actor=LifecycleActor(actor_id="reviewer", role="reviewer"),
            correction_reason="Correct.",
        ),
        KnowledgeAuditEventType.CORRECTION_REQUEST,
    ),
    (
        LifecycleAction.VALIDATE_REVIEWED,
        LifecycleState.REVIEWED,
        ValidateReviewedCommand(
            object_id=uuid4(),
            expected_revision=3,
            actor=LifecycleActor(actor_id="validator", role="validator"),
            validation_note="Validated.",
        ),
        KnowledgeAuditEventType.TRANSITION,
    ),
    (
        LifecycleAction.REJECT_REVIEWED,
        LifecycleState.REVIEWED,
        RejectReviewedCommand(
            object_id=uuid4(),
            expected_revision=3,
            actor=LifecycleActor(actor_id="reviewer", role="reviewer"),
            rejection_reason="Reject.",
        ),
        KnowledgeAuditEventType.REJECT,
    ),
    (
        LifecycleAction.REQUEST_VALIDATED_CORRECTION,
        LifecycleState.VALIDATED,
        RequestValidatedCorrectionCommand(
            object_id=uuid4(),
            expected_revision=4,
            actor=LifecycleActor(actor_id="validator", role="validator"),
            correction_reason="Correct.",
        ),
        KnowledgeAuditEventType.CORRECTION_REQUEST,
    ),
    (
        LifecycleAction.APPROVE_VALIDATED,
        LifecycleState.VALIDATED,
        ApproveValidatedCommand(
            object_id=uuid4(),
            expected_revision=4,
            actor=LifecycleActor(actor_id="approver", role="approver"),
            approval_note="Approved.",
        ),
        KnowledgeAuditEventType.APPROVE,
    ),
    (
        LifecycleAction.REJECT_VALIDATED,
        LifecycleState.VALIDATED,
        RejectValidatedCommand(
            object_id=uuid4(),
            expected_revision=4,
            actor=LifecycleActor(actor_id="validator", role="validator"),
            rejection_reason="Reject.",
        ),
        KnowledgeAuditEventType.REJECT,
    ),
    (
        LifecycleAction.DEPRECATE_APPROVED,
        LifecycleState.APPROVED,
        DeprecateApprovedCommand(
            object_id=uuid4(),
            expected_revision=5,
            actor=LifecycleActor(actor_id="steward", role="knowledge_steward"),
            deprecation_reason="Deprecated.",
        ),
        KnowledgeAuditEventType.DEPRECATE,
    ),
    (
        LifecycleAction.REOPEN_REJECTED,
        LifecycleState.REJECTED,
        ReopenRejectedCommand(
            object_id=uuid4(),
            expected_revision=4,
            actor=LifecycleActor(actor_id="author", role="knowledge_author"),
            reopen_reason="Reopen.",
        ),
        KnowledgeAuditEventType.REOPEN,
    ),
)


@pytest.mark.parametrize(
    ("action", "source", "template", "event_type"),
    _TRANSITION_CASES,
)
def test_all_accepted_lifecycle_actions_create_one_mapped_event(
    action: LifecycleAction,
    source: LifecycleState,
    template: LifecycleTransitionCommand,
    event_type: KnowledgeAuditEventType,
) -> None:
    service, repository, events = _service()
    object_id, _ = _created(service)
    repository.force_lifecycle(
        object_id=object_id,
        lifecycle=source,
        revision=template.expected_revision,
    )
    command = template.model_copy(update={"object_id": object_id})

    result = service.transition(
        organization_id="synthetic-org",
        command=command,
        correlation_id=uuid4(),
    )

    assert result.audit_event is not None
    assert result.audit_event.lifecycle_action is action
    assert result.audit_event.event_type is event_type
    assert result.audit_event.changed_fields == (
        KnowledgeAuditChangedField.LIFECYCLE_STATE,
        KnowledgeAuditChangedField.REVISION,
    )
    assert result.audit_event.replacement_object_id is None
    assert len(events) == 2


def test_ir_c02_deprecation_preserves_optional_replacement_in_audit_sink() -> None:
    replacement_object_id = uuid4()
    service, repository, events = _service()
    object_id, _ = _created(service)
    repository.force_lifecycle(
        object_id=object_id,
        lifecycle=LifecycleState.APPROVED,
        revision=5,
    )

    with_replacement = service.transition(
        organization_id="synthetic-org",
        command=DeprecateApprovedCommand(
            object_id=object_id,
            expected_revision=5,
            actor=LifecycleActor(
                actor_id="synthetic-steward",
                role="knowledge_steward",
            ),
            deprecation_reason="Replace synthetic approved knowledge.",
            replacement_object_id=replacement_object_id,
        ),
        correlation_id=uuid4(),
    )

    assert with_replacement.audit_event is not None
    assert with_replacement.audit_event.replacement_object_id == replacement_object_id
    assert events[-1].replacement_object_id == replacement_object_id

    second_service, second_repository, second_events = _service()
    second_id, _ = _created(second_service)
    second_repository.force_lifecycle(
        object_id=second_id,
        lifecycle=LifecycleState.APPROVED,
        revision=5,
    )
    without_replacement = second_service.transition(
        organization_id="synthetic-org",
        command=DeprecateApprovedCommand(
            object_id=second_id,
            expected_revision=5,
            actor=LifecycleActor(
                actor_id="synthetic-steward",
                role="knowledge_steward",
            ),
            deprecation_reason="Deprecate without a replacement.",
        ),
        correlation_id=uuid4(),
    )

    assert without_replacement.audit_event is not None
    assert without_replacement.audit_event.replacement_object_id is None
    assert second_events[-1].replacement_object_id is None


def test_invalid_lifecycle_action_creates_no_event() -> None:
    service, _, events = _service()
    object_id, _ = _created(service)

    with pytest.raises(Exception, match="invalid_lifecycle_transition"):
        service.transition(
            organization_id="synthetic-org",
            command=CompleteReviewCommand(
                object_id=object_id,
                expected_revision=1,
                actor=LifecycleActor(actor_id="reviewer", role="reviewer"),
                review_note="Invalid from draft.",
            ),
            correlation_id=uuid4(),
        )

    assert len(events) == 1


def test_draft_deletion_retains_create_and_safe_tombstone_events() -> None:
    service, repository, events = _service()
    object_id, _ = _created(service)

    result = service.delete_draft(
        organization_id="synthetic-org",
        command=DeleteDraftCommand(
            object_id=object_id,
            expected_revision=1,
            actor=LifecycleActor(
                actor_id="synthetic-author",
                role="knowledge_author",
            ),
            reason="Remove accidental synthetic draft.",
        ),
        correlation_id=uuid4(),
    )

    assert result.knowledge is None
    assert object_id not in repository.objects
    assert tuple(event.event_type for event in events) == (
        KnowledgeAuditEventType.CREATE,
        KnowledgeAuditEventType.DRAFT_DELETE,
    )
    assert events[-1].changed_fields == ()
    assert "title" not in events[-1].model_dump_json()


def test_audit_flush_failure_rolls_back_object_create() -> None:
    service, repository, events = _service(failing_audit=True)

    with pytest.raises(RuntimeError, match="audit flush failure"):
        service.create(_create_command())

    assert repository.objects == {}
    assert events == []


def test_object_mutation_failure_leaves_no_audit_event() -> None:
    service, repository, events = _service(repository=FailingMutationRepository())

    with pytest.raises(RuntimeError, match="object mutation failure"):
        service.create(_create_command())

    assert repository.objects == {}
    assert events == []


def test_audit_flush_failure_rolls_back_object_update() -> None:
    working_service, repository, events = _service()
    object_id, _ = _created(working_service)
    before = repository.objects[object_id]
    failing_service, _, _ = _service(
        repository=repository,
        sink=events,
        failing_audit=True,
    )

    with pytest.raises(RuntimeError, match="audit flush failure"):
        failing_service.update(
            GovernedKnowledgeUpdateCommand(
                organization_id="synthetic-org",
                update=KnowledgeObjectV2UpdateCommand(
                    object_id=object_id,
                    expected_revision=1,
                    replacement=_state(content={"result": False}),
                ),
                actor=LifecycleActor(
                    actor_id="synthetic-author",
                    role="knowledge_author",
                ),
                reason_or_note="Synthetic failed update.",
                correlation_id=uuid4(),
            )
        )

    assert repository.objects[object_id] == before
    assert len(events) == 1


def test_correlation_id_is_preserved_for_one_atomic_action() -> None:
    service, _, _ = _service()
    correlation_id = uuid4()
    command = _create_command().model_copy(update={"correlation_id": correlation_id})

    result = service.create(command)

    assert result.audit_event is not None
    assert result.audit_event.correlation_id == correlation_id
