"""Eval API routes."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/evals", tags=["evals"])


@router.post("/run")
async def run_eval(request: dict):
    """Run an eval suite."""
    return {"status": "not_implemented", "message": "Coming in Sprint 3"}


@router.get("/suites")
async def list_suites():
    """List all eval suites."""
    return {"suites": []}
