"""Circuit breaker implementation for agent failure management.

Implements the CLOSED → OPEN → HALF-OPEN state machine pattern
to prevent cascading failures in multi-agent pipelines.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional

from agentkit.models.pipeline import CircuitState


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker."""

    failure_threshold: int = 3  # Failures before tripping to OPEN
    recovery_timeout_seconds: int = 60  # Time in OPEN before trying HALF_OPEN
    success_threshold: int = 1  # Successes in HALF_OPEN to return to CLOSED
    rolling_window_size: int = 5  # Number of recent calls to track


@dataclass
class CircuitBreaker:
    """Per-agent circuit breaker with thread-safe state management.

    State machine:
        CLOSED (normal) → OPEN (failing) → HALF-OPEN (testing) → CLOSED

    Usage:
        cb = CircuitBreaker("researcher")
        if cb.can_execute():
            try:
                result = call_agent()
                cb.record_success()
            except Exception:
                cb.record_failure()
        else:
            # Circuit is open, use fallback
            pass
    """

    agent_id: str
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)

    _state: CircuitState = CircuitState.CLOSED
    _failure_count: int = 0
    _success_count: int = 0
    _last_failure_time: float = 0.0
    _recent_calls: list[bool] = field(default_factory=list)
    _lock: Lock = field(default_factory=Lock)

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def is_tripped(self) -> bool:
        return self._state == CircuitState.OPEN

    def can_execute(self) -> bool:
        """Check if the agent can be called."""
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return True
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has elapsed
                if time.time() - self._last_failure_time >= self.config.recovery_timeout_seconds:
                    self._transition_to(CircuitState.HALF_OPEN)
                    return True
                return False
            if self._state == CircuitState.HALF_OPEN:
                return True
            return False

    def record_success(self) -> None:
        """Record a successful execution."""
        with self._lock:
            self._recent_calls.append(True)
            if len(self._recent_calls) > self.config.rolling_window_size:
                self._recent_calls.pop(0)

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed execution."""
        with self._lock:
            self._recent_calls.append(False)
            if len(self._recent_calls) > self.config.rolling_window_size:
                self._recent_calls.pop(0)

            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Failed during recovery → back to OPEN
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)

    def trip(self) -> None:
        """Manually trip the circuit breaker."""
        with self._lock:
            self._transition_to(CircuitState.OPEN)
            self._last_failure_time = time.time()

    def reset(self) -> None:
        """Manually reset to CLOSED."""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)

    def _transition_to(self, new_state: CircuitState) -> None:
        old_state = self._state
        self._state = new_state
        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._success_count = 0

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate over the rolling window."""
        if not self._recent_calls:
            return 0.0
        failures = sum(1 for call in self._recent_calls if not call)
        return failures / len(self._recent_calls)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "failure_rate": round(self.failure_rate, 2),
            "last_failure_time": self._last_failure_time,
        }


class CircuitBreakerRegistry:
    """Registry of circuit breakers for all agents in a pipeline."""

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_or_create(
        self, agent_id: str, config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        if agent_id not in self._breakers:
            self._breakers[agent_id] = CircuitBreaker(
                agent_id=agent_id,
                config=config or CircuitBreakerConfig(),
            )
        return self._breakers[agent_id]

    def get(self, agent_id: str) -> Optional[CircuitBreaker]:
        return self._breakers.get(agent_id)

    def reset_all(self) -> None:
        for breaker in self._breakers.values():
            breaker.reset()

    def to_dict(self) -> dict:
        return {aid: cb.to_dict() for aid, cb in self._breakers.items()}
