from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from smartcoat.domain.base import EnterpriseBaseObject
from smartcoat.domain.context_references import ContextReference, validate_context_references


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
    """Canonical unit of reusable enterprise knowledge.

    ``context_references`` is the canonical typed context channel. The retained
    ``related_entities`` UUID list is an opaque Release 1.7 compatibility field;
    it is never reinterpreted, merged with, or promoted over canonical context.
    Persistence and API round-trip support for non-empty canonical context is a
    coordinated T02/T05/T09 responsibility.
    """

    knowledge_type: KnowledgeObjectType
    evidence: list[str] = Field(default_factory=list)
    context_references: list[ContextReference] = Field(
        default_factory=list,
        description=(
            "Canonical ADR-0024 context. Current persistence/API adapters require "
            "separate T02/T05/T09 integration before non-empty production use."
        ),
    )
    related_entities: list[UUID] = Field(
        default_factory=list,
        description=(
            "Opaque legacy UUID links retained without inferred type, label, or merge behavior."
        ),
    )
    related_decisions: list[UUID] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    content: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_typed_context(self) -> "KnowledgeObject":
        validate_context_references(self.context_references)
        return self
