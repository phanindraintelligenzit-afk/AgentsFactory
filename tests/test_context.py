"""Tests for context manager."""

import pytest
from agentkit.core.context import ContextBudget, ContextManager
from agentkit.models.pipeline import AgentResult, AgentStatus


class TestContextBudget:
    def test_available_tokens(self):
        budget = ContextBudget(max_tokens=4000, reserved_tokens=500)
        assert budget.available_tokens == 3500

    def test_consume(self):
        budget = ContextBudget(max_tokens=4000)
        budget.consume(1000)
        assert budget.used_tokens == 1000
        assert budget.available_tokens == 2500

    def test_can_fit(self):
        budget = ContextBudget(max_tokens=4000, used_tokens=3000)
        assert budget.can_fit(400) is True
        assert budget.can_fit(600) is False

    def test_utilization(self):
        budget = ContextBudget(max_tokens=4000, used_tokens=2000)
        assert budget.utilization == 0.5


class TestContextManager:
    def test_build_context(self, sample_state, context_manager):
        context = context_manager.build_agent_context(sample_state, "agent_a")
        assert "input" in context
        assert "constraints" in context
        assert context["input"] == "Test input"

    def test_estimate_tokens(self, context_manager):
        assert context_manager.estimate_token_count("hello world") == 2

    def test_compress_result_with_summary(self, context_manager):
        result = AgentResult(
            agent_id="test",
            summary="Short summary",
            status=AgentStatus.SUCCESS,
        )
        compressed = context_manager.compress_result(result)
        assert compressed == "Short summary"

    def test_compress_result_truncates_long_summary(self, context_manager):
        result = AgentResult(
            agent_id="test",
            summary="x" * 1000,
            status=AgentStatus.SUCCESS,
        )
        compressed = context_manager.compress_result(result, max_tokens=50)
        assert len(compressed) < 300  # Truncated

    def test_check_budget(self, sample_state, context_manager):
        check = context_manager.check_budget(sample_state, "agent_a")
        assert "can_execute" in check
        assert "budget_status" in check
        assert check["budget_status"] == "ok"
