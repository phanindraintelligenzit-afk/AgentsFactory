"""Test configuration and fixtures."""

import pytest
from agentkit.core.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerRegistry
from agentkit.core.context import ContextManager
from agentkit.core.fallback import FallbackChain, FallbackManager
from agentkit.core.hitl import HITLManager
from agentkit.core.permissions import ToolAccessMatrix
from agentkit.models.pipeline import PipelineState
from agentkit.models.topology import AgentConfig, TopologyConfig, TopologyType


@pytest.fixture
def sample_state():
    return PipelineState(
        original_input="Test input",
        constraints=["constraint1"],
    )


@pytest.fixture
def sample_agent_config():
    return AgentConfig(
        agent_id="test_agent",
        role="researcher",
        model="openrouter/owl-alpha",
    )


@pytest.fixture
def sample_topology():
    return TopologyConfig(
        name="test_pipeline",
        topology_type=TopologyType.SEQUENTIAL,
        agents=[
            AgentConfig(agent_id="agent_a", role="researcher"),
            AgentConfig(agent_id="agent_b", role="analyzer"),
            AgentConfig(agent_id="agent_c", role="writer"),
        ],
    )


@pytest.fixture
def circuit_breaker():
    return CircuitBreaker(
        agent_id="test_agent",
        config=CircuitBreakerConfig(failure_threshold=3, recovery_timeout_seconds=1),
    )


@pytest.fixture
def context_manager():
    return ContextManager(default_budget_tokens=4000)


@pytest.fixture
def fallback_manager():
    fm = FallbackManager()
    fm.register(FallbackChain.default_chain("test_agent"))
    return fm
