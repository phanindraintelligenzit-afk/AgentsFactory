"""Pipeline API routes."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.post("/run")
async def run_pipeline(request: dict):
    """Execute a pipeline."""
    return {"status": "not_implemented", "message": "Coming in Sprint 2"}


@router.get("/{pipeline_id}")
async def get_pipeline(pipeline_id: str):
    """Get pipeline status."""
    return {"pipeline_id": pipeline_id, "status": "not_implemented"}


@router.get("/{pipeline_id}/trace")
async def get_pipeline_trace(pipeline_id: str):
    """Get pipeline execution trace."""
    return {"pipeline_id": pipeline_id, "trace": []}
