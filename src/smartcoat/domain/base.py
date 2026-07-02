from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class LifecycleState(StrEnum):
    DRAFT = "draft"
    CAPTURED = "captured"
    REVIEWED = "reviewed"
    VALIDATED = "validated"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


class Provenance(BaseModel):
    """Provenance explains where an enterprise object came from."""

    source_system: str | None = None
    source_reference: str | None = None
    created_by: str | None = None
    method: str | None = None


class EnterpriseBaseObject(BaseModel):
    """Base object for canonical SmartCoat enterprise objects."""

    object_id: UUID = Field(default_factory=uuid4)
    title: str
    description: str | None = None
    domain: str | None = None
    owner: str | None = None
    lifecycle_state: LifecycleState = LifecycleState.DRAFT
    provenance: Provenance = Field(default_factory=Provenance)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
