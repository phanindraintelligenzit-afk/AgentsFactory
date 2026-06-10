"""YAML-based pipeline definition loader.

Allows defining pipelines in YAML config files instead of Python code.

Example pipeline.yaml:
```yaml
name: research_pipeline
topology: sequential
settings:
  cost_budget_usd: 1.0
  token_budget: 50000
  enable_circuit_breaker: true

agents:
  - id: researcher
    role: researcher
    model: openrouter/owl-alpha
    system_prompt: "You are a research analyst..."
    max_tokens: 2000
    context_budget_tokens: 4000

  - id: analyzer
    role: analyzer
    model: openrouter/owl-alpha
    max_tokens: 1500

  - id: writer
    role: writer
    model: openrouter/owl-alpha
    max_tokens: 3000

hitl_gates:
  - step: 1
    type: advisory
    criteria:
      - low_confidence
```
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agentkit.models.topology import AgentConfig, TopologyConfig, TopologyType


def load_pipeline_config(path: str | Path) -> TopologyConfig:
    """Load a pipeline configuration from a YAML file.

    Args:
        path: Path to the YAML config file

    Returns:
        TopologyConfig ready for use with Orchestrator
    """
    with open(path) as f:
        data = yaml.safe_load(f)

    if not data:
        raise ValueError(f"Empty or invalid YAML: {path}")

    # Parse topology type
    topology_str = data.get("topology", "sequential")
    topology_type = TopologyType(topology_str)

    # Parse agents
    agents = []
    for agent_data in data.get("agents", []):
        agents.append(AgentConfig(
            agent_id=agent_data["id"],
            role=agent_data.get("role", ""),
            system_prompt=agent_data.get("system_prompt", ""),
            model=agent_data.get("model", "openrouter/owl-alpha"),
            temperature=agent_data.get("temperature", 0.0),
            max_tokens=agent_data.get("max_tokens", 2000),
            tools=agent_data.get("tools", []),
            context_budget_tokens=agent_data.get("context_budget_tokens", 4000),
            fallback_agent_id=agent_data.get("fallback_agent_id"),
            fallback_model=agent_data.get("fallback_model"),
            allowed_tools=agent_data.get("allowed_tools", []),
            require_hitl=agent_data.get("require_hitl", False),
            hitl_criteria=agent_data.get("hitl_criteria", []),
            metadata=agent_data.get("metadata", {}),
        ))

    # Parse settings
    settings = data.get("settings", {})

    return TopologyConfig(
        name=data.get("name", "unnamed"),
        topology_type=topology_type,
        agents=agents,
        synthesizer_agent_id=settings.get("synthesizer_agent_id"),
        max_parallel_agents=settings.get("max_parallel_agents", 7),
        merge_strategy=settings.get("merge_strategy", "concatenate"),
        evaluator_agent_id=settings.get("evaluator_agent_id"),
        max_iterations=settings.get("max_iterations", 3),
        score_threshold=settings.get("score_threshold", 0.8),
        max_chain_length=settings.get("max_chain_length", 5),
        enable_circuit_breaker=settings.get("enable_circuit_breaker", True),
        enable_context_compression=settings.get("enable_context_compression", True),
        cost_budget_usd=settings.get("cost_budget_usd", 1.0),
        token_budget=settings.get("token_budget", 50000),
    )


def save_pipeline_config(config: TopologyConfig, path: str | Path) -> None:
    """Save a pipeline configuration to a YAML file."""
    data = {
        "name": config.name,
        "topology": config.topology_type.value,
        "settings": {
            "cost_budget_usd": config.cost_budget_usd,
            "token_budget": config.token_budget,
            "enable_circuit_breaker": config.enable_circuit_breaker,
            "enable_context_compression": config.enable_context_compression,
            "max_iterations": config.max_iterations,
            "score_threshold": config.score_threshold,
        },
        "agents": [
            {
                "id": a.agent_id,
                "role": a.role,
                "model": a.model,
                "temperature": a.temperature,
                "max_tokens": a.max_tokens,
                "context_budget_tokens": a.context_budget_tokens,
                "system_prompt": a.system_prompt,
            }
            for a in config.agents
        ],
    }

    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
