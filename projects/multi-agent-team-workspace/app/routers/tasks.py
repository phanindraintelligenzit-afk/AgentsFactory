"""Task router for Multi-Agent Team Workspace."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from ..models.models import Task, TaskCreate, TaskUpdate, TaskStatus, Handoff, HandoffCreate
from ..services.task_service import TaskService

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

_task_service: Optional[TaskService] = None


def set_task_service(svc: TaskService) -> None:
    global _task_service
    _task_service = svc


def _svc() -> TaskService:
    if _task_service is None:
        raise RuntimeError("TaskService not initialised")
    return _task_service


@router.get("/", response_model=List[Task])
def list_tasks(status: Optional[str] = None):
    status_filter = None
    if status:
        try:
            status_filter = TaskStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    return _svc().list_all(status=status_filter)


@router.post("/", response_model=Task, status_code=201)
def create_task(data: TaskCreate):
    return _svc().create_task(data, actor="api")


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: str):
    task = _svc().get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=Task)
def update_task(task_id: str, payload: TaskUpdate, actor: str = "system"):
    task = _svc().update_task(task_id, payload, actor=actor)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/handoff", response_model=Handoff, status_code=201)
def initiate_handoff(task_id: str, payload: HandoffCreate, actor: str = "system"):
    task = _svc().get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    handoff = _svc().handoff_task(task_id, payload, actor=actor)
    if not handoff:
        raise HTTPException(status_code=500, detail="Handoff could not be created")
    return handoff


@router.put("/{task_id}/handoff/{handoff_id}", response_model=Handoff)
def resolve_handoff(task_id: str, handoff_id: str, actor: str = "system", body: dict = None):
    decision = (body or {}).get("decision", "accepted")
    if decision == "accepted":
        handoff = _svc().accept_handoff(handoff_id, actor=actor)
    else:
        handoff = _svc().reject_handoff(handoff_id, actor=actor)
    if handoff is None:
        raise HTTPException(status_code=404, detail="Handoff not found")
    return handoff
