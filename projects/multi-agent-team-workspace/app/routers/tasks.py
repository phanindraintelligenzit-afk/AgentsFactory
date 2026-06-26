"""Task router for Multi-Agent Team Workspace."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from ..models.models import Task, TaskCreate, TaskUpdate, TaskStatus
from ..services.task_service import TaskService
from ..services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

audit = AuditService()
service = TaskService(audit)


@router.get("/", response_model=List[Task])
def list_tasks(status: Optional[str] = None):
    status_filter = None
    if status:
        try:
            status_filter = TaskStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    return service.list_all(status=status_filter)


@router.post("/", response_model=Task)
def create_task(data: TaskCreate):
    return service.create(data, actor="api")


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: str):
    task = service.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=Task)
def update_task(task_id: str, data: TaskUpdate):
    task = service.update(task_id, data, actor="api")
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/handoff")
def initiate_handoff(task_id: str, from_assignee: str, to_assignee: str, reason: str = ""):
    handoff = service.initiate_handoff(task_id, from_assignee, to_assignee, reason, actor="api")
    if not handoff:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "ok", "handoff_id": handoff.id}


@router.put("/{task_id}/handoff/{handoff_id}")
def respond_handoff(task_id: str, handoff_id: str, accept: bool):
    if accept:
        handoff = service.accept_handoff(handoff_id, actor="api")
    else:
        handoff = service.reject_handoff(handoff_id, actor="api")
    if not handoff:
        raise HTTPException(status_code=404, detail="Handoff not found")
    return {"status": "accepted" if accept else "rejected"}
