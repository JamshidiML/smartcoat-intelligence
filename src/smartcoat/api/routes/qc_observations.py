from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator
from sqlalchemy.orm import Session

from smartcoat.api.dependencies.database import get_db_session

QC_SOURCE_SYSTEM = "smartcoat-qc"
QC_OBSERVATION_TAG = "qc-observation"
QC_OBSERVATION_ROLE = "quality_control_record"
CREATE_REASON = "Manual QC finding capture"


class QCObservationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    qc_record_id: str = Field(min_length=1, max_length=512)
    qc_record_name: str = Field(min_length=1, max_length=256)
    title: str = Field(min_length=1, max_length=256)
    finding: str = Field(min_length=1, max_length=4096)
    source_reference: str = Field(min_length=1, max_length=2048)
    inspected_at: datetime
    actor_id: str = Field(min_length=1, max_length=512)
    actor_role: str = Field(min_length=1, max_length=128)

    @field_validator(
        "qc_record_id",
        "qc_record_name",
        "title",
        "finding",
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

    @field_validator("inspected_at")
    @classmethod
    def normalize_inspected_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("inspected_at must be timezone-aware")
        return value.astimezone(UTC)


class QCObservationProvenanceView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_system: str | None
    source_reference: str | None
    created_by: str | None
    creation_method: str | None
    captured_at: datetime | None
    source_created_at: datetime | None
    completeness: str


class QCObservationView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    object_id: UUID
    organization_id: str
    revision: int
    lifecycle_state: str
    knowledge_type: str
    title: str
    finding: str
    qc_record_id: str
    qc_record_name: str
    evidence_id: str
    source_reference: str
    inspected_at: datetime
    created_at: datetime
    updated_at: datetime
    provenance: QCObservationProvenanceView


class QCObservationCreateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation: QCObservationView
    audit_event_id: UUID
    audit_sequence: int


def get_qc_observation_audit_service() -> Any:
    from smartcoat.services.knowledge_audit_service import KnowledgeAuditService
    from smartcoat.storage.database.session import SessionLocal

    return KnowledgeAuditService(SessionLocal)


def get_qc_observation_repository(
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
    payload: QCObservationCreateRequest,
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

    evidence_id = f"qc-observation:{uuid4()}"
    correlation_id = uuid4()
    try:
        test_result_reference = ContextReference(
            context_type=ContextType.TEST_RESULT,
            reference_id=payload.qc_record_id,
            id_kind=ContextIdKind.EXTERNAL,
            source_system=QC_SOURCE_SYSTEM,
            display_name=payload.qc_record_name,
            version=None,
            relationship_role=QC_OBSERVATION_ROLE,
            source_reference=payload.source_reference,
            evidence_reference=evidence_id,
            attributes={},
        )
        evidence = EvidenceReference.model_validate(
            {
                "evidence_id": evidence_id,
                "evidence_type": EvidenceType.TEST_RESULT,
                "completeness": EvidenceCompleteness.COMPLETE,
                "title": payload.title,
                "description": payload.finding,
                "source_reference": payload.source_reference,
                "source_system": QC_SOURCE_SYSTEM,
                "captured_by": payload.actor_id,
                "captured_at": payload.inspected_at,
                "source_created_at": payload.inspected_at,
                "integrity": None,
                "media_type": None,
                "confidentiality": ConfidentialityLevel.INTERNAL,
                "context_reference": test_result_reference,
            }
        )
        provenance = ProvenanceV2(
            source_system=QC_SOURCE_SYSTEM,
            source_reference=payload.source_reference,
            created_by=payload.actor_id,
            creation_method=CreationMethod.MANUAL,
            captured_at=payload.inspected_at,
            source_created_at=payload.inspected_at,
            transformation_history=(),
            derived_from_object_id=None,
            derived_from_revision=None,
            completeness=ProvenanceCompleteness.COMPLETE,
        )
        mutable_state = KnowledgeObjectV2MutableState(
            title=payload.title,
            description=None,
            knowledge_type=KnowledgeObjectType.FINDING,
            owner=OwnerReference(
                owner_id=payload.actor_id,
                role=payload.actor_role,
            ),
            confidentiality=ConfidentialityLevel.INTERNAL,
            uncertainty=None,
            tags=(QC_OBSERVATION_TAG,),
            content={"finding": payload.finding},
            context=KnowledgeContext(references=[test_result_reference]),
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
            detail="Invalid QC observation payload",
        ) from error


def _to_view(composition: Any) -> QCObservationView:
    from smartcoat.domain.context_references import ContextType
    from smartcoat.domain.evidence_provenance import EvidenceType
    from smartcoat.domain.knowledge_objects import KnowledgeObjectType

    state = composition.core.mutable_state.to_mutable_state()
    test_result_references = [
        reference
        for reference in state.context.references
        if reference.context_type is ContextType.TEST_RESULT
        and reference.source_system == QC_SOURCE_SYSTEM
    ]
    if (
        state.knowledge_type is not KnowledgeObjectType.FINDING
        or not isinstance(state.content.get("finding"), str)
        or not state.content["finding"]
        or len(test_result_references) != 1
        or len(composition.evidence) != 1
        or composition.evidence[0].evidence_type is not EvidenceType.TEST_RESULT
        or composition.provenance.source_system != QC_SOURCE_SYSTEM
        or composition.provenance.source_created_at is None
        or composition.provenance.source_reference is None
    ):
        raise ValueError("not_a_qc_observation")

    test_result_reference = test_result_references[0]
    evidence = composition.evidence[0]
    return QCObservationView(
        object_id=composition.core.object_id,
        organization_id=composition.core.organization_id,
        revision=composition.core.revision,
        lifecycle_state=composition.core.lifecycle_state.value,
        knowledge_type=state.knowledge_type.value,
        title=state.title,
        finding=state.content["finding"],
        qc_record_id=test_result_reference.reference_id,
        qc_record_name=test_result_reference.display_name,
        evidence_id=evidence.evidence_id,
        source_reference=composition.provenance.source_reference,
        inspected_at=composition.provenance.source_created_at,
        created_at=composition.core.created_at,
        updated_at=composition.core.updated_at,
        provenance=QCObservationProvenanceView(
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
    prefix="/api/v2/qc-observations",
    tags=["qc-observations"],
)


@router.post("", status_code=201, response_model=QCObservationCreateResponse)
def create_qc_observation(
    payload: QCObservationCreateRequest,
    organization_id: Annotated[
        str,
        Header(
            alias="X-SmartCoat-Organization-ID",
            min_length=1,
            max_length=512,
        ),
    ],
    service: Annotated[Any, Depends(get_qc_observation_audit_service)],
) -> QCObservationCreateResponse:
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
                detail="QC observation creation failed",
            )
        observation = _to_view(result.knowledge)
        return QCObservationCreateResponse(
            observation=observation,
            audit_event_id=result.audit_event.event_id,
            audit_sequence=result.audit_event.audit_sequence,
        )
    except KnowledgeObjectV2RepositoryError as error:
        if error.code == "knowledge_object_not_found":
            raise HTTPException(
                status_code=404,
                detail="QC observation not found",
            ) from error
        raise HTTPException(
            status_code=409,
            detail="QC observation could not be persisted",
        ) from error
    except KnowledgeAuditServiceError as error:
        raise HTTPException(
            status_code=409,
            detail="QC observation could not be persisted",
        ) from error


@router.get("/{object_id}", status_code=200, response_model=QCObservationView)
def get_qc_observation(
    object_id: UUID,
    organization_id: Annotated[
        str,
        Header(
            alias="X-SmartCoat-Organization-ID",
            min_length=1,
            max_length=512,
        ),
    ],
    repository: Annotated[Any, Depends(get_qc_observation_repository)],
) -> QCObservationView:
    organization_id = _normalize_organization_id(organization_id)
    composition = repository.get(
        object_id=object_id,
        organization_id=organization_id,
    )
    if composition is None:
        raise HTTPException(
            status_code=404,
            detail="QC observation not found",
        )
    try:
        return _to_view(composition)
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail="QC observation not found",
        ) from error
