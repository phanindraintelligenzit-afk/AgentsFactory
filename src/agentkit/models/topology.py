"""Topology configuration models."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class TopologyType(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    EVALUATOR_OPTIMIZER = "evaluator_optimizer"


class AgentConfig(BaseModel):
    """Configuration for a single agent in a pipeline."""

    agent_id: str
    role: str = ""
    system_prompt: str = ""
    model: str = "openrouter/owl-alpha"
    temperature: float = 0.0
    max_tokens: int = 2000
    tools: list[str] = Field(default_factory=list)
    # Context management
    context_budget_tokens: int = 4000
    # Fallback
    fallback_agent_id: Optional[str] = None
    fallback_model: Optional[str] = None
    # Permissions
    allowed_tools: list[str] = Field(default_factory=list)
    # HITL
    require_hitl: bool = False
    hitl_criteria: list[str] = Field(default_factory=list)
    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)


class TopologyConfig(BaseModel):
    """Configuration for a pipeline topology."""

    name: str = "default"
    topology_type: TopologyType = TopologyType.SEQUENTIAL
    agents: list[AgentConfig] = Field(default_factory=list)
    # Parallel-specific
    synthesizer_agent_id: Optional[str] = None  # For fan-in
    max_parallel_agents: int = 7
    merge_strategy: str = "concatenate"  # concatenate | vote | weight
    # Evaluator-optimizer specific
    evaluator_agent_id: Optional[str] = None
    max_iterations: int = 3
    score_threshold: float = 0.8
    # Global settings
    max_chain_length: int = 5
    enable_circuit_breaker: bool = True
    enable_context_compression: bool = True
    cost_budget_usd: float = 1.0
    token_budget: int = 50000

    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        for agent in self.agents:
            if agent.agent_id == agent_id:
                return agent
        return None
