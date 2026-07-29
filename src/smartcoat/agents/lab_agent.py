from typing import Any

from smartcoat.agents.base import AgentResponse, BaseAgent


class LabAgent(BaseAgent):
    """Agent skeleton for R&D and laboratory knowledge capture."""

    def __init__(self) -> None:
        super().__init__(
            name="Lab Agent",
            purpose=(
                "Capture laboratory experiments, hypotheses, results, failures, "
                "and lessons learned."
            ),
        )

    def run(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResponse:
        return AgentResponse(
            summary="Captured lab input for structured review.",
            knowledge_candidates=[
                {
                    "type": "finding",
                    "title": "Lab knowledge candidate",
                    "description": user_input,
                    "context": context or {},
                }
            ],
            follow_up_questions=[
                "Which project does this belong to?",
                "Which formulation or material was involved?",
                "What was the expected result?",
                "What was the actual result?",
                "What lesson should be preserved?",
            ],
            confidence=0.5,
        )
