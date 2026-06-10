"""Tests for LLM-powered agents."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agentkit.agents.roles.llm_agents import (
    LLMAgent,
    ResearcherAgent,
    AnalyzerAgent,
    WriterAgent,
    EvaluatorAgent,
    SynthesizerAgent,
)
from agentkit.llm import LLMClient, LLMResponse
from agentkit.models.pipeline import PipelineState
from agentkit.models.topology import AgentConfig


@pytest.fixture
def mock_llm_client():
    client = AsyncMock(spec=LLMClient)
    client.chat.return_value = LLMResponse(
        content="Test response content",
        model="openrouter/owl-alpha",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost_usd=0.0,
        latency_ms=500,
    )
    client.chat_json.return_value = {
        "scores": {"accuracy": 8, "completeness": 7, "clarity": 9, "relevance": 8},
        "overall_score": 8.0,
        "feedback": "Good quality output",
        "passed": True,
    }
    return client


@pytest.fixture
def researcher_config():
    return AgentConfig(
        agent_id="researcher",
        role="researcher",
        model="openrouter/owl-alpha",
    )


@pytest.fixture
def evaluator_config():
    return AgentConfig(
        agent_id="evaluator",
        role="evaluator",
        model="openrouter/owl-alpha",
    )


class TestLLMAgent:
    def test_build_messages(self, researcher_config):
        agent = LLMAgent(config=researcher_config)
        context = {
            "input": "Test input",
            "constraints": ["constraint1"],
            "prior_results": {"prior_agent": {"summary": "Prior summary"}},
        }
        messages = agent._build_messages(context, PipelineState(original_input="test"))
        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert any(m["role"] == "user" for m in messages)

    async def test_run_returns_result(self, researcher_config, mock_llm_client):
        agent = LLMAgent(config=researcher_config)
        LLMAgent.set_client(mock_llm_client)

        context = {"input": "Test", "constraints": []}
        state = PipelineState(original_input="Test")
        result = await agent._run(context, state)

        assert "result" in result
        assert "confidence" in result
        assert "tokens_used" in result
        assert "cost_usd" in result
        mock_llm_client.chat.assert_called_once()


class TestResearcherAgent:
    def test_default_prompt_contains_research(self, researcher_config):
        agent = ResearcherAgent(config=researcher_config)
        prompt = agent._default_system_prompt()
        assert "research" in prompt.lower()


class TestEvaluatorAgent:
    def test_default_prompt_contains_criteria(self, evaluator_config):
        agent = EvaluatorAgent(config=evaluator_config)
        prompt = agent._default_system_prompt()
        assert "accuracy" in prompt.lower()
        assert "completeness" in prompt.lower()

    async def test_run_returns_score(self, evaluator_config, mock_llm_client):
        agent = EvaluatorAgent(config=evaluator_config)
        LLMAgent.set_client(mock_llm_client)

        context = {"input": "Test", "constraints": []}
        state = PipelineState(original_input="Test")
        result = await agent._run(context, state)

        assert "score" in result
        assert "passed" in result
        assert "feedback" in result
