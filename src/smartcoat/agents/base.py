from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    """Standard response from a SmartCoat agent."""

    summary: str
    knowledge_candidates: list[dict[str, Any]] = Field(default_factory=list)
    decision_candidates: list[dict[str, Any]] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class BaseAgent(ABC):
    """Base class for governed SmartCoat agents."""

    name: str
    purpose: str

    def __init__(self, name: str, purpose: str) -> None:
        self.name = name
        self.purpose = purpose

    @abstractmethod
    def run(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResponse:
        """Run the agent on user input."""
