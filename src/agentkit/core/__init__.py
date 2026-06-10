"""Core framework modules."""

from agentkit.core.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerRegistry
from agentkit.core.context import ContextBudget, ContextManager
from agentkit.core.fallback import FallbackChain, FallbackLevel, FallbackManager
from agentkit.core.hitl import HITLManager, GateType, GateDecision, GateResult
from agentkit.core.permissions import ToolAccessMatrix, PermissionScope, ROLE_TEMPLATES

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerRegistry",
    "ContextBudget",
    "ContextManager",
    "FallbackChain",
    "FallbackLevel",
    "FallbackManager",
    "HITLManager",
    "GateType",
    "GateDecision",
    "GateResult",
    "ToolAccessMatrix",
    "PermissionScope",
    "ROLE_TEMPLATES",
]
