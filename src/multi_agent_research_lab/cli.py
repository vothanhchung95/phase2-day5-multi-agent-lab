"""Command-line entrypoint for the lab starter."""

import logging
from time import perf_counter
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import BenchmarkMetrics, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()
logger = logging.getLogger(__name__)


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a single-agent baseline implementation."""

    _init()
    logger.info(f"Running baseline for query: {query}")

    request = ResearchQuery(query=query)
    state = ResearchState(request=request)

    started = perf_counter()

    try:
        # Single-agent approach: one LLM call does everything
        llm_client = LLMClient(temperature=0.3)

        system_prompt = """You are a research assistant. Answer the user's query comprehensively.

Your response should:
1. Be well-researched and factual
2. Be structured with clear sections
3. Be 400-600 words
4. Acknowledge limitations if you lack specific information

Note: You are working without real-time search, so use your training knowledge."""

        user_prompt = f"Query: {query}\n\nProvide a comprehensive answer:"

        response = llm_client.complete(system_prompt, user_prompt)
        state.final_answer = response.content

        # Record metrics
        latency = perf_counter() - started
        metrics = BenchmarkMetrics(
            run_name="baseline",
            latency_seconds=latency,
            estimated_cost_usd=response.cost_usd,
            notes="Single-agent baseline without search",
        )

        # Display results
        console.print(Panel.fit(state.final_answer, title="Single-Agent Baseline"))
        console.print(f"\n[bold]Metrics:[/bold]")
        console.print(f"  Latency: {metrics.latency_seconds:.2f}s")
        console.print(f"  Cost: ${metrics.estimated_cost_usd:.4f}" if metrics.estimated_cost_usd else "  Cost: N/A")
        console.print(f"  Tokens: {response.input_tokens}/{response.output_tokens}")

    except Exception as e:
        logger.error(f"Baseline failed: {e}")
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow."""

    _init()
    logger.info(f"Running multi-agent workflow for query: {query}")

    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()

    started = perf_counter()

    try:
        result = workflow.run(state)
        latency = perf_counter() - started

        # Display results
        console.print("\n[bold green]Multi-Agent Workflow Complete[/bold green]\n")

        if result.final_answer:
            console.print(Panel.fit(result.final_answer, title="Final Answer"))
        else:
            console.print("[yellow]Warning: No final answer generated[/yellow]")

        # Display metrics
        console.print(f"\n[bold]Workflow Metrics:[/bold]")
        console.print(f"  Latency: {latency:.2f}s")
        console.print(f"  Iterations: {result.iteration}")
        console.print(f"  Route history: {' → '.join(result.route_history)}")
        console.print(f"  Sources collected: {len(result.sources)}")
        console.print(f"  Agents executed: {len(result.agent_results)}")

        if result.errors:
            console.print(f"\n[yellow]Errors encountered:[/yellow]")
            for error in result.errors:
                console.print(f"  - {error}")

        # Calculate total cost
        total_cost = sum(
            r.metadata.get("cost_usd", 0) for r in result.agent_results if "cost_usd" in r.metadata
        )
        if total_cost > 0:
            console.print(f"  Estimated cost: ${total_cost:.4f}")

    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Execution Error", style="red"))
        raise typer.Exit(code=2) from exc
    except Exception as e:
        logger.error(f"Multi-agent workflow failed: {e}")
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
