"""Fallback chain management for graceful degradation.

Implements the fallback chain pattern:
    Primary → Narrowed Fallback → Degraded/Rules → Human Escalation

The system must always produce something — even a degraded structured
response is better than a silent failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from agentkit.models.pipeline import AgentResult, AgentStatus


@dataclass
class FallbackLevel:
    """A single level in a fallback chain."""

    name: str
    agent_id: Optional[str] = None
    model: Optional[str] = None
    handler: Optional[Callable] = None  # For rule-based degraded mode
    condition: str = "failure"  # failure | timeout | cost | quality


@dataclass
class FallbackChain:
    """Defines the fallback chain for a single agent.

    Priority order:
    1. Primary — full capability agent
    2. Fallback — lighter/narrowed agent
    3. Degraded — rule-based or template output
    4. Human — escalate to human review
    """

    agent_id: str
    levels: list[FallbackLevel] = field(default_factory=list)
    _current_level: int = 0

    @property
    def current_level(self) -> FallbackLevel:
        if self._current_level < len(self.levels):
            return self.levels[self._current_level]
        return FallbackLevel(name="exhausted")

    @property
    def has_fallback(self) -> bool:
        return self._current_level < len(self.levels) - 1

    def escalate(self) -> FallbackLevel:
        """Move to the next fallback level."""
        if self.has_fallback:
            self._current_level += 1
        return self.current_level

    def reset(self) -> None:
        self._current_level = 0

    @classmethod
    def default_chain(cls, agent_id: str, fallback_model: str | None = None) -> FallbackChain:
        """Create a standard 4-level fallback chain."""
        return cls(
            agent_id=agent_id,
            levels=[
                FallbackLevel(name="primary", agent_id=agent_id),
                FallbackLevel(
                    name="fallback",
                    agent_id=agent_id,
                    model=fallback_model,
                    condition="failure",
                ),
                FallbackLevel(name="degraded", condition="failure"),
                FallbackLevel(name="human", condition="failure"),
            ],
        )


@dataclass
class FallbackManager:
    """Manages fallback chains for all agents in a pipeline."""

    _chains: dict[str, FallbackChain] = field(default_factory=dict)

    def register(self, chain: FallbackChain) -> None:
        self._chains[chain.agent_id] = chain

    def get_chain(self, agent_id: str) -> Optional[FallbackChain]:
        return self._chains.get(agent_id)

    def handle_failure(
        self,
        agent_id: str,
        failure_type: str = "failure",
    ) -> dict[str, Any]:
        """Handle an agent failure by escalating the fallback chain.

        Returns a dict with:
        - action: retry | fallback | degraded | escalate
        - level: current fallback level name
        - agent_id: which agent to use next
        - model: which model to use next
        """
        chain = self._chains.get(agent_id)
        if not chain:
            return {"action": "escalate", "level": "none", "agent_id": None, "model": None}

        level = chain.current_level

        if level.name == "primary":
            # First failure — retry with fallback
            chain.escalate()
            next_level = chain.current_level
            return {
                "action": "fallback",
                "level": next_level.name,
                "agent_id": next_level.agent_id,
                "model": next_level.model,
            }

        if level.name == "fallback":
            # Fallback also failed — go to degraded
            chain.escalate()
            return {
                "action": "degraded",
                "level": "degraded",
                "agent_id": None,
                "model": None,
            }

        if level.name == "degraded":
            # Degraded also failed — escalate to human
            chain.escalate()
            return {
                "action": "escalate",
                "level": "human",
                "agent_id": None,
                "model": None,
            }

        # All levels exhausted
        return {
            "action": "escalate",
            "level": "exhausted",
            "agent_id": None,
            "model": None,
        }

    def create_degraded_result(
        self,
        agent_id: str,
        error: str = "",
    ) -> AgentResult:
        """Create a degraded-mode structured result when all automated paths fail."""
        return AgentResult(
            agent_id=agent_id,
            status=AgentStatus.PARTIAL,
            output={
                "degraded": True,
                "message": "All automated paths failed. Human review required.",
                "error": error,
            },
            summary=f"Agent {agent_id} failed — degraded mode output.",
            confidence=0.0,
            errors=[error] if error else [],
        )

    def reset_all(self) -> None:
        for chain in self._chains.values():
            chain.reset()
