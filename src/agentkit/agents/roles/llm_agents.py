"""Real LLM-powered agents using OpenRouter.

Each agent extends BaseAgent and implements _run() with actual LLM calls.
They use the shared LLMClient for all API communication.
"""

from __future__ import annotations

import json
from typing import Any

import structlog

from agentkit.agents.base import BaseAgent
from agentkit.llm import LLMClient, LLMError
from agentkit.models.pipeline import PipelineState

logger = structlog.get_logger("agentkit.agents")


class LLMAgent(BaseAgent):
    """Base class for agents that use LLM calls.

    Provides:
    - Shared LLMClient instance
    - Standard message formatting
    - Error handling for LLM failures
    - Token/cost tracking from actual responses
    """

    _shared_client: LLMClient | None = None

    @classmethod
    def get_client(cls) -> LLMClient:
        if cls._shared_client is None:
            cls._shared_client = LLMClient()
        return cls._shared_client

    @classmethod
    def set_client(cls, client: LLMClient) -> None:
        cls._shared_client = client

    def _build_messages(
        self,
        context: dict[str, Any],
        state: PipelineState,
    ) -> list[dict[str, str]]:
        """Build messages for the LLM call from pipeline context."""
        messages = []

        # System prompt
        system = self.config.system_prompt or self._default_system_prompt()
        # Inject context into system prompt
        if "{input}" in system:
            system = system.format(input=context.get("input", ""))
        messages.append({"role": "system", "content": system})

        # Add prior results as context
        prior = context.get("prior_results", {})
        if prior:
            prior_text = "\n\n## Prior Agent Results\n"
            for agent_id, summary in prior.items():
                if isinstance(summary, dict):
                    prior_text += f"\n### {agent_id}\n{summary.get('summary', '')}"
                else:
                    prior_text += f"\n### {agent_id}\n{summary}"
            messages.append({"role": "user", "content": prior_text})

        # Add decisions if any
        decisions = context.get("decisions", [])
        if decisions:
            messages.append({
                "role": "user",
                "content": f"## Prior Decisions\n{json.dumps(decisions, indent=2)}",
            })

        # Main input
        user_input = context.get("input", "")
        if user_input and not self.config.system_prompt:
            messages.append({"role": "user", "content": user_input})

        return messages

    def _default_system_prompt(self) -> str:
        return f"You are a {self.config.role or 'helpful AI assistant'}."

    async def _run(
        self,
        context: dict[str, Any],
        state: PipelineState,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute the agent by calling the LLM."""
        client = self.get_client()
        messages = self._build_messages(context, state)

        try:
            response = await client.chat(
                messages=messages,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            logger.info(
                "agent_llm_call",
                agent_id=self.agent_id,
                model=response.model,
                tokens=response.total_tokens,
                cost=round(response.cost_usd, 6),
                latency_ms=round(response.latency_ms, 0),
            )

            return {
                "result": response.content,
                "confidence": 0.85,  # Default; subclasses can override
                "tokens_used": response.total_tokens,
                "cost_usd": response.cost_usd,
                "model": response.model,
            }

        except LLMError as e:
            logger.error("agent_llm_error", agent_id=self.agent_id, error=str(e))
            return {
                "result": f"Error: {str(e)}",
                "confidence": 0.0,
                "tokens_used": 0,
                "cost_usd": 0.0,
                "error": str(e),
            }


class ResearcherAgent(LLMAgent):
    """Agent that gathers and synthesizes information."""

    def _default_system_prompt(self) -> str:
        return (
            "You are a research analyst. Your job is to gather, analyze, and synthesize "
            "information on the given topic. Provide comprehensive, well-structured findings "
            "with specific details and evidence. Be objective and thorough.\n\n"
            "Format your response as a clear analysis with key findings."
        )

    async def _run(self, context: dict, state: PipelineState, **kwargs) -> dict:
        result = await super()._run(context, state, **kwargs)
        result["confidence"] = 0.85
        result["sources"] = []  # In production, would extract from response
        return result


class AnalyzerAgent(LLMAgent):
    """Agent that analyzes data and identifies patterns/risks."""

    def _default_system_prompt(self) -> str:
        return (
            "You are a data analyst. Your job is to analyze the provided information, "
            "identify patterns, risks, and insights. Provide structured analysis with:\n"
            "1. Key findings\n"
            "2. Risks and concerns\n"
            "3. Recommendations\n\n"
            "Be specific and data-driven in your analysis."
        )

    async def _run(self, context: dict, state: PipelineState, **kwargs) -> dict:
        result = await super()._run(context, state, **kwargs)
        result["confidence"] = 0.8
        return result


class WriterAgent(LLMAgent):
    """Agent that produces written output based on research and analysis."""

    def _default_system_prompt(self) -> str:
        return (
            "You are a professional writer. Your job is to produce clear, well-structured "
            "written content based on the provided research and analysis. "
            "Adapt your writing style to the audience and purpose.\n\n"
            "Prioritize clarity, accuracy, and engagement."
        )

    async def _run(self, context: dict, state: PipelineState, **kwargs) -> dict:
        result = await super()._run(context, state, **kwargs)
        result["confidence"] = 0.9
        result["format"] = "markdown"
        return result


class EvaluatorAgent(LLMAgent):
    """Agent that evaluates output quality against criteria."""

    def _default_system_prompt(self) -> str:
        return (
            "You are a quality evaluator. Your job is to evaluate the provided output "
            "against these criteria:\n"
            "1. Accuracy (0-10): Is the information correct?\n"
            "2. Completeness (0-10): Does it cover all required aspects?\n"
            "3. Clarity (0-10): Is it well-written and easy to understand?\n"
            "4. Relevance (0-10): Is it on-topic and useful?\n\n"
            "Respond with JSON: {\"scores\": {\"accuracy\": N, \"completeness\": N, "
            "\"clarity\": N, \"relevance\": N}, \"overall_score\": N, \"feedback\": \"...\", "
            "\"passed\": true/false}"
        )

    async def _run(self, context: dict, state: PipelineState, **kwargs) -> dict:
        client = self.get_client()
        messages = self._build_messages(context, state)

        try:
            eval_result = await client.chat_json(
                messages=messages,
                model=self.config.model,
                temperature=0.0,
                max_tokens=1000,
            )

            overall = eval_result.get("overall_score", 0.0)
            if isinstance(overall, (int, float)):
                overall = overall / 10.0  # Normalize to 0-1

            return {
                "result": eval_result,
                "score": overall,
                "feedback": eval_result.get("feedback", ""),
                "passed": eval_result.get("passed", overall >= 0.7),
                "confidence": 0.9,
                "tokens_used": 0,  # Would track from response
                "cost_usd": 0.0,
            }

        except (LLMError, json.JSONDecodeError) as e:
            return {
                "result": {"error": str(e)},
                "score": 0.0,
                "feedback": f"Evaluation failed: {str(e)}",
                "passed": False,
                "confidence": 0.0,
                "tokens_used": 0,
                "cost_usd": 0.0,
                "error": str(e),
            }


class SynthesizerAgent(LLMAgent):
    """Agent that combines outputs from multiple parallel agents."""

    def _default_system_prompt(self) -> str:
        return (
            "You are a synthesis expert. Your job is to combine and reconcile outputs "
            "from multiple agents into a single, coherent result. "
            "Identify areas of agreement and disagreement. "
            "Produce a unified output that captures the best insights from all sources.\n\n"
            "Be explicit about any contradictions and how you resolved them."
        )

    async def _run(self, context: dict, state: PipelineState, **kwargs) -> dict:
        # Build a special context that includes full prior results
        prior = context.get("prior_results", {})
        if prior:
            synthesis_input = "## Outputs to Synthesize\n\n"
            for agent_id, summary in prior.items():
                if isinstance(summary, dict):
                    synthesis_input += f"\n### {agent_id}\n{summary.get('summary', '')}\n"
                else:
                    synthesis_input += f"\n### {agent_id}\n{summary}\n"

            messages = [
                {"role": "system", "content": self._default_system_prompt()},
                {"role": "user", "content": synthesis_input},
            ]

            client = self.get_client()
            try:
                response = await client.chat(
                    messages=messages,
                    model=self.config.model,
                    temperature=0.0,
                    max_tokens=self.config.max_tokens,
                )
                return {
                    "result": response.content,
                    "confidence": 0.85,
                    "tokens_used": response.total_tokens,
                    "cost_usd": response.cost_usd,
                    "model": response.model,
                }
            except LLMError as e:
                return {
                    "result": f"Synthesis failed: {str(e)}",
                    "confidence": 0.0,
                    "tokens_used": 0,
                    "cost_usd": 0.0,
                    "error": str(e),
                }

        return await super()._run(context, state, **kwargs)
