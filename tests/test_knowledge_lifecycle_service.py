from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta, timezone
from itertools import product
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from smartcoat.domain.base import LifecycleState
from smartcoat.domain.context_references import KnowledgeContext
from smartcoat.domain.knowledge_lifecycle import (
    ALLOWED_LIFECYCLE_TRANSITIONS,
    ApproveValidatedCommand,
    CompleteReviewCommand,
    DeleteDraftCommand,
    DeprecateApprovedCommand,
    DraftDeletionAuditTombstoneRequest,
    DraftDeletionFacts,
    KnowledgeAuditAppendRequest,
    KnowledgeLifecycleError,
    LifecycleAction,
    LifecycleActor,
    LifecycleHistoryFacts,
    LifecycleMutationPlan,
    LifecycleReviewProjection,
    RejectCapturedCommand,
    RejectReviewedCommand,
    RejectValidatedCommand,
    ReopenRejectedCommand,
    RequestCapturedCorrectionCommand,
    RequestReviewedCorrectionCommand,
    RequestValidatedCorrectionCommand,
    SubmitDraftCommand,
    ValidateReviewedCommand,
    project_lifecycle_review_status,
    validate_lifecycle_transition,
)
from smartcoat.domain.knowledge_objects import KnowledgeObjectType
from smartcoat.domain.knowledge_objects_v2 import (
    ConfidentialityLevel,
    KnowledgeObjectV2CoreRecord,
    KnowledgeObjectV2MutableState,
    OwnerReference,
)
from smartcoat.services.knowledge_lifecycle_service import KnowledgeLifecyclePlanner

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 7, 23, 10, 15, tzinfo=UTC)
OBJECT_ID = UUID("1ef65d52-bca5-4f77-9151-c7883f60ce6c")
REPLACEMENT_ID = UUID("a4b319f5-d94e-43a0-ab91-0ab0653f328a")


class FixedClock:
    def __init__(self, value: datetime = NOW) -> None:
        self.value = value
        self.calls = 0

    def now(self) -> datetime:
        self.calls += 1
        return self.value


def actor(role: str = "domain-specialist") -> LifecycleActor:
    return LifecycleActor(actor_id="actor_synthetic_01", role=role)


def mutable_state(
    *,
    content: dict[str, Any] | None = None,
    evidence_ids: tuple[str, ...] = ("evidence-synthetic-01",),
) -> KnowledgeObjectV2MutableState:
    return KnowledgeObjectV2MutableState(
        title="Synthetic observation",
        description="Generalized lifecycle fixture",
        knowledge_type=KnowledgeObjectType.OBSERVATION,
        owner=OwnerReference(owner_id="owner_synthetic_01", role="capture-author"),
        confidentiality=ConfidentialityLevel.INTERNAL,
        tags=("synthetic",),
        content={"observation": "Generalized result"} if content is None else content,
        context=KnowledgeContext(references=[]),
        evidence_ids=evidence_ids,
    )


def core_record(
    lifecycle: LifecycleState,
    *,
    object_id: UUID = OBJECT_ID,
    revision: int = 3,
    content: dict[str, Any] | None = None,
    evidence_ids: tuple[str, ...] = ("evidence-synthetic-01",),
) -> KnowledgeObjectV2CoreRecord:
    return KnowledgeObjectV2CoreRecord(
        object_id=object_id,
        organization_id="org_synthetic",
        revision=revision,
        lifecycle_state=lifecycle,
        created_at=NOW - timedelta(days=1),
        updated_at=NOW - timedelta(hours=1),
        mutable_state=mutable_state(content=content, evidence_ids=evidence_ids),
    )


def history_for(lifecycle: LifecycleState) -> LifecycleHistoryFacts:
    return LifecycleHistoryFacts(
        has_ever_left_draft=lifecycle is not LifecycleState.DRAFT,
        last_pre_deprecation_lifecycle=(
            LifecycleState.APPROVED if lifecycle is LifecycleState.DEPRECATED else None
        ),
    )


type CommandFactory = Callable[[UUID, int, str], object]


def submit(object_id: UUID, revision: int, role: str) -> SubmitDraftCommand:
    return SubmitDraftCommand(
        object_id=object_id,
        expected_revision=revision,
        actor=actor(role),
        submission_note="Ready for review",
    )


def captured_correction(
    object_id: UUID,
    revision: int,
    role: str,
) -> RequestCapturedCorrectionCommand:
    return RequestCapturedCorrectionCommand(
        object_id=object_id,
        expected_revision=revision,
        actor=actor(role),
        correction_reason="Clarify the generalized observation",
    )


def complete_review(object_id: UUID, revision: int, role: str) -> CompleteReviewCommand:
    return CompleteReviewCommand(
        object_id=object_id,
        expected_revision=revision,
        actor=actor(role),
        review_note="Review completed",
    )


def reject_captured(object_id: UUID, revision: int, role: str) -> RejectCapturedCommand:
    return RejectCapturedCommand(
        object_id=object_id,
        expected_revision=revision,
        actor=actor(role),
        rejection_reason="Evidence identity is insufficient",
    )


def reviewed_correction(
    object_id: UUID,
    revision: int,
    role: str,
) -> RequestReviewedCorrectionCommand:
    return RequestReviewedCorrectionCommand(
        object_id=object_id,
        expected_revision=revision,
        actor=actor(role),
        correction_reason="Correct the reusable summary",
    )


def validate_reviewed(
    object_id: UUID,
    revision: int,
    role: str,
) -> ValidateReviewedCommand:
    return ValidateReviewedCommand(
        object_id=object_id,
        expected_revision=revision,
        actor=actor(role),
        validation_note="Evidence and context checked",
    )


def reject_reviewed(object_id: UUID, revision: int, role: str) -> RejectReviewedCommand:
    return RejectReviewedCommand(
        object_id=object_id,
        expected_revision=revision,
        actor=actor(role),
        rejection_reason="Review identified a material conflict",
    )


def validated_correction(
    object_id: UUID,
    revision: int,
    role: str,
) -> RequestValidatedCorrectionCommand:
    return RequestValidatedCorrectionCommand(
        object_id=object_id,
        expected_revision=revision,
        actor=actor(role),
        correction_reason="Resolve the validation finding",
    )


def approve_validated(
    object_id: UUID,
    revision: int,
    role: str,
) -> ApproveValidatedCommand:
    return ApproveValidatedCommand(
        object_id=object_id,
        expected_revision=revision,
        actor=actor(role),
        approval_note="Approved for governed reuse",
    )


def reject_validated(
    object_id: UUID,
    revision: int,
    role: str,
) -> RejectValidatedCommand:
    return RejectValidatedCommand(
        object_id=object_id,
        expected_revision=revision,
        actor=actor(role),
        rejection_reason="Validation cannot support reuse",
    )


def deprecate_approved(
    object_id: UUID,
    revision: int,
    role: str,
) -> DeprecateApprovedCommand:
    return DeprecateApprovedCommand(
        object_id=object_id,
        expected_revision=revision,
        actor=actor(role),
        deprecation_reason="Superseded by a reviewed replacement",
        replacement_object_id=REPLACEMENT_ID,
    )


def reopen_rejected(object_id: UUID, revision: int, role: str) -> ReopenRejectedCommand:
    return ReopenRejectedCommand(
        object_id=object_id,
        expected_revision=revision,
        actor=actor(role),
        reopen_reason="New information permits correction",
    )


ALLOWED_CASES: tuple[
    tuple[
        LifecycleState,
        LifecycleState,
        CommandFactory,
        str,
        LifecycleReviewProjection,
        LifecycleAction,
    ],
    ...,
] = (
    (
        LifecycleState.DRAFT,
        LifecycleState.CAPTURED,
        submit,
        "capture-author",
        LifecycleReviewProjection.IN_REVIEW,
        LifecycleAction.SUBMIT_DRAFT,
    ),
    (
        LifecycleState.CAPTURED,
        LifecycleState.DRAFT,
        captured_correction,
        "reviewer",
        LifecycleReviewProjection.NEEDS_CORRECTION,
        LifecycleAction.REQUEST_CAPTURED_CORRECTION,
    ),
    (
        LifecycleState.CAPTURED,
        LifecycleState.REVIEWED,
        complete_review,
        "reviewer",
        LifecycleReviewProjection.ACCEPTED,
        LifecycleAction.COMPLETE_REVIEW,
    ),
    (
        LifecycleState.CAPTURED,
        LifecycleState.REJECTED,
        reject_captured,
        "reviewer",
        LifecycleReviewProjection.REJECTED,
        LifecycleAction.REJECT_CAPTURED,
    ),
    (
        LifecycleState.REVIEWED,
        LifecycleState.DRAFT,
        reviewed_correction,
        "reviewer",
        LifecycleReviewProjection.NEEDS_CORRECTION,
        LifecycleAction.REQUEST_REVIEWED_CORRECTION,
    ),
    (
        LifecycleState.REVIEWED,
        LifecycleState.VALIDATED,
        validate_reviewed,
        "validator",
        LifecycleReviewProjection.VALIDATED,
        LifecycleAction.VALIDATE_REVIEWED,
    ),
    (
        LifecycleState.REVIEWED,
        LifecycleState.REJECTED,
        reject_reviewed,
        "reviewer",
        LifecycleReviewProjection.REJECTED,
        LifecycleAction.REJECT_REVIEWED,
    ),
    (
        LifecycleState.VALIDATED,
        LifecycleState.DRAFT,
        validated_correction,
        "reviewer",
        LifecycleReviewProjection.NEEDS_CORRECTION,
        LifecycleAction.REQUEST_VALIDATED_CORRECTION,
    ),
    (
        LifecycleState.VALIDATED,
        LifecycleState.APPROVED,
        approve_validated,
        "approver",
        LifecycleReviewProjection.VALIDATED,
        LifecycleAction.APPROVE_VALIDATED,
    ),
    (
        LifecycleState.VALIDATED,
        LifecycleState.REJECTED,
        reject_validated,
        "reviewer",
        LifecycleReviewProjection.REJECTED,
        LifecycleAction.REJECT_VALIDATED,
    ),
    (
        LifecycleState.APPROVED,
        LifecycleState.DEPRECATED,
        deprecate_approved,
        "records-steward",
        LifecycleReviewProjection.VALIDATED,
        LifecycleAction.DEPRECATE_APPROVED,
    ),
    (
        LifecycleState.REJECTED,
        LifecycleState.DRAFT,
        reopen_rejected,
        "capture-author",
        LifecycleReviewProjection.NEEDS_CORRECTION,
        LifecycleAction.REOPEN_REJECTED,
    ),
)


@pytest.mark.parametrize(
    (
        "from_lifecycle",
        "to_lifecycle",
        "factory",
        "role",
        "projection",
        "action",
    ),
    ALLOWED_CASES,
)
def test_every_allowed_transition_returns_one_immutable_plan(
    from_lifecycle: LifecycleState,
    to_lifecycle: LifecycleState,
    factory: CommandFactory,
    role: str,
    projection: LifecycleReviewProjection,
    action: LifecycleAction,
) -> None:
    clock = FixedClock()
    planner = KnowledgeLifecyclePlanner(clock)
    current = core_record(from_lifecycle)
    command = factory(current.object_id, current.revision, role)
    current_before = current.model_dump_json()
    command_before = command.model_dump_json()  # type: ignore[attr-defined]

    plan = planner.plan_transition(  # type: ignore[arg-type]
        current,
        command,
        history_for(from_lifecycle),
    )

    assert isinstance(plan, LifecycleMutationPlan)
    assert plan.object_id == current.object_id
    assert plan.action is action
    assert plan.from_lifecycle is from_lifecycle
    assert plan.to_lifecycle is to_lifecycle
    assert plan.expected_revision == current.revision
    assert plan.resulting_revision == current.revision + 1
    assert plan.actor == command.actor  # type: ignore[attr-defined]
    assert plan.note_or_reason
    assert plan.occurred_at == NOW
    assert plan.resulting_review_projection is projection
    assert isinstance(plan.audit_append_request, KnowledgeAuditAppendRequest)
    assert plan.audit_append_request.action is action
    assert plan.audit_append_request.previous_lifecycle is from_lifecycle
    assert plan.audit_append_request.resulting_lifecycle is to_lifecycle
    assert plan.audit_append_request.resulting_revision == current.revision + 1
    assert clock.calls == 1
    assert current.model_dump_json() == current_before
    assert command.model_dump_json() == command_before  # type: ignore[attr-defined]

    with pytest.raises(ValidationError):
        plan.resulting_revision = 99  # type: ignore[misc]


def test_allowed_transition_contract_contains_exactly_twelve_rows() -> None:
    expected = {(case[0], case[1]) for case in ALLOWED_CASES}

    assert len(ALLOWED_LIFECYCLE_TRANSITIONS) == 12
    assert ALLOWED_LIFECYCLE_TRANSITIONS == expected


@pytest.mark.parametrize(
    ("from_lifecycle", "to_lifecycle"),
    [
        pair
        for pair in product(LifecycleState, repeat=2)
        if pair not in ALLOWED_LIFECYCLE_TRANSITIONS
    ],
)
def test_every_unsupported_lifecycle_pair_fails_deterministically(
    from_lifecycle: LifecycleState,
    to_lifecycle: LifecycleState,
) -> None:
    with pytest.raises(KnowledgeLifecycleError) as error:
        validate_lifecycle_transition(from_lifecycle, to_lifecycle)

    assert error.value.code == "invalid_lifecycle_transition"


@pytest.mark.parametrize(
    ("valid_from", "factory", "role", "wrong_from"),
    [(case[0], case[2], case[3], LifecycleState.DEPRECATED) for case in ALLOWED_CASES],
)
def test_each_command_is_bound_to_its_exact_source_state(
    valid_from: LifecycleState,
    factory: CommandFactory,
    role: str,
    wrong_from: LifecycleState,
) -> None:
    if valid_from is wrong_from:
        wrong_from = LifecycleState.DRAFT
    current = core_record(wrong_from)
    command = factory(current.object_id, current.revision, role)

    with pytest.raises(KnowledgeLifecycleError) as error:
        KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
            current,
            command,  # type: ignore[arg-type]
            history_for(wrong_from),
        )

    assert error.value.code == "invalid_lifecycle_transition"


@pytest.mark.parametrize(
    ("lifecycle", "factory", "required_role"),
    (
        (LifecycleState.CAPTURED, captured_correction, "reviewer"),
        (LifecycleState.CAPTURED, complete_review, "reviewer"),
        (LifecycleState.CAPTURED, reject_captured, "reviewer"),
        (LifecycleState.REVIEWED, validate_reviewed, "validator"),
        (LifecycleState.VALIDATED, approve_validated, "approver"),
    ),
)
def test_required_role_rows_reject_another_declared_role(
    lifecycle: LifecycleState,
    factory: CommandFactory,
    required_role: str,
) -> None:
    current = core_record(lifecycle)
    command = factory(current.object_id, current.revision, f"not-{required_role}")

    with pytest.raises(KnowledgeLifecycleError) as error:
        KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
            current,
            command,  # type: ignore[arg-type]
            history_for(lifecycle),
        )

    assert error.value.code == "lifecycle_role_mismatch"


@pytest.mark.parametrize(
    ("lifecycle", "factory"),
    (
        (LifecycleState.DRAFT, submit),
        (LifecycleState.REVIEWED, reviewed_correction),
        (LifecycleState.REVIEWED, reject_reviewed),
        (LifecycleState.VALIDATED, validated_correction),
        (LifecycleState.VALIDATED, reject_validated),
        (LifecycleState.APPROVED, deprecate_approved),
        (LifecycleState.REJECTED, reopen_rejected),
    ),
)
def test_actor_only_rows_accept_any_non_empty_declared_role(
    lifecycle: LifecycleState,
    factory: CommandFactory,
) -> None:
    current = core_record(lifecycle)

    plan = KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
        current,
        factory(current.object_id, current.revision, "synthetic-specialist"),  # type: ignore[arg-type]
        history_for(lifecycle),
    )

    assert plan.actor.role == "synthetic-specialist"


@pytest.mark.parametrize(
    ("field", "value", "code"),
    (
        ("actor_id", " ", "lifecycle_actor_required"),
        ("role", " ", "lifecycle_role_required"),
    ),
)
def test_actor_rejects_blank_required_values(
    field: str,
    value: str,
    code: str,
) -> None:
    payload = {"actor_id": "actor_synthetic", "role": "reviewer", field: value}

    with pytest.raises(ValidationError) as error:
        LifecycleActor.model_validate(payload)

    assert error.value.errors()[0]["type"] == code


@pytest.mark.parametrize(
    ("lifecycle", "command"),
    (
        (
            LifecycleState.DRAFT,
            SubmitDraftCommand(
                object_id=OBJECT_ID,
                expected_revision=3,
                actor=actor(),
                submission_note=" ",
            ),
        ),
        (
            LifecycleState.CAPTURED,
            RequestCapturedCorrectionCommand(
                object_id=OBJECT_ID,
                expected_revision=3,
                actor=actor("reviewer"),
                correction_reason=" ",
            ),
        ),
        (
            LifecycleState.CAPTURED,
            CompleteReviewCommand(
                object_id=OBJECT_ID,
                expected_revision=3,
                actor=actor("reviewer"),
                review_note=" ",
            ),
        ),
        (
            LifecycleState.CAPTURED,
            RejectCapturedCommand(
                object_id=OBJECT_ID,
                expected_revision=3,
                actor=actor("reviewer"),
                rejection_reason=" ",
            ),
        ),
        (
            LifecycleState.REVIEWED,
            RequestReviewedCorrectionCommand(
                object_id=OBJECT_ID,
                expected_revision=3,
                actor=actor(),
                correction_reason=" ",
            ),
        ),
        (
            LifecycleState.REVIEWED,
            ValidateReviewedCommand(
                object_id=OBJECT_ID,
                expected_revision=3,
                actor=actor("validator"),
                validation_note=" ",
            ),
        ),
        (
            LifecycleState.REVIEWED,
            RejectReviewedCommand(
                object_id=OBJECT_ID,
                expected_revision=3,
                actor=actor(),
                rejection_reason=" ",
            ),
        ),
        (
            LifecycleState.VALIDATED,
            RequestValidatedCorrectionCommand(
                object_id=OBJECT_ID,
                expected_revision=3,
                actor=actor(),
                correction_reason=" ",
            ),
        ),
        (
            LifecycleState.VALIDATED,
            ApproveValidatedCommand(
                object_id=OBJECT_ID,
                expected_revision=3,
                actor=actor("approver"),
                approval_note=" ",
            ),
        ),
        (
            LifecycleState.VALIDATED,
            RejectValidatedCommand(
                object_id=OBJECT_ID,
                expected_revision=3,
                actor=actor(),
                rejection_reason=" ",
            ),
        ),
        (
            LifecycleState.APPROVED,
            DeprecateApprovedCommand(
                object_id=OBJECT_ID,
                expected_revision=3,
                actor=actor(),
                deprecation_reason=" ",
            ),
        ),
        (
            LifecycleState.REJECTED,
            ReopenRejectedCommand(
                object_id=OBJECT_ID,
                expected_revision=3,
                actor=actor(),
                reopen_reason=" ",
            ),
        ),
    ),
)
def test_every_transition_rejects_a_blank_note_or_reason(
    lifecycle: LifecycleState,
    command: object,
) -> None:
    current = core_record(lifecycle)

    with pytest.raises(KnowledgeLifecycleError) as error:
        KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
            current,
            command,  # type: ignore[arg-type]
            history_for(lifecycle),
        )

    assert error.value.code == "lifecycle_note_required"


def test_missing_required_reason_is_rejected_by_explicit_command_contract() -> None:
    with pytest.raises(ValidationError) as error:
        ReopenRejectedCommand.model_validate(
            {
                "object_id": str(OBJECT_ID),
                "expected_revision": 3,
                "actor": actor().model_dump(),
            }
        )

    assert error.value.errors()[0]["type"] == "missing"


@pytest.mark.parametrize(
    "forbidden_field",
    (
        "resulting_revision",
        "occurred_at",
        "lifecycle_state",
        "review_status",
        "created_at",
        "updated_at",
        "audit_event_id",
        "database_id",
        "organization_id",
        "mutation_payload",
    ),
)
def test_command_contract_forbids_server_and_generic_mutation_fields(
    forbidden_field: str,
) -> None:
    payload = submit(OBJECT_ID, 3, "capture-author").model_dump(mode="json")
    payload[forbidden_field] = "client-supplied"

    with pytest.raises(ValidationError) as error:
        SubmitDraftCommand.model_validate(payload)

    assert error.value.errors()[0]["type"] == "extra_forbidden"


def test_target_mismatch_wins_before_stale_and_invalid_transition() -> None:
    current = core_record(LifecycleState.APPROVED)
    command = SubmitDraftCommand(
        object_id=uuid4(),
        expected_revision=current.revision - 1,
        actor=actor(),
        submission_note="",
    )

    with pytest.raises(KnowledgeLifecycleError) as error:
        KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
            current,
            command,
            LifecycleHistoryFacts(has_ever_left_draft=False),
        )

    assert error.value.code == "knowledge_object_target_mismatch"


def test_stale_revision_wins_before_transition_role_note_and_capture_checks() -> None:
    current = core_record(
        LifecycleState.APPROVED,
        content={},
        evidence_ids=(),
    )
    command = SubmitDraftCommand(
        object_id=current.object_id,
        expected_revision=current.revision - 1,
        actor=actor("wrong-role"),
        submission_note="",
    )

    with pytest.raises(KnowledgeLifecycleError) as error:
        KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
            current,
            command,
            LifecycleHistoryFacts(has_ever_left_draft=False),
        )

    assert error.value.code == "stale_revision"
    assert current.revision == 3


def test_valid_complete_draft_is_capture_ready() -> None:
    current = core_record(LifecycleState.DRAFT)

    plan = KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
        current,
        submit(current.object_id, current.revision, "capture-author"),
        LifecycleHistoryFacts(has_ever_left_draft=False),
    )

    assert plan.to_lifecycle is LifecycleState.CAPTURED
    assert current.mutable_state.owner.owner_id == "owner_synthetic_01"
    assert current.mutable_state.confidentiality is ConfidentialityLevel.INTERNAL
    assert current.organization_id == "org_synthetic"


@pytest.mark.parametrize(
    ("content", "evidence_ids"),
    (
        ({}, ("evidence-synthetic-01",)),
        ({"observation": "Generalized result"}, ()),
    ),
)
def test_incomplete_capture_returns_one_deterministic_error(
    content: dict[str, Any],
    evidence_ids: tuple[str, ...],
) -> None:
    current = core_record(
        LifecycleState.DRAFT,
        content=content,
        evidence_ids=evidence_ids,
    )

    with pytest.raises(KnowledgeLifecycleError) as error:
        KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
            current,
            submit(current.object_id, current.revision, "capture-author"),
            LifecycleHistoryFacts(has_ever_left_draft=False),
        )

    assert error.value.code == "knowledge_capture_incomplete"


@pytest.mark.parametrize(
    ("lifecycle", "history", "expected"),
    (
        (
            LifecycleState.DRAFT,
            LifecycleHistoryFacts(has_ever_left_draft=False),
            LifecycleReviewProjection.NOT_REVIEWED,
        ),
        (
            LifecycleState.DRAFT,
            LifecycleHistoryFacts(has_ever_left_draft=True),
            LifecycleReviewProjection.NEEDS_CORRECTION,
        ),
        (
            LifecycleState.CAPTURED,
            LifecycleHistoryFacts(has_ever_left_draft=True),
            LifecycleReviewProjection.IN_REVIEW,
        ),
        (
            LifecycleState.REVIEWED,
            LifecycleHistoryFacts(has_ever_left_draft=True),
            LifecycleReviewProjection.ACCEPTED,
        ),
        (
            LifecycleState.VALIDATED,
            LifecycleHistoryFacts(has_ever_left_draft=True),
            LifecycleReviewProjection.VALIDATED,
        ),
        (
            LifecycleState.APPROVED,
            LifecycleHistoryFacts(has_ever_left_draft=True),
            LifecycleReviewProjection.VALIDATED,
        ),
        (
            LifecycleState.REJECTED,
            LifecycleHistoryFacts(has_ever_left_draft=True),
            LifecycleReviewProjection.REJECTED,
        ),
        (
            LifecycleState.DEPRECATED,
            LifecycleHistoryFacts(
                has_ever_left_draft=True,
                last_pre_deprecation_lifecycle=LifecycleState.APPROVED,
            ),
            LifecycleReviewProjection.VALIDATED,
        ),
    ),
)
def test_review_projection_matrix(
    lifecycle: LifecycleState,
    history: LifecycleHistoryFacts,
    expected: LifecycleReviewProjection,
) -> None:
    assert project_lifecycle_review_status(lifecycle, history) is expected


def test_deprecated_projection_accepts_approved_predecessor() -> None:
    history = LifecycleHistoryFacts(
        has_ever_left_draft=True,
        last_pre_deprecation_lifecycle=LifecycleState.APPROVED,
    )

    assert (
        project_lifecycle_review_status(LifecycleState.DEPRECATED, history)
        is LifecycleReviewProjection.VALIDATED
    )


@pytest.mark.parametrize(
    "predecessor",
    (
        None,
        LifecycleState.DRAFT,
        LifecycleState.CAPTURED,
        LifecycleState.REVIEWED,
        LifecycleState.VALIDATED,
        LifecycleState.REJECTED,
        LifecycleState.DEPRECATED,
    ),
)
def test_deprecated_projection_rejects_every_non_approved_predecessor(
    predecessor: LifecycleState | None,
) -> None:
    history = LifecycleHistoryFacts(
        has_ever_left_draft=True,
        last_pre_deprecation_lifecycle=predecessor,
    )

    with pytest.raises(KnowledgeLifecycleError) as error:
        project_lifecycle_review_status(LifecycleState.DEPRECATED, history)

    assert error.value.code == "lifecycle_history_inconsistent"


def test_deprecated_projection_rejects_approved_predecessor_without_history() -> None:
    history = LifecycleHistoryFacts(
        has_ever_left_draft=False,
        last_pre_deprecation_lifecycle=LifecycleState.APPROVED,
    )

    with pytest.raises(KnowledgeLifecycleError) as error:
        project_lifecycle_review_status(LifecycleState.DEPRECATED, history)

    assert error.value.code == "lifecycle_history_inconsistent"


@pytest.mark.parametrize(
    ("lifecycle", "history"),
    (
        (
            LifecycleState.REVIEWED,
            LifecycleHistoryFacts(has_ever_left_draft=False),
        ),
        (
            LifecycleState.DRAFT,
            LifecycleHistoryFacts(
                has_ever_left_draft=True,
                last_pre_deprecation_lifecycle=LifecycleState.REVIEWED,
            ),
        ),
    ),
)
def test_missing_or_contradictory_history_fails_closed(
    lifecycle: LifecycleState,
    history: LifecycleHistoryFacts,
) -> None:
    with pytest.raises(KnowledgeLifecycleError) as error:
        project_lifecycle_review_status(lifecycle, history)

    assert error.value.code == "lifecycle_history_inconsistent"


def test_validated_projection_never_proves_approved_lifecycle() -> None:
    validated_projection = project_lifecycle_review_status(
        LifecycleState.VALIDATED,
        LifecycleHistoryFacts(has_ever_left_draft=True),
    )
    approved_projection = project_lifecycle_review_status(
        LifecycleState.APPROVED,
        LifecycleHistoryFacts(has_ever_left_draft=True),
    )

    assert validated_projection is LifecycleReviewProjection.VALIDATED
    assert approved_projection is LifecycleReviewProjection.VALIDATED
    assert "approved" not in {item.value for item in LifecycleReviewProjection}


def delete_command(
    current: KnowledgeObjectV2CoreRecord,
    *,
    object_id: UUID | None = None,
    revision: int | None = None,
    reason: str = "Remove accidental synthetic draft",
) -> DeleteDraftCommand:
    return DeleteDraftCommand(
        object_id=current.object_id if object_id is None else object_id,
        expected_revision=current.revision if revision is None else revision,
        actor=actor("capture-author"),
        reason=reason,
    )


def test_never_left_draft_without_inbound_reference_is_delete_eligible() -> None:
    clock = FixedClock()
    planner = KnowledgeLifecyclePlanner(clock)
    current = core_record(LifecycleState.DRAFT)
    current_before = current.model_dump_json()

    plan = planner.plan_draft_deletion(
        current,
        delete_command(current),
        LifecycleHistoryFacts(has_ever_left_draft=False),
        DraftDeletionFacts(has_inbound_governed_references=False),
    )

    assert plan.object_id == current.object_id
    assert plan.expected_revision == current.revision
    assert plan.reason == "Remove accidental synthetic draft"
    assert plan.occurred_at == NOW
    assert isinstance(plan.tombstone_request, DraftDeletionAuditTombstoneRequest)
    assert plan.tombstone_request.action is LifecycleAction.DELETE_DRAFT
    assert plan.tombstone_request.object_revision == current.revision
    assert current.model_dump_json() == current_before
    assert clock.calls == 1


def test_create_and_update_audit_history_do_not_disqualify_new_draft() -> None:
    current = core_record(LifecycleState.DRAFT)
    facts = LifecycleHistoryFacts(has_ever_left_draft=False)

    plan = KnowledgeLifecyclePlanner(FixedClock()).plan_draft_deletion(
        current,
        delete_command(current),
        facts,
        DraftDeletionFacts(has_inbound_governed_references=False),
    )

    assert "audit" not in DraftDeletionFacts.model_fields
    assert plan.object_id == current.object_id


def test_correction_draft_is_delete_ineligible() -> None:
    current = core_record(LifecycleState.DRAFT)

    with pytest.raises(KnowledgeLifecycleError) as error:
        KnowledgeLifecyclePlanner(FixedClock()).plan_draft_deletion(
            current,
            delete_command(current),
            LifecycleHistoryFacts(has_ever_left_draft=True),
            DraftDeletionFacts(has_inbound_governed_references=False),
        )

    assert error.value.code == "draft_delete_ineligible"


def test_draft_delete_requires_a_non_blank_reason() -> None:
    current = core_record(LifecycleState.DRAFT)

    with pytest.raises(KnowledgeLifecycleError) as error:
        KnowledgeLifecyclePlanner(FixedClock()).plan_draft_deletion(
            current,
            delete_command(current, reason=" "),
            LifecycleHistoryFacts(has_ever_left_draft=False),
            DraftDeletionFacts(has_inbound_governed_references=False),
        )

    assert error.value.code == "lifecycle_note_required"


@pytest.mark.parametrize("reference_kind", ("Knowledge", "Decision"))
def test_inbound_governed_reference_aggregate_blocks_deletion(
    reference_kind: str,
) -> None:
    current = core_record(LifecycleState.DRAFT)

    with pytest.raises(KnowledgeLifecycleError) as error:
        KnowledgeLifecyclePlanner(FixedClock()).plan_draft_deletion(
            current,
            delete_command(current, reason=f"Blocked by {reference_kind} reference"),
            LifecycleHistoryFacts(has_ever_left_draft=False),
            DraftDeletionFacts(has_inbound_governed_references=True),
        )

    assert error.value.code == "inbound_reference_blocks_deletion"


@pytest.mark.parametrize(
    "lifecycle",
    [state for state in LifecycleState if state is not LifecycleState.DRAFT],
)
def test_every_non_draft_lifecycle_forbids_hard_delete(
    lifecycle: LifecycleState,
) -> None:
    current = core_record(lifecycle)

    with pytest.raises(KnowledgeLifecycleError) as error:
        KnowledgeLifecyclePlanner(FixedClock()).plan_draft_deletion(
            current,
            delete_command(current),
            history_for(lifecycle),
            DraftDeletionFacts(has_inbound_governed_references=False),
        )

    assert error.value.code == "trusted_record_hard_delete_forbidden"


def test_delete_target_mismatch_and_stale_precedence() -> None:
    current = core_record(LifecycleState.APPROVED)
    planner = KnowledgeLifecyclePlanner(FixedClock())

    with pytest.raises(KnowledgeLifecycleError) as target_error:
        planner.plan_draft_deletion(
            current,
            delete_command(current, object_id=uuid4(), revision=1, reason=""),
            LifecycleHistoryFacts(has_ever_left_draft=False),
            DraftDeletionFacts(has_inbound_governed_references=True),
        )
    assert target_error.value.code == "knowledge_object_target_mismatch"

    with pytest.raises(KnowledgeLifecycleError) as stale_error:
        planner.plan_draft_deletion(
            current,
            delete_command(current, revision=1, reason=""),
            LifecycleHistoryFacts(has_ever_left_draft=False),
            DraftDeletionFacts(has_inbound_governed_references=True),
        )
    assert stale_error.value.code == "stale_revision"


def test_safe_tombstone_contains_only_minimum_fields() -> None:
    current = core_record(LifecycleState.DRAFT)
    plan = KnowledgeLifecyclePlanner(FixedClock()).plan_draft_deletion(
        current,
        delete_command(current),
        LifecycleHistoryFacts(has_ever_left_draft=False),
        DraftDeletionFacts(has_inbound_governed_references=False),
    )

    assert set(plan.tombstone_request.model_dump()) == {
        "action",
        "object_id",
        "object_revision",
        "actor",
        "reason",
        "occurred_at",
    }
    serialized = plan.tombstone_request.model_dump_json()
    for prohibited in (
        "title",
        "description",
        "evidence",
        "content",
        "context",
        "owner",
        "confidentiality",
        "organization",
    ):
        assert prohibited not in serialized


def test_rejected_reopen_creates_correction_draft_plan() -> None:
    current = core_record(LifecycleState.REJECTED)

    plan = KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
        current,
        reopen_rejected(current.object_id, current.revision, "capture-author"),
        history_for(LifecycleState.REJECTED),
    )

    assert plan.to_lifecycle is LifecycleState.DRAFT
    assert plan.resulting_review_projection is LifecycleReviewProjection.NEEDS_CORRECTION
    assert plan.resulting_revision == current.revision + 1


def test_approved_deprecation_preserves_projection_and_replacement_reference() -> None:
    current = core_record(LifecycleState.APPROVED)

    plan = KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
        current,
        deprecate_approved(current.object_id, current.revision, "records-steward"),
        history_for(LifecycleState.APPROVED),
    )

    assert plan.to_lifecycle is LifecycleState.DEPRECATED
    assert plan.resulting_review_projection is LifecycleReviewProjection.VALIDATED
    assert plan.audit_append_request.replacement_object_id == REPLACEMENT_ID
    assert current.lifecycle_state is LifecycleState.APPROVED


def test_deprecated_record_cannot_transition_or_reopen() -> None:
    current = core_record(LifecycleState.DEPRECATED)

    with pytest.raises(KnowledgeLifecycleError) as error:
        KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
            current,
            reopen_rejected(current.object_id, current.revision, "capture-author"),
            history_for(LifecycleState.DEPRECATED),
        )

    assert error.value.code == "invalid_lifecycle_transition"


def test_audit_append_request_has_only_safe_future_event_inputs() -> None:
    current = core_record(LifecycleState.CAPTURED)
    plan = KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
        current,
        complete_review(current.object_id, current.revision, "reviewer"),
        history_for(LifecycleState.CAPTURED),
    )

    assert set(plan.audit_append_request.model_dump()) == {
        "object_id",
        "action",
        "previous_lifecycle",
        "resulting_lifecycle",
        "actor",
        "reason_or_note",
        "expected_revision",
        "resulting_revision",
        "occurred_at",
        "replacement_object_id",
    }
    assert plan.audit_append_request.replacement_object_id is None
    for prohibited in (
        "event_id",
        "event_type",
        "title",
        "description",
        "evidence",
        "content",
        "context",
        "formulation",
        "database",
    ):
        assert prohibited not in plan.audit_append_request.model_dump_json()


def test_audit_request_rejects_revision_and_transition_inconsistency() -> None:
    current = core_record(LifecycleState.CAPTURED)
    request = (
        KnowledgeLifecyclePlanner(FixedClock())
        .plan_transition(
            current,
            complete_review(current.object_id, current.revision, "reviewer"),
            history_for(LifecycleState.CAPTURED),
        )
        .audit_append_request
    )

    revision_payload = request.model_dump()
    revision_payload["resulting_revision"] = current.revision + 2
    with pytest.raises(ValidationError) as revision_error:
        KnowledgeAuditAppendRequest.model_validate(revision_payload)
    assert revision_error.value.errors()[0]["type"] == "lifecycle_revision_plan_inconsistent"

    transition_payload = request.model_dump()
    transition_payload["resulting_lifecycle"] = LifecycleState.REJECTED
    with pytest.raises(ValidationError) as transition_error:
        KnowledgeAuditAppendRequest.model_validate(transition_payload)
    assert transition_error.value.errors()[0]["type"] == "lifecycle_audit_request_inconsistent"


def test_mutation_plan_rejects_an_inconsistent_audit_request() -> None:
    current = core_record(LifecycleState.CAPTURED)
    plan = KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
        current,
        complete_review(current.object_id, current.revision, "reviewer"),
        history_for(LifecycleState.CAPTURED),
    )
    payload = plan.model_dump()
    payload["note_or_reason"] = "A different note"

    with pytest.raises(ValidationError) as error:
        LifecycleMutationPlan.model_validate(payload)

    assert error.value.errors()[0]["type"] == "lifecycle_audit_request_inconsistent"


@pytest.mark.parametrize(
    "model",
    (KnowledgeAuditAppendRequest, DraftDeletionAuditTombstoneRequest),
)
def test_audit_request_contracts_forbid_arbitrary_event_fields(
    model: type[KnowledgeAuditAppendRequest] | type[DraftDeletionAuditTombstoneRequest],
) -> None:
    current = core_record(LifecycleState.CAPTURED)
    plan = KnowledgeLifecyclePlanner(FixedClock()).plan_transition(
        current,
        complete_review(current.object_id, current.revision, "reviewer"),
        history_for(LifecycleState.CAPTURED),
    )
    payload = (
        plan.audit_append_request.model_dump()
        if model is KnowledgeAuditAppendRequest
        else {
            "object_id": current.object_id,
            "object_revision": current.revision,
            "actor": actor(),
            "reason": "Synthetic cleanup",
            "occurred_at": NOW,
        }
    )
    payload["event_id"] = str(uuid4())

    with pytest.raises(ValidationError) as error:
        model.model_validate(payload)

    assert error.value.errors()[0]["type"] == "extra_forbidden"


def test_deletion_plan_rejects_an_inconsistent_tombstone() -> None:
    current = core_record(LifecycleState.DRAFT)
    plan = KnowledgeLifecyclePlanner(FixedClock()).plan_draft_deletion(
        current,
        delete_command(current),
        LifecycleHistoryFacts(has_ever_left_draft=False),
        DraftDeletionFacts(has_inbound_governed_references=False),
    )
    payload = plan.model_dump()
    payload["reason"] = "A different deletion reason"

    with pytest.raises(ValidationError) as error:
        type(plan).model_validate(payload)

    assert error.value.errors()[0]["type"] == "lifecycle_deletion_tombstone_inconsistent"


def test_audit_contract_rejects_naive_direct_timestamp() -> None:
    current = core_record(LifecycleState.CAPTURED)
    request = (
        KnowledgeLifecyclePlanner(FixedClock())
        .plan_transition(
            current,
            complete_review(current.object_id, current.revision, "reviewer"),
            history_for(LifecycleState.CAPTURED),
        )
        .audit_append_request
    )
    payload = request.model_dump()
    payload["occurred_at"] = datetime(2026, 7, 23, 10, 15)

    with pytest.raises(ValidationError) as error:
        KnowledgeAuditAppendRequest.model_validate(payload)

    assert error.value.errors()[0]["type"] == "lifecycle_naive_timestamp"


def test_server_clock_is_normalized_to_utc() -> None:
    supplied = datetime(2026, 7, 23, 12, 15, tzinfo=timezone(timedelta(hours=2)))
    current = core_record(LifecycleState.DRAFT)

    plan = KnowledgeLifecyclePlanner(FixedClock(supplied)).plan_transition(
        current,
        submit(current.object_id, current.revision, "capture-author"),
        LifecycleHistoryFacts(has_ever_left_draft=False),
    )

    assert plan.occurred_at == NOW
    assert plan.occurred_at.tzinfo is UTC


def test_naive_trusted_clock_fails_closed() -> None:
    current = core_record(LifecycleState.DRAFT)

    with pytest.raises(KnowledgeLifecycleError) as error:
        KnowledgeLifecyclePlanner(FixedClock(datetime(2026, 7, 23, 10, 15))).plan_transition(
            current,
            submit(current.object_id, current.revision, "capture-author"),
            LifecycleHistoryFacts(has_ever_left_draft=False),
        )

    assert error.value.code == "lifecycle_clock_invalid"


def test_planner_has_no_persistence_or_final_event_dependencies() -> None:
    domain_source = (ROOT / "src/smartcoat/domain/knowledge_lifecycle.py").read_text(
        encoding="utf-8"
    )
    service_source = (ROOT / "src/smartcoat/services/knowledge_lifecycle_service.py").read_text(
        encoding="utf-8"
    )
    combined = f"{domain_source}\n{service_source}"

    for prohibited_import in (
        "sqlalchemy",
        "KnowledgeRepository",
        "session.commit",
        "EnterpriseEvent(",
        "EventType",
        "smartcoat.storage",
        "smartcoat.api",
    ):
        assert prohibited_import not in combined


def test_t02_core_and_current_api_are_not_modified_or_redefined() -> None:
    domain_source = (ROOT / "src/smartcoat/domain/knowledge_lifecycle.py").read_text(
        encoding="utf-8"
    )
    service_source = (ROOT / "src/smartcoat/services/knowledge_lifecycle_service.py").read_text(
        encoding="utf-8"
    )

    assert "class KnowledgeObjectV2CoreRecord" not in domain_source
    assert "KnowledgeObjectV2CoreRecord" in service_source
    assert "FastAPI" not in domain_source + service_source
    assert "router" not in domain_source + service_source


def test_no_production_authorization_claim_or_generic_transition_command_exists() -> None:
    source = (ROOT / "src/smartcoat/domain/knowledge_lifecycle.py").read_text(encoding="utf-8")

    assert "class TransitionCommand" not in source
    assert "authenticate actors, authorize roles" in source
    assert "tenant" not in source.casefold()
