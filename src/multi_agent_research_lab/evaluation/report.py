"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown with rich analysis."""

    lines = [
        "# Benchmark Report: Single-Agent vs Multi-Agent",
        "",
        "## Executive Summary",
        "",
        "This report compares the performance of single-agent baseline vs multi-agent workflow",
        "for research tasks. Metrics include latency, cost, and quality scores.",
        "",
        "## Results",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality | Notes |",
        "|---|---:|---:|---:|---|",
    ]

    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"${item.estimated_cost_usd:.4f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}/10"
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f} | {cost} | {quality} | {item.notes} |"
        )

    # Add analysis section
    lines.extend(
        [
            "",
            "## Analysis",
            "",
        ]
    )

    if len(metrics) >= 2:
        # Compare first two runs (typically baseline vs multi-agent)
        baseline = metrics[0]
        multi = metrics[1]

        lines.append("### Latency Comparison")
        lines.append("")
        latency_diff = multi.latency_seconds - baseline.latency_seconds
        latency_pct = (latency_diff / baseline.latency_seconds) * 100
        lines.append(
            f"- Baseline: {baseline.latency_seconds:.2f}s"
        )
        lines.append(f"- Multi-agent: {multi.latency_seconds:.2f}s")
        lines.append(
            f"- Difference: {latency_diff:+.2f}s ({latency_pct:+.1f}%)"
        )
        lines.append("")

        if baseline.estimated_cost_usd and multi.estimated_cost_usd:
            lines.append("### Cost Comparison")
            lines.append("")
            cost_diff = multi.estimated_cost_usd - baseline.estimated_cost_usd
            cost_pct = (cost_diff / baseline.estimated_cost_usd) * 100
            lines.append(f"- Baseline: ${baseline.estimated_cost_usd:.4f}")
            lines.append(f"- Multi-agent: ${multi.estimated_cost_usd:.4f}")
            lines.append(f"- Difference: ${cost_diff:+.4f} ({cost_pct:+.1f}%)")
            lines.append("")

        if baseline.quality_score and multi.quality_score:
            lines.append("### Quality Comparison")
            lines.append("")
            quality_diff = multi.quality_score - baseline.quality_score
            lines.append(f"- Baseline: {baseline.quality_score:.1f}/10")
            lines.append(f"- Multi-agent: {multi.quality_score:.1f}/10")
            lines.append(f"- Difference: {quality_diff:+.1f}")
            lines.append("")

    lines.extend(
        [
            "## Observations",
            "",
            "### Multi-Agent Advantages",
            "- Specialized agents can focus on specific tasks",
            "- Better source collection through dedicated researcher",
            "- Structured analysis phase improves insight quality",
            "- Clear separation of concerns aids debugging",
            "",
            "### Multi-Agent Tradeoffs",
            "- Higher latency due to multiple LLM calls",
            "- Increased cost from additional API calls",
            "- More complex orchestration and error handling",
            "- Requires careful state management",
            "",
            "## Recommendations",
            "",
            "**Use Multi-Agent when:**",
            "- Task requires deep research and analysis",
            "- Quality is more important than speed",
            "- Need clear audit trail of reasoning",
            "- Task can be decomposed into distinct phases",
            "",
            "**Use Single-Agent when:**",
            "- Simple queries with straightforward answers",
            "- Low latency is critical",
            "- Cost optimization is priority",
            "- Task doesn't benefit from specialization",
            "",
        ]
    )

    return "\n".join(lines) + "\n"
