"""Tests for circuit breaker."""

import pytest
from agentkit.core.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerRegistry


class TestCircuitBreaker:
    def test_starts_closed(self, circuit_breaker):
        assert circuit_breaker.state.value == "closed"
        assert circuit_breaker.can_execute() is True

    def test_trips_after_failures(self, circuit_breaker):
        for _ in range(3):
            circuit_breaker.record_failure()
        assert circuit_breaker.state.value == "open"
        assert circuit_breaker.can_execute() is False

    def test_success_resets_failure_count(self, circuit_breaker):
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        circuit_breaker.record_success()
        assert circuit_breaker._failure_count == 0

    def test_manual_trip(self, circuit_breaker):
        circuit_breaker.trip()
        assert circuit_breaker.is_tripped

    def test_manual_reset(self, circuit_breaker):
        circuit_breaker.trip()
        circuit_breaker.reset()
        assert circuit_breaker.state.value == "closed"
        assert circuit_breaker.can_execute() is True

    def test_failure_rate_calculation(self, circuit_breaker):
        circuit_breaker.record_failure()
        circuit_breaker.record_success()
        circuit_breaker.record_failure()
        assert circuit_breaker.failure_rate == pytest.approx(0.67, rel=0.1)

    def test_to_dict(self, circuit_breaker):
        d = circuit_breaker.to_dict()
        assert "agent_id" in d
        assert "state" in d
        assert "failure_rate" in d


class TestCircuitBreakerRegistry:
    def test_get_or_create(self):
        reg = CircuitBreakerRegistry()
        cb = reg.get_or_create("agent_1")
        assert cb.agent_id == "agent_1"
        # Same agent returns same breaker
        cb2 = reg.get_or_create("agent_1")
        assert cb is cb2

    def test_reset_all(self):
        reg = CircuitBreakerRegistry()
        cb1 = reg.get_or_create("a1")
        cb2 = reg.get_or_create("a2")
        cb1.trip()
        cb2.trip()
        reg.reset_all()
        assert cb1.state.value == "closed"
        assert cb2.state.value == "closed"
