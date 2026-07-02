from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from smartcoat.domain.base import EnterpriseBaseObject


class KnowledgeObjectType(StrEnum):
    OBSERVATION = "observation"
    EVIDENCE = "evidence"
    HYPOTHESIS = "hypothesis"
    FINDING = "finding"
    LESSON_LEARNED = "lesson_learned"
    RULE = "rule"
    CONSTRAINT = "constraint"
    ASSUMPTION = "assumption"
    TRADE_OFF = "trade_off"
    FAILURE_MODE = "failure_mode"
    ROOT_CAUSE = "root_cause"
    RECOMMENDATION = "recommendation"
    INSIGHT = "insight"
    DECISION_RATIONALE = "decision_rationale"


class KnowledgeObject(EnterpriseBaseObject):
    """Canonical unit of reusable enterprise knowledge."""

    knowledge_type: KnowledgeObjectType
    evidence: list[str] = Field(default_factory=list)
    related_entities: list[UUID] = Field(default_factory=list)
    related_decisions: list[UUID] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    content: dict[str, Any] = Field(default_factory=dict)
