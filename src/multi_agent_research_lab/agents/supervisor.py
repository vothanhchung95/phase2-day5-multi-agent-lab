"""Supervisor / router implementation."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import AgentName
from multi_agent_research_lab.core.state import ResearchState

logger = logging.getLogger(__name__)


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self):
        self.settings = get_settings()

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route.

        Routing policy:
        1. Check max iterations
        2. Analyze state completeness
        3. Route to appropriate agent or done
        """
        logger.info(f"Supervisor evaluating state (iteration {state.iteration})")

        # Guardrail: max iterations
        if state.iteration >= self.settings.max_iterations:
            logger.warning(f"Max iterations ({self.settings.max_iterations}) reached")
            state.record_route("done")
            state.errors.append(f"Max iterations ({self.settings.max_iterations}) reached")
            # If we have no final answer, create a fallback
            if not state.final_answer:
                state.final_answer = self._create_fallback_answer(state)
            return state

        # Determine next route based on state
        next_route = self._determine_next_route(state)
        logger.info(f"Supervisor routing to: {next_route}")

        state.record_route(next_route)
        state.add_trace_event(
            "supervisor_decision",
            {
                "iteration": state.iteration,
                "route": next_route,
                "has_sources": len(state.sources) > 0,
                "has_research_notes": state.research_notes is not None,
                "has_analysis_notes": state.analysis_notes is not None,
                "has_final_answer": state.final_answer is not None,
            },
        )

        return state

    def _determine_next_route(self, state: ResearchState) -> str:
        """Determine next agent to call based on state completeness."""

        # If no final answer yet, check what's missing
        if not state.final_answer:
            # Need research first
            if not state.sources or not state.research_notes:
                return AgentName.RESEARCHER

            # Have research, need analysis
            if not state.analysis_notes:
                return AgentName.ANALYST

            # Have research and analysis, need final answer
            return AgentName.WRITER

        # Have final answer, we're done
        return "done"

    def _create_fallback_answer(self, state: ResearchState) -> str:
        """Create a fallback answer when max iterations reached."""
        logger.warning("Creating fallback answer due to max iterations")

        # Try to synthesize from whatever we have
        parts = []

        if state.research_notes:
            parts.append(f"Research findings:\n{state.research_notes}")

        if state.analysis_notes:
            parts.append(f"\nAnalysis:\n{state.analysis_notes}")

        if state.sources:
            parts.append(f"\nSources consulted: {len(state.sources)}")

        if parts:
            return (
                "Note: This response was generated with incomplete processing due to iteration limits.\n\n"
                + "\n".join(parts)
            )
        else:
            return (
                f"Unable to complete research for query: {state.request.query}. "
                "The system reached maximum iterations before gathering sufficient information."
            )
