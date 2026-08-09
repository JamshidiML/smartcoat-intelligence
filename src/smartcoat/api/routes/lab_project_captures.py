from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy.orm import Session

from smartcoat.api.dependencies.database import get_db_session
from smartcoat.domain.lab_project_capture import (
    CaptureSourceKind,
    EvidenceDescriptor,
    LabProjectCaptureCandidate,
    apply_candidate_completeness,
    to_knowledge_object_content,
)
from smartcoat.domain.lab_project_capture import (
    EvidenceType as CaptureEvidenceType,
)

LAB_PROJECT_CAPTURE_SOURCE_SYSTEM = "smartcoat-lab-project-capture"
LAB_PROJECT_CAPTURE_TAG = "lab-project-capture-v1"
LAB_PROJECT_CAPTURE_ROLE = "project"
LAB_PROJECT_CAPTURE_ACTOR_ROLE = "lab_project_reviewer"
CREATE_REASON = "Human-confirmed voice/import project capture"


class LabProjectCaptureView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    object_id: UUID
    organization_id: str
    project_id: str | None
    project_name: str | None
    customer: str | None
    current_status: str
    completeness_score: int
    lifecycle: str
    revision: int
    observed_at: datetime
    captured_at: datetime
    unresolved_question_count: int
    next_action: str | None
    follow_up_due_at: datetime | None


class LabProjectCaptureCreateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    capture: LabProjectCaptureView
    audit_event_id: UUID
    audit_sequence: int


class LabProjectCaptureListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    items: tuple[LabProjectCaptureView, ...]
    limit: int
    offset: int
    returned_count: int
    has_more: bool


def get_lab_project_capture_audit_service() -> Any:
    from smartcoat.services.knowledge_audit_service import KnowledgeAuditService
    from smartcoat.storage.database.session import SessionLocal

    return KnowledgeAuditService(SessionLocal)


def get_lab_project_capture_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> Any:
    from smartcoat.storage.repositories.knowledge_v2_repository import (
        KnowledgeObjectV2Repository,
    )

    return KnowledgeObjectV2Repository(session)


def _normalize_organization_id(organization_id: str) -> str:
    normalized = organization_id.strip()
    if not normalized:
        raise HTTPException(
            status_code=422,
            detail="X-SmartCoat-Organization-ID must not be blank",
        )
    return normalized


def _capture_source_reference(candidate: LabProjectCaptureCandidate) -> str:
    return f"lab-project-capture://{candidate.capture_session_id}"


def _observed_at(candidate: LabProjectCaptureCandidate) -> datetime:
    assert candidate.human_confirmed_at is not None
    source_times = [descriptor.captured_at for descriptor in candidate.evidence]
    if candidate.extraction_started_at is not None:
        source_times.append(candidate.extraction_started_at)
    return min(source_times, default=candidate.human_confirmed_at).astimezone(UTC)


def _project_reference(candidate: LabProjectCaptureCandidate) -> Any:
    from smartcoat.domain.context_references import (
        ContextIdKind,
        ContextReference,
        ContextType,
    )

    project_id = candidate.project.project_id
    project_name = candidate.project.project_name
    return ContextReference(
        context_type=ContextType.PROJECT,
        reference_id=project_id or str(candidate.capture_session_id),
        id_kind=ContextIdKind.EXTERNAL,
        source_system=LAB_PROJECT_CAPTURE_SOURCE_SYSTEM,
        display_name=project_name or "Unidentified lab project capture",
        version="lab-project-capture-v1",
        relationship_role=LAB_PROJECT_CAPTURE_ROLE,
        source_reference=_capture_source_reference(candidate),
        evidence_reference=(candidate.evidence[0].evidence_id if candidate.evidence else None),
        attributes={
            "project_identity_state": "known" if project_id is not None else "unknown",
            "capture_session_id": str(candidate.capture_session_id),
        },
    )


def _canonical_evidence_type(evidence_type: CaptureEvidenceType) -> Any:
    from smartcoat.domain.evidence_provenance import EvidenceType

    return {
        CaptureEvidenceType.AUDIO: EvidenceType.OBSERVATION,
        CaptureEvidenceType.TRANSCRIPT: EvidenceType.DOCUMENT,
        CaptureEvidenceType.IMAGE: EvidenceType.IMAGE,
        CaptureEvidenceType.PDF: EvidenceType.DOCUMENT,
        CaptureEvidenceType.EXCEL: EvidenceType.DATASET,
        CaptureEvidenceType.TEST_RESULT: EvidenceType.TEST_RESULT,
        CaptureEvidenceType.ERP_RECORD: EvidenceType.EXTERNAL_RECORD,
        CaptureEvidenceType.OTHER: EvidenceType.OTHER,
    }[evidence_type]


def _evidence_reference(
    descriptor: EvidenceDescriptor,
    *,
    candidate: LabProjectCaptureCandidate,
    project_reference: Any,
) -> Any:
    from smartcoat.domain.evidence_provenance import (
        EvidenceCompleteness,
        EvidenceIntegrity,
        EvidenceReference,
        IntegrityAlgorithm,
    )
    from smartcoat.domain.knowledge_objects_v2 import ConfidentialityLevel

    context_attributes = dict(project_reference.attributes)
    if descriptor.approach_id is not None:
        context_attributes["approach_id"] = descriptor.approach_id
    if descriptor.sample_id is not None:
        context_attributes["sample_id"] = descriptor.sample_id
    evidence_context = project_reference.model_copy(
        update={
            "source_reference": descriptor.source_reference,
            "evidence_reference": descriptor.evidence_id,
            "attributes": context_attributes,
        }
    )
    return EvidenceReference.model_validate(
        {
            "evidence_id": descriptor.evidence_id,
            "evidence_type": _canonical_evidence_type(descriptor.evidence_type),
            "completeness": EvidenceCompleteness.COMPLETE,
            "title": descriptor.filename or f"{descriptor.evidence_type.value} evidence",
            "description": descriptor.description,
            "source_reference": descriptor.source_reference,
            "source_system": LAB_PROJECT_CAPTURE_SOURCE_SYSTEM,
            "captured_by": candidate.human_confirmed_by,
            "captured_at": descriptor.captured_at,
            "source_created_at": descriptor.captured_at,
            "integrity": EvidenceIntegrity(
                algorithm=IntegrityAlgorithm.SHA256,
                value=descriptor.sha256,
            ),
            "media_type": descriptor.media_type,
            "confidentiality": ConfidentialityLevel.CONFIDENTIAL,
            "context_reference": evidence_context,
        }
    )


def _transformation_history(candidate: LabProjectCaptureCandidate) -> tuple[Any, ...]:
    from smartcoat.domain.evidence_provenance import ProvenanceTransformation

    assert candidate.human_confirmed_by is not None
    assert candidate.human_confirmed_at is not None
    source_reference = _capture_source_reference(candidate)
    transformations: list[ProvenanceTransformation] = []
    if candidate.extraction_model is not None and candidate.extraction_completed_at is not None:
        transformations.append(
            ProvenanceTransformation(
                transformation_type="local_structured_extraction",
                performed_by=candidate.extraction_model,
                performed_at=candidate.extraction_completed_at,
                note="Generated an unapproved structured candidate for human review.",
                source_reference=source_reference,
            )
        )
    transformations.append(
        ProvenanceTransformation(
            transformation_type="human_confirmation",
            performed_by=candidate.human_confirmed_by,
            performed_at=candidate.human_confirmed_at,
            note="Human reviewed and explicitly confirmed the candidate for draft creation.",
            source_reference=source_reference,
        )
    )
    return tuple(transformations)


def _creation_method(source_kind: CaptureSourceKind) -> Any:
    from smartcoat.domain.evidence_provenance import CreationMethod

    if source_kind is CaptureSourceKind.MANUAL:
        return CreationMethod.MANUAL
    return CreationMethod.IMPORTED


def _build_create_command(
    candidate: LabProjectCaptureCandidate,
    organization_id: str,
) -> Any:
    if not candidate.human_confirmed:
        raise HTTPException(
            status_code=422,
            detail="A human-confirmed candidate is required",
        )
    assert candidate.human_confirmed_by is not None
    assert candidate.human_confirmed_at is not None

    from smartcoat.domain.context_references import KnowledgeContext
    from smartcoat.domain.evidence_provenance import (
        ProvenanceCompleteness,
        ProvenanceV2,
    )
    from smartcoat.domain.knowledge_audit import GovernedKnowledgeCreateCommand
    from smartcoat.domain.knowledge_lifecycle import LifecycleActor
    from smartcoat.domain.knowledge_objects import KnowledgeObjectType
    from smartcoat.domain.knowledge_objects_v2 import (
        ConfidentialityLevel,
        KnowledgeObjectV2CreateCommand,
        KnowledgeObjectV2MutableState,
        OwnerReference,
    )

    evaluated = apply_candidate_completeness(candidate)
    confirmed_by = evaluated.human_confirmed_by
    confirmed_at = evaluated.human_confirmed_at
    assert confirmed_by is not None
    assert confirmed_at is not None
    source_reference = _capture_source_reference(evaluated)
    project_reference = _project_reference(evaluated)
    try:
        evidence = tuple(
            _evidence_reference(
                descriptor,
                candidate=evaluated,
                project_reference=project_reference,
            )
            for descriptor in evaluated.evidence
        )
        mutable_state = KnowledgeObjectV2MutableState(
            title=evaluated.project.project_name or "Lab project capture",
            description=evaluated.project.request_summary,
            knowledge_type=KnowledgeObjectType.OBSERVATION,
            owner=OwnerReference(
                owner_id=confirmed_by,
                role=LAB_PROJECT_CAPTURE_ACTOR_ROLE,
            ),
            confidentiality=ConfidentialityLevel.CONFIDENTIAL,
            uncertainty=None,
            tags=(LAB_PROJECT_CAPTURE_TAG,),
            content=to_knowledge_object_content(evaluated),
            context=KnowledgeContext(references=[project_reference]),
            evidence_ids=tuple(item.evidence_id for item in evidence),
            knowledge_relationships=(),
            decision_relationships=(),
        )
        provenance = ProvenanceV2(
            source_system=LAB_PROJECT_CAPTURE_SOURCE_SYSTEM,
            source_reference=source_reference,
            created_by=confirmed_by,
            creation_method=_creation_method(evaluated.source_kind),
            captured_at=confirmed_at,
            source_created_at=_observed_at(evaluated),
            transformation_history=_transformation_history(evaluated),
            derived_from_object_id=None,
            derived_from_revision=None,
            completeness=ProvenanceCompleteness.COMPLETE,
        )
        return GovernedKnowledgeCreateCommand(
            create=KnowledgeObjectV2CreateCommand(
                organization_id=organization_id,
                mutable_state=mutable_state,
            ),
            evidence=evidence,
            provenance=provenance,
            actor=LifecycleActor(
                actor_id=confirmed_by,
                role=LAB_PROJECT_CAPTURE_ACTOR_ROLE,
            ),
            reason_or_note=CREATE_REASON,
            correlation_id=uuid4(),
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=422,
            detail="Invalid confirmed project capture",
        ) from error


def _single_mapping(content: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    section = content.get(key)
    if (
        not isinstance(section, Sequence)
        or isinstance(section, (str, bytes))
        or len(section) != 1
        or not isinstance(section[0], Mapping)
    ):
        raise ValueError(f"invalid_{key}")
    return section[0]


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("invalid_optional_string")
    return value


def _string_sequence(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("invalid_string_sequence")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError("invalid_string_sequence")
    return tuple(value)


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("invalid_optional_datetime")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("invalid_optional_datetime")
    return parsed.astimezone(UTC)


def _to_view(composition: Any) -> LabProjectCaptureView:
    from smartcoat.domain.context_references import ContextType
    from smartcoat.domain.knowledge_objects import KnowledgeObjectType

    state = composition.core.mutable_state.to_mutable_state()
    project_contexts = [
        reference
        for reference in state.context.references
        if reference.context_type is ContextType.PROJECT
        and reference.source_system == LAB_PROJECT_CAPTURE_SOURCE_SYSTEM
    ]
    if (
        state.knowledge_type is not KnowledgeObjectType.OBSERVATION
        or LAB_PROJECT_CAPTURE_TAG not in state.tags
        or len(project_contexts) != 1
        or composition.provenance.source_system != LAB_PROJECT_CAPTURE_SOURCE_SYSTEM
        or composition.provenance.captured_at is None
        or composition.provenance.source_created_at is None
    ):
        raise ValueError("not_a_lab_project_capture")

    project = _single_mapping(state.content, "project")
    quality = _single_mapping(state.content, "quality_summary")
    follow_up = _single_mapping(state.content, "follow_ups")
    if quality.get("human_confirmed") is not True:
        raise ValueError("not_a_human_confirmed_capture")
    completeness_score = quality.get("completeness_score")
    if isinstance(completeness_score, bool) or not isinstance(completeness_score, int):
        raise ValueError("invalid_completeness_score")

    explicit_questions = _string_sequence(follow_up.get("unresolved_questions"))
    recommended_questions = _string_sequence(quality.get("recommended_questions"))
    unresolved_questions = tuple(dict.fromkeys((*explicit_questions, *recommended_questions)))
    current_status = project.get("project_status", "unknown")
    if not isinstance(current_status, str) or not current_status.strip():
        raise ValueError("invalid_project_status")

    return LabProjectCaptureView(
        object_id=composition.core.object_id,
        organization_id=composition.core.organization_id,
        project_id=_optional_string(project.get("project_id")),
        project_name=_optional_string(project.get("project_name")),
        customer=_optional_string(project.get("customer_company")),
        current_status=current_status,
        completeness_score=completeness_score,
        lifecycle=composition.core.lifecycle_state.value,
        revision=composition.core.revision,
        observed_at=composition.provenance.source_created_at,
        captured_at=composition.provenance.captured_at,
        unresolved_question_count=len(unresolved_questions),
        next_action=_optional_string(follow_up.get("current_next_action")),
        follow_up_due_at=_optional_datetime(follow_up.get("next_action_due_at")),
    )


router = APIRouter(
    prefix="/api/v2/lab-project-captures",
    tags=["lab-project-captures"],
)


@router.post("", status_code=201, response_model=LabProjectCaptureCreateResponse)
def create_lab_project_capture(
    candidate: LabProjectCaptureCandidate,
    organization_id: Annotated[
        str,
        Header(
            alias="X-SmartCoat-Organization-ID",
            min_length=1,
            max_length=512,
        ),
    ],
    service: Annotated[Any, Depends(get_lab_project_capture_audit_service)],
) -> LabProjectCaptureCreateResponse:
    organization_id = _normalize_organization_id(organization_id)
    command = _build_create_command(candidate, organization_id)
    from smartcoat.services.knowledge_audit_service import KnowledgeAuditServiceError
    from smartcoat.storage.repositories.knowledge_v2_repository import (
        KnowledgeObjectV2RepositoryError,
    )

    try:
        result = service.create(command)
        if result.knowledge is None or result.audit_event is None:
            raise HTTPException(
                status_code=500,
                detail="Lab project capture creation failed",
            )
        return LabProjectCaptureCreateResponse(
            capture=_to_view(result.knowledge),
            audit_event_id=result.audit_event.event_id,
            audit_sequence=result.audit_event.audit_sequence,
        )
    except (KnowledgeObjectV2RepositoryError, KnowledgeAuditServiceError) as error:
        raise HTTPException(
            status_code=409,
            detail="Lab project capture could not be persisted",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=500,
            detail="Lab project capture creation failed",
        ) from error


@router.get("", status_code=200, response_model=LabProjectCaptureListResponse)
def list_lab_project_captures(
    organization_id: Annotated[
        str,
        Header(
            alias="X-SmartCoat-Organization-ID",
            min_length=1,
            max_length=512,
        ),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    *,
    repository: Annotated[Any, Depends(get_lab_project_capture_repository)],
) -> LabProjectCaptureListResponse:
    organization_id = _normalize_organization_id(organization_id)
    from smartcoat.storage.repositories.knowledge_v2_repository import (
        KnowledgeObjectV2RepositoryError,
    )

    try:
        object_ids = repository.list_object_ids_by_type_and_tag(
            organization_id=organization_id,
            knowledge_type="observation",
            required_tag=LAB_PROJECT_CAPTURE_TAG,
            limit=limit + 1,
            offset=offset,
        )
        has_more = len(object_ids) > limit
        items: list[LabProjectCaptureView] = []
        for object_id in object_ids[:limit]:
            composition = repository.get(
                object_id=object_id,
                organization_id=organization_id,
            )
            if composition is None:
                raise ValueError("missing_list_composition")
            items.append(_to_view(composition))
        return LabProjectCaptureListResponse(
            items=tuple(items),
            limit=limit,
            offset=offset,
            returned_count=len(items),
            has_more=has_more,
        )
    except (KnowledgeObjectV2RepositoryError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail="Lab project capture list could not be loaded",
        ) from error


@router.get("/{object_id}", status_code=200, response_model=LabProjectCaptureView)
def get_lab_project_capture(
    object_id: UUID,
    organization_id: Annotated[
        str,
        Header(
            alias="X-SmartCoat-Organization-ID",
            min_length=1,
            max_length=512,
        ),
    ],
    repository: Annotated[Any, Depends(get_lab_project_capture_repository)],
) -> LabProjectCaptureView:
    organization_id = _normalize_organization_id(organization_id)
    composition = repository.get(
        object_id=object_id,
        organization_id=organization_id,
    )
    if composition is None:
        raise HTTPException(status_code=404, detail="Lab project capture not found")
    try:
        return _to_view(composition)
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail="Lab project capture not found",
        ) from error


__all__ = [
    "CREATE_REASON",
    "LAB_PROJECT_CAPTURE_ACTOR_ROLE",
    "LAB_PROJECT_CAPTURE_ROLE",
    "LAB_PROJECT_CAPTURE_SOURCE_SYSTEM",
    "LAB_PROJECT_CAPTURE_TAG",
    "get_lab_project_capture_audit_service",
    "get_lab_project_capture_repository",
    "router",
]
