from multi_agent_research_lab.agents import SupervisorAgent
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_routes_to_researcher_initially() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    result = SupervisorAgent().run(state)

    assert result.route_history[-1] == "researcher"
    assert result.iteration == 1


def test_supervisor_routes_to_done_when_final_answer_exists() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain multi-agent systems"),
        sources=[],
        research_notes="notes",
        analysis_notes="analysis",
        final_answer="final answer",
    )
    result = SupervisorAgent().run(state)

    assert result.route_history[-1] == "done"
