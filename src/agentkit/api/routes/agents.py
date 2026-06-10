"""Agent API routes."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/")
async def list_agents():
    """List all registered agents."""
    return {"agents": []}


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent details."""
    return {"agent_id": agent_id, "status": "not_implemented"}
