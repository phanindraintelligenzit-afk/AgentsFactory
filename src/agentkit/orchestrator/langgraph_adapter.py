"""LangGraph adapter — bridges AgentsFactory with LangGraph's state graph.

Maps PipelineState to LangGraph's TypedDict state and provides
node functions for each topology pattern.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional

import structlog
from langgraph.graph import StateGraph, END

from agentkit.agents.base import BaseAgent
from agentkit.core.circuit_breaker import CircuitBreakerConfig, CircuitBreakerRegistry
from agentkit.core.context import ContextManager
from agentkit.core.fallback import FallbackManager
from agentkit.core.hitl import HITLManager
from agentkit.models.pipeline import AgentResult, AgentStatus, PipelineState
from agentkit.models.topology import TopologyConfig, TopologyType
from agentkit.observability.tracer import PipelineTracer

logger = structlog.get_logger("agentkit.langgraph")


class LangGraphAdapter:
    """Adapters AgentsFactory pipelines to LangGraph StateGraph.

    This allows you to:
    1. Define pipelines using AgentsFactory's config system
    2. Execute them via LangGraph's compiled graph
    3. Get LangGraph's features (checkpointing, streaming, persistence)
       on top of AgentsFactory's safety systems

    Usage:
        adapter = LangGraphAdapter(topology_config, agents)
        graph = adapter.build_graph()
        compiled = graph.compile()

        result = await compiled.ainvoke({
            "input": "Research topic",
            "constraints": [],
        })
    """

    def __init__(
        self,
        config: TopologyConfig,
        agents: list[BaseAgent],
        tracer: PipelineTracer | None = None,
    ):
        self.config = config
        self.agents = {a.agent_id: a for a in agents}
        self.agent_order = [a.agent_id for a in agents]
        self.tracer = tracer or PipelineTracer()

        # Safety subsystems
        self.circuit_breakers = CircuitBreakerRegistry()
        self.context_manager = ContextManager()
        self.fallback_manager = FallbackManager()
        self.hitl_manager = HITLManager()

        for agent_id in self.agents:
            self.circuit_breakers.get_or_create(
                agent_id,
                CircuitBreakerConfig(failure_threshold=3, recovery_timeout_seconds=60),
            )

    def build_graph(self) -> StateGraph:
        """Build a LangGraph StateGraph from the topology config.

        The graph state is a dict with:
        - input: str
        - constraints: list[str]
        - current_agent_index: int
        - agent_results: dict[str, dict]
        - status: str
        - total_tokens: int
        - total_cost_usd: float
        - error: str
        """
        graph = StateGraph(LangGraphState)

        if self.config.topology_type == TopologyType.SEQUENTIAL:
            self._add_sequential_nodes(graph)
        elif self.config.topology_type == TopologyType.PARALLEL:
            self._add_parallel_nodes(graph)
        elif self.config.topology_type == TopologyType.EVALUATOR_OPTIMIZER:
            self._add_evaluator_optimizer_nodes(graph)
        else:
            # Default to sequential
            self._add_sequential_nodes(graph)

        return graph

    def _add_sequential_nodes(self, graph: StateGraph) -> None:
        """Add nodes for sequential chain: A → B → C → END."""
        # Add a node for each agent
        for agent_id in self.agent_order:
            graph.add_node(agent_id, self._make_agent_node(agent_id))

        # Add routing node
        graph.add_node("route", self._make_route_node())

        # Entry point
        graph.set_entry_point("route")

        # Route to first agent or END
        graph.add_conditional_edges(
            "route",
            self._route_sequential,
            {**{aid: aid for aid in self.agent_order}, "END": END},
        )

        # Each agent routes back to the router
        for agent_id in self.agent_order:
            graph.add_edge(agent_id, "route")

    def _add_parallel_nodes(self, graph: StateGraph) -> None:
        """Add nodes for parallel fan-out: Router → [A, B, C] → Synthesizer → END."""
        # Add agent nodes
        for agent_id in self.agent_order:
            graph.add_node(agent_id, self._make_agent_node(agent_id))

        # Synthesizer
        if self.config.synthesizer_agent_id:
            graph.add_node(
                "synthesize",
                self._make_synthesize_node(),
            )

        # Router
        graph.add_node("route", self._make_route_node())
        graph.set_entry_point("route")

        # Fan-out: route to all agents
        graph.add_conditional_edges(
            "route",
            self._route_parallel,
            {**{aid: aid for aid in self.agent_order}, "END": END},
        )

        # All agents go to synthesizer or END
        for agent_id in self.agent_order:
            if self.config.synthesizer_agent_id:
                graph.add_edge(agent_id, "synthesize")
            else:
                graph.add_edge(agent_id, END)

        if self.config.synthesizer_agent_id:
            graph.add_edge("synthesize", END)

    def _add_evaluator_optimizer_nodes(self, graph: StateGraph) -> None:
        """Add nodes for evaluator-optimizer loop: Gen → Eval → (loop or END)."""
        if len(self.agent_order) < 2:
            raise ValueError("Evaluator-optimizer needs at least 2 agents")

        generator_id = self.agent_order[0]
        evaluator_id = self.config.evaluator_agent_id or self.agent_order[1]

        graph.add_node("generate", self._make_agent_node(generator_id))
        graph.add_node("evaluate", self._make_agent_node(evaluator_id))
        graph.add_node("route", self._make_route_node())

        graph.set_entry_point("route")

        graph.add_conditional_edges(
            "route",
            lambda s: "generate",
            {"generate": "generate"},
        )

        graph.add_edge("generate", "evaluate")
        graph.add_conditional_edges(
            "evaluate",
            self._route_evaluator,
            {"generate": "generate", "END": END},
        )

    def _make_agent_node(self, agent_id: str) -> Callable:
        """Create a LangGraph node function for an agent."""
        async def node_fn(state: dict) -> dict:
            agent = self.agents.get(agent_id)
            if not agent:
                return {"error": f"Agent {agent_id} not found"}

            # Check circuit breaker
            cb = self.circuit_breakers.get(agent_id)
            if cb and not cb.can_execute():
                return {
                    "agent_results": {
                        **state.get("agent_results", {}),
                        agent_id: {
                            "status": "skipped",
                            "error": "Circuit breaker open",
                        },
                    },
                }

            # Build context
            context = {
                "input": state.get("input", ""),
                "constraints": state.get("constraints", []),
                "prior_results": state.get("agent_results", {}),
            }

            # Execute
            try:
                result = await agent.execute(
                    PipelineState(
                        original_input=context["input"],
                        constraints=context["constraints"],
                    ),
                )

                # Update circuit breaker
                if cb:
                    if result.failed:
                        cb.record_failure()
                    else:
                        cb.record_success()

                return {
                    "agent_results": {
                        **state.get("agent_results", {}),
                        agent_id: {
                            "status": result.status.value,
                            "output": result.output,
                            "summary": result.summary,
                            "confidence": result.confidence,
                            "tokens_used": result.tokens_used,
                            "cost_usd": result.cost_usd,
                            "latency_ms": result.latency_ms,
                            "model": result.model,
                            "errors": result.errors,
                        },
                    },
                    "total_tokens": state.get("total_tokens", 0) + result.tokens_used,
                    "total_cost_usd": state.get("total_cost_usd", 0) + result.cost_usd,
                }

            except Exception as e:
                if cb:
                    cb.record_failure()
                return {
                    "agent_results": {
                        **state.get("agent_results", {}),
                        agent_id: {
                            "status": "failure",
                            "error": str(e),
                        },
                    },
                    "error": str(e),
                }

        return node_fn

    def _make_route_node(self) -> Callable:
        """Create a routing node that initializes state."""
        async def route_fn(state: dict) -> dict:
            return state
        return route_fn

    def _make_synthesize_node(self) -> Callable:
        """Create a synthesizer node that combines parallel results."""
        async def synthesize_fn(state: dict) -> dict:
            results = state.get("agent_results", {})
            if not results:
                return state

            summaries = []
            for agent_id, result in results.items():
                if isinstance(result, dict) and "summary" in result:
                    summaries.append(f"### {agent_id}\n{result['summary']}")

            combined = "\n\n".join(summaries) if summaries else "No results to synthesize"

            return {
                **state,
                "synthesis": combined,
                "agent_results": {
                    **results,
                    "synthesizer": {
                        "status": "success",
                        "output": {"result": combined},
                        "summary": combined[:200],
                        "confidence": 0.85,
                    },
                },
            }

        return synthesize_fn

    def _route_sequential(self, state: dict) -> str:
        """Route to the next agent in sequential chain."""
        results = state.get("agent_results", {})
        for agent_id in self.agent_order:
            if agent_id not in results:
                return agent_id
        return "END"

    def _route_parallel(self, state: dict) -> str:
        """Route to first unexecuted agent (for parallel fan-out)."""
        results = state.get("agent_results", {})
        for agent_id in self.agent_order:
            if agent_id not in results:
                return agent_id
        return "END"

    def _route_evaluator(self, state: dict) -> str:
        """Route evaluator output: loop back to generator or end."""
        results = state.get("agent_results", {})
        evaluator_id = self.config.evaluator_agent_id or self.agent_order[1]

        eval_result = results.get(evaluator_id, {})
        output = eval_result.get("output", {})

        # Check score
        score = output.get("score", 0.0)
        if isinstance(score, (int, float)) and score >= self.config.score_threshold:
            return "END"

        # Check iteration count
        gen_count = sum(1 for k in results if k == self.agent_order[0])
        if gen_count >= self.config.max_iterations:
            return "END"

        return "generate"


# LangGraph state schema (TypedDict would be better but dict is more flexible)
LangGraphState = dict[str, Any]
