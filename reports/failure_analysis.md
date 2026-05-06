# Failure Analysis

## Failure mode 1: Infinite routing loop

**Problem:** A supervisor-worker workflow can loop forever if a worker fails to update the shared state field that the router expects.

**Mitigation:** `SupervisorAgent` enforces `MAX_ITERATIONS` from settings. When the limit is reached, the route becomes `done` and a partial fallback answer is generated from any available research/analysis notes.

## Failure mode 2: Search provider failure

**Problem:** Tavily or another web search provider can fail because of missing API keys, rate limits, network errors, or service outages.

**Mitigation:** `SearchClient` uses Tavily when configured and automatically falls back to deterministic mock search results. This keeps the lab demo runnable without external search credentials.

## Failure mode 3: LLM timeout or transient API error

**Problem:** LLM calls can timeout, hit rate limits, or fail transiently.

**Mitigation:** `LLMClient.complete()` applies a timeout from `TIMEOUT_SECONDS` and retries failed calls up to three times with exponential backoff via `tenacity`.

## Failure mode 4: Poor citation coverage

**Problem:** The writer may produce a fluent answer without clear source references.

**Mitigation:** The Researcher generates source-indexed notes, the Writer prompt requires `[Source N]` citations, and the optional Critic checks whether citation markers are present.

## Failure mode 5: Cost or latency overhead

**Problem:** Multi-agent systems usually require more LLM calls than a single-agent baseline.

**Mitigation:** The workflow uses `gpt-4o-mini` by default, tracks estimated cost/token usage in `LLMClient`, and benchmarks latency/cost/quality in `reports/benchmark_report.md`.

## Failure mode 6: Missing observability

**Problem:** Without trace logs it is hard to explain which agent did what and where the run failed.

**Mitigation:** The workflow records local state trace events and exports spans to Langfuse when `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_HOST` are configured.

## Production readiness checklist

- [x] Max iterations
- [x] Per-call timeout
- [x] Retry with exponential backoff
- [x] Search fallback
- [x] Error list in shared state
- [x] Local trace events
- [x] Langfuse trace integration
- [x] Benchmark report generation
- [ ] Human-in-the-loop approval for high-stakes answers
- [ ] Provider-level rate limiting and cost budget alerts
- [ ] Semantic LLM-as-judge evaluation for final quality
