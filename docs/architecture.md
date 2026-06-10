# AgentsFactory Architecture

## Design Philosophy

AgentsFactory is built on the principle that **multi-agent AI systems should be treated with the same rigor as distributed software systems**. Demos lie; production tells the truth.

## Core Components

### 1. PipelineState (models/pipeline.py)
The central data structure that flows through the orchestrator:
- Shared state object passed between agents
- Tracks all agent results, decisions, and metrics
- Provides context scoping per agent (only expose what's needed)
- Automatic aggregate metric tracking (tokens, cost, latency)

### 2. Topology Engine (orchestrator/engine.py)
Supports 4 topology patterns:
- **Sequential**: A→B→C linear chains
- **Parallel**: Router→[A,B,C]→Synthesizer fan-out/in
- **Hierarchical**: Orchestrator delegates to subagents dynamically
- **Evaluator-Optimizer**: Generate→Evaluate→Refine loop

### 3. Circuit Breaker (core/circuit_breaker.py)
CLOSED→OPEN→HALF-OPEN state machine per agent:
- Prevents cascading failures from repeatedly calling a failing agent
- Rolling window failure rate tracking
- Configurable thresholds and recovery timeouts
- Thread-safe for parallel execution

### 4. Context Manager (core/context.py)
Token budget management:
- Per-agent context budgets with utilization tracking
- Automatic summarization compression between agents
- Structured state transfer (only required fields passed)
- Checkpoint support for long pipelines

### 5. Fallback Manager (core/fallback.py)
4-level degradation chain:
- Primary → Narrowed fallback → Rule-based degraded → Human escalation
- Always produces output (degraded beats silent failure)
- Per-agent fallback configuration

### 6. HITL Gates (core/hitl.py)
Human-in-the-loop escalation:
- Blocking, advisory, and sampling gate types
- Configurable escalation criteria (irreversibility, blast radius, confidence)
- Timeout behavior configuration
- Gate evaluation against pipeline state

### 7. Permission Matrix (core/permissions.py)
Least-privilege tool access:
- Per-agent tool allowlists
- Predefined role templates (researcher, analyzer, writer, etc.)
- Tool validation before execution
- Scoped permission tokens

### 8. Pipeline Tracer (observability/tracer.py)
Structured tracing:
- Shared trace_id across all agents
- Per-span timing, cost, and status logging
- Error tracking with context
- Exportable traces for debugging

### 9. Eval Framework (eval/runner.py)
Eval-driven development:
- Test case definitions with expected outputs
- Per-agent and pipeline-level eval suites
- Baseline scoring and regression detection
- Automated feedback generation

## Architecture Review Checklist

Before deploying a pipeline:
- [ ] Topology documented with data flow diagram
- [ ] Each agent has defined role, input contract, output contract
- [ ] No agent has tools/data beyond its scope
- [ ] Context budget calculated for worst-case input
- [ ] All failure modes documented with recovery paths
- [ ] Circuit breakers configured for all agents
- [ ] Fallback chains defined for every agent
- [ ] HITL gates placed at irreversible/high-impact points
- [ ] Structured tracing enabled
- [ ] Eval suite with ≥20 cases per agent
- [ ] Baseline scores recorded

## LangGraph Integration

AgentsFactory is designed to work **on top of LangGraph**, not replace it:
- LangGraph handles the low-level state graph and conditional routing
- AgentsFactory adds the production patterns LangGraph lacks
- The `LangGraphAdapter` (Sprint 2) will bridge the two
