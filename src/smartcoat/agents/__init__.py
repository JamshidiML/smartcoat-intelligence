"""SmartCoat agent skeletons."""

from smartcoat.agents.base import AgentResponse, BaseAgent
from smartcoat.agents.lab_agent import LabAgent
from smartcoat.agents.memory_agent import MemoryAgent

__all__ = ["AgentResponse", "BaseAgent", "MemoryAgent", "LabAgent"]
