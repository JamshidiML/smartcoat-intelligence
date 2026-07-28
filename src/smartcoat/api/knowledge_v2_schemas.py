"""Explicit HTTP contracts and domain mappings for Knowledge Object API v2."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from smartcoat.domain.base import LifecycleState
from smartcoat.domain.context_references import ContextReference
from smartcoat.domain.evidence_provenance import (
    EvidenceCompleteness,
    EvidenceIntegrity,
    EvidenceReference,
    EvidenceType,
    KnowledgeObjectV2EvidenceComposition,
    ProvenanceV2,
)
from smartcoat.domain.knowledge_audit import (
    GovernedKnowledgeCreateCommand,
    GovernedKnowledgeUpdateCommand,
    KnowledgeAuditChangedField,
    KnowledgeAuditEvent,
    KnowledgeAuditEventType,
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
    DecisionObjectRelationship,
    JsonValue,
    KnowledgeObjectRelationship,
    KnowledgeObjectV2CreateCommand,
    KnowledgeObjectV2MutableState,
    KnowledgeObjectV2UpdateCommand,
    OwnerReference,
    UncertaintyDeclaration,
)
from smartcoat.domain.knowledge_query import (
    KnowledgeObjectV2CollectionItem,
    KnowledgeObjectV2Page,
    KnowledgeQuerySort,
)

ActionNote = Annotated[str, Field(min_length=1, max_length=2000)]


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("response timestamps must be timezone-aware")
    return value.astimezone(UTC)


class DeclaredActor(BaseModel):
    """Caller-declared metadata; this contract does not authenticate the actor."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    actor_id: str = Field(min_length=1, max_length=256)
    actor_role: str = Field(min_length=1, max_length=128)

    def to_domain(self) -> LifecycleActor:
        return LifecycleActor(actor_id=self.actor_id, role=self.actor_role)


class EvidenceReferenceAPI(BaseModel):
    """Public metadata-only evidence contract without canonical storage fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str = Field(min_length=1, max_length=512)
    evidence_type: EvidenceType
    completeness: EvidenceCompleteness
    title: str | None = Field(default=None, max_length=256)
    description: str | None = Field(default=None, max_length=2000)
    source_reference: str = Field(min_length=1, max_length=2048)
    source_system: str | None = Field(default=None, max_length=128)
    captured_by: str | None = Field(default=None, max_length=256)
    captured_at: datetime | None = None
    source_created_at: datetime | None = None
    integrity: EvidenceIntegrity | None = None
    media_type: str | None = Field(default=None, max_length=128)
    confidentiality: ConfidentialityLevel | None = None
    context_reference: ContextReference | None = None

    def to_domain(self) -> EvidenceReference:
        return EvidenceReference.model_validate(self.model_dump(mode="python"))

    @classmethod
    def from_domain(cls, value: EvidenceReference) -> EvidenceReferenceAPI:
        return cls.model_validate(value.model_dump(mode="python"))


class KnowledgeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mutable_state: KnowledgeObjectV2MutableState
    evidence: tuple[EvidenceReferenceAPI, ...]
    provenance: ProvenanceV2
    actor: DeclaredActor
    reason_or_note: str = Field(min_length=1, max_length=2000)

    def to_domain(
        self,
        *,
        organization_id: str,
        correlation_id: UUID,
    ) -> GovernedKnowledgeCreateCommand:
        return GovernedKnowledgeCreateCommand(
            create=KnowledgeObjectV2CreateCommand(
                organization_id=organization_id,
                mutable_state=self.mutable_state,
            ),
            evidence=tuple(item.to_domain() for item in self.evidence),
            provenance=self.provenance,
            actor=self.actor.to_domain(),
            reason_or_note=self.reason_or_note,
            correlation_id=correlation_id,
        )


class KnowledgeUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_revision: int = Field(gt=0)
    replacement: KnowledgeObjectV2MutableState
    evidence: tuple[EvidenceReferenceAPI, ...] | None = None
    provenance: ProvenanceV2 | None = None
    actor: DeclaredActor
    reason_or_note: str = Field(min_length=1, max_length=2000)

    def to_domain(
        self,
        *,
        object_id: UUID,
        organization_id: str,
        correlation_id: UUID,
    ) -> GovernedKnowledgeUpdateCommand:
        return GovernedKnowledgeUpdateCommand(
            organization_id=organization_id,
            update=KnowledgeObjectV2UpdateCommand(
                object_id=object_id,
                expected_revision=self.expected_revision,
                replacement=self.replacement,
            ),
            evidence=(
                tuple(item.to_domain() for item in self.evidence)
                if self.evidence is not None
                else None
            ),
            provenance=self.provenance,
            actor=self.actor.to_domain(),
            reason_or_note=self.reason_or_note,
            correlation_id=correlation_id,
        )


class _LifecycleActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_revision: int = Field(gt=0)
    actor: DeclaredActor


class SubmitDraftActionRequest(_LifecycleActionRequest):
    action: Literal["submit_draft"]
    submission_note: ActionNote


class RequestCapturedCorrectionActionRequest(_LifecycleActionRequest):
    action: Literal["request_captured_correction"]
    correction_reason: ActionNote


class CompleteReviewActionRequest(_LifecycleActionRequest):
    action: Literal["complete_review"]
    review_note: ActionNote


class RejectCapturedActionRequest(_LifecycleActionRequest):
    action: Literal["reject_captured"]
    rejection_reason: ActionNote


class RequestReviewedCorrectionActionRequest(_LifecycleActionRequest):
    action: Literal["request_reviewed_correction"]
    correction_reason: ActionNote


class ValidateReviewedActionRequest(_LifecycleActionRequest):
    action: Literal["validate_reviewed"]
    validation_note: ActionNote


class RejectReviewedActionRequest(_LifecycleActionRequest):
    action: Literal["reject_reviewed"]
    rejection_reason: ActionNote


class RequestValidatedCorrectionActionRequest(_LifecycleActionRequest):
    action: Literal["request_validated_correction"]
    correction_reason: ActionNote


class ApproveValidatedActionRequest(_LifecycleActionRequest):
    action: Literal["approve_validated"]
    approval_note: ActionNote


class RejectValidatedActionRequest(_LifecycleActionRequest):
    action: Literal["reject_validated"]
    rejection_reason: ActionNote


class DeprecateApprovedActionRequest(_LifecycleActionRequest):
    action: Literal["deprecate_approved"]
    deprecation_reason: ActionNote
    replacement_object_id: UUID | None = None


class ReopenRejectedActionRequest(_LifecycleActionRequest):
    action: Literal["reopen_rejected"]
    reopen_reason: ActionNote


KnowledgeLifecycleActionRequest = Annotated[
    SubmitDraftActionRequest
    | RequestCapturedCorrectionActionRequest
    | CompleteReviewActionRequest
    | RejectCapturedActionRequest
    | RequestReviewedCorrectionActionRequest
    | ValidateReviewedActionRequest
    | RejectReviewedActionRequest
    | RequestValidatedCorrectionActionRequest
    | ApproveValidatedActionRequest
    | RejectValidatedActionRequest
    | DeprecateApprovedActionRequest
    | ReopenRejectedActionRequest,
    Field(discriminator="action"),
]


def lifecycle_request_to_domain(
    request: KnowledgeLifecycleActionRequest,
    *,
    object_id: UUID,
) -> LifecycleTransitionCommand:
    actor = request.actor.to_domain()
    if isinstance(request, SubmitDraftActionRequest):
        return SubmitDraftCommand(
            object_id=object_id,
            expected_revision=request.expected_revision,
            actor=actor,
            submission_note=request.submission_note,
        )
    if isinstance(request, RequestCapturedCorrectionActionRequest):
        return RequestCapturedCorrectionCommand(
            object_id=object_id,
            expected_revision=request.expected_revision,
            actor=actor,
            correction_reason=request.correction_reason,
        )
    if isinstance(request, CompleteReviewActionRequest):
        return CompleteReviewCommand(
            object_id=object_id,
            expected_revision=request.expected_revision,
            actor=actor,
            review_note=request.review_note,
        )
    if isinstance(request, RejectCapturedActionRequest):
        return RejectCapturedCommand(
            object_id=object_id,
            expected_revision=request.expected_revision,
            actor=actor,
            rejection_reason=request.rejection_reason,
        )
    if isinstance(request, RequestReviewedCorrectionActionRequest):
        return RequestReviewedCorrectionCommand(
            object_id=object_id,
            expected_revision=request.expected_revision,
            actor=actor,
            correction_reason=request.correction_reason,
        )
    if isinstance(request, ValidateReviewedActionRequest):
        return ValidateReviewedCommand(
            object_id=object_id,
            expected_revision=request.expected_revision,
            actor=actor,
            validation_note=request.validation_note,
        )
    if isinstance(request, RejectReviewedActionRequest):
        return RejectReviewedCommand(
            object_id=object_id,
            expected_revision=request.expected_revision,
            actor=actor,
            rejection_reason=request.rejection_reason,
        )
    if isinstance(request, RequestValidatedCorrectionActionRequest):
        return RequestValidatedCorrectionCommand(
            object_id=object_id,
            expected_revision=request.expected_revision,
            actor=actor,
            correction_reason=request.correction_reason,
        )
    if isinstance(request, ApproveValidatedActionRequest):
        return ApproveValidatedCommand(
            object_id=object_id,
            expected_revision=request.expected_revision,
            actor=actor,
            approval_note=request.approval_note,
        )
    if isinstance(request, RejectValidatedActionRequest):
        return RejectValidatedCommand(
            object_id=object_id,
            expected_revision=request.expected_revision,
            actor=actor,
            rejection_reason=request.rejection_reason,
        )
    if isinstance(request, DeprecateApprovedActionRequest):
        return DeprecateApprovedCommand(
            object_id=object_id,
            expected_revision=request.expected_revision,
            actor=actor,
            deprecation_reason=request.deprecation_reason,
            replacement_object_id=request.replacement_object_id,
        )
    if isinstance(request, ReopenRejectedActionRequest):
        return ReopenRejectedCommand(
            object_id=object_id,
            expected_revision=request.expected_revision,
            actor=actor,
            reopen_reason=request.reopen_reason,
        )
    raise TypeError("unsupported lifecycle action request")


class KnowledgeDraftDeleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_revision: int = Field(gt=0)
    actor: DeclaredActor
    reason: str = Field(min_length=1, max_length=2000)

    def to_domain(self, *, object_id: UUID) -> DeleteDraftCommand:
        return DeleteDraftCommand(
            object_id=object_id,
            expected_revision=self.expected_revision,
            actor=self.actor.to_domain(),
            reason=self.reason,
        )


class KnowledgeObjectV2MutableStateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str
    description: str | None
    knowledge_type: KnowledgeObjectType
    owner: OwnerReference
    confidentiality: ConfidentialityLevel
    uncertainty: UncertaintyDeclaration | None
    tags: tuple[str, ...]
    content: dict[str, JsonValue]
    context_references: tuple[ContextReference, ...]
    evidence_ids: tuple[str, ...]
    knowledge_relationships: tuple[KnowledgeObjectRelationship, ...]
    decision_relationships: tuple[DecisionObjectRelationship, ...]

    @classmethod
    def from_domain(
        cls,
        value: KnowledgeObjectV2MutableState,
    ) -> KnowledgeObjectV2MutableStateResponse:
        return cls(
            title=value.title,
            description=value.description,
            knowledge_type=value.knowledge_type,
            owner=value.owner,
            confidentiality=value.confidentiality,
            uncertainty=value.uncertainty,
            tags=value.tags,
            content=value.content,
            context_references=tuple(value.context.references),
            evidence_ids=value.evidence_ids,
            knowledge_relationships=value.knowledge_relationships,
            decision_relationships=value.decision_relationships,
        )


class KnowledgeObjectV2Response(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    object_id: UUID
    organization_id: str
    revision: int
    lifecycle_state: LifecycleState
    created_at: datetime
    updated_at: datetime
    mutable_state: KnowledgeObjectV2MutableStateResponse
    evidence: tuple[EvidenceReferenceAPI, ...]
    provenance: ProvenanceV2

    _normalize_timestamps = field_validator("created_at", "updated_at")(_aware_utc)

    @classmethod
    def from_domain(
        cls,
        value: KnowledgeObjectV2EvidenceComposition,
    ) -> KnowledgeObjectV2Response:
        core = value.core
        return cls(
            object_id=core.object_id,
            organization_id=core.organization_id,
            revision=core.revision,
            lifecycle_state=core.lifecycle_state,
            created_at=core.created_at,
            updated_at=core.updated_at,
            mutable_state=KnowledgeObjectV2MutableStateResponse.from_domain(
                core.mutable_state.to_mutable_state()
            ),
            evidence=tuple(EvidenceReferenceAPI.from_domain(item) for item in value.evidence),
            provenance=ProvenanceV2.model_validate(value.provenance.model_dump(mode="python")),
        )


class KnowledgeAuditEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: UUID
    schema_version: Literal["1"]
    event_family: Literal["enterprise_event"]
    organization_id: str
    object_id: UUID
    event_type: KnowledgeAuditEventType
    lifecycle_action: LifecycleAction | None
    actor_id: str
    actor_role: str
    occurred_at: datetime
    recorded_at: datetime
    audit_sequence: int
    correlation_id: UUID
    replacement_object_id: UUID | None
    previous_lifecycle: LifecycleState | None
    resulting_lifecycle: LifecycleState | None
    previous_revision: int | None
    resulting_revision: int | None
    reason_or_note: str
    changed_fields: tuple[KnowledgeAuditChangedField, ...]

    _normalize_timestamps = field_validator("occurred_at", "recorded_at")(_aware_utc)

    @classmethod
    def from_domain(cls, value: KnowledgeAuditEvent) -> KnowledgeAuditEventResponse:
        return cls.model_validate(value.model_dump(mode="python"))


class KnowledgeMutationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    knowledge: KnowledgeObjectV2Response
    audit_event: KnowledgeAuditEventResponse | None


class KnowledgeDraftDeleteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    deleted_object_id: UUID
    deleted: Literal[True] = True
    audit_event: KnowledgeAuditEventResponse


class KnowledgeObjectV2CollectionItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    object_id: UUID
    revision: int
    lifecycle_state: LifecycleState
    title: str
    knowledge_type: KnowledgeObjectType
    owner: OwnerReference
    confidentiality: ConfidentialityLevel
    created_at: datetime
    updated_at: datetime

    _normalize_timestamps = field_validator("created_at", "updated_at")(_aware_utc)

    @classmethod
    def from_domain(
        cls,
        value: KnowledgeObjectV2CollectionItem,
    ) -> KnowledgeObjectV2CollectionItemResponse:
        return cls(
            object_id=value.object_id,
            revision=value.revision,
            lifecycle_state=value.lifecycle_state,
            title=value.title,
            knowledge_type=value.knowledge_type,
            owner=OwnerReference(
                owner_id=value.owner.owner_id,
                role=value.owner.role,
            ),
            confidentiality=value.confidentiality,
            created_at=value.created_at,
            updated_at=value.updated_at,
        )


class KnowledgeObjectV2PageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    items: tuple[KnowledgeObjectV2CollectionItemResponse, ...]
    returned_count: int
    requested_page_size: int
    has_more: bool
    next_cursor: str | None
    applied_sort: KnowledgeQuerySort

    @classmethod
    def from_domain(cls, value: KnowledgeObjectV2Page) -> KnowledgeObjectV2PageResponse:
        return cls(
            items=tuple(
                KnowledgeObjectV2CollectionItemResponse.from_domain(item) for item in value.items
            ),
            returned_count=value.returned_count,
            requested_page_size=value.requested_page_size,
            has_more=value.has_more,
            next_cursor=value.next_cursor,
            applied_sort=value.applied_sort,
        )


class KnowledgeAuditHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    object_id: UUID
    events: tuple[KnowledgeAuditEventResponse, ...]


class SmartCoatAPIError(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    message: str
    correlation_id: str


class SmartCoatAPIErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    error: SmartCoatAPIError
