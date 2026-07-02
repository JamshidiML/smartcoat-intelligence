from typing import Any

from smartcoat.agents.base import AgentResponse, BaseAgent


class MemoryAgent(BaseAgent):
    """Agent skeleton for enterprise knowledge capture."""

    def __init__(self) -> None:
        super().__init__(
            name="Memory Agent",
            purpose="Capture enterprise experience and transform it into reusable knowledge.",
        )

    def run(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResponse:
        return AgentResponse(
            summary="Captured initial memory input for review.",
            knowledge_candidates=[
                {
                    "type": "observation",
                    "title": "Captured memory input",
                    "description": user_input,
                    "context": context or {},
                }
            ],
            follow_up_questions=[
                "What happened?",
                "Why did it happen?",
                "What evidence supports this?",
                "What should be remembered for the future?",
            ],
            confidence=0.5,
        )
