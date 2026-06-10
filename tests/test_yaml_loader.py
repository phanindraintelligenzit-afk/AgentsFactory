"""Tests for YAML pipeline loader."""

import pytest
import tempfile
import os

from agentkit.orchestrator.yaml_loader import load_pipeline_config, save_pipeline_config
from agentkit.models.topology import TopologyType


SAMPLE_YAML = """
name: test_pipeline
topology: sequential
settings:
  cost_budget_usd: 0.5
  token_budget: 10000
  enable_circuit_breaker: true

agents:
  - id: researcher
    role: researcher
    model: openrouter/owl-alpha
    temperature: 0.3
    max_tokens: 2000

  - id: writer
    role: writer
    model: openrouter/owl-alpha
    max_tokens: 3000
"""


class TestYamlLoader:
    def test_load_pipeline_config(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(SAMPLE_YAML)
            path = f.name

        try:
            config = load_pipeline_config(path)
            assert config.name == "test_pipeline"
            assert config.topology_type == TopologyType.SEQUENTIAL
            assert len(config.agents) == 2
            assert config.agents[0].agent_id == "researcher"
            assert config.agents[0].role == "researcher"
            assert config.agents[0].model == "openrouter/owl-alpha"
            assert config.agents[1].agent_id == "writer"
            assert config.cost_budget_usd == 0.5
            assert config.token_budget == 10000
            assert config.enable_circuit_breaker is True
        finally:
            os.unlink(path)

    def test_save_and_load_roundtrip(self):
        from agentkit.models.topology import AgentConfig, TopologyConfig

        original = TopologyConfig(
            name="roundtrip_test",
            topology_type=TopologyType.PARALLEL,
            agents=[
                AgentConfig(agent_id="a1", role="researcher"),
                AgentConfig(agent_id="a2", role="analyzer"),
            ],
            cost_budget_usd=1.0,
        )

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            path = f.name

        try:
            save_pipeline_config(original, path)
            loaded = load_pipeline_config(path)
            assert loaded.name == original.name
            assert loaded.topology_type == original.topology_type
            assert len(loaded.agents) == len(original.agents)
        finally:
            os.unlink(path)

    def test_load_empty_yaml_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            path = f.name

        try:
            with pytest.raises((ValueError, TypeError)):
                load_pipeline_config(path)
        finally:
            os.unlink(path)
