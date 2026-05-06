"""Search client abstraction for ResearcherAgent."""

import logging
from typing import Any

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument

logger = logging.getLogger(__name__)


class SearchClient:
    """Provider-agnostic search client with Tavily and mock fallback."""

    def __init__(self):
        settings = get_settings()
        self.tavily_api_key = settings.tavily_api_key
        self.use_tavily = bool(self.tavily_api_key)

        if self.use_tavily:
            try:
                from tavily import TavilyClient

                self.tavily_client = TavilyClient(api_key=self.tavily_api_key)
                logger.info("Using Tavily search client")
            except ImportError:
                logger.warning("Tavily not installed, falling back to mock search")
                self.use_tavily = False
        else:
            logger.info("No Tavily API key, using mock search")

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query."""
        if self.use_tavily:
            return self._search_tavily(query, max_results)
        else:
            return self._search_mock(query, max_results)

    def _search_tavily(self, query: str, max_results: int) -> list[SourceDocument]:
        """Search using Tavily API."""
        try:
            response = self.tavily_client.search(query=query, max_results=max_results)
            results = response.get("results", [])

            sources = []
            for item in results:
                sources.append(
                    SourceDocument(
                        title=item.get("title", "Untitled"),
                        url=item.get("url"),
                        snippet=item.get("content", ""),
                        metadata={"score": item.get("score", 0.0)},
                    )
                )

            logger.info(f"Tavily search returned {len(sources)} results for: {query}")
            return sources

        except Exception as e:
            logger.error(f"Tavily search failed: {e}, falling back to mock")
            return self._search_mock(query, max_results)

    def _search_mock(self, query: str, max_results: int) -> list[SourceDocument]:
        """Mock search with hardcoded relevant results."""
        logger.info(f"Mock search for: {query}")

        # Generate mock results based on query keywords
        mock_data = self._generate_mock_results(query)
        return mock_data[:max_results]

    def _generate_mock_results(self, query: str) -> list[SourceDocument]:
        """Generate contextually relevant mock results."""
        query_lower = query.lower()

        # GraphRAG related
        if "graphrag" in query_lower or "graph rag" in query_lower:
            return [
                SourceDocument(
                    title="GraphRAG: Unlocking LLM discovery on narrative private data",
                    url="https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/",
                    snippet="GraphRAG is a structured, hierarchical approach to Retrieval Augmented Generation (RAG) that uses knowledge graphs to provide substantial improvements in question-answering performance when reasoning about complex information.",
                    metadata={"source": "Microsoft Research", "year": 2024},
                ),
                SourceDocument(
                    title="From Local to Global: A Graph RAG Approach",
                    url="https://arxiv.org/abs/2404.16130",
                    snippet="We present Graph RAG, a novel approach that combines knowledge graphs with retrieval augmented generation to enable better reasoning over private datasets. Our method builds a graph index and uses community detection for hierarchical summarization.",
                    metadata={"source": "arXiv", "year": 2024},
                ),
                SourceDocument(
                    title="GraphRAG Implementation Guide",
                    url="https://github.com/microsoft/graphrag",
                    snippet="GraphRAG is a data pipeline and transformation suite designed to extract meaningful, structured data from unstructured text using LLMs. It creates knowledge graphs that can be used for advanced RAG patterns.",
                    metadata={"source": "GitHub", "year": 2024},
                ),
            ]

        # Multi-agent systems
        elif "multi-agent" in query_lower or "multi agent" in query_lower:
            return [
                SourceDocument(
                    title="Building Effective Agents - Anthropic",
                    url="https://www.anthropic.com/research/building-effective-agents",
                    snippet="When building agents, we recommend starting simple and adding complexity only when needed. Multi-agent systems can be powerful but introduce coordination overhead. Consider workflows, routing, and parallelization patterns.",
                    metadata={"source": "Anthropic", "year": 2024},
                ),
                SourceDocument(
                    title="Multi-Agent Orchestration Patterns",
                    url="https://www.deeplearning.ai/short-courses/multi-ai-agent-systems/",
                    snippet="Multi-agent systems enable specialization and parallel execution. Common patterns include supervisor-worker, sequential chains, and hierarchical teams. Each agent should have clear responsibilities.",
                    metadata={"source": "DeepLearning.AI", "year": 2024},
                ),
                SourceDocument(
                    title="LangGraph Multi-Agent Tutorial",
                    url="https://langchain-ai.github.io/langgraph/tutorials/multi_agent/",
                    snippet="LangGraph provides primitives for building multi-agent systems with state management, conditional routing, and human-in-the-loop patterns. Agents can hand off work and maintain shared context.",
                    metadata={"source": "LangChain", "year": 2024},
                ),
            ]

        # LLM guardrails
        elif "guardrail" in query_lower or "safety" in query_lower:
            return [
                SourceDocument(
                    title="Production LLM Guardrails Best Practices",
                    url="https://www.anthropic.com/research/building-effective-agents",
                    snippet="Essential guardrails include: max iterations to prevent infinite loops, timeouts for long-running operations, retry logic with exponential backoff, input/output validation, and fallback strategies.",
                    metadata={"source": "Anthropic", "year": 2024},
                ),
                SourceDocument(
                    title="NeMo Guardrails Framework",
                    url="https://github.com/NVIDIA/NeMo-Guardrails",
                    snippet="NeMo Guardrails is an open-source toolkit for adding programmable guardrails to LLM applications. It supports input/output rails, dialog rails, and fact-checking mechanisms.",
                    metadata={"source": "NVIDIA", "year": 2024},
                ),
                SourceDocument(
                    title="Guardrails AI: Validating LLM Outputs",
                    url="https://www.guardrailsai.com/",
                    snippet="Guardrails AI provides validators for LLM outputs including PII detection, toxicity filtering, factual consistency checks, and structured output validation. It integrates with major LLM providers.",
                    metadata={"source": "Guardrails AI", "year": 2024},
                ),
            ]

        # Default generic results
        else:
            return [
                SourceDocument(
                    title=f"Research Overview: {query}",
                    url="https://example.com/research",
                    snippet=f"This document provides an overview of {query}. It covers key concepts, recent developments, and practical applications in the field.",
                    metadata={"source": "Mock Database", "relevance": "high"},
                ),
                SourceDocument(
                    title=f"Technical Guide: {query}",
                    url="https://example.com/guide",
                    snippet=f"A comprehensive technical guide covering {query}. Includes implementation details, best practices, and common pitfalls to avoid.",
                    metadata={"source": "Mock Database", "relevance": "medium"},
                ),
                SourceDocument(
                    title=f"Case Studies: {query}",
                    url="https://example.com/cases",
                    snippet=f"Real-world case studies demonstrating successful applications of {query}. Learn from production deployments and lessons learned.",
                    metadata={"source": "Mock Database", "relevance": "medium"},
                ),
            ]
