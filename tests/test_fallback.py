"""Tests for fallback chains."""

import pytest
from agentkit.core.fallback import FallbackChain, FallbackManager


class TestFallbackChain:
    def test_default_chain(self):
        chain = FallbackChain.default_chain("agent_a")
        assert len(chain.levels) == 4
        assert chain.levels[0].name == "primary"
        assert chain.levels[-1].name == "human"

    def test_escalate(self):
        chain = FallbackChain.default_chain("agent_a")
        assert chain.current_level.name == "primary"
        chain.escalate()
        assert chain.current_level.name == "fallback"
        chain.escalate()
        assert chain.current_level.name == "degraded"
        chain.escalate()
        assert chain.current_level.name == "human"

    def test_has_fallback(self):
        chain = FallbackChain.default_chain("agent_a")
        assert chain.has_fallback is True
        chain.escalate()
        chain.escalate()
        chain.escalate()
        assert chain.has_fallback is False

    def test_reset(self):
        chain = FallbackChain.default_chain("agent_a")
        chain.escalate()
        chain.escalate()
        chain.reset()
        assert chain.current_level.name == "primary"


class TestFallbackManager:
    def test_handle_failure_escalates(self, fallback_manager):
        result = fallback_manager.handle_failure("test_agent")
        assert result["action"] == "fallback"
        assert result["level"] == "fallback"

    def test_handle_failure_exhausts(self, fallback_manager):
        # Exhaust all levels
        for _ in range(4):
            result = fallback_manager.handle_failure("test_agent")
        assert result["action"] == "escalate"
        assert result["level"] == "exhausted"

    def test_degraded_result(self, fallback_manager):
        result = fallback_manager.create_degraded_result("agent_a", "test error")
        assert result.agent_id == "agent_a"
        assert result.output["degraded"] is True
        assert "test error" in result.errors
