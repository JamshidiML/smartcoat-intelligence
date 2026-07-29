from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator
from sqlalchemy.orm import Session

from smartcoat.api.dependencies.database import get_db_session

LAB_SOURCE_SYSTEM = "smartcoat-lab"
LAB_OBSERVATION_TAG = "lab-observation"
LAB_OBSERVATION_ROLE = "project"
CREATE_REASON = "Manual lab observation capture"


class LabObservationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1, max_length=512)
    project_name: str = Field(min_length=1, max_length=256)
    title: str = Field(min_length=1, max_length=256)
    observation: str = Field(min_length=1, max_length=4096)
    source_reference: str = Field(min_length=1, max_length=2048)
    observed_at: datetime
    actor_id: str = Field(min_length=1, max_length=512)
    actor_role: str = Field(min_length=1, max_length=128)

    @field_validator(
        "project_id",
        "project_name",
        "title",
        "observation",
        "source_reference",
        "actor_id",
        "actor_role",
        mode="before",
    )
    @classmethod
    def normalize_required_text(cls, value: Any, info: ValidationInfo) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{info.field_name} must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{info.field_name} must not be blank")
        return normalized

    @field_validator("observed_at")
    @classmethod
    def normalize_observed_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        return value.astimezone(UTC)


class LabObservationProvenanceView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_system: str | None
    source_reference: str | None
    created_by: str | None
    creation_method: str | None
    captured_at: datetime | None
    source_created_at: datetime | None
    completeness: str


class LabObservationView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    object_id: UUID
    organization_id: str
    revision: int
    lifecycle_state: str
    title: str
    observation: str
    project_id: str
    project_name: str
    evidence_id: str
    source_reference: str
    observed_at: datetime
    created_at: datetime
    updated_at: datetime
    provenance: LabObservationProvenanceView


class LabObservationCreateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation: LabObservationView
    audit_event_id: UUID
    audit_sequence: int


class LabObservationListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    items: tuple[LabObservationView, ...]
    limit: int
    offset: int
    returned_count: int
    has_more: bool


def get_lab_observation_audit_service() -> Any:
    from smartcoat.services.knowledge_audit_service import KnowledgeAuditService
    from smartcoat.storage.database.session import SessionLocal

    return KnowledgeAuditService(SessionLocal)


def get_lab_observation_repository(
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


def _build_create_command(
    payload: LabObservationCreateRequest,
    organization_id: str,
) -> Any:
    from pydantic import ValidationError

    from smartcoat.domain.context_references import (
        ContextIdKind,
        ContextReference,
        ContextType,
        KnowledgeContext,
    )
    from smartcoat.domain.evidence_provenance import (
        CreationMethod,
        EvidenceCompleteness,
        EvidenceReference,
        EvidenceType,
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

    evidence_id = f"lab-observation:{uuid4()}"
    correlation_id = uuid4()
    try:
        project_reference = ContextReference(
            context_type=ContextType.PROJECT,
            reference_id=payload.project_id,
            id_kind=ContextIdKind.EXTERNAL,
            source_system=LAB_SOURCE_SYSTEM,
            display_name=payload.project_name,
            version=None,
            relationship_role=LAB_OBSERVATION_ROLE,
            source_reference=payload.source_reference,
            evidence_reference=evidence_id,
            attributes={},
        )
        evidence = EvidenceReference.model_validate(
            {
                "evidence_id": evidence_id,
                "evidence_type": EvidenceType.OBSERVATION,
                "completeness": EvidenceCompleteness.COMPLETE,
                "title": payload.title,
                "description": payload.observation,
                "source_reference": payload.source_reference,
                "source_system": LAB_SOURCE_SYSTEM,
                "captured_by": payload.actor_id,
                "captured_at": payload.observed_at,
                "source_created_at": payload.observed_at,
                "integrity": None,
                "media_type": None,
                "confidentiality": ConfidentialityLevel.INTERNAL,
                "context_reference": project_reference,
            }
        )
        provenance = ProvenanceV2(
            source_system=LAB_SOURCE_SYSTEM,
            source_reference=payload.source_reference,
            created_by=payload.actor_id,
            creation_method=CreationMethod.MANUAL,
            captured_at=payload.observed_at,
            source_created_at=payload.observed_at,
            transformation_history=(),
            derived_from_object_id=None,
            derived_from_revision=None,
            completeness=ProvenanceCompleteness.COMPLETE,
        )
        mutable_state = KnowledgeObjectV2MutableState(
            title=payload.title,
            description=None,
            knowledge_type=KnowledgeObjectType.OBSERVATION,
            owner=OwnerReference(
                owner_id=payload.actor_id,
                role=payload.actor_role,
            ),
            confidentiality=ConfidentialityLevel.INTERNAL,
            uncertainty=None,
            tags=(LAB_OBSERVATION_TAG,),
            content={"observation": payload.observation},
            context=KnowledgeContext(references=[project_reference]),
            evidence_ids=(evidence_id,),
            knowledge_relationships=(),
            decision_relationships=(),
        )
        create = KnowledgeObjectV2CreateCommand(
            organization_id=organization_id,
            mutable_state=mutable_state,
        )
        return GovernedKnowledgeCreateCommand(
            create=create,
            evidence=(evidence,),
            provenance=provenance,
            actor=LifecycleActor(
                actor_id=payload.actor_id,
                role=payload.actor_role,
            ),
            reason_or_note=CREATE_REASON,
            correlation_id=correlation_id,
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=422,
            detail="Invalid lab observation payload",
        ) from error


def _to_view(composition: Any) -> LabObservationView:
    from smartcoat.domain.context_references import ContextType
    from smartcoat.domain.evidence_provenance import EvidenceType
    from smartcoat.domain.knowledge_objects import KnowledgeObjectType

    state = composition.core.mutable_state.to_mutable_state()
    project_references = [
        reference
        for reference in state.context.references
        if reference.context_type is ContextType.PROJECT
        and reference.source_system == LAB_SOURCE_SYSTEM
    ]
    if (
        state.knowledge_type is not KnowledgeObjectType.OBSERVATION
        or not isinstance(state.content.get("observation"), str)
        or not state.content["observation"]
        or len(project_references) != 1
        or len(composition.evidence) != 1
        or composition.evidence[0].evidence_type is not EvidenceType.OBSERVATION
        or composition.provenance.source_system != LAB_SOURCE_SYSTEM
        or composition.provenance.source_created_at is None
        or composition.provenance.source_reference is None
    ):
        raise ValueError("not_a_lab_observation")

    project_reference = project_references[0]
    evidence = composition.evidence[0]
    return LabObservationView(
        object_id=composition.core.object_id,
        organization_id=composition.core.organization_id,
        revision=composition.core.revision,
        lifecycle_state=composition.core.lifecycle_state.value,
        title=state.title,
        observation=state.content["observation"],
        project_id=project_reference.reference_id,
        project_name=project_reference.display_name,
        evidence_id=evidence.evidence_id,
        source_reference=composition.provenance.source_reference,
        observed_at=composition.provenance.source_created_at,
        created_at=composition.core.created_at,
        updated_at=composition.core.updated_at,
        provenance=LabObservationProvenanceView(
            source_system=composition.provenance.source_system,
            source_reference=composition.provenance.source_reference,
            created_by=composition.provenance.created_by,
            creation_method=(
                composition.provenance.creation_method.value
                if composition.provenance.creation_method is not None
                else None
            ),
            captured_at=composition.provenance.captured_at,
            source_created_at=composition.provenance.source_created_at,
            completeness=composition.provenance.completeness.value,
        ),
    )


router = APIRouter(
    prefix="/api/v2/lab-observations",
    tags=["lab-observations"],
)


@router.post("", status_code=201, response_model=LabObservationCreateResponse)
def create_lab_observation(
    payload: LabObservationCreateRequest,
    organization_id: Annotated[
        str,
        Header(
            alias="X-SmartCoat-Organization-ID",
            min_length=1,
            max_length=512,
        ),
    ],
    service: Annotated[Any, Depends(get_lab_observation_audit_service)],
) -> LabObservationCreateResponse:
    organization_id = _normalize_organization_id(organization_id)
    command = _build_create_command(payload, organization_id)
    from smartcoat.services.knowledge_audit_service import KnowledgeAuditServiceError
    from smartcoat.storage.repositories.knowledge_v2_repository import (
        KnowledgeObjectV2RepositoryError,
    )

    try:
        result = service.create(command)
        if result.knowledge is None or result.audit_event is None:
            raise HTTPException(
                status_code=500,
                detail="Lab observation creation failed",
            )
        observation = _to_view(result.knowledge)
        return LabObservationCreateResponse(
            observation=observation,
            audit_event_id=result.audit_event.event_id,
            audit_sequence=result.audit_event.audit_sequence,
        )
    except KnowledgeObjectV2RepositoryError as error:
        if error.code == "knowledge_object_not_found":
            raise HTTPException(
                status_code=404,
                detail="Lab observation not found",
            ) from error
        raise HTTPException(
            status_code=409,
            detail="Lab observation could not be persisted",
        ) from error
    except KnowledgeAuditServiceError as error:
        raise HTTPException(
            status_code=409,
            detail="Lab observation could not be persisted",
        ) from error


@router.get("", status_code=200, response_model=LabObservationListResponse)
def list_lab_observations(
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
    repository: Annotated[Any, Depends(get_lab_observation_repository)],
) -> LabObservationListResponse:
    organization_id = _normalize_organization_id(organization_id)
    from smartcoat.storage.repositories.knowledge_v2_repository import (
        KnowledgeObjectV2RepositoryError,
    )

    try:
        object_ids = repository.list_object_ids_by_type_and_tag(
            organization_id=organization_id,
            knowledge_type="observation",
            required_tag=LAB_OBSERVATION_TAG,
            limit=limit + 1,
            offset=offset,
        )
        has_more = len(object_ids) > limit
        selected_ids = object_ids[:limit]
        items = []
        for object_id in selected_ids:
            composition = repository.get(
                object_id=object_id,
                organization_id=organization_id,
            )
            if composition is None:
                raise HTTPException(
                    status_code=500,
                    detail="Lab observation list could not be loaded",
                )
            items.append(_to_view(composition))
        return LabObservationListResponse(
            items=tuple(items),
            limit=limit,
            offset=offset,
            returned_count=len(items),
            has_more=has_more,
        )
    except KnowledgeObjectV2RepositoryError as error:
        raise HTTPException(
            status_code=500,
            detail="Lab observation list could not be loaded",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=500,
            detail="Lab observation list could not be loaded",
        ) from error


@router.get("/{object_id}", status_code=200, response_model=LabObservationView)
def get_lab_observation(
    object_id: UUID,
    organization_id: Annotated[
        str,
        Header(
            alias="X-SmartCoat-Organization-ID",
            min_length=1,
            max_length=512,
        ),
    ],
    repository: Annotated[Any, Depends(get_lab_observation_repository)],
) -> LabObservationView:
    organization_id = _normalize_organization_id(organization_id)
    composition = repository.get(
        object_id=object_id,
        organization_id=organization_id,
    )
    if composition is None:
        raise HTTPException(
            status_code=404,
            detail="Lab observation not found",
        )
    try:
        return _to_view(composition)
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail="Lab observation not found",
        ) from error
