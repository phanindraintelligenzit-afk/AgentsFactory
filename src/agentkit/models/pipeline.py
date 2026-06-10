"""Pydantic state models for pipeline and agent state management."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Status of an individual agent execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    ESCALATED = "escalated"
    SKIPPED = "skipped"


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class AgentResult(BaseModel):
    """Output from a single agent execution."""

    agent_id: str
    step: int = 0
    status: AgentStatus = AgentStatus.PENDING
    output: dict[str, Any] = Field(default_factory=dict)
    summary: str = ""  # Compressed summary for downstream agents
    confidence: float = 0.0
    tokens_used: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    model: str = ""
    errors: list[str] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def failed(self) -> bool:
        return self.status in (AgentStatus.FAILURE, AgentStatus.PARTIAL)


class HITLGate(BaseModel):
    """Human-in-the-loop gate configuration."""

    gate_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    step: int = 0  # Which agent step triggers this gate
    gate_type: str = "blocking"  # blocking | advisory | sampling
    criteria: list[str] = Field(default_factory=list)  # What triggers escalation
    timeout_seconds: int = 300  # Max wait before timeout
    timeout_behavior: str = "reject"  # approve | reject | escalate
    approved: Optional[bool] = None
    reviewer_notes: str = ""


class PipelineState(BaseModel):
    """Shared state object passed between agents in a pipeline.

    This is the core data structure that flows through the orchestrator.
    Each agent reads its required fields and writes its output here.
    """

    pipeline_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_input: str = ""
    constraints: list[str] = Field(default_factory=list)
    agent_results: dict[str, AgentResult] = Field(default_factory=dict)
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    current_step: int = 0
    status: str = "in_progress"  # in_progress | completed | failed | escalated
    hitl_gates: list[HITLGate] = Field(default_factory=list)
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_agent_output(self, agent_id: str) -> dict[str, Any]:
        """Get the output of a specific agent."""
        if agent_id in self.agent_results:
            return self.agent_results[agent_id].output
        return {}

    def get_agent_summary(self, agent_id: str) -> str:
        """Get the compressed summary of a specific agent."""
        if agent_id in self.agent_results:
            return self.agent_results[agent_id].summary
        return ""

    def add_result(self, result: AgentResult) -> None:
        """Add an agent result and update aggregate metrics."""
        self.agent_results[result.agent_id] = result
        self.total_tokens += result.tokens_used
        self.total_cost_usd += result.cost_usd
        self.total_latency_ms += result.latency_ms

    def get_context_for_agent(self, agent_id: str, max_tokens: int = 4000) -> dict[str, Any]:
        """Build the context dict for a specific agent, respecting token budget."""
        context: dict[str, Any] = {
            "input": self.original_input,
            "constraints": self.constraints,
        }
        # Include summaries of prior agents (not full outputs)
        prior_summaries = {}
        for aid, result in self.agent_results.items():
            if aid != agent_id and result.summary:
                prior_summaries[aid] = result.summary
        if prior_summaries:
            context["prior_results"] = prior_summaries
        if self.decisions:
            context["decisions"] = self.decisions
        return context

    def mark_completed(self) -> None:
        self.status = "completed"
        self.completed_at = datetime.utcnow()

    def mark_failed(self, reason: str = "") -> None:
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        if reason:
            self.metadata["failure_reason"] = reason
