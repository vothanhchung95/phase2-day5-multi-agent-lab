#!/usr/bin/env python3
"""Run benchmark comparing single-agent and multi-agent workflows."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from multi_agent_research_lab.core.schemas import AgentName, AgentResult, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.observability.tracing import flush_traces, start_trace, trace_span
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


QUERIES = [
    "Research GraphRAG state-of-the-art and write a 500-word summary",
    "Compare single-agent and multi-agent workflows for customer support",
    "Summarize production guardrails for LLM agents",
]


def run_baseline(query: str) -> ResearchState:
    """Run a single-agent baseline using one LLM call."""
    start_trace("single-agent-baseline", user_id="lab-user", metadata={"query": query})
    try:
        with trace_span("baseline.llm", {"query": query}) as span:
            state = ResearchState(request=ResearchQuery(query=query))
            llm_client = LLMClient(temperature=0.3)
            response = llm_client.complete(
                """You are a single-agent research assistant. Answer the query directly.
Be clear, factual, structured, and around 400-600 words. If you cannot verify a
fact with live sources, state the limitation.""",
                f"Query: {query}\n\nWrite the answer:",
            )
            state.final_answer = response.content
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.WRITER,
                    content=response.content,
                    metadata={
                        "input_tokens": response.input_tokens or 0,
                        "output_tokens": response.output_tokens or 0,
                        "cost_usd": response.cost_usd or 0.0,
                    },
                )
            )
            span["output"] = {
                "answer_words": len(response.content.split()),
                "cost_usd": response.cost_usd,
            }
            return state
    finally:
        flush_traces()


def run_multi_agent(query: str) -> ResearchState:
    """Run the implemented multi-agent workflow."""
    workflow = MultiAgentWorkflow()
    return workflow.run(ResearchState(request=ResearchQuery(query=query)))


def main() -> None:
    """Run all benchmark queries and write reports/benchmark_report.md."""
    configure_logging("INFO")
    all_metrics = []

    for index, query in enumerate(QUERIES, start=1):
        logger.info("Benchmark query %s/%s: %s", index, len(QUERIES), query)
        for run_name, runner in (
            (f"baseline-q{index}", run_baseline),
            (f"multi-agent-q{index}", run_multi_agent),
        ):
            try:
                _, metrics = run_benchmark(run_name, query, runner)
                all_metrics.append(metrics)
            except Exception as exc:
                logger.exception("%s failed: %s", run_name, exc)

    report = render_markdown_report(all_metrics)
    report_path = ROOT / "reports" / "benchmark_report.md"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nSaved benchmark report to {report_path}")


if __name__ == "__main__":
    main()
