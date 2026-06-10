"""Placeholder agent roles — override _run() with actual LLM calls."""

from __future__ import annotations

from agentkit.agents.base import BaseAgent


class ResearcherAgent(BaseAgent):
    """Agent that gathers information from various sources."""

    async def _run(self, context: dict, state, **kwargs) -> dict:
        return {
            "result": f"Research output for: {context.get('input', '')[:100]}",
            "sources": [],
            "confidence": 0.85,
            "tokens_used": 0,
            "cost_usd": 0.0,
        }


class AnalyzerAgent(BaseAgent):
    """Agent that analyzes data and produces insights."""

    async def _run(self, context: dict, state, **kwargs) -> dict:
        return {
            "findings": f"Analysis of: {context.get('input', '')[:100]}",
            "risks": [],
            "confidence": 0.8,
            "tokens_used": 0,
            "cost_usd": 0.0,
        }


class WriterAgent(BaseAgent):
    """Agent that produces written output."""

    async def _run(self, context: dict, state, **kwargs) -> dict:
        return {
            "draft": f"Draft based on: {context.get('input', '')[:100]}",
            "format": "markdown",
            "confidence": 0.9,
            "tokens_used": 0,
            "cost_usd": 0.0,
        }


class EvaluatorAgent(BaseAgent):
    """Agent that evaluates output quality against criteria."""

    async def _run(self, context: dict, state, **kwargs) -> dict:
        return {
            "score": 0.85,
            "feedback": "Meets quality criteria",
            "passed": True,
            "confidence": 0.9,
            "tokens_used": 0,
            "cost_usd": 0.0,
        }
