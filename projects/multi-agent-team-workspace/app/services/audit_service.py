"""Audit service for Multi-Agent Team Workspace."""
from datetime import datetime
from typing import List
from ..models.models import AuditEntry


class AuditService:
    def __init__(self):
        self.entries: List[AuditEntry] = []

    def log(self, action: str, actor: str, task_id: str, details: str = "") -> AuditEntry:
        entry = AuditEntry(action=action, actor=actor, task_id=task_id, details=details)
        self.entries.append(entry)
        return entry

    def get_trail(self, task_id: str = None, actor: str = None) -> List[AuditEntry]:
        results = self.entries
        if task_id:
            results = [e for e in results if e.task_id == task_id]
        if actor:
            results = [e for e in results if e.actor == actor]
        return results
