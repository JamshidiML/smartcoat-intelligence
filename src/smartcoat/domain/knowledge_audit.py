"""Canonical Knowledge Object audit contracts for Release 1.8.

Knowledge audit events are a dedicated typed profile in the Enterprise Event
family. They are system-created facts, not payloads for the legacy ``/events``
route and not a general event-sourcing contract.
"""

from __future__ import annotations

from collections.abc import Sequence
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
from smartcoat.domain.evidence_provenance import EvidenceReference, ProvenanceV2
from smartcoat.domain.knowledge_lifecycle import (
    MAX_ACTOR_ID_LENGTH,
    MAX_NOTE_LENGTH,
    MAX_ROLE_LENGTH,
    DraftDeletionPlan,
    LifecycleAction,
    LifecycleActor,
    LifecycleMutationPlan,
)
from smartcoat.domain.knowledge_objects_v2 import (
    MAX_IDENTIFIER_LENGTH,
    KnowledgeObjectV2CreateCommand,
    KnowledgeObjectV2UpdateCommand,
)

KNOWLEDGE_AUDIT_SCHEMA_VERSION = "1"
KNOWLEDGE_AUDIT_EVENT_FAMILY = "enterprise_event"
MAX_CHANGED_FIELDS = 32


def _custom_error(code: str, message: str) -> PydanticCustomError:
    return PydanticCustomError(code, message)


def _normalize_required_text(
    value: Any,
    *,
    field_name: str,
    max_length: int,
) -> str:
    if not isinstance(value, str):
        raise _custom_error(
            "knowledge_audit_invalid_text",
            f"{field_name} must be a string",
        )
    normalized = value.strip()
    if not normalized:
        raise _custom_error(
            "knowledge_audit_blank_text",
            f"{field_name} must not be blank",
        )
    if len(normalized) > max_length:
        raise _custom_error(
            "knowledge_audit_text_too_long",
            f"{field_name} must contain at most {max_length} characters",
        )
    return normalized


def _normalize_aware_utc(value: datetime, *, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise _custom_error(
            "knowledge_audit_naive_timestamp",
            f"{field_name} must be timezone-aware",
        )
    return value.astimezone(UTC)


class KnowledgeAuditEventType(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DRAFT_DELETE = "draft_delete"
    TRANSITION = "transition"
    CORRECTION_REQUEST = "correction_request"
    REJECT = "reject"
    REOPEN = "reopen"
    APPROVE = "approve"
    DEPRECATE = "deprecate"


class KnowledgeAuditChangedField(StrEnum):
    TITLE = "title"
    DESCRIPTION = "description"
    KNOWLEDGE_TYPE = "knowledge_type"
    OWNER = "owner"
    CONFIDENTIALITY = "confidentiality"
    UNCERTAINTY = "uncertainty"
    TAGS = "tags"
    CONTENT = "content"
    CONTEXT = "context"
    EVIDENCE = "evidence"
    PROVENANCE = "provenance"
    KNOWLEDGE_RELATIONSHIPS = "knowledge_relationships"
    DECISION_RELATIONSHIPS = "decision_relationships"
    LIFECYCLE_STATE = "lifecycle_state"
    REVISION = "revision"


_ACTION_EVENT_TYPES = {
    LifecycleAction.SUBMIT_DRAFT: KnowledgeAuditEventType.TRANSITION,
    LifecycleAction.REQUEST_CAPTURED_CORRECTION: (KnowledgeAuditEventType.CORRECTION_REQUEST),
    LifecycleAction.COMPLETE_REVIEW: KnowledgeAuditEventType.TRANSITION,
    LifecycleAction.REJECT_CAPTURED: KnowledgeAuditEventType.REJECT,
    LifecycleAction.REQUEST_REVIEWED_CORRECTION: (KnowledgeAuditEventType.CORRECTION_REQUEST),
    LifecycleAction.VALIDATE_REVIEWED: KnowledgeAuditEventType.TRANSITION,
    LifecycleAction.REJECT_REVIEWED: KnowledgeAuditEventType.REJECT,
    LifecycleAction.REQUEST_VALIDATED_CORRECTION: (KnowledgeAuditEventType.CORRECTION_REQUEST),
    LifecycleAction.APPROVE_VALIDATED: KnowledgeAuditEventType.APPROVE,
    LifecycleAction.REJECT_VALIDATED: KnowledgeAuditEventType.REJECT,
    LifecycleAction.DEPRECATE_APPROVED: KnowledgeAuditEventType.DEPRECATE,
    LifecycleAction.REOPEN_REJECTED: KnowledgeAuditEventType.REOPEN,
    LifecycleAction.DELETE_DRAFT: KnowledgeAuditEventType.DRAFT_DELETE,
}

_ACTION_LIFECYCLES = {
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


def audit_event_type_for_lifecycle_action(
    action: LifecycleAction,
) -> KnowledgeAuditEventType:
    """Map each accepted T04 action to one canonical audit event type."""

    return _ACTION_EVENT_TYPES[action]


class _KnowledgeAuditPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)

    organization_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    object_id: UUID
    event_type: KnowledgeAuditEventType
    lifecycle_action: LifecycleAction | None = None
    actor_id: str = Field(min_length=1, max_length=MAX_ACTOR_ID_LENGTH)
    actor_role: str = Field(min_length=1, max_length=MAX_ROLE_LENGTH)
    occurred_at: datetime
    correlation_id: UUID
    previous_lifecycle: LifecycleState | None = None
    resulting_lifecycle: LifecycleState | None = None
    previous_revision: int | None = Field(default=None, gt=0)
    resulting_revision: int | None = Field(default=None, gt=0)
    reason_or_note: str = Field(min_length=1, max_length=MAX_NOTE_LENGTH)
    changed_fields: tuple[KnowledgeAuditChangedField, ...] = Field(
        default_factory=tuple,
        max_length=MAX_CHANGED_FIELDS,
    )

    @field_validator(
        "organization_id",
        "actor_id",
        "actor_role",
        "reason_or_note",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value: Any, info: ValidationInfo) -> str:
        field_name = info.field_name or "audit field"
        max_lengths = {
            "organization_id": MAX_IDENTIFIER_LENGTH,
            "actor_id": MAX_ACTOR_ID_LENGTH,
            "actor_role": MAX_ROLE_LENGTH,
            "reason_or_note": MAX_NOTE_LENGTH,
        }
        return _normalize_required_text(
            value,
            field_name=field_name,
            max_length=max_lengths[field_name],
        )

    @field_validator("occurred_at")
    @classmethod
    def normalize_occurred_at(cls, value: datetime) -> datetime:
        return _normalize_aware_utc(value, field_name="occurred_at")

    @field_validator("changed_fields", mode="before")
    @classmethod
    def normalize_changed_fields(
        cls,
        value: Any,
    ) -> tuple[KnowledgeAuditChangedField, ...]:
        if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
            raise _custom_error(
                "knowledge_audit_invalid_changed_fields",
                "changed_fields must be an ordered collection of top-level names",
            )
        if len(value) > MAX_CHANGED_FIELDS:
            raise _custom_error(
                "knowledge_audit_changed_fields_too_large",
                f"changed_fields must contain at most {MAX_CHANGED_FIELDS} items",
            )
        normalized: list[KnowledgeAuditChangedField] = []
        seen: set[KnowledgeAuditChangedField] = set()
        for item in value:
            candidate = item.strip().lower() if isinstance(item, str) else item
            try:
                field = KnowledgeAuditChangedField(candidate)
            except (TypeError, ValueError) as error:
                raise _custom_error(
                    "knowledge_audit_unsafe_changed_field",
                    "changed_fields may contain only approved top-level field names",
                ) from error
            if field in seen:
                raise _custom_error(
                    "knowledge_audit_duplicate_changed_field",
                    f"changed_fields contains duplicate {field.value}",
                )
            normalized.append(field)
            seen.add(field)
        return tuple(normalized)

    @model_validator(mode="after")
    def validate_event_semantics(self) -> _KnowledgeAuditPayload:
        if self.event_type is KnowledgeAuditEventType.CREATE:
            if (
                self.lifecycle_action is not None
                or self.previous_lifecycle is not None
                or self.previous_revision is not None
                or self.resulting_lifecycle is not LifecycleState.DRAFT
                or self.resulting_revision != 1
                or not self.changed_fields
            ):
                raise _custom_error(
                    "knowledge_audit_create_inconsistent",
                    "create must establish draft revision 1 from no previous state",
                )
            return self

        if self.event_type is KnowledgeAuditEventType.UPDATE:
            if (
                self.lifecycle_action is not None
                or self.previous_lifecycle is None
                or self.resulting_lifecycle is not self.previous_lifecycle
                or self.previous_revision is None
                or self.resulting_revision != self.previous_revision + 1
                or not self.changed_fields
                or KnowledgeAuditChangedField.LIFECYCLE_STATE in self.changed_fields
            ):
                raise _custom_error(
                    "knowledge_audit_update_inconsistent",
                    "update must preserve lifecycle, increment revision once, and name changes",
                )
            return self

        if self.event_type is KnowledgeAuditEventType.DRAFT_DELETE:
            if (
                self.lifecycle_action is not LifecycleAction.DELETE_DRAFT
                or self.previous_lifecycle is not LifecycleState.DRAFT
                or self.previous_revision is None
                or self.resulting_lifecycle is not None
                or self.resulting_revision is not None
                or self.changed_fields
            ):
                raise _custom_error(
                    "knowledge_audit_delete_inconsistent",
                    "draft deletion must be a content-free tombstone of a draft revision",
                )
            return self

        if self.lifecycle_action is None:
            raise _custom_error(
                "knowledge_audit_lifecycle_action_required",
                "lifecycle audit events require a canonical lifecycle action",
            )
        expected_event_type = _ACTION_EVENT_TYPES[self.lifecycle_action]
        expected_lifecycles = _ACTION_LIFECYCLES.get(self.lifecycle_action)
        if (
            self.lifecycle_action is LifecycleAction.DELETE_DRAFT
            or expected_event_type is not self.event_type
            or expected_lifecycles != (self.previous_lifecycle, self.resulting_lifecycle)
            or self.previous_revision is None
            or self.resulting_revision != self.previous_revision + 1
            or set(self.changed_fields)
            != {
                KnowledgeAuditChangedField.LIFECYCLE_STATE,
                KnowledgeAuditChangedField.REVISION,
            }
        ):
            raise _custom_error(
                "knowledge_audit_lifecycle_inconsistent",
                "lifecycle audit fields must exactly match the accepted T04 action",
            )
        return self


class KnowledgeAuditAppendRequest(_KnowledgeAuditPayload):
    """Internal canonical append intent; server sequence and record time are absent."""


class KnowledgeAuditEvent(_KnowledgeAuditPayload):
    """Immutable, alias-free canonical Knowledge audit event."""

    event_id: UUID
    schema_version: Literal["1"] = "1"
    event_family: Literal["enterprise_event"] = "enterprise_event"
    recorded_at: datetime
    audit_sequence: int = Field(gt=0)

    @field_validator("recorded_at")
    @classmethod
    def normalize_recorded_at(cls, value: datetime) -> datetime:
        return _normalize_aware_utc(value, field_name="recorded_at")

    @model_validator(mode="after")
    def validate_recording_order(self) -> KnowledgeAuditEvent:
        if self.recorded_at < self.occurred_at:
            raise _custom_error(
                "knowledge_audit_recorded_before_occurred",
                "recorded_at must not precede occurred_at",
            )
        return self


class GovernedKnowledgeCreateCommand(BaseModel):
    """Create intent plus the actor metadata required for atomic audit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    create: KnowledgeObjectV2CreateCommand
    evidence: tuple[EvidenceReference, ...]
    provenance: ProvenanceV2
    actor: LifecycleActor
    reason_or_note: str = Field(min_length=1, max_length=MAX_NOTE_LENGTH)
    correlation_id: UUID

    @field_validator("reason_or_note", mode="before")
    @classmethod
    def normalize_reason_or_note(cls, value: Any) -> str:
        return _normalize_required_text(
            value,
            field_name="reason_or_note",
            max_length=MAX_NOTE_LENGTH,
        )


class GovernedKnowledgeUpdateCommand(BaseModel):
    """Complete update intent plus actor and correlation metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    organization_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    update: KnowledgeObjectV2UpdateCommand
    evidence: tuple[EvidenceReference, ...] | None = None
    provenance: ProvenanceV2 | None = None
    actor: LifecycleActor
    reason_or_note: str = Field(min_length=1, max_length=MAX_NOTE_LENGTH)
    correlation_id: UUID

    @field_validator("organization_id", "reason_or_note", mode="before")
    @classmethod
    def normalize_text(cls, value: Any, info: ValidationInfo) -> str:
        field_name = info.field_name or "update field"
        return _normalize_required_text(
            value,
            field_name=field_name,
            max_length=(
                MAX_IDENTIFIER_LENGTH if field_name == "organization_id" else MAX_NOTE_LENGTH
            ),
        )


def audit_request_from_lifecycle_plan(
    *,
    organization_id: str,
    plan: LifecycleMutationPlan,
    correlation_id: UUID,
) -> KnowledgeAuditAppendRequest:
    """Translate one accepted T04 mutation plan without redefining its rules."""

    return KnowledgeAuditAppendRequest(
        organization_id=organization_id,
        object_id=plan.object_id,
        event_type=audit_event_type_for_lifecycle_action(plan.action),
        lifecycle_action=plan.action,
        actor_id=plan.actor.actor_id,
        actor_role=plan.actor.role,
        occurred_at=plan.occurred_at,
        correlation_id=correlation_id,
        previous_lifecycle=plan.from_lifecycle,
        resulting_lifecycle=plan.to_lifecycle,
        previous_revision=plan.expected_revision,
        resulting_revision=plan.resulting_revision,
        reason_or_note=plan.note_or_reason,
        changed_fields=(
            KnowledgeAuditChangedField.LIFECYCLE_STATE,
            KnowledgeAuditChangedField.REVISION,
        ),
    )


def audit_request_from_deletion_plan(
    *,
    organization_id: str,
    plan: DraftDeletionPlan,
    correlation_id: UUID,
) -> KnowledgeAuditAppendRequest:
    """Translate one accepted T04 deletion plan into a safe tombstone."""

    return KnowledgeAuditAppendRequest(
        organization_id=organization_id,
        object_id=plan.object_id,
        event_type=KnowledgeAuditEventType.DRAFT_DELETE,
        lifecycle_action=LifecycleAction.DELETE_DRAFT,
        actor_id=plan.actor.actor_id,
        actor_role=plan.actor.role,
        occurred_at=plan.occurred_at,
        correlation_id=correlation_id,
        previous_lifecycle=LifecycleState.DRAFT,
        resulting_lifecycle=None,
        previous_revision=plan.expected_revision,
        resulting_revision=None,
        reason_or_note=plan.reason,
        changed_fields=(),
    )
