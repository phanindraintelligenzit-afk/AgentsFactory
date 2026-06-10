"""Human-in-the-Loop (HITL) gate system.

Implements configurable escalation points where the pipeline pauses
for human review before proceeding with irreversible, high-impact,
or low-confidence actions.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from agentkit.models.pipeline import HITLGate, PipelineState


class GateType(str, Enum):
    BLOCKING = "blocking"  # Pipeline pauses, waits for human
    ADVISORY = "advisory"  # Pipeline continues, flags for async review
    SAMPLING = "sampling"  # Random X% of outputs reviewed


class GateDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    TIMEOUT = "timeout"
    PENDING = "pending"


@dataclass
class GateResult:
    """Result of a HITL gate evaluation."""

    gate_id: str
    decision: GateDecision = GateDecision.PENDING
    reviewer_notes: str = ""
    modified_output: Optional[dict[str, Any]] = None
    reviewed_at: Optional[float] = None
    timed_out: bool = False


@dataclass
class HITLManager:
    """Manages human-in-the-loop gates for a pipeline.

    Gate placement criteria:
    - Irreversibility: send email, delete records, publish content
    - High blast radius: affects >100 users or >$10k value
    - Low confidence: agent confidence < 0.7 or contradictory outputs
    - Novel situation: out-of-distribution input
    - Regulatory exposure: legal, medical, financial advice
    """

    _gates: dict[str, HITLGate] = field(default_factory=dict)
    _results: dict[str, GateResult] = field(default_factory=dict)

    def add_gate(self, gate: HITLGate) -> None:
        self._gates[gate.gate_id] = gate

    def remove_gate(self, gate_id: str) -> None:
        self._gates.pop(gate_id, None)

    def get_gate(self, gate_id: str) -> Optional[HITLGate]:
        return self._gates.get(gate_id)

    def evaluate_gates(self, state: PipelineState) -> list[dict[str, Any]]:
        """Evaluate all gates against the current pipeline state.

        Returns a list of gate evaluations that need human attention.
        """
        evaluations = []
        for gate in self._gates.values():
            if gate.step == state.current_step:
                evaluation = self._evaluate_single_gate(gate, state)
                evaluations.append(evaluation)
        return evaluations

    def _evaluate_single_gate(
        self, gate: HITLGate, state: PipelineState
    ) -> dict[str, Any]:
        """Evaluate a single gate against the pipeline state."""
        reasons = []

        # Check confidence
        current_result = None
        for result in state.agent_results.values():
            if result.step == gate.step:
                current_result = result
                break

        if current_result and current_result.confidence < 0.7:
            reasons.append(f"Low confidence: {current_result.confidence:.2f}")

        # Check for contradictions
        if self._detect_contradictions(state):
            reasons.append("Contradictory agent outputs detected")

        # Check cost overrun
        if state.total_cost_usd > 0.5:  # Configurable threshold
            reasons.append(f"Cost threshold exceeded: ${state.total_cost_usd:.4f}")

        return {
            "gate_id": gate.gate_id,
            "gate_type": gate.gate_type,
            "step": gate.step,
            "needs_review": len(reasons) > 0,
            "reasons": reasons,
            "current_state": {
                "step": state.current_step,
                "total_cost": state.total_cost_usd,
                "total_tokens": state.total_tokens,
                "agent_count": len(state.agent_results),
            },
        }

    def _detect_contradictions(self, state: PipelineState) -> bool:
        """Detect if any agent outputs contradict each other.

        Simple heuristic: check if any agent explicitly flagged contradiction.
        In production, this would use an LLM or semantic similarity check.
        """
        for result in state.agent_results.values():
            if result.output.get("contradiction_detected"):
                return True
        return False

    def approve(self, gate_id: str, notes: str = "") -> GateResult:
        """Approve a gate."""
        result = GateResult(
            gate_id=gate_id,
            decision=GateDecision.APPROVED,
            reviewer_notes=notes,
            reviewed_at=time.time(),
        )
        self._results[gate_id] = result
        if gate_id in self._gates:
            self._gates[gate_id].approved = True
        return result

    def reject(self, gate_id: str, notes: str = "") -> GateResult:
        """Reject a gate."""
        result = GateResult(
            gate_id=gate_id,
            decision=GateDecision.REJECTED,
            reviewer_notes=notes,
            reviewed_at=time.time(),
        )
        self._results[gate_id] = result
        if gate_id in self._gates:
            self._gates[gate_id].approved = False
        return result

    def check_timeouts(self) -> list[str]:
        """Check for gates that have timed out."""
        timed_out = []
        current_time = time.time()
        for gate_id, gate in self._gates.items():
            if gate_id not in self._results:
                # Gate hasn't been reviewed yet — check timeout
                # (In production, track when the gate was triggered)
                pass
        return timed_out

    def get_result(self, gate_id: str) -> Optional[GateResult]:
        return self._results.get(gate_id)

    def to_dict(self) -> dict:
        return {
            "gates": len(self._gates),
            "results": len(self._results),
            "pending": len(self._gates) - len(self._results),
        }
