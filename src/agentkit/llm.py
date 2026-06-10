"""LLM client for OpenRouter API.

Handles all LLM calls with:
- Token counting and cost tracking
- Retry with exponential backoff
- Structured output parsing
- Model fallback support
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx
import structlog

from agentkit.config import settings

logger = structlog.get_logger("agentkit.llm")

# OpenRouter API endpoint
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Free model defaults (in priority order)
FREE_MODELS = [
    "openrouter/owl-alpha",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-001:free",
]

# Approximate pricing per 1M tokens (for cost tracking)
MODEL_PRICING: dict[str, dict[str, float]] = {
    "openrouter/owl-alpha": {"input": 0.0, "output": 0.0},
    "meta-llama/llama-3.3-70b-instruct:free": {"input": 0.0, "output": 0.0},
    "google/gemini-2.0-flash-001:free": {"input": 0.0, "output": 0.0},
    "anthropic/claude-sonnet-4": {"input": 3.0, "output": 15.0},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.6},
}


@dataclass
class LLMResponse:
    """Structured response from an LLM call."""

    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    finish_reason: str = ""
    raw_response: dict[str, Any] = field(default_factory=dict)

    @property
    def total_token_count(self) -> int:
        return self.total_tokens or (self.prompt_tokens + self.completion_tokens)


@dataclass
class LLMClient:
    """Async LLM client for OpenRouter.

    Usage:
        client = LLMClient()
        response = await client.chat(
            model="openrouter/owl-alpha",
            messages=[{"role": "user", "content": "Hello"}],
        )
        print(response.content)
        print(f"Tokens: {response.total_tokens}, Cost: ${response.cost_usd:.6f}")
    """

    api_key: str = ""
    base_url: str = OPENROUTER_BASE_URL
    default_model: str = "openrouter/owl-alpha"
    max_retries: int = 3
    retry_delay: float = 2.0
    timeout: float = 60.0

    def __post_init__(self):
        if not self.api_key:
            self.api_key = settings.openrouter_api_key
        if not self.default_model:
            self.default_model = "openrouter/owl-alpha"

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2000,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """Send a chat completion request.

        Args:
            messages: List of {role, content} dicts
            model: Model identifier (defaults to default_model)
            temperature: Sampling temperature
            max_tokens: Max tokens in response
            response_format: Optional structured output format (e.g., {"type": "json_object"})

        Returns:
            LLMResponse with content, tokens, cost, and latency
        """
        model = model or self.default_model
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/phanindraintelligenzit-afk/AgentsFactory",
            "X-Title": "AgentsFactory",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        start_time = time.time()
        last_error = None

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )

                    if resp.status_code == 429:
                        # Rate limited — wait and retry
                        wait = self.retry_delay * (2 ** attempt)
                        logger.warning("rate_limited", model=model, wait_seconds=wait)
                        time.sleep(wait)
                        continue

                    if resp.status_code == 401:
                        raise LLMError("Invalid OpenRouter API key. Check your .env file.")

                    if resp.status_code >= 400:
                        error_body = resp.text[:500]
                        logger.error("llm_error", status=resp.status_code, body=error_body)
                        if resp.status_code >= 500:
                            # Server error — retry
                            last_error = f"Server error {resp.status_code}: {error_body}"
                            time.sleep(self.retry_delay * (2 ** attempt))
                            continue
                        raise LLMError(f"HTTP {resp.status_code}: {error_body}")

                    data = resp.json()
                    elapsed_ms = (time.time() - start_time) * 1000

                    # Extract response
                    choice = data.get("choices", [{}])[0]
                    message = choice.get("message", {})
                    content = message.get("content", "")

                    # Extract usage
                    usage = data.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

                    # Calculate cost
                    cost = self._calculate_cost(model, prompt_tokens, completion_tokens)

                    return LLMResponse(
                        content=content,
                        model=data.get("model", model),
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        cost_usd=cost,
                        latency_ms=elapsed_ms,
                        finish_reason=choice.get("finish_reason", ""),
                        raw_response=data,
                    )

            except httpx.TimeoutException:
                last_error = "Request timed out"
                logger.warning("llm_timeout", model=model, attempt=attempt + 1)
                time.sleep(self.retry_delay * (2 ** attempt))
            except httpx.ConnectError:
                last_error = "Connection error"
                logger.warning("llm_connection_error", model=model, attempt=attempt + 1)
                time.sleep(self.retry_delay * (2 ** attempt))
            except LLMError:
                raise
            except Exception as e:
                last_error = str(e)
                logger.error("llm_unexpected_error", model=model, error=str(e))
                time.sleep(self.retry_delay * (2 ** attempt))

        raise LLMError(f"Failed after {self.max_retries} retries. Last error: {last_error}")

    async def chat_with_system(
        self,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Convenience method: single system + user message."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return await self.chat(messages, model, temperature, max_tokens)

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> dict[str, Any]:
        """Request JSON-structured output and parse it."""
        response = await self.chat(
            messages,
            model,
            temperature,
            max_tokens,
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate approximate cost in USD."""
        pricing = MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token for English)."""
        return len(text) // 4


class LLMError(Exception):
    """Error from LLM API call."""
    pass
