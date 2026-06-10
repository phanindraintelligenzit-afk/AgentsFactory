"""Context budget management for multi-agent pipelines.

Handles token budget tracking, summarization compression, and structured
state transfer between agents to prevent context window exhaustion.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from agentkit.models.pipeline import AgentResult, PipelineState


@dataclass
class ContextBudget:
    """Token budget tracker for a single agent."""

    max_tokens: int = 4000
    used_tokens: int = 0
    reserved_tokens: int = 500  # For system prompt + overhead

    @property
    def available_tokens(self) -> int:
        return max(0, self.max_tokens - self.used_tokens - self.reserved_tokens)

    @property
    def utilization(self) -> float:
        if self.max_tokens == 0:
            return 1.0
        return self.used_tokens / self.max_tokens

    def can_fit(self, tokens: int) -> bool:
        return tokens <= self.available_tokens

    def consume(self, tokens: int) -> None:
        self.used_tokens += tokens

    def reset(self) -> None:
        self.used_tokens = 0


@dataclass
class ContextManager:
    """Manages context flow between agents in a pipeline.

    Strategies:
    1. Summarization — compress prior agent outputs to summaries
    2. Structured state — pass only required fields, not full history
    3. Checkpointing — compress all prior state at milestones
    """

    default_budget_tokens: int = 4000
    compression_ratio: float = 0.2  # Target 20% of original size
    _budgets: dict[str, ContextBudget] = field(default_factory=dict)

    def get_budget(self, agent_id: str, max_tokens: Optional[int] = None) -> ContextBudget:
        if agent_id not in self._budgets:
            self._budgets[agent_id] = ContextBudget(
                max_tokens=max_tokens or self.default_budget_tokens
            )
        return self._budgets[agent_id]

    def build_agent_context(
        self,
        state: PipelineState,
        agent_id: str,
        include_prior_summaries: bool = True,
    ) -> dict[str, Any]:
        """Build the context dict for an agent, respecting its token budget.

        Returns a structured dict with:
        - input: original user input
        - constraints: pipeline constraints
        - prior_results: summaries of prior agent outputs (compressed)
        - decisions: key decisions made so far
        """
        budget = self.get_budget(agent_id)
        context: dict[str, Any] = {
            "input": state.original_input,
            "constraints": state.constraints,
        }

        if include_prior_summaries:
            prior = {}
            for aid, result in state.agent_results.items():
                if aid != agent_id and result.summary:
                    prior[aid] = {
                        "summary": result.summary,
                        "confidence": result.confidence,
                        "status": result.status.value,
                    }
            if prior:
                context["prior_results"] = prior

        if state.decisions:
            context["decisions"] = state.decisions

        return context

    def estimate_token_count(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token for English)."""
        return len(text) // 4

    def estimate_dict_tokens(self, data: dict[str, Any]) -> int:
        """Estimate token count for a dict."""
        return self.estimate_token_count(json.dumps(data, default=str))

    def compress_result(self, result: AgentResult, max_tokens: int = 200) -> str:
        """Compress an agent result to a summary within token budget.

        In production, this would call an LLM to generate the summary.
        For now, uses a simple truncation approach.
        """
        if result.summary:
            # Already has a summary, truncate if needed
            tokens = self.estimate_token_count(result.summary)
            if tokens <= max_tokens:
                return result.summary
            # Truncate
            chars = max_tokens * 4
            return result.summary[:chars] + "..."

        # Generate a basic summary from output
        parts = []
        if result.output:
            for key, value in result.output.items():
                val_str = str(value)
                if len(val_str) > 100:
                    val_str = val_str[:100] + "..."
                parts.append(f"{key}: {val_str}")

        summary = " | ".join(parts) if parts else f"Agent {result.agent_id} completed"
        if self.estimate_token_count(summary) > max_tokens:
            chars = max_tokens * 4
            summary = summary[:chars] + "..."
        return summary

    def check_budget(self, state: PipelineState, agent_id: str) -> dict[str, Any]:
        """Check if an agent can execute within its context budget.

        Returns a status dict with:
        - can_execute: bool
        - budget_status: ok | warning | exceeded
        - estimated_tokens: int
        - available_tokens: int
        """
        budget = self.get_budget(agent_id)
        context = self.build_agent_context(state, agent_id)
        estimated = self.estimate_dict_tokens(context)

        status = "ok"
        if estimated > budget.available_tokens:
            status = "exceeded"
        elif estimated > budget.available_tokens * 0.8:
            status = "warning"

        return {
            "can_execute": status != "exceeded",
            "budget_status": status,
            "estimated_tokens": estimated,
            "available_tokens": budget.available_tokens,
            "utilization": budget.utilization,
        }

    def reset(self) -> None:
        self._budgets.clear()
