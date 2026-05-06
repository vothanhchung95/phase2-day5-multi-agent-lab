"""Writer agent implementation."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self):
        self.llm_client = LLMClient(temperature=0.4)

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        logger.info("Writer agent starting")

        try:
            if not state.research_notes:
                raise AgentExecutionError("No research notes available for writing")

            # Generate final answer
            state.final_answer = self._write_final_answer(state)

            # Record result
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.WRITER,
                    content=state.final_answer,
                    metadata={
                        "word_count": len(state.final_answer.split()),
                        "sources_cited": len(state.sources),
                    },
                )
            )

            state.add_trace_event(
                "writer_complete",
                {"answer_length": len(state.final_answer)},
            )

            logger.info("Writer agent completed successfully")
            return state

        except Exception as e:
            logger.error(f"Writer agent failed: {e}")
            state.errors.append(f"Writer failed: {str(e)}")
            raise AgentExecutionError(f"Writer agent failed: {e}") from e

    def _write_final_answer(self, state: ResearchState) -> str:
        """Synthesize a clear response with citations."""

        # Build context from all available information
        context_parts = [f"Research Notes:\n{state.research_notes}"]

        if state.analysis_notes:
            context_parts.append(f"\nAnalysis:\n{state.analysis_notes}")

        if state.sources:
            sources_list = "\n".join(
                [
                    f"[{i+1}] {source.title} - {source.url or 'N/A'}"
                    for i, source in enumerate(state.sources)
                ]
            )
            context_parts.append(f"\nSources:\n{sources_list}")

        context = "\n".join(context_parts)

        system_prompt = f"""You are a skilled technical writer. Create a comprehensive, well-structured
answer to the user's query based on the research and analysis provided.

Requirements:
- Write for audience: {state.request.audience}
- Use clear, engaging language
- Include proper citations using [Source N] format
- Organize with clear sections/paragraphs
- Be accurate and balanced
- Aim for 400-600 words unless otherwise specified

Do not add information not supported by the sources."""

        user_prompt = f"""Query: {state.request.query}

{context}

Write a comprehensive answer:"""

        try:
            response = self.llm_client.complete(system_prompt, user_prompt)
            answer = response.content.strip()

            # Add sources section at the end
            if state.sources:
                answer += "\n\n## Sources\n\n"
                for i, source in enumerate(state.sources):
                    answer += f"[{i+1}] {source.title}"
                    if source.url:
                        answer += f" - {source.url}"
                    answer += "\n"

            return answer

        except Exception as e:
            logger.error(f"Failed to generate final answer: {e}")
            raise
