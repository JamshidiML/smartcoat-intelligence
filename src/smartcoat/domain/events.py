from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from smartcoat.domain.base import EnterpriseBaseObject


class EventType(StrEnum):
    KNOWLEDGE_CREATED = "knowledge_created"
    DECISION_CREATED = "decision_created"
    DECISION_EXECUTED = "decision_executed"
    OUTCOME_OBSERVED = "outcome_observed"
    LESSON_LEARNED_CREATED = "lesson_learned_created"
    AGENT_INTERACTION = "agent_interaction"
    SYSTEM_EVENT = "system_event"


class EnterpriseEvent(EnterpriseBaseObject):
    """Recorded meaningful change in enterprise reality."""

    event_type: EventType
    actor: str | None = None
    related_object_id: UUID | None = None
    previous_state: dict[str, Any] | None = None
    new_state: dict[str, Any] | None = None
    evidence: list[str] = Field(default_factory=list)
    impact: str | None = None
