# Design Template

## Problem

Build a research assistant that can handle complex queries requiring information gathering, analysis, and synthesis. The system needs to:
- Search for relevant information from multiple sources
- Analyze and extract key insights
- Synthesize a comprehensive, well-cited answer
- Provide transparency into the research process

## Why multi-agent?

Single-agent approaches have limitations:
- **Cognitive overload**: One agent trying to do research, analysis, and writing simultaneously leads to shallow results
- **No specialization**: Generic prompts can't optimize for each task (search vs analysis vs writing)
- **Poor traceability**: Hard to debug which part of the process failed
- **Limited parallelization**: Can't leverage concurrent execution for independent tasks

Multi-agent benefits:
- **Specialization**: Each agent optimized for its specific task
- **Clear handoffs**: Explicit state transitions make debugging easier
- **Modularity**: Can swap or improve individual agents without rewriting everything
- **Structured workflow**: Forces systematic approach (research → analyze → write)

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Route to next agent, enforce guardrails | Current state | Next route decision | Infinite loops, premature termination |
| Researcher | Find sources, synthesize research notes | User query | sources, research_notes | No results found, poor query generation |
| Analyst | Extract insights, identify patterns | research_notes, sources | analysis_notes | Shallow analysis, missing key points |
| Writer | Create final answer with citations | research_notes, analysis_notes, sources | final_answer | Poor structure, missing citations |

## Shared state

**ResearchState** contains:

- `request: ResearchQuery` - Original user query and parameters
- `iteration: int` - Current iteration count (for max_iterations guard)
- `route_history: list[str]` - Sequence of agents called (for debugging)
- `sources: list[SourceDocument]` - Collected sources with URLs and snippets
- `research_notes: str` - Synthesized research findings
- `analysis_notes: str` - Analytical insights and patterns
- `final_answer: str` - Final synthesized response
- `agent_results: list[AgentResult]` - Full history of agent outputs
- `trace: list[dict]` - Trace events for observability
- `errors: list[str]` - Accumulated errors

**Why these fields:**
- Sources needed for citation and verification
- Separate notes fields allow incremental progress
- History fields enable debugging and tracing
- Error tracking for graceful degradation

## Routing policy

```
START
  ↓
Supervisor
  ├─→ No sources? → Researcher → Supervisor
  ├─→ No analysis? → Analyst → Supervisor
  ├─→ No final_answer? → Writer → Supervisor
  └─→ Has final_answer? → DONE

Guardrails:
- Max iterations: 6 (prevents infinite loops)
- Timeout: 60s per agent
- Fallback: Generate partial answer if max iterations reached
```

**Decision logic:**
1. Check iteration < max_iterations
2. If no sources or research_notes → route to researcher
3. Else if no analysis_notes → route to analyst
4. Else if no final_answer → route to writer
5. Else → done

## Guardrails

- **Max iterations**: 6 iterations enforced by Supervisor
- **Timeout**: 60s timeout per LLM call (in LLMClient)
- **Retry**: 3 retries with exponential backoff for LLM calls (tenacity)
- **Fallback**: Supervisor creates partial answer if max iterations reached
- **Validation**: Each agent validates its inputs before processing
- **Error tracking**: All errors logged to state.errors for debugging

## Benchmark plan

**Queries:**
1. "Research GraphRAG state-of-the-art and write a 500-word summary"
2. "Compare single-agent and multi-agent workflows for customer support"
3. "Summarize production guardrails for LLM agents"

**Metrics:**
- Latency (wall-clock time)
- Cost (estimated USD from token usage)
- Quality score (0-10 heuristic based on completeness, citations, length)
- Source count
- Iteration count
- Error rate

**Expected outcomes:**
- Multi-agent: Higher latency, higher cost, better quality (more sources, better structure)
- Single-agent: Lower latency, lower cost, adequate quality for simple queries
- Multi-agent should score 7-9 on quality, single-agent 5-7
