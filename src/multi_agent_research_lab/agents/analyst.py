"""Analyst agent implementation."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self):
        self.llm_client = LLMClient(temperature=0.1)

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        logger.info("Analyst agent starting")

        try:
            if not state.research_notes:
                raise AgentExecutionError("No research notes available for analysis")

            # Perform analysis
            state.analysis_notes = self._analyze_research(state)

            # Record result
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.ANALYST,
                    content=state.analysis_notes,
                    metadata={"sources_analyzed": len(state.sources)},
                )
            )

            state.add_trace_event(
                "analyst_complete",
                {"analysis_length": len(state.analysis_notes)},
            )

            logger.info("Analyst agent completed successfully")
            return state

        except Exception as e:
            logger.error(f"Analyst agent failed: {e}")
            state.errors.append(f"Analyst failed: {str(e)}")
            raise AgentExecutionError(f"Analyst agent failed: {e}") from e

    def _analyze_research(self, state: ResearchState) -> str:
        """Extract key claims, compare viewpoints, and identify gaps."""

        system_prompt = """You are an analytical research assistant. Your job is to:

1. Extract key claims and findings from the research notes
2. Compare different viewpoints or approaches mentioned
3. Identify patterns, trends, or themes
4. Flag any gaps, contradictions, or areas needing more evidence
5. Provide structured insights that will help a writer create a comprehensive answer

Be critical but fair. Focus on substance over style."""

        user_prompt = f"""Query: {state.request.query}

Research Notes:
{state.research_notes}

Number of sources: {len(state.sources)}

Provide a structured analysis (200-400 words):"""

        try:
            response = self.llm_client.complete(system_prompt, user_prompt)
            return response.content.strip()
        except Exception as e:
            logger.error(f"Failed to generate analysis: {e}")
            raise
