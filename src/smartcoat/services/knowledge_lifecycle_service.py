"""Pure planning service for governed Knowledge Object lifecycle work."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from smartcoat.domain.base import LifecycleState
from smartcoat.domain.knowledge_lifecycle import (
    ApproveValidatedCommand,
    CompleteReviewCommand,
    DeleteDraftCommand,
    DeprecateApprovedCommand,
    DraftDeletionAuditTombstoneRequest,
    DraftDeletionFacts,
    DraftDeletionPlan,
    KnowledgeAuditAppendRequest,
    KnowledgeLifecycleError,
    LifecycleAction,
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
    project_lifecycle_review_status,
    validate_lifecycle_transition,
)
from smartcoat.domain.knowledge_objects_v2 import KnowledgeObjectV2CoreRecord


class TrustedClock(Protocol):
    """Trusted server-side time source injected by the application boundary."""

    def now(self) -> datetime: ...


@dataclass(frozen=True)
class _TransitionSpec:
    action: LifecycleAction
    from_lifecycle: LifecycleState
    to_lifecycle: LifecycleState
    note_or_reason: str
    required_role: str | None = None


def _spec_for_command(command: LifecycleTransitionCommand) -> _TransitionSpec:
    if isinstance(command, SubmitDraftCommand):
        return _TransitionSpec(
            LifecycleAction.SUBMIT_DRAFT,
            LifecycleState.DRAFT,
            LifecycleState.CAPTURED,
            command.submission_note,
        )
    if isinstance(command, RequestCapturedCorrectionCommand):
        return _TransitionSpec(
            LifecycleAction.REQUEST_CAPTURED_CORRECTION,
            LifecycleState.CAPTURED,
            LifecycleState.DRAFT,
            command.correction_reason,
            "reviewer",
        )
    if isinstance(command, CompleteReviewCommand):
        return _TransitionSpec(
            LifecycleAction.COMPLETE_REVIEW,
            LifecycleState.CAPTURED,
            LifecycleState.REVIEWED,
            command.review_note,
            "reviewer",
        )
    if isinstance(command, RejectCapturedCommand):
        return _TransitionSpec(
            LifecycleAction.REJECT_CAPTURED,
            LifecycleState.CAPTURED,
            LifecycleState.REJECTED,
            command.rejection_reason,
            "reviewer",
        )
    if isinstance(command, RequestReviewedCorrectionCommand):
        return _TransitionSpec(
            LifecycleAction.REQUEST_REVIEWED_CORRECTION,
            LifecycleState.REVIEWED,
            LifecycleState.DRAFT,
            command.correction_reason,
        )
    if isinstance(command, ValidateReviewedCommand):
        return _TransitionSpec(
            LifecycleAction.VALIDATE_REVIEWED,
            LifecycleState.REVIEWED,
            LifecycleState.VALIDATED,
            command.validation_note,
            "validator",
        )
    if isinstance(command, RejectReviewedCommand):
        return _TransitionSpec(
            LifecycleAction.REJECT_REVIEWED,
            LifecycleState.REVIEWED,
            LifecycleState.REJECTED,
            command.rejection_reason,
        )
    if isinstance(command, RequestValidatedCorrectionCommand):
        return _TransitionSpec(
            LifecycleAction.REQUEST_VALIDATED_CORRECTION,
            LifecycleState.VALIDATED,
            LifecycleState.DRAFT,
            command.correction_reason,
        )
    if isinstance(command, ApproveValidatedCommand):
        return _TransitionSpec(
            LifecycleAction.APPROVE_VALIDATED,
            LifecycleState.VALIDATED,
            LifecycleState.APPROVED,
            command.approval_note,
            "approver",
        )
    if isinstance(command, RejectValidatedCommand):
        return _TransitionSpec(
            LifecycleAction.REJECT_VALIDATED,
            LifecycleState.VALIDATED,
            LifecycleState.REJECTED,
            command.rejection_reason,
        )
    if isinstance(command, DeprecateApprovedCommand):
        return _TransitionSpec(
            LifecycleAction.DEPRECATE_APPROVED,
            LifecycleState.APPROVED,
            LifecycleState.DEPRECATED,
            command.deprecation_reason,
        )
    if isinstance(command, ReopenRejectedCommand):
        return _TransitionSpec(
            LifecycleAction.REOPEN_REJECTED,
            LifecycleState.REJECTED,
            LifecycleState.DRAFT,
            command.reopen_reason,
        )
    raise TypeError(f"unsupported lifecycle command: {type(command).__name__}")


def _validate_target_and_revision(
    current: KnowledgeObjectV2CoreRecord,
    *,
    object_id: object,
    expected_revision: int,
) -> None:
    if object_id != current.object_id:
        raise KnowledgeLifecycleError(
            "knowledge_object_target_mismatch",
            "the lifecycle command target does not match the current record",
        )
    if expected_revision != current.revision:
        raise KnowledgeLifecycleError(
            "stale_revision",
            "the lifecycle command expected revision does not match the current record",
        )


def _validate_note(note_or_reason: str) -> None:
    if not note_or_reason:
        raise KnowledgeLifecycleError(
            "lifecycle_note_required",
            "the lifecycle action requires a non-blank note or reason",
        )


def _resulting_history(spec: _TransitionSpec) -> LifecycleHistoryFacts:
    return LifecycleHistoryFacts(
        has_ever_left_draft=True,
        last_pre_deprecation_lifecycle=(
            spec.from_lifecycle if spec.to_lifecycle is LifecycleState.DEPRECATED else None
        ),
    )


class KnowledgeLifecyclePlanner:
    """Plan transitions and eligible draft deletion without side effects."""

    def __init__(self, clock: TrustedClock) -> None:
        self._clock = clock

    def _trusted_now(self) -> datetime:
        occurred_at = self._clock.now()
        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise KnowledgeLifecycleError(
                "lifecycle_clock_invalid",
                "the trusted clock must return a timezone-aware timestamp",
            )
        return occurred_at.astimezone(UTC)

    def plan_transition(
        self,
        current: KnowledgeObjectV2CoreRecord,
        command: LifecycleTransitionCommand,
        history: LifecycleHistoryFacts,
    ) -> LifecycleMutationPlan:
        """Return desired atomic work without mutating, persisting, or committing."""

        _validate_target_and_revision(
            current,
            object_id=command.object_id,
            expected_revision=command.expected_revision,
        )
        spec = _spec_for_command(command)
        if current.lifecycle_state is not spec.from_lifecycle:
            raise KnowledgeLifecycleError(
                "invalid_lifecycle_transition",
                f"{type(command).__name__} cannot run from {current.lifecycle_state.value}",
            )
        validate_lifecycle_transition(current.lifecycle_state, spec.to_lifecycle)

        project_lifecycle_review_status(current.lifecycle_state, history)
        if spec.required_role is not None and command.actor.role != spec.required_role:
            raise KnowledgeLifecycleError(
                "lifecycle_role_mismatch",
                f"{spec.action.value} requires role {spec.required_role}",
            )
        _validate_note(spec.note_or_reason)

        if spec.action is LifecycleAction.SUBMIT_DRAFT:
            mutable_state = current.mutable_state
            if not mutable_state.content or not mutable_state.evidence_ids:
                raise KnowledgeLifecycleError(
                    "knowledge_capture_incomplete",
                    "capture requires non-empty bounded content and evidence IDs",
                )

        resulting_revision = current.revision + 1
        occurred_at = self._trusted_now()
        resulting_projection = project_lifecycle_review_status(
            spec.to_lifecycle,
            _resulting_history(spec),
        )
        replacement_object_id = (
            command.replacement_object_id if isinstance(command, DeprecateApprovedCommand) else None
        )
        audit_request = KnowledgeAuditAppendRequest(
            object_id=current.object_id,
            action=spec.action,
            previous_lifecycle=current.lifecycle_state,
            resulting_lifecycle=spec.to_lifecycle,
            actor=command.actor,
            reason_or_note=spec.note_or_reason,
            expected_revision=current.revision,
            resulting_revision=resulting_revision,
            occurred_at=occurred_at,
            replacement_object_id=replacement_object_id,
        )
        return LifecycleMutationPlan(
            object_id=current.object_id,
            action=spec.action,
            from_lifecycle=current.lifecycle_state,
            to_lifecycle=spec.to_lifecycle,
            expected_revision=current.revision,
            resulting_revision=resulting_revision,
            actor=command.actor,
            note_or_reason=spec.note_or_reason,
            occurred_at=occurred_at,
            resulting_review_projection=resulting_projection,
            audit_append_request=audit_request,
        )

    def plan_draft_deletion(
        self,
        current: KnowledgeObjectV2CoreRecord,
        command: DeleteDraftCommand,
        history: LifecycleHistoryFacts,
        deletion_facts: DraftDeletionFacts,
    ) -> DraftDeletionPlan:
        """Plan deletion of an eligible never-left-draft record."""

        _validate_target_and_revision(
            current,
            object_id=command.object_id,
            expected_revision=command.expected_revision,
        )
        if current.lifecycle_state is not LifecycleState.DRAFT:
            raise KnowledgeLifecycleError(
                "trusted_record_hard_delete_forbidden",
                "non-draft Knowledge Objects cannot use hard-delete planning",
            )
        project_lifecycle_review_status(current.lifecycle_state, history)
        _validate_note(command.reason)
        if history.has_ever_left_draft:
            raise KnowledgeLifecycleError(
                "draft_delete_ineligible",
                "a draft that has left draft cannot be hard-deleted",
            )
        if deletion_facts.has_inbound_governed_references:
            raise KnowledgeLifecycleError(
                "inbound_reference_blocks_deletion",
                "an inbound governed reference blocks draft deletion",
            )

        occurred_at = self._trusted_now()
        tombstone = DraftDeletionAuditTombstoneRequest(
            object_id=current.object_id,
            object_revision=current.revision,
            actor=command.actor,
            reason=command.reason,
            occurred_at=occurred_at,
        )
        return DraftDeletionPlan(
            object_id=current.object_id,
            expected_revision=current.revision,
            actor=command.actor,
            reason=command.reason,
            occurred_at=occurred_at,
            tombstone_request=tombstone,
        )
