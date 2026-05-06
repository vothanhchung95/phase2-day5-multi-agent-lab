"""LangGraph workflow implementation."""

import logging
from typing import Literal

from langgraph.graph import END, StateGraph

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import flush_traces, start_trace, trace_span

logger = logging.getLogger(__name__)


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph."""

    def __init__(self):
        self.settings = get_settings()
        self.supervisor = SupervisorAgent()
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()

    def build(self) -> StateGraph:
        """Create a LangGraph graph with supervisor routing."""
        logger.info("Building multi-agent workflow graph")

        # Create graph with ResearchState
        graph = StateGraph(ResearchState)

        # Add nodes
        graph.add_node("supervisor", self._supervisor_node)
        graph.add_node("researcher", self._researcher_node)
        graph.add_node("analyst", self._analyst_node)
        graph.add_node("writer", self._writer_node)

        # Set entry point
        graph.set_entry_point("supervisor")

        # Add conditional edges from supervisor
        graph.add_conditional_edges(
            "supervisor",
            self._route_decision,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "done": END,
            },
        )

        # All workers return to supervisor for next decision
        graph.add_edge("researcher", "supervisor")
        graph.add_edge("analyst", "supervisor")
        graph.add_edge("writer", "supervisor")

        return graph.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        logger.info(f"Starting multi-agent workflow for query: {state.request.query}")

        start_trace(
            name="multi-agent-research-workflow",
            user_id="lab-user",
            metadata={"query": state.request.query, "audience": state.request.audience},
        )
        try:
            with trace_span("workflow.run", {"query": state.request.query}) as span:
                graph = self.build()

                # Convert state to dict for LangGraph
                state_dict = state.model_dump()

                # Run the graph
                result = graph.invoke(state_dict)

                # Convert result back to ResearchState
                final_state = ResearchState(**result)
                span["output"] = {
                    "iterations": final_state.iteration,
                    "route_history": final_state.route_history,
                    "sources": len(final_state.sources),
                    "errors": final_state.errors,
                }

                logger.info(
                    f"Workflow completed: iterations={final_state.iteration}, "
                    f"routes={final_state.route_history}"
                )

                return final_state

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            state.errors.append(f"Workflow failed: {str(e)}")
            raise
        finally:
            flush_traces()

    def _supervisor_node(self, state: ResearchState) -> ResearchState:
        """Supervisor node wrapper."""
        logger.info("Executing supervisor node")
        with trace_span("agent.supervisor", {"iteration": state.iteration}) as span:
            result = self.supervisor.run(state)
            span["output"] = {"route": result.route_history[-1] if result.route_history else None}
            return result

    def _researcher_node(self, state: ResearchState) -> ResearchState:
        """Researcher node wrapper."""
        logger.info("Executing researcher node")
        with trace_span("agent.researcher", {"query": state.request.query}) as span:
            result = self.researcher.run(state)
            span["output"] = {"sources": len(result.sources), "has_notes": result.research_notes is not None}
            return result

    def _analyst_node(self, state: ResearchState) -> ResearchState:
        """Analyst node wrapper."""
        logger.info("Executing analyst node")
        with trace_span("agent.analyst", {"sources": len(state.sources)}) as span:
            result = self.analyst.run(state)
            span["output"] = {"has_analysis": result.analysis_notes is not None}
            return result

    def _writer_node(self, state: ResearchState) -> ResearchState:
        """Writer node wrapper."""
        logger.info("Executing writer node")
        with trace_span("agent.writer", {"has_analysis": state.analysis_notes is not None}) as span:
            result = self.writer.run(state)
            span["output"] = {"answer_words": len(result.final_answer.split()) if result.final_answer else 0}
            return result

    def _route_decision(
        self, state: ResearchState
    ) -> Literal["researcher", "analyst", "writer", "done"]:
        """Determine next route based on supervisor's decision."""
        if not state.route_history:
            logger.warning("No route history, defaulting to done")
            return "done"

        last_route = state.route_history[-1]
        logger.info(f"Routing to: {last_route}")

        if last_route in ["researcher", "analyst", "writer", "done"]:
            return last_route  # type: ignore

        logger.warning(f"Unknown route '{last_route}', defaulting to done")
        return "done"
