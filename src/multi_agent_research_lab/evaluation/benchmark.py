"""Benchmark implementation for single-agent vs multi-agent."""

import logging
from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

logger = logging.getLogger(__name__)

Runner = Callable[[str], ResearchState]


def run_benchmark(run_name: str, query: str, runner: Runner) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, cost, and quality metrics."""
    logger.info(f"Running benchmark: {run_name} for query: {query}")

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started

    # Calculate total cost from agent results
    total_cost = 0.0
    total_input_tokens = 0
    total_output_tokens = 0

    for result in state.agent_results:
        if "cost_usd" in result.metadata:
            total_cost += result.metadata["cost_usd"]
        if "input_tokens" in result.metadata:
            total_input_tokens += result.metadata["input_tokens"]
        if "output_tokens" in result.metadata:
            total_output_tokens += result.metadata["output_tokens"]

    # Simple quality scoring based on heuristics
    quality_score = calculate_quality_score(state)

    # Build notes
    notes_parts = []
    if state.errors:
        notes_parts.append(f"{len(state.errors)} errors")
    if hasattr(state, "iteration"):
        notes_parts.append(f"{state.iteration} iterations")
    notes = ", ".join(notes_parts) if notes_parts else "completed successfully"

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=total_cost if total_cost > 0 else None,
        quality_score=quality_score,
        notes=notes,
    )

    logger.info(
        f"Benchmark complete: latency={latency:.2f}s, "
        f"cost=${total_cost:.4f}, quality={quality_score:.1f}"
    )

    return state, metrics


def calculate_quality_score(state: ResearchState) -> float:
    """Calculate quality score based on heuristics (0-10 scale)."""
    score = 5.0  # Start with baseline

    # Has final answer
    if state.final_answer:
        score += 2.0

        # Length check (400-800 words is good)
        word_count = len(state.final_answer.split())
        if 400 <= word_count <= 800:
            score += 1.0
        elif word_count < 200:
            score -= 1.0

        # Has citations
        if "[Source" in state.final_answer or "[1]" in state.final_answer:
            score += 1.0

    # Has sources
    if state.sources:
        score += min(len(state.sources) * 0.3, 1.5)

    # Has research notes
    if state.research_notes:
        score += 0.5

    # Has analysis notes
    if state.analysis_notes:
        score += 0.5

    # Penalize errors
    if state.errors:
        score -= len(state.errors) * 0.5

    # Clamp to 0-10
    return max(0.0, min(10.0, score))
