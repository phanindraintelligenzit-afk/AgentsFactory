"""Audit router -- REST API endpoints for the audit trail."""

from typing import List, Optional

from fastapi import APIRouter, Query

from app.models.models import AuditEntry
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

_audit_service: Optional[AuditService] = None


def set_audit_service(svc: AuditService) -> None:
    global _audit_service
    _audit_service = svc


def _svc() -> AuditService:
    if _audit_service is None:
        raise RuntimeError("AuditService not initialised")
    return _audit_service


@router.get("", response_model=List[AuditEntry])
def get_audit_trail(
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    actor: Optional[str] = Query(None, description="Filter by actor"),
):
    """Return the audit trail, optionally filtered by task_id and/or actor."""
    return _svc().get_trail(task_id=task_id, actor=actor)
