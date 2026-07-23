"""Governed Knowledge Object lifecycle contracts for Release 1.8.

The types in this module describe application intent and desired atomic work.
They do not authenticate actors, authorize roles, persist records, or create
canonical Enterprise Events.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError

from smartcoat.domain.base import LifecycleState

MAX_ACTOR_ID_LENGTH = 512
MAX_ROLE_LENGTH = 128
MAX_NOTE_LENGTH = 4096


def _custom_error(code: str, message: str) -> PydanticCustomError:
    return PydanticCustomError(code, message)


def _normalize_required_text(
    value: Any,
    *,
    field_name: str,
    max_length: int,
    blank_error_code: str,
) -> str:
    if not isinstance(value, str):
        raise _custom_error(
            blank_error_code,
            f"{field_name} must be a string",
        )
    normalized = value.strip()
    if not normalized:
        raise _custom_error(
            blank_error_code,
            f"{field_name} must not be blank",
        )
    if len(normalized) > max_length:
        raise _custom_error(
            "lifecycle_text_too_long",
            f"{field_name} must contain at most {max_length} characters",
        )
    return normalized


def _normalize_note_input(value: Any, *, field_name: str) -> str:
    """Normalize a supplied note while leaving blank rejection to the planner."""

    if not isinstance(value, str):
        raise _custom_error(
            "lifecycle_note_required",
            f"{field_name} must be a string",
        )
    normalized = value.strip()
    if len(normalized) > MAX_NOTE_LENGTH:
        raise _custom_error(
            "lifecycle_text_too_long",
            f"{field_name} must contain at most {MAX_NOTE_LENGTH} characters",
        )
    return normalized


def _normalize_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise _custom_error(
            "lifecycle_naive_timestamp",
            "lifecycle timestamps must be timezone-aware",
        )
    return value.astimezone(UTC)


class LifecycleActor(BaseModel):
    """Declared application actor metadata, not proof of IAM or authority."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    actor_id: str = Field(min_length=1, max_length=MAX_ACTOR_ID_LENGTH)
    role: str = Field(min_length=1, max_length=MAX_ROLE_LENGTH)

    @field_validator("actor_id", "role", mode="before")
    @classmethod
    def normalize_actor_fields(cls, value: Any, info: ValidationInfo) -> str:
        field_name = info.field_name or "actor field"
        return _normalize_required_text(
            value,
            field_name=field_name,
            max_length=(MAX_ACTOR_ID_LENGTH if field_name == "actor_id" else MAX_ROLE_LENGTH),
            blank_error_code=(
                "lifecycle_actor_required"
                if field_name == "actor_id"
                else "lifecycle_role_required"
            ),
        )


class _LifecycleCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    object_id: UUID
    expected_revision: int = Field(gt=0)
    actor: LifecycleActor


class SubmitDraftCommand(_LifecycleCommand):
    submission_note: str

    @field_validator("submission_note", mode="before")
    @classmethod
    def normalize_submission_note(cls, value: Any) -> str:
        return _normalize_note_input(value, field_name="submission_note")


class RequestCapturedCorrectionCommand(_LifecycleCommand):
    correction_reason: str

    @field_validator("correction_reason", mode="before")
    @classmethod
    def normalize_correction_reason(cls, value: Any) -> str:
        return _normalize_note_input(value, field_name="correction_reason")


class CompleteReviewCommand(_LifecycleCommand):
    review_note: str

    @field_validator("review_note", mode="before")
    @classmethod
    def normalize_review_note(cls, value: Any) -> str:
        return _normalize_note_input(value, field_name="review_note")


class RejectCapturedCommand(_LifecycleCommand):
    rejection_reason: str

    @field_validator("rejection_reason", mode="before")
    @classmethod
    def normalize_rejection_reason(cls, value: Any) -> str:
        return _normalize_note_input(value, field_name="rejection_reason")


class RequestReviewedCorrectionCommand(_LifecycleCommand):
    correction_reason: str

    @field_validator("correction_reason", mode="before")
    @classmethod
    def normalize_correction_reason(cls, value: Any) -> str:
        return _normalize_note_input(value, field_name="correction_reason")


class ValidateReviewedCommand(_LifecycleCommand):
    validation_note: str

    @field_validator("validation_note", mode="before")
    @classmethod
    def normalize_validation_note(cls, value: Any) -> str:
        return _normalize_note_input(value, field_name="validation_note")


class RejectReviewedCommand(_LifecycleCommand):
    rejection_reason: str

    @field_validator("rejection_reason", mode="before")
    @classmethod
    def normalize_rejection_reason(cls, value: Any) -> str:
        return _normalize_note_input(value, field_name="rejection_reason")


class RequestValidatedCorrectionCommand(_LifecycleCommand):
    correction_reason: str

    @field_validator("correction_reason", mode="before")
    @classmethod
    def normalize_correction_reason(cls, value: Any) -> str:
        return _normalize_note_input(value, field_name="correction_reason")


class ApproveValidatedCommand(_LifecycleCommand):
    approval_note: str

    @field_validator("approval_note", mode="before")
    @classmethod
    def normalize_approval_note(cls, value: Any) -> str:
        return _normalize_note_input(value, field_name="approval_note")


class RejectValidatedCommand(_LifecycleCommand):
    rejection_reason: str

    @field_validator("rejection_reason", mode="before")
    @classmethod
    def normalize_rejection_reason(cls, value: Any) -> str:
        return _normalize_note_input(value, field_name="rejection_reason")


class DeprecateApprovedCommand(_LifecycleCommand):
    deprecation_reason: str
    replacement_object_id: UUID | None = None

    @field_validator("deprecation_reason", mode="before")
    @classmethod
    def normalize_deprecation_reason(cls, value: Any) -> str:
        return _normalize_note_input(value, field_name="deprecation_reason")


class ReopenRejectedCommand(_LifecycleCommand):
    reopen_reason: str

    @field_validator("reopen_reason", mode="before")
    @classmethod
    def normalize_reopen_reason(cls, value: Any) -> str:
        return _normalize_note_input(value, field_name="reopen_reason")


class DeleteDraftCommand(_LifecycleCommand):
    reason: str

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: Any) -> str:
        return _normalize_note_input(value, field_name="reason")


type LifecycleTransitionCommand = (
    SubmitDraftCommand
    | RequestCapturedCorrectionCommand
    | CompleteReviewCommand
    | RejectCapturedCommand
    | RequestReviewedCorrectionCommand
    | ValidateReviewedCommand
    | RejectReviewedCommand
    | RequestValidatedCorrectionCommand
    | ApproveValidatedCommand
    | RejectValidatedCommand
    | DeprecateApprovedCommand
    | ReopenRejectedCommand
)


class LifecycleReviewProjection(StrEnum):
    NOT_REVIEWED = "not_reviewed"
    NEEDS_CORRECTION = "needs_correction"
    IN_REVIEW = "in_review"
    ACCEPTED = "accepted"
    VALIDATED = "validated"
    REJECTED = "rejected"


class LifecycleHistoryFacts(BaseModel):
    """Trusted application/audit facts, never fields on a public transition command."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    has_ever_left_draft: bool
    last_pre_deprecation_lifecycle: LifecycleState | None = None


class DraftDeletionFacts(BaseModel):
    """Trusted aggregate inbound-reference fact for draft deletion planning."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    has_inbound_governed_references: bool


class LifecycleAction(StrEnum):
    SUBMIT_DRAFT = "submit_draft"
    REQUEST_CAPTURED_CORRECTION = "request_captured_correction"
    COMPLETE_REVIEW = "complete_review"
    REJECT_CAPTURED = "reject_captured"
    REQUEST_REVIEWED_CORRECTION = "request_reviewed_correction"
    VALIDATE_REVIEWED = "validate_reviewed"
    REJECT_REVIEWED = "reject_reviewed"
    REQUEST_VALIDATED_CORRECTION = "request_validated_correction"
    APPROVE_VALIDATED = "approve_validated"
    REJECT_VALIDATED = "reject_validated"
    DEPRECATE_APPROVED = "deprecate_approved"
    REOPEN_REJECTED = "reopen_rejected"
    DELETE_DRAFT = "delete_draft"


_ACTION_TRANSITIONS = {
    LifecycleAction.SUBMIT_DRAFT: (
        LifecycleState.DRAFT,
        LifecycleState.CAPTURED,
    ),
    LifecycleAction.REQUEST_CAPTURED_CORRECTION: (
        LifecycleState.CAPTURED,
        LifecycleState.DRAFT,
    ),
    LifecycleAction.COMPLETE_REVIEW: (
        LifecycleState.CAPTURED,
        LifecycleState.REVIEWED,
    ),
    LifecycleAction.REJECT_CAPTURED: (
        LifecycleState.CAPTURED,
        LifecycleState.REJECTED,
    ),
    LifecycleAction.REQUEST_REVIEWED_CORRECTION: (
        LifecycleState.REVIEWED,
        LifecycleState.DRAFT,
    ),
    LifecycleAction.VALIDATE_REVIEWED: (
        LifecycleState.REVIEWED,
        LifecycleState.VALIDATED,
    ),
    LifecycleAction.REJECT_REVIEWED: (
        LifecycleState.REVIEWED,
        LifecycleState.REJECTED,
    ),
    LifecycleAction.REQUEST_VALIDATED_CORRECTION: (
        LifecycleState.VALIDATED,
        LifecycleState.DRAFT,
    ),
    LifecycleAction.APPROVE_VALIDATED: (
        LifecycleState.VALIDATED,
        LifecycleState.APPROVED,
    ),
    LifecycleAction.REJECT_VALIDATED: (
        LifecycleState.VALIDATED,
        LifecycleState.REJECTED,
    ),
    LifecycleAction.DEPRECATE_APPROVED: (
        LifecycleState.APPROVED,
        LifecycleState.DEPRECATED,
    ),
    LifecycleAction.REOPEN_REJECTED: (
        LifecycleState.REJECTED,
        LifecycleState.DRAFT,
    ),
}


class KnowledgeLifecycleError(ValueError):
    """Typed deterministic lifecycle-planning failure."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


ALLOWED_LIFECYCLE_TRANSITIONS = frozenset(_ACTION_TRANSITIONS.values())


def validate_lifecycle_transition(
    from_lifecycle: LifecycleState,
    to_lifecycle: LifecycleState,
) -> None:
    """Validate the closed ADR-0020 matrix without accepting a generic command."""

    if (from_lifecycle, to_lifecycle) not in ALLOWED_LIFECYCLE_TRANSITIONS:
        raise KnowledgeLifecycleError(
            "invalid_lifecycle_transition",
            f"{from_lifecycle.value} cannot transition to {to_lifecycle.value}",
        )


_DIRECT_REVIEW_PROJECTIONS = {
    LifecycleState.CAPTURED: LifecycleReviewProjection.IN_REVIEW,
    LifecycleState.REVIEWED: LifecycleReviewProjection.ACCEPTED,
    LifecycleState.VALIDATED: LifecycleReviewProjection.VALIDATED,
    LifecycleState.APPROVED: LifecycleReviewProjection.VALIDATED,
    LifecycleState.REJECTED: LifecycleReviewProjection.REJECTED,
}


def project_lifecycle_review_status(
    lifecycle: LifecycleState,
    history: LifecycleHistoryFacts,
) -> LifecycleReviewProjection:
    """Compute the read-only compatibility projection and fail closed."""

    if lifecycle is LifecycleState.DEPRECATED:
        previous = history.last_pre_deprecation_lifecycle
        if (
            not history.has_ever_left_draft
            or previous is None
            or previous in {LifecycleState.DRAFT, LifecycleState.DEPRECATED}
        ):
            raise KnowledgeLifecycleError(
                "lifecycle_history_inconsistent",
                "deprecated lifecycle requires a valid pre-deprecation lifecycle",
            )
        projection = _DIRECT_REVIEW_PROJECTIONS.get(previous)
        if projection is None:
            raise KnowledgeLifecycleError(
                "lifecycle_history_inconsistent",
                "pre-deprecation lifecycle cannot be projected",
            )
        return projection

    if history.last_pre_deprecation_lifecycle is not None:
        raise KnowledgeLifecycleError(
            "lifecycle_history_inconsistent",
            "pre-deprecation lifecycle is valid only for a deprecated record",
        )

    if lifecycle is LifecycleState.DRAFT:
        if history.has_ever_left_draft:
            return LifecycleReviewProjection.NEEDS_CORRECTION
        return LifecycleReviewProjection.NOT_REVIEWED

    if not history.has_ever_left_draft:
        raise KnowledgeLifecycleError(
            "lifecycle_history_inconsistent",
            "a non-draft lifecycle must have left draft",
        )

    projection = _DIRECT_REVIEW_PROJECTIONS.get(lifecycle)
    if projection is None:
        raise KnowledgeLifecycleError(
            "lifecycle_history_inconsistent",
            "lifecycle cannot be projected",
        )
    return projection


class KnowledgeAuditAppendRequest(BaseModel):
    """Internal request for T07/T05; not a final canonical EnterpriseEvent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    object_id: UUID
    action: LifecycleAction
    previous_lifecycle: LifecycleState
    resulting_lifecycle: LifecycleState
    actor: LifecycleActor
    reason_or_note: str
    expected_revision: int = Field(gt=0)
    resulting_revision: int = Field(gt=1)
    occurred_at: datetime
    replacement_object_id: UUID | None = None

    @field_validator("reason_or_note", mode="before")
    @classmethod
    def normalize_reason_or_note(cls, value: Any) -> str:
        return _normalize_required_text(
            value,
            field_name="reason_or_note",
            max_length=MAX_NOTE_LENGTH,
            blank_error_code="lifecycle_note_required",
        )

    @field_validator("occurred_at")
    @classmethod
    def normalize_occurred_at(cls, value: datetime) -> datetime:
        return _normalize_aware_utc(value)

    @model_validator(mode="after")
    def validate_audit_request(self) -> KnowledgeAuditAppendRequest:
        if self.resulting_revision != self.expected_revision + 1:
            raise _custom_error(
                "lifecycle_revision_plan_inconsistent",
                "resulting revision must equal expected revision plus one",
            )
        expected_transition = _ACTION_TRANSITIONS.get(self.action)
        if expected_transition != (
            self.previous_lifecycle,
            self.resulting_lifecycle,
        ):
            raise _custom_error(
                "lifecycle_audit_request_inconsistent",
                "audit action does not match its lifecycle transition",
            )
        if (
            self.action is not LifecycleAction.DEPRECATE_APPROVED
            and self.replacement_object_id is not None
        ):
            raise _custom_error(
                "lifecycle_audit_request_inconsistent",
                "replacement object is valid only for deprecation",
            )
        return self


class LifecycleMutationPlan(BaseModel):
    """Immutable desired atomic work; persistence and one commit remain T05 scope."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    object_id: UUID
    action: LifecycleAction
    from_lifecycle: LifecycleState
    to_lifecycle: LifecycleState
    expected_revision: int = Field(gt=0)
    resulting_revision: int = Field(gt=1)
    actor: LifecycleActor
    note_or_reason: str
    occurred_at: datetime
    resulting_review_projection: LifecycleReviewProjection
    audit_append_request: KnowledgeAuditAppendRequest

    @field_validator("note_or_reason", mode="before")
    @classmethod
    def normalize_note_or_reason(cls, value: Any) -> str:
        return _normalize_required_text(
            value,
            field_name="note_or_reason",
            max_length=MAX_NOTE_LENGTH,
            blank_error_code="lifecycle_note_required",
        )

    @field_validator("occurred_at")
    @classmethod
    def normalize_occurred_at(cls, value: datetime) -> datetime:
        return _normalize_aware_utc(value)

    @model_validator(mode="after")
    def validate_plan_consistency(self) -> LifecycleMutationPlan:
        if self.resulting_revision != self.expected_revision + 1:
            raise _custom_error(
                "lifecycle_revision_plan_inconsistent",
                "resulting revision must equal expected revision plus one",
            )
        request = self.audit_append_request
        if (
            request.object_id != self.object_id
            or request.action is not self.action
            or request.previous_lifecycle is not self.from_lifecycle
            or request.resulting_lifecycle is not self.to_lifecycle
            or request.actor != self.actor
            or request.reason_or_note != self.note_or_reason
            or request.expected_revision != self.expected_revision
            or request.resulting_revision != self.resulting_revision
            or request.occurred_at != self.occurred_at
        ):
            raise _custom_error(
                "lifecycle_audit_request_inconsistent",
                "audit append request must exactly describe the mutation plan",
            )
        return self


class DraftDeletionAuditTombstoneRequest(BaseModel):
    """Minimal safe retained audit request for a future typed deletion event."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action: Literal[LifecycleAction.DELETE_DRAFT] = LifecycleAction.DELETE_DRAFT
    object_id: UUID
    object_revision: int = Field(gt=0)
    actor: LifecycleActor
    reason: str
    occurred_at: datetime

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: Any) -> str:
        return _normalize_required_text(
            value,
            field_name="reason",
            max_length=MAX_NOTE_LENGTH,
            blank_error_code="lifecycle_note_required",
        )

    @field_validator("occurred_at")
    @classmethod
    def normalize_occurred_at(cls, value: datetime) -> datetime:
        return _normalize_aware_utc(value)


class DraftDeletionPlan(BaseModel):
    """Desired deletion work only; it never deletes or claims legal erasure."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    object_id: UUID
    expected_revision: int = Field(gt=0)
    actor: LifecycleActor
    reason: str
    occurred_at: datetime
    tombstone_request: DraftDeletionAuditTombstoneRequest

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: Any) -> str:
        return _normalize_required_text(
            value,
            field_name="reason",
            max_length=MAX_NOTE_LENGTH,
            blank_error_code="lifecycle_note_required",
        )

    @field_validator("occurred_at")
    @classmethod
    def normalize_occurred_at(cls, value: datetime) -> datetime:
        return _normalize_aware_utc(value)

    @model_validator(mode="after")
    def validate_tombstone_consistency(self) -> DraftDeletionPlan:
        tombstone = self.tombstone_request
        if (
            tombstone.object_id != self.object_id
            or tombstone.object_revision != self.expected_revision
            or tombstone.actor != self.actor
            or tombstone.reason != self.reason
            or tombstone.occurred_at != self.occurred_at
        ):
            raise _custom_error(
                "lifecycle_deletion_tombstone_inconsistent",
                "deletion tombstone must exactly describe the deletion plan",
            )
        return self
