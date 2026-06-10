"""Base agent class and agent builder."""

from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from agentkit.core.context import ContextManager
from agentkit.core.permissions import PermissionScope
from agentkit.models.pipeline import AgentResult, AgentStatus, PipelineState
from agentkit.models.topology import AgentConfig


class BaseAgent:
    """Base class for all agents in a pipeline.

    Each agent:
    - Has a unique ID and role
    - Receives structured input from the pipeline state
    - Produces structured output (AgentResult)
    - Respects its context budget and tool permissions
    """

    def __init__(
        self,
        config: AgentConfig,
        permission_scope: Optional[PermissionScope] = None,
        context_manager: Optional[ContextManager] = None,
    ):
        self.config = config
        self.agent_id = config.agent_id
        self.permission_scope = permission_scope
        self.context_manager = context_manager or ContextManager()

    async def execute(
        self,
        state: PipelineState,
        **kwargs: Any,
    ) -> AgentResult:
        """Execute the agent's task.

        Subclasses should override _run() with their specific logic.
        This method handles the common boilerplate: timing, error handling,
        context budget checking, and result construction.
        """
        start_time = time.time()
        result = AgentResult(
            agent_id=self.agent_id,
            step=state.current_step,
            status=AgentStatus.RUNNING,
            model=self.config.model,
            started_at=__import__("datetime").datetime.utcnow(),
        )

        try:
            # Check context budget
            budget_check = self.context_manager.check_budget(state, self.agent_id)
            if not budget_check["can_execute"]:
                result.status = AgentStatus.PARTIAL
                result.errors.append(
                    f"Context budget exceeded: {budget_check['estimated_tokens']} > "
                    f"{budget_check['available_tokens']} available"
                )
                result.summary = "Skipped due to context budget constraints"
                return result

            # Build context for this agent
            context = self.context_manager.build_agent_context(
                state, self.agent_id
            )

            # Run the agent's specific logic
            output = await self._run(context, state, **kwargs)

            # Build result
            elapsed_ms = (time.time() - start_time) * 1000
            result.output = output
            result.status = AgentStatus.SUCCESS
            result.confidence = output.get("confidence", 0.8)
            result.tokens_used = output.get("tokens_used", 0)
            result.cost_usd = output.get("cost_usd", 0.0)
            result.latency_ms = elapsed_ms

            # Generate summary for downstream agents
            result.summary = self.context_manager.compress_result(result)

        except Exception as e:
            result.status = AgentStatus.FAILURE
            result.errors.append(str(e))
            result.summary = f"Agent {self.agent_id} failed: {str(e)}"

        finally:
            result.completed_at = __import__("datetime").datetime.utcnow()

        return result

    async def _run(
        self,
        context: dict[str, Any],
        state: PipelineState,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Override this method in subclasses with agent-specific logic.

        Must return a dict with at least:
        - result: the agent's output
        - confidence: float 0-1
        - tokens_used: int (optional)
        - cost_usd: float (optional)
        """
        raise NotImplementedError(f"Agent {self.agent_id} must implement _run()")

    def validate_tools(self, requested_tools: list[str]) -> dict[str, Any]:
        """Validate requested tools against this agent's permissions."""
        if self.permission_scope:
            allowed = self.permission_scope.allowed_tools
            return {
                "allowed": [t for t in requested_tools if t in allowed],
                "denied": [t for t in requested_tools if t not in allowed],
            }
        return {"allowed": requested_tools, "denied": []}
