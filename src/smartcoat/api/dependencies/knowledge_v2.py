"""Dependency composition for the versioned Knowledge Object API."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Request
from pydantic import SecretStr
from sqlalchemy.orm import Session

from smartcoat.api.knowledge_v2_errors import (
    KnowledgeV2APIError,
    correlation_uuid,
)
from smartcoat.core.config import Settings, get_settings
from smartcoat.domain.knowledge_objects_v2 import MAX_IDENTIFIER_LENGTH
from smartcoat.services.knowledge_audit_service import KnowledgeAuditService
from smartcoat.services.knowledge_query_service import KnowledgeObjectV2QueryService
from smartcoat.services.knowledge_v2_read_service import KnowledgeObjectV2ReadService
from smartcoat.storage.database.session import SessionLocal

type SessionFactory = Callable[[], Session]


def get_knowledge_v2_session_factory() -> SessionFactory:
    return SessionLocal


SessionFactoryDependency = Annotated[
    SessionFactory,
    Depends(get_knowledge_v2_session_factory),
]


def get_knowledge_audit_service(
    session_factory: SessionFactoryDependency,
) -> KnowledgeAuditService:
    return KnowledgeAuditService(session_factory)


def get_knowledge_v2_read_service(
    session_factory: SessionFactoryDependency,
) -> KnowledgeObjectV2ReadService:
    return KnowledgeObjectV2ReadService(session_factory)


def _cursor_key_bytes(value: SecretStr | None) -> bytes:
    if value is None:
        raise KnowledgeV2APIError("knowledge_cursor_signing_key_unavailable")
    encoded = value.get_secret_value().encode("utf-8")
    if len(encoded) < 32:
        raise KnowledgeV2APIError("knowledge_cursor_signing_key_unavailable")
    return encoded


def get_knowledge_query_service(
    session_factory: SessionFactoryDependency,
    settings: Annotated[Settings, Depends(get_settings)],
) -> KnowledgeObjectV2QueryService:
    return KnowledgeObjectV2QueryService(
        session_factory,
        cursor_signing_key=_cursor_key_bytes(settings.knowledge_cursor_signing_key),
    )


def get_organization_id(
    organization_id: Annotated[
        str,
        Header(
            alias="X-SmartCoat-Organization-ID",
            min_length=1,
            max_length=MAX_IDENTIFIER_LENGTH,
            description=(
                "Declared application-boundary metadata; not authentication, IAM, "
                "tenant isolation, or legal authorization."
            ),
        ),
    ],
    correlation_id: Annotated[
        str | None,
        Header(
            alias="X-Correlation-ID",
            description=(
                "Optional caller-supplied UUID preserved across the response and "
                "canonical audit event."
            ),
        ),
    ] = None,
) -> str:
    del correlation_id
    normalized = organization_id.strip()
    if not normalized:
        raise KnowledgeV2APIError("organization_id_invalid")
    return normalized


def get_correlation_id(request: Request) -> UUID:
    return correlation_uuid(request)


OrganizationDependency = Annotated[str, Depends(get_organization_id)]
CorrelationDependency = Annotated[UUID, Depends(get_correlation_id)]
AuditServiceDependency = Annotated[
    KnowledgeAuditService,
    Depends(get_knowledge_audit_service),
]
ReadServiceDependency = Annotated[
    KnowledgeObjectV2ReadService,
    Depends(get_knowledge_v2_read_service),
]
QueryServiceDependency = Annotated[
    KnowledgeObjectV2QueryService,
    Depends(get_knowledge_query_service),
]
