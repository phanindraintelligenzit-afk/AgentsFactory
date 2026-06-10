"""Permission scoping and tool access control for agents.

Implements least-privilege access control where each agent gets only
the tools and data its role requires — nothing more.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# Standard tool categories
TOOL_CATEGORIES = {
    "web_search": "Search the web for information",
    "web_fetch": "Fetch and extract content from URLs",
    "code_execution": "Execute code in a sandboxed environment",
    "file_read": "Read files from the filesystem",
    "file_write": "Write files to the filesystem",
    "file_search": "Search for files by name or content",
    "database_read": "Read from the database",
    "database_write": "Write to the database",
    "external_api": "Call external APIs",
    "message_send": "Send messages to users or channels",
    "llm_call": "Call LLM APIs",
    "memory_read": "Read from persistent memory",
    "memory_write": "Write to persistent memory",
}

# Predefined role templates
ROLE_TEMPLATES = {
    "researcher": {
        "description": "Gathers information from various sources",
        "tools": ["web_search", "web_fetch", "file_read", "database_read", "llm_call"],
    },
    "analyzer": {
        "description": "Analyzes data and produces insights",
        "tools": ["code_execution", "file_read", "database_read", "llm_call"],
    },
    "writer": {
        "description": "Produces written output",
        "tools": ["file_write", "llm_call"],
    },
    "evaluator": {
        "description": "Evaluates output quality against criteria",
        "tools": ["file_read", "llm_call"],
    },
    "publisher": {
        "description": "Publishes or distributes final output",
        "tools": ["file_write", "external_api", "message_send", "database_write"],
    },
    "orchestrator": {
        "description": "Coordinates other agents",
        "tools": ["database_read", "database_write", "llm_call", "memory_read", "memory_write"],
    },
    "synthesizer": {
        "description": "Combines outputs from multiple agents",
        "tools": ["file_read", "file_write", "llm_call"],
    },
}


@dataclass
class ToolAccessMatrix:
    """Defines which tools each agent role can access."""

    _permissions: dict[str, list[str]] = field(default_factory=dict)

    def grant(self, agent_id: str, tools: list[str]) -> None:
        """Grant a set of tools to an agent."""
        self._permissions[agent_id] = list(set(tools))

    def revoke(self, agent_id: str, tools: list[str]) -> None:
        """Revoke specific tools from an agent."""
        if agent_id in self._permissions:
            self._permissions[agent_id] = [
                t for t in self._permissions[agent_id] if t not in tools
            ]

    def can_use(self, agent_id: str, tool: str) -> bool:
        """Check if an agent can use a specific tool."""
        allowed = self._permissions.get(agent_id, [])
        return tool in allowed

    def get_allowed_tools(self, agent_id: str) -> list[str]:
        """Get the list of tools an agent can use."""
        return self._permissions.get(agent_id, [])

    def validate_tools(self, agent_id: str, requested_tools: list[str]) -> dict[str, Any]:
        """Validate a set of requested tools against permissions.

        Returns:
            allowed: list of allowed tools
            denied: list of denied tools
        """
        allowed = self.get_allowed_tools(agent_id)
        return {
            "allowed": [t for t in requested_tools if t in allowed],
            "denied": [t for t in requested_tools if t not in allowed],
        }

    @classmethod
    def from_role_templates(cls, agent_roles: dict[str, str]) -> ToolAccessMatrix:
        """Create a matrix from role templates.

        Args:
            agent_roles: mapping of agent_id → role_name
        """
        matrix = cls()
        for agent_id, role in agent_roles.items():
            if role in ROLE_TEMPLATES:
                matrix.grant(agent_id, ROLE_TEMPLATES[role]["tools"])
            else:
                # Unknown role — no tools by default (least privilege)
                matrix.grant(agent_id, [])
        return matrix

    def to_dict(self) -> dict:
        return dict(self._permissions)


@dataclass
class PermissionScope:
    """Scoped permission token for an agent instance.

    Each agent gets a scope that defines:
    - What tools it can use
    - What data it can read/write
    - What other agents it can communicate with
    """

    agent_id: str
    role: str = ""
    allowed_tools: list[str] = field(default_factory=list)
    allowed_data_sources: list[str] = field(default_factory=list)
    can_initiate_hitl: bool = False
    max_tokens_per_call: int = 4000
    max_retries: int = 2

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "allowed_tools": self.allowed_tools,
            "allowed_data_sources": self.allowed_data_sources,
            "can_initiate_hitl": self.can_initiate_hitl,
            "max_tokens_per_call": self.max_tokens_per_call,
            "max_retries": self.max_retries,
        }
