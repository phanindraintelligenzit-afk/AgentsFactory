"""Main pipeline orchestrator — executes multi-agent topologies."""

from __future__ import annotations

import time
from typing import Any, Optional

from agentkit.agents.base import BaseAgent
from agentkit.core.circuit_breaker import CircuitBreakerConfig, CircuitBreakerRegistry
from agentkit.core.context import ContextManager
from agentkit.core.fallback import FallbackManager
from agentkit.core.hitl import HITLManager
from agentkit.core.permissions import ToolAccessMatrix
from agentkit.models.pipeline import AgentResult, AgentStatus, PipelineState
from agentkit.models.topology import TopologyConfig, TopologyType
from agentkit.observability.tracer import PipelineTracer


class Orchestrator:
    """Executes multi-agent pipelines with full production safeguards.

    Features:
    - Multiple topology patterns (sequential, parallel, hierarchical, evaluator-optimizer)
    - Circuit breakers per agent
    - Context budget management
    - Fallback chains
    - HITL gates
    - Structured observability
    """

    def __init__(
        self,
        config: TopologyConfig,
        agents: list[BaseAgent],
        tracer: Optional[PipelineTracer] = None,
    ):
        self.config = config
        self.agents = {a.agent_id: a for a in agents}
        self.agent_order = [a.agent_id for a in agents]

        # Initialize subsystems
        self.circuit_breakers = CircuitBreakerRegistry()
        self.context_manager = ContextManager()
        self.fallback_manager = FallbackManager()
        self.hitl_manager = HITLManager()
        self.tracer = tracer or PipelineTracer()
        self.permission_matrix = ToolAccessMatrix()

        # Initialize circuit breakers for all agents
        for agent_id in self.agents:
            self.circuit_breakers.get_or_create(
                agent_id,
                CircuitBreakerConfig(failure_threshold=3, recovery_timeout_seconds=60),
            )

    async def execute(
        self,
        input_text: str,
        constraints: list[str] | None = None,
        **kwargs: Any,
    ) -> PipelineState:
        """Execute the pipeline.

        Args:
            input_text: The user's input/query
            constraints: Optional constraints for the pipeline
            **kwargs: Additional arguments passed to agents

        Returns:
            PipelineState with all agent results
        """
        state = PipelineState(
            original_input=input_text,
            constraints=constraints or [],
        )

        self.tracer.start_pipeline(state)

        try:
            if self.config.topology_type == TopologyType.SEQUENTIAL:
                state = await self._execute_sequential(state, **kwargs)
            elif self.config.topology_type == TopologyType.PARALLEL:
                state = await self._execute_parallel(state, **kwargs)
            elif self.config.topology_type == TopologyType.HIERARCHICAL:
                state = await self._execute_hierarchical(state, **kwargs)
            elif self.config.topology_type == TopologyType.EVALUATOR_OPTIMIZER:
                state = await self._execute_evaluator_optimizer(state, **kwargs)
            else:
                raise ValueError(f"Unknown topology: {self.config.topology_type}")

            if state.status == "in_progress":
                state.mark_completed()

        except Exception as e:
            state.mark_failed(str(e))
            self.tracer.log_error(state, str(e))

        self.tracer.end_pipeline(state)
        return state

    async def _execute_sequential(
        self, state: PipelineState, **kwargs: Any
    ) -> PipelineState:
        """Execute agents in sequential chain: A → B → C."""
        for step, agent_id in enumerate(self.agent_order):
            state.current_step = step
            result = await self._execute_agent(agent_id, state, **kwargs)
            state.add_result(result)

            # Check for HITL gates
            gate_evaluations = self.hitl_manager.evaluate_gates(state)
            for evaluation in gate_evaluations:
                if evaluation["needs_review"] and evaluation["gate_type"] == "blocking":
                    hitl_gate = self.hitl_manager.get_gate(evaluation["gate_id"])
                    if hitl_gate:
                        state.hitl_gates.append(hitl_gate)
                        state.status = "escalated"
                        return state

            # Stop on failure (unless fallback handles it)
            if result.failed:
                fallback_result = self.fallback_manager.handle_failure(agent_id)
                if fallback_result["action"] == "escalate":
                    break

        return state

    async def _execute_parallel(
        self, state: PipelineState, **kwargs: Any
    ) -> PipelineState:
        """Execute agents in parallel: Router → [A, B, C] → Synthesizer."""
        import asyncio

        step = 0
        state.current_step = step

        # Execute all agents in parallel
        tasks = [
            self._execute_agent(agent_id, state, **kwargs)
            for agent_id in self.agent_order
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                # Handle exception as failure
                agent_id = self.agent_order[results.index(result)]
                result = AgentResult(
                    agent_id=agent_id,
                    step=step,
                    status=AgentStatus.FAILURE,
                    errors=[str(result)],
                )
            state.add_result(result)

        # Synthesize results if synthesizer is configured
        if self.config.synthesizer_agent_id:
            synth_agent = self.agents.get(self.config.synthesizer_agent_id)
            if synth_agent:
                synth_result = await self._execute_agent(
                    self.config.synthesizer_agent_id, state, **kwargs
                )
                state.add_result(synth_result)

        return state

    async def _execute_hierarchical(
        self, state: PipelineState, **kwargs: Any
    ) -> PipelineState:
        """Execute with orchestrator → subagents pattern.

        The first agent is the orchestrator that decides which subagents to invoke.
        """
        if not self.agent_order:
            return state

        # First agent is the orchestrator
        orchestrator_id = self.agent_order[0]
        orchestrator_result = await self._execute_agent(
            orchestrator_id, state, **kwargs
        )
        state.add_result(orchestrator_result)

        # Parse orchestrator's delegation decisions
        delegated_agents = orchestrator_result.output.get("delegate_to", [])
        if delegated_agents:
            import asyncio
            tasks = [
                self._execute_agent(aid, state, **kwargs)
                for aid in delegated_agents
                if aid in self.agents
            ]
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if not isinstance(result, Exception):
                        state.add_result(result)

        return state

    async def _execute_evaluator_optimizer(
        self, state: PipelineState, **kwargs: Any
    ) -> PipelineState:
        """Execute generator → evaluator → loop until quality threshold or max iterations."""
        generator_id = self.agent_order[0] if self.agent_order else None
        evaluator_id = self.config.evaluator_agent_id

        if not generator_id or not evaluator_id:
            raise ValueError("Evaluator-optimizer requires generator and evaluator agents")

        best_result = None
        best_score = 0.0

        for iteration in range(self.config.max_iterations):
            state.current_step = iteration

            # Generate
            gen_result = await self._execute_agent(generator_id, state, **kwargs)
            state.add_result(gen_result)

            # Evaluate
            eval_result = await self._execute_agent(evaluator_id, state, **kwargs)
            state.add_result(eval_result)

            score = eval_result.output.get("score", 0.0)
            if score > best_score:
                best_score = score
                best_result = gen_result

            # Check if quality threshold met
            if score >= self.config.score_threshold:
                break

            # Check for score plateau
            if iteration > 0 and abs(score - best_score) < 0.05:
                break

        if best_result:
            state.metadata["best_score"] = best_score
            state.metadata["iterations"] = iteration + 1

        return state

    async def _execute_agent(
        self,
        agent_id: str,
        state: PipelineState,
        **kwargs: Any,
    ) -> AgentResult:
        """Execute a single agent with circuit breaker and fallback support."""
        agent = self.agents.get(agent_id)
        if not agent:
            return AgentResult(
                agent_id=agent_id,
                step=state.current_step,
                status=AgentStatus.FAILURE,
                errors=[f"Agent {agent_id} not found"],
            )

        # Check circuit breaker
        cb = self.circuit_breakers.get(agent_id)
        if cb and not cb.can_execute():
            self.tracer.log_event(state, "circuit_breaker_tripped", {"agent_id": agent_id})
            # Try fallback
            if agent.config.fallback_agent_id:
                return await self._execute_agent(
                    agent.config.fallback_agent_id, state, **kwargs
                )
            return AgentResult(
                agent_id=agent_id,
                step=state.current_step,
                status=AgentStatus.SKIPPED,
                errors=[f"Circuit breaker open for {agent_id}"],
            )

        # Execute
        self.tracer.log_event(state, "agent_start", {"agent_id": agent_id})
        result = await agent.execute(state, **kwargs)
        self.tracer.log_event(
            state,
            "agent_end",
            {"agent_id": agent_id, "status": result.status.value},
        )

        # Update circuit breaker
        if cb:
            if result.failed:
                cb.record_failure()
            else:
                cb.record_success()

        return result
