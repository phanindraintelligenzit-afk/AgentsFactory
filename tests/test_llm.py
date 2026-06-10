"""Tests for LLM client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agentkit.llm import LLMClient, LLMError, LLMResponse, MODEL_PRICING


class TestLLMClient:
    def test_init_defaults(self):
        client = LLMClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.default_model == "openrouter/owl-alpha"
        assert client.max_retries == 3

    def test_estimate_tokens(self):
        client = LLMClient(api_key="test")
        assert client.estimate_tokens("hello world") == 2
        assert client.estimate_tokens("a" * 400) == 100

    def test_calculate_cost_free_model(self):
        client = LLMClient(api_key="test")
        cost = client._calculate_cost("openrouter/owl-alpha", 1000, 500)
        assert cost == 0.0

    def test_calculate_cost_paid_model(self):
        client = LLMClient(api_key="test")
        cost = client._calculate_cost("anthropic/claude-sonnet-4", 1_000_000, 500_000)
        expected = (1_000_000 / 1_000_000 * 3.0) + (500_000 / 1_000_000 * 15.0)
        assert cost == pytest.approx(expected)

    def test_model_pricing_has_free_models(self):
        for model in ["openrouter/owl-alpha", "meta-llama/llama-3.3-70b-instruct:free"]:
            assert model in MODEL_PRICING
            assert MODEL_PRICING[model]["input"] == 0.0
            assert MODEL_PRICING[model]["output"] == 0.0


class TestLLMResponse:
    def test_total_token_count(self):
        resp = LLMResponse(
            content="test",
            model="test",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )
        assert resp.total_token_count == 150

    def test_total_token_count_fallback(self):
        resp = LLMResponse(
            content="test",
            model="test",
            prompt_tokens=100,
            completion_tokens=50,
        )
        assert resp.total_token_count == 150
