# AgentsFactory

> Production Multi-Agent Orchestration Framework

Build, deploy, and observe multi-agent AI pipelines with confidence. AgentsFactory provides the production patterns that raw LLM frameworks are missing: circuit breakers, context budget management, fallback chains, structured observability, eval-driven deployment gates, and human-in-the-loop escalation.

## Why AgentsFactory?

Building multi-agent systems with raw LangGraph/LangChain gets you 60% of the way. The remaining 40% — the stuff that makes or breaks production — is what AgentsFactory provides:

| Problem | AgentsFactory Solution |
|---------|----------------------|
| One agent failure kills the pipeline | Circuit breakers + fallback chains |
| Context window explodes in multi-hop pipelines | Automatic summarization + structured state |
| Can't trace which agent caused a bad output | Structured tracing with trace_id per span |
| No way to know if a model change regressed quality | Eval suites with baseline comparison + deployment gates |
| Runaway API costs from retry loops | Token budget enforcement + cost circuit breakers |
| Humans don't know when to intervene | HITL gates with configurable escalation criteria |

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  API Layer (FastAPI)              │
├─────────────────────────────────────────────────┤
│              Orchestrator Engine                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │
│  │ Topology  │ │ Context  │ │  Fallback    │    │
│  │ Builder   │ │ Manager  │ │  Chains      │    │
│  └──────────┘ └──────────┘ └──────────────┘    │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │
│  │ Circuit  │ │   HITL   │ │ Permissions  │    │
│  │ Breaker  │ │  Gates   │ │   Matrix     │    │
│  └──────────┘ └──────────┘ └──────────────┘    │
├─────────────────────────────────────────────────┤
│           LangGraph Integration Layer            │
├─────────────────────────────────────────────────┤
│  Observability  │  Eval Framework  │  LLM SDKs  │
└─────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Install
uv pip install -e ".[dev]"

# Run the dev API
uv run uvicorn agentkit.api.app:app --reload

# Run tests
uv run pytest
```

## Topology Patterns

- **Sequential Chain** — A→B→C for linear workflows
- **Parallel Fan-Out/In** — Router→[A,B,C]→Synthesizer for concurrent subtasks
- **Hierarchical** — Orchestrator→Subagents for dynamic decomposition
- **Evaluator-Optimizer** — Generator→Eval→loop for iterative refinement

## License

MIT
