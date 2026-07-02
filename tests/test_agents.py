from smartcoat.agents.lab_agent import LabAgent
from smartcoat.agents.memory_agent import MemoryAgent


def test_memory_agent_runs() -> None:
    agent = MemoryAgent()
    response = agent.run("The coating failed after curing.")

    assert response.summary
    assert response.knowledge_candidates


def test_lab_agent_runs() -> None:
    agent = LabAgent()
    response = agent.run("Sample A had better flexibility than Sample B.")

    assert response.summary
    assert response.follow_up_questions
