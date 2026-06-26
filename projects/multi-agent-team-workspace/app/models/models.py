"""Pydantic models for Multi-Agent Team Workspace."""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel

class AssigneeType(str, Enum):
    HUMAN = "human"
    AGENT = "agent"

class TaskStatus(str, Enum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"

class Task(BaseModel):
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.BACKLOG
    assignee_type: AssigneeType = AssigneeType.HUMAN
    assignee_id: str = ""
    context: str = ""
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    assignee_type: AssigneeType = AssigneeType.HUMAN
    assignee_id: str = ""

class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    context: Optional[str] = None
    notes: Optional[str] = None

class Handoff(BaseModel):
    id: str
    task_id: str
    from_assignee: str
    to_assignee: str
    reason: str
    status: str = "pending"
    created_at: datetime = datetime.now()

class AuditEntry(BaseModel):
    action: str
    actor: str
    task_id: str
    details: str = ""
    timestamp: datetime = datetime.now()
