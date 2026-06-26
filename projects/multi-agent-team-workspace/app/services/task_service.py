"""Task service for Multi-Agent Team Workspace."""

import uuid
from datetime import datetime
from typing import List, Optional
from ..models.models import Task, TaskCreate, TaskUpdate, TaskStatus, Handoff
from .audit_service import AuditService


class TaskService:
    def __init__(self, audit: AuditService):
        self.tasks: dict[str, Task] = {}
        self.handoffs: dict[str, Handoff] = {}
        self.audit = audit

    def create(self, data: TaskCreate, actor: str = "system") -> Task:
        task = Task(
            id=str(uuid.uuid4())[:8],
            title=data.title,
            description=data.description,
            assignee_type=data.assignee_type,
            assignee_id=data.assignee_id,
        )
        self.tasks[task.id] = task
        self.audit.log("create_task", actor, task.id, f"Created: {task.title}")
        return task

    def get(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def list_all(self, status: Optional[TaskStatus] = None) -> List[Task]:
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    def update(self, task_id: str, data: TaskUpdate, actor: str = "system") -> Optional[Task]:
        task = self.tasks.get(task_id)
        if not task:
            return None
        if data.status:
            task.status = data.status
        if data.context is not None:
            task.context = data.context
        task.updated_at = datetime.now()
        self.audit.log("update_task", actor, task_id, f"Updated status to {task.status}")
        return task

    def assign(self, task_id: str, assignee_type, assignee_id: str, actor: str = "system") -> Optional[Task]:
        task = self.tasks.get(task_id)
        if not task:
            return None
        task.assignee_type = assignee_type
        task.assignee_id = assignee_id
        task.updated_at = datetime.now()
        self.audit.log("assign_task", actor, task_id, f"Assigned to {assignee_type}:{assignee_id}")
        return task

    def initiate_handoff(self, task_id: str, from_assignee: str, to_assignee: str, reason: str, actor: str = "system") -> Optional[Handoff]:
        task = self.tasks.get(task_id)
        if not task:
            return None
        handoff = Handoff(
            id=str(uuid.uuid4())[:8],
            task_id=task_id,
            from_assignee=from_assignee,
            to_assignee=to_assignee,
            reason=reason,
        )
        self.handoffs[handoff.id] = handoff
        task.status = TaskStatus.IN_REVIEW
        self.audit.log("initiate_handoff", actor, task_id, f"Handoff from {from_assignee} to {to_assignee}")
        return handoff

    def accept_handoff(self, handoff_id: str, actor: str = "system") -> Optional[Handoff]:
        handoff = self.handoffs.get(handoff_id)
        if not handoff:
            return None
        handoff.status = "accepted"
        task = self.tasks.get(handoff.task_id)
        if task:
            task.assignee_id = handoff.to_assignee
            task.status = TaskStatus.IN_PROGRESS
            task.updated_at = datetime.now()
        self.audit.log("accept_handoff", actor, handoff.task_id, f"Accepted handoff {handoff_id}")
        return handoff

    def reject_handoff(self, handoff_id: str, actor: str = "system") -> Optional[Handoff]:
        handoff = self.handoffs.get(handoff_id)
        if not handoff:
            return None
        handoff.status = "rejected"
        task = self.tasks.get(handoff.task_id)
        if task:
            task.status = TaskStatus.IN_PROGRESS
            task.updated_at = datetime.now()
        self.audit.log("reject_handoff", actor, handoff.task_id, f"Rejected handoff {handoff_id}")
        return handoff
