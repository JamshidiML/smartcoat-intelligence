"""Versioned governed Knowledge Object HTTP routes."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Query, status

from smartcoat.api.dependencies.knowledge_v2 import (
    AuditServiceDependency,
    CorrelationDependency,
    OrganizationDependency,
    QueryServiceDependency,
    ReadServiceDependency,
)
from smartcoat.api.knowledge_v2_errors import (
    KnowledgeV2APIError,
    api_error_responses,
)
from smartcoat.api.knowledge_v2_schemas import (
    KnowledgeAuditEventResponse,
    KnowledgeAuditHistoryResponse,
    KnowledgeCreateRequest,
    KnowledgeDraftDeleteRequest,
    KnowledgeDraftDeleteResponse,
    KnowledgeLifecycleActionRequest,
    KnowledgeMutationResponse,
    KnowledgeObjectV2PageResponse,
    KnowledgeObjectV2Response,
    KnowledgeUpdateRequest,
    lifecycle_request_to_domain,
)
from smartcoat.domain.base import LifecycleState
from smartcoat.domain.context_references import ContextIdKind, ContextType
from smartcoat.domain.knowledge_objects import KnowledgeObjectType
from smartcoat.domain.knowledge_query import (
    KnowledgeContextIdentityFilter,
    KnowledgeObjectV2Query,
    KnowledgeQueryFilters,
    KnowledgeQuerySort,
)
from smartcoat.services.knowledge_audit_service import (
    KnowledgeAuditMutationResult,
)

router = APIRouter(prefix="/api/v2/knowledge", tags=["knowledge-v2"])
API_ERROR_RESPONSES = api_error_responses()


def _mutation_response(result: KnowledgeAuditMutationResult) -> KnowledgeMutationResponse:
    if result.knowledge is None:
        raise KnowledgeV2APIError("knowledge_mutation_result_invalid")
    return KnowledgeMutationResponse(
        knowledge=KnowledgeObjectV2Response.from_domain(result.knowledge),
        audit_event=(
            KnowledgeAuditEventResponse.from_domain(result.audit_event)
            if result.audit_event is not None
            else None
        ),
    )


@router.post(
    "",
    response_model=KnowledgeMutationResponse,
    status_code=status.HTTP_201_CREATED,
    responses=API_ERROR_RESPONSES,
    operation_id="create_knowledge_object_v2",
)
def create_knowledge_object_v2(
    payload: KnowledgeCreateRequest,
    organization_id: OrganizationDependency,
    correlation_id: CorrelationDependency,
    service: AuditServiceDependency,
) -> KnowledgeMutationResponse:
    result = service.create(
        payload.to_domain(
            organization_id=organization_id,
            correlation_id=correlation_id,
        )
    )
    response = _mutation_response(result)
    if response.audit_event is None:
        raise KnowledgeV2APIError("knowledge_mutation_result_invalid")
    return response


@router.get(
    "",
    response_model=KnowledgeObjectV2PageResponse,
    responses=API_ERROR_RESPONSES,
    operation_id="list_knowledge_objects_v2",
)
def list_knowledge_objects_v2(
    organization_id: OrganizationDependency,
    service: QueryServiceDependency,
    knowledge_type: KnowledgeObjectType | None = None,
    lifecycle_state: LifecycleState | None = None,
    owner_id: Annotated[str | None, Query(max_length=512)] = None,
    tags_all: Annotated[list[str] | None, Query()] = None,
    context_type: ContextType | None = None,
    context_id_kind: ContextIdKind | None = None,
    context_reference_id: Annotated[str | None, Query(max_length=512)] = None,
    context_source_system: Annotated[str | None, Query(max_length=128)] = None,
    context_relationship_role: Annotated[str | None, Query(max_length=128)] = None,
    created_from: datetime | None = None,
    created_before: datetime | None = None,
    updated_from: datetime | None = None,
    updated_before: datetime | None = None,
    sort: KnowledgeQuerySort = KnowledgeQuerySort.UPDATED_AT_DESC,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    cursor: Annotated[str | None, Query(max_length=4096)] = None,
) -> KnowledgeObjectV2PageResponse:
    context_values = (
        context_type,
        context_id_kind,
        context_reference_id,
        context_source_system,
        context_relationship_role,
    )
    if any(item is not None for item in context_values):
        if context_type is None or context_id_kind is None or context_reference_id is None:
            raise KnowledgeV2APIError("context_filter_incomplete")
        context = KnowledgeContextIdentityFilter(
            context_type=context_type,
            id_kind=context_id_kind,
            reference_id=context_reference_id,
            source_system=context_source_system,
            relationship_role=context_relationship_role,
        )
    else:
        context = None

    command = KnowledgeObjectV2Query(
        organization_id=organization_id,
        filters=KnowledgeQueryFilters(
            knowledge_type=knowledge_type,
            lifecycle_state=lifecycle_state,
            owner_id=owner_id,
            tags_all=tuple(tags_all or ()),
            context=context,
            created_from=created_from,
            created_before=created_before,
            updated_from=updated_from,
            updated_before=updated_before,
        ),
        sort=sort,
        page_size=page_size,
        cursor=cursor,
    )
    return KnowledgeObjectV2PageResponse.from_domain(service.query(command))


@router.post(
    "/{object_id}/lifecycle-actions",
    response_model=KnowledgeMutationResponse,
    responses=API_ERROR_RESPONSES,
    operation_id="apply_knowledge_lifecycle_action_v2",
)
def apply_knowledge_lifecycle_action_v2(
    object_id: UUID,
    payload: Annotated[KnowledgeLifecycleActionRequest, Body(discriminator="action")],
    organization_id: OrganizationDependency,
    correlation_id: CorrelationDependency,
    service: AuditServiceDependency,
) -> KnowledgeMutationResponse:
    result = service.transition(
        organization_id=organization_id,
        command=lifecycle_request_to_domain(payload, object_id=object_id),
        correlation_id=correlation_id,
    )
    response = _mutation_response(result)
    if response.audit_event is None:
        raise KnowledgeV2APIError("knowledge_mutation_result_invalid")
    return response


@router.get(
    "/{object_id}/audit-history",
    response_model=KnowledgeAuditHistoryResponse,
    responses=API_ERROR_RESPONSES,
    operation_id="get_knowledge_audit_history_v2",
)
def get_knowledge_audit_history_v2(
    object_id: UUID,
    organization_id: OrganizationDependency,
    service: AuditServiceDependency,
) -> KnowledgeAuditHistoryResponse:
    events = service.history_for_object(
        organization_id=organization_id,
        object_id=object_id,
    )
    if not events:
        raise KnowledgeV2APIError("knowledge_history_not_found")
    return KnowledgeAuditHistoryResponse(
        object_id=object_id,
        events=tuple(KnowledgeAuditEventResponse.from_domain(event) for event in events),
    )


@router.get(
    "/{object_id}",
    response_model=KnowledgeObjectV2Response,
    responses=API_ERROR_RESPONSES,
    operation_id="get_knowledge_object_v2",
)
def get_knowledge_object_v2(
    object_id: UUID,
    organization_id: OrganizationDependency,
    service: ReadServiceDependency,
) -> KnowledgeObjectV2Response:
    knowledge = service.get(
        object_id=object_id,
        organization_id=organization_id,
    )
    if knowledge is None:
        raise KnowledgeV2APIError("knowledge_object_not_found")
    return KnowledgeObjectV2Response.from_domain(knowledge)


@router.put(
    "/{object_id}",
    response_model=KnowledgeMutationResponse,
    responses=API_ERROR_RESPONSES,
    operation_id="replace_knowledge_object_v2",
)
def replace_knowledge_object_v2(
    object_id: UUID,
    payload: KnowledgeUpdateRequest,
    organization_id: OrganizationDependency,
    correlation_id: CorrelationDependency,
    service: AuditServiceDependency,
) -> KnowledgeMutationResponse:
    return _mutation_response(
        service.update(
            payload.to_domain(
                object_id=object_id,
                organization_id=organization_id,
                correlation_id=correlation_id,
            )
        )
    )


@router.delete(
    "/{object_id}",
    response_model=KnowledgeDraftDeleteResponse,
    responses=API_ERROR_RESPONSES,
    operation_id="delete_knowledge_draft_v2",
)
def delete_knowledge_draft_v2(
    object_id: UUID,
    payload: KnowledgeDraftDeleteRequest,
    organization_id: OrganizationDependency,
    correlation_id: CorrelationDependency,
    service: AuditServiceDependency,
) -> KnowledgeDraftDeleteResponse:
    result = service.delete_draft(
        organization_id=organization_id,
        command=payload.to_domain(object_id=object_id),
        correlation_id=correlation_id,
    )
    if result.knowledge is not None or result.audit_event is None:
        raise KnowledgeV2APIError("knowledge_mutation_result_invalid")
    return KnowledgeDraftDeleteResponse(
        deleted_object_id=object_id,
        audit_event=KnowledgeAuditEventResponse.from_domain(result.audit_event),
    )
