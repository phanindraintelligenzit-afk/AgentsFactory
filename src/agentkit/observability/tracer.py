"""Structured tracing and observability for multi-agent pipelines."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import structlog

from agentkit.models.pipeline import AgentResult, PipelineState

logger = structlog.get_logger("agentkit.tracer")


@dataclass
class Span:
    """A single operation span within a pipeline trace."""

    span_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    trace_id: str = ""
    agent_id: str = ""
    step: int = 0
    event: str = ""
    started_at: float = field(default_factory=time.time)
    completed_at: float = 0.0
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        end = self.completed_at or time.time()
        return (end - self.started_at) * 1000

    def to_dict(self) -> dict:
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "agent_id": self.agent_id,
            "step": self.step,
            "event": self.event,
            "duration_ms": round(self.duration_ms, 2),
            "data": self.data,
        }


class PipelineTracer:
    """Structured tracing for pipeline execution.

    Logs every agent call, decision, and error with a shared trace_id
    for end-to-end debugging.
    """

    def __init__(self):
        self._spans: list[Span] = []
        self._current_trace_id: str = ""

    def start_pipeline(self, state: PipelineState) -> None:
        """Start tracing a pipeline run."""
        self._current_trace_id = state.trace_id
        self._spans = []
        self.log_event(state, "pipeline_start", {
            "pipeline_id": state.pipeline_id,
            "input_length": len(state.original_input),
        })

    def end_pipeline(self, state: PipelineState) -> None:
        """End tracing a pipeline run."""
        self.log_event(state, "pipeline_end", {
            "pipeline_id": state.pipeline_id,
            "status": state.status,
            "total_tokens": state.total_tokens,
            "total_cost_usd": round(state.total_cost_usd, 6),
            "total_latency_ms": round(state.total_latency_ms, 2),
            "agents_executed": len(state.agent_results),
        })

    def log_event(
        self,
        state: PipelineState,
        event: str,
        data: dict[str, Any] | None = None,
    ) -> Span:
        """Log a pipeline event."""
        span = Span(
            trace_id=state.trace_id,
            event=event,
            step=state.current_step,
            data=data or {},
        )
        self._spans.append(span)

        logger.info(
            f"pipeline.{event}",
            trace_id=span.trace_id,
            step=span.step,
            **(data or {}),
        )
        return span

    def log_error(self, state: PipelineState, error: str) -> None:
        """Log a pipeline error."""
        logger.error(
            "pipeline.error",
            trace_id=state.trace_id,
            error=error,
            step=state.current_step,
        )

    def get_trace(self) -> list[dict]:
        """Get the full trace as a list of span dicts."""
        return [span.to_dict() for span in self._spans]

    def get_summary(self, state: PipelineState) -> dict:
        """Get a summary of the pipeline execution."""
        return {
            "trace_id": state.trace_id,
            "pipeline_id": state.pipeline_id,
            "status": state.status,
            "total_spans": len(self._spans),
            "total_tokens": state.total_tokens,
            "total_cost_usd": round(state.total_cost_usd, 6),
            "total_latency_ms": round(state.total_latency_ms, 2),
            "agents": {
                aid: {
                    "status": r.status.value,
                    "confidence": r.confidence,
                    "latency_ms": round(r.latency_ms, 2),
                }
                for aid, r in state.agent_results.items()
            },
        }
