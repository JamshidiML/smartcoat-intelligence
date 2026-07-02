from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from smartcoat.domain.base import EnterpriseBaseObject


class DecisionType(StrEnum):
    ENGINEERING = "engineering"
    PRODUCTION = "production"
    QUALITY = "quality"
    SUPPLIER = "supplier"
    PROCUREMENT = "procurement"
    FINANCIAL = "financial"
    CUSTOMER = "customer"
    REGULATORY = "regulatory"
    STRATEGIC = "strategic"
    RND = "rnd"


class DecisionStatus(StrEnum):
    DRAFT = "draft"
    RECOMMENDED = "recommended"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    COMPLETED = "completed"


class DecisionObject(EnterpriseBaseObject):
    """Canonical representation of an enterprise decision."""

    decision_type: DecisionType
    status: DecisionStatus = DecisionStatus.DRAFT
    problem: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)
    alternatives: list[dict[str, Any]] = Field(default_factory=list)
    recommendation: str | None = None
    rationale: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    outcome: str | None = None
    learning: str | None = None
    related_knowledge: list[UUID] = Field(default_factory=list)
