"""Agent factory — build agents from configuration."""

from __future__ import annotations

from agentkit.agents.base import BaseAgent
from agentkit.core.context import ContextManager
from agentkit.core.permissions import PermissionScope
from agentkit.models.topology import AgentConfig


class AgentBuilder:
    """Builds agent instances from configuration.

    Usage:
        builder = AgentBuilder()
        agent = builder.build(agent_config, context_manager)
    """

    def __init__(self):
        self._agent_registry: dict[str, type[BaseAgent]] = {}

    def register(self, role: str, agent_class: type[BaseAgent]) -> None:
        """Register an agent class for a role."""
        self._agent_registry[role] = agent_class

    def build(
        self,
        config: AgentConfig,
        context_manager: ContextManager | None = None,
        permission_scope: PermissionScope | None = None,
    ) -> BaseAgent:
        """Build an agent from config.

        If a custom class is registered for the role, use it.
        Otherwise, return a BaseAgent (which will need _run overridden).
        """
        agent_class = self._agent_registry.get(config.role, BaseAgent)
        return agent_class(
            config=config,
            permission_scope=permission_scope,
            context_manager=context_manager,
        )

    def build_from_configs(
        self,
        configs: list[AgentConfig],
        context_manager: ContextManager | None = None,
    ) -> list[BaseAgent]:
        """Build multiple agents from a list of configs."""
        agents = []
        for config in configs:
            scope = None
            if config.allowed_tools:
                scope = PermissionScope(
                    agent_id=config.agent_id,
                    role=config.role,
                    allowed_tools=config.allowed_tools,
                )
            agent = self.build(config, context_manager, scope)
            agents.append(agent)
        return agents
