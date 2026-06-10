"""Tests for pipeline state."""

import pytest
from agentkit.models.pipeline import AgentResult, AgentStatus, PipelineState


class TestPipelineState:
    def test_creation(self, sample_state):
        assert sample_state.original_input == "Test input"
        assert sample_state.status == "in_progress"
        assert len(sample_state.constraints) == 1

    def test_add_result(self, sample_state):
        result = AgentResult(
            agent_id="agent_a",
            status=AgentStatus.SUCCESS,
            tokens_used=100,
            cost_usd=0.001,
            latency_ms=500,
        )
        sample_state.add_result(result)
        assert "agent_a" in sample_state.agent_results
        assert sample_state.total_tokens == 100
        assert sample_state.total_cost_usd == 0.001

    def test_get_agent_output(self, sample_state):
        result = AgentResult(
            agent_id="agent_a",
            output={"key": "value"},
            status=AgentStatus.SUCCESS,
        )
        sample_state.add_result(result)
        assert sample_state.get_agent_output("agent_a") == {"key": "value"}
        assert sample_state.get_agent_output("nonexistent") == {}

    def test_mark_completed(self, sample_state):
        sample_state.mark_completed()
        assert sample_state.status == "completed"
        assert sample_state.completed_at is not None

    def test_mark_failed(self, sample_state):
        sample_state.mark_failed("test error")
        assert sample_state.status == "failed"
        assert sample_state.metadata["failure_reason"] == "test error"

    def test_get_context_for_agent(self, sample_state):
        result = AgentResult(
            agent_id="agent_a",
            summary="Agent A summary",
            confidence=0.9,
            status=AgentStatus.SUCCESS,
        )
        sample_state.add_result(result)
        context = sample_state.get_context_for_agent("agent_b")
        assert "input" in context
        assert "prior_results" in context
        assert "agent_a" in context["prior_results"]
