# Benchmark Report: Single-Agent vs Multi-Agent

> This checked-in report is a submission-ready sample. Re-run `python scripts/run_benchmark.py` with your `OPENAI_API_KEY` and Langfuse credentials to replace it with live measurements.

## Benchmark setup

- **Baseline:** one LLM call answers the full query directly.
- **Multi-agent:** Supervisor routes through Researcher, Analyst, and Writer.
- **Tracing:** local trace events plus Langfuse spans when configured.
- **Quality score:** heuristic 0-10 score from final-answer presence, length, sources, citations, analysis notes, and errors.

## Queries

1. Research GraphRAG state-of-the-art and write a 500-word summary
2. Compare single-agent and multi-agent workflows for customer support
3. Summarize production guardrails for LLM agents

## Expected results table

| Run | Latency (s) | Cost (USD) | Quality | Citation coverage | Notes |
|---|---:|---:|---:|---:|---|
| baseline-q1 | 5-15 | low | 5-7/10 | low | Fast but no live source collection |
| multi-agent-q1 | 20-60 | medium | 7-9/10 | high | Researcher collects sources, Writer cites them |
| baseline-q2 | 5-15 | low | 5-7/10 | low | Good for broad conceptual answer |
| multi-agent-q2 | 20-60 | medium | 7-9/10 | high | Better structured comparison |
| baseline-q3 | 5-15 | low | 5-7/10 | low | Good if query is simple |
| multi-agent-q3 | 20-60 | medium | 7-9/10 | high | Better guardrail coverage and traceability |

## Trace evidence

For each multi-agent run, the expected route history is:

```text
researcher → analyst → writer → done
```

Langfuse trace names:

- `multi-agent-research-workflow`
- `single-agent-baseline`

Important spans:

- `workflow.run`
- `agent.supervisor`
- `agent.researcher`
- `agent.analyst`
- `agent.writer`
- `baseline.llm`

## Analysis

The multi-agent workflow is expected to be slower and slightly more expensive because it performs several specialized LLM calls. The quality should be higher for research-heavy tasks because the workflow explicitly separates information gathering, analysis, and writing.

The baseline is better when the query is simple, latency-sensitive, or does not require citation-backed research.

## Recommendation

Use the multi-agent workflow for tasks requiring source collection, structured analysis, and auditable traces. Use the single-agent baseline for quick answers, low-cost execution, or simple conceptual questions.

## How to regenerate live numbers

```bash
pip install -r requirements.txt
python scripts/run_benchmark.py
```

The script overwrites this file with measured latency, estimated cost, and quality scores.
