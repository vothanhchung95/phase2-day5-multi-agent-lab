"""Researcher agent implementation."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient

logger = logging.getLogger(__name__)


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self):
        self.llm_client = LLMClient(temperature=0.2)
        self.search_client = SearchClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        logger.info(f"Researcher agent starting for query: {state.request.query}")

        try:
            # Step 1: Generate search queries
            search_queries = self._generate_search_queries(state.request.query)
            logger.info(f"Generated {len(search_queries)} search queries")

            # Step 2: Search for sources
            all_sources = []
            for query in search_queries:
                sources = self.search_client.search(query, max_results=3)
                all_sources.extend(sources)

            # Deduplicate by URL
            seen_urls = set()
            unique_sources = []
            for source in all_sources:
                if source.url and source.url not in seen_urls:
                    seen_urls.add(source.url)
                    unique_sources.append(source)
                elif not source.url:
                    unique_sources.append(source)

            # Limit to max_sources
            state.sources = unique_sources[: state.request.max_sources]
            logger.info(f"Collected {len(state.sources)} unique sources")

            # Step 3: Synthesize research notes
            state.research_notes = self._synthesize_research_notes(state)

            # Record result
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.RESEARCHER,
                    content=state.research_notes,
                    metadata={
                        "sources_count": len(state.sources),
                        "search_queries": search_queries,
                    },
                )
            )

            state.add_trace_event(
                "researcher_complete",
                {
                    "sources_collected": len(state.sources),
                    "notes_length": len(state.research_notes),
                },
            )

            logger.info("Researcher agent completed successfully")
            return state

        except Exception as e:
            logger.error(f"Researcher agent failed: {e}")
            state.errors.append(f"Researcher failed: {str(e)}")
            raise AgentExecutionError(f"Researcher agent failed: {e}") from e

    def _generate_search_queries(self, original_query: str) -> list[str]:
        """Generate 2-3 focused search queries from the original query."""
        system_prompt = """You are a research assistant. Generate 2-3 focused search queries
that will help answer the user's question. Each query should target a specific aspect.

Return only the queries, one per line, without numbering or explanation."""

        user_prompt = f"Original question: {original_query}\n\nGenerate 2-3 search queries:"

        try:
            response = self.llm_client.complete(system_prompt, user_prompt)
            queries = [q.strip() for q in response.content.strip().split("\n") if q.strip()]
            return queries[:3] if queries else [original_query]
        except Exception as e:
            logger.warning(f"Failed to generate search queries: {e}, using original query")
            return [original_query]

    def _synthesize_research_notes(self, state: ResearchState) -> str:
        """Synthesize research notes from collected sources."""
        if not state.sources:
            return "No sources found for this query."

        # Prepare sources summary
        sources_text = "\n\n".join(
            [
                f"Source {i+1}: {source.title}\n"
                f"URL: {source.url or 'N/A'}\n"
                f"Content: {source.snippet}"
                for i, source in enumerate(state.sources)
            ]
        )

        system_prompt = """You are a research assistant. Synthesize the provided sources into
concise research notes. Focus on key facts, findings, and insights relevant to the query.

Include inline citations like [Source 1], [Source 2], etc.
Be factual and objective. Highlight any conflicting information."""

        user_prompt = f"""Query: {state.request.query}

Sources:
{sources_text}

Synthesize these sources into research notes (300-500 words):"""

        try:
            response = self.llm_client.complete(system_prompt, user_prompt)
            return response.content.strip()
        except Exception as e:
            logger.error(f"Failed to synthesize research notes: {e}")
            # Fallback: just concatenate source snippets
            return "Research notes (raw sources):\n\n" + sources_text
