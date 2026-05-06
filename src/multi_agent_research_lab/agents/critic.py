"""Optional critic agent for lightweight answer validation."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Fact-checking and citation-review agent used as an optional quality gate."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append lightweight review findings."""
        findings: list[str] = []

        if not state.final_answer:
            findings.append("No final answer available for review.")
        else:
            word_count = len(state.final_answer.split())
            if word_count < 150:
                findings.append("Final answer may be too short for a research response.")
            else:
                findings.append("Final answer length is acceptable.")

            has_citations = "[Source" in state.final_answer or "[1]" in state.final_answer
            if state.sources and not has_citations:
                findings.append("Citation coverage may be weak: no source markers found.")
            elif state.sources:
                findings.append("Citation markers are present.")
            else:
                findings.append("No sources were available to verify citation coverage.")

        review = "\n".join(findings)
        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content=review,
                metadata={"checked_sources": len(state.sources)},
            )
        )
        state.add_trace_event("critic_complete", {"findings": findings})
        return state
