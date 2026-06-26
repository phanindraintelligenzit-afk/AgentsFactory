"""Pytest tests for Multi-Agent Team Workspace."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.models import AssigneeType, HandoffCreate, HandoffStatus, TaskCreate, TaskStatus, TaskUpdate
from app.services.audit_service import AuditService
from app.services.task_service import TaskService


# --- Fixtures ---

@pytest.fixture
def fresh_services():
    """Provide a fresh pair of services for isolated tests."""
    audit = AuditService()
    tasks = TaskService(audit)
    return audit, tasks


@pytest.fixture
def client():
    """FastAPI test client (uses the app-level singletons)."""
    return TestClient(app)


# --- Unit tests (direct service calls) ---

class TestCreateTask:
    def test_create_task_basic(self, fresh_services):
        audit, svc = fresh_services
        payload = TaskCreate(title="Write docs", description="Document the API", assignee_type=AssigneeType.human, assignee_id="alice")
        task = svc.create_task(payload)
        assert task.id
        assert task.title == "Write docs"
        assert task.status == TaskStatus.backlog
        assert task.assignee_type == AssigneeType.human
        assert task.assignee_id == "alice"

    def test_create_task_defaults(self, fresh_services):
        audit, svc = fresh_services
        payload = TaskCreate(title="Bug fix")
        task = svc.create_task(payload)
        assert task.assignee_type == AssigneeType.human
        assert task.assignee_id == "unassigned"
        assert task.description == ""


class TestAssignTask:
    def test_assign_to_agent(self, fresh_services):
        audit, svc = fresh_services
        payload = TaskCreate(title="Review PR", assignee_type=AssigneeType.human, assignee_id="bob")
        task = svc.create_task(payload)
        updated = svc.assign_task(task.id, AssigneeType.agent, "code-reviewer-agent", actor="bob")
        assert updated.assignee_type == AssigneeType.agent
        assert updated.assignee_id == "code-reviewer-agent"

    def test_assign_to_human(self, fresh_services):
        audit, svc = fresh_services
        payload = TaskCreate(title="Deploy", assignee_type=AssigneeType.agent, assignee_id="deploy-bot")
        task = svc.create_task(payload)
        updated = svc.assign_task(task.id, AssigneeType.human, "carol", actor="deploy-bot")
        assert updated.assignee_type == AssigneeType.human
        assert updated.assignee_id == "carol"

    def test_assign_nonexistent_task(self, fresh_services):
        audit, svc = fresh_services
        result = svc.assign_task("fake-id", AssigneeType.human, "dave")
        assert result is None


class TestHandoffFlow:
    def test_handoff_task(self, fresh_services):
        audit, svc = fresh_services
        task = svc.create_task(TaskCreate(title="Research", assignee_type=AssigneeType.human, assignee_id="eve"))
        handoff = svc.handoff_task(
            task.id,
            HandoffCreate(to_assignee_type=AssigneeType.agent, to_assignee_id="research-agent", reason="Needs ML expertise"),
            actor="eve",
        )
        assert handoff is not None
        assert handoff.status == HandoffStatus.pending
        assert handoff.from_assignee_id == "eve"
        assert handoff.to_assignee_id == "research-agent"

    def test_accept_handoff_reassigns_task(self, fresh_services):
        audit, svc = fresh_services
        task = svc.create_task(TaskCreate(title="Analyze", assignee_type=AssigneeType.human, assignee_id="frank"))
        handoff = svc.handoff_task(
            task.id,
            HandoffCreate(to_assignee_type=AssigneeType.agent, to_assignee_id="analysis-agent", reason="Needs data crunching"),
            actor="frank",
        )
        accepted = svc.accept_handoff(handoff.id, actor="analysis-agent")
        assert accepted.status == HandoffStatus.accepted
        updated_task = svc.get_task(task.id)
        assert updated_task.assignee_type == AssigneeType.agent
        assert updated_task.assignee_id == "analysis-agent"

    def test_reject_handoff_keeps_original_assignee(self, fresh_services):
        audit, svc = fresh_services
        task = svc.create_task(TaskCreate(title="Design", assignee_type=AssigneeType.agent, assignee_id="design-agent"))
        handoff = svc.handoff_task(
            task.id,
            HandoffCreate(to_assignee_type=AssigneeType.human, to_assignee_id="gina", reason="Needs creative direction"),
            actor="design-agent",
        )
        rejected = svc.reject_handoff(handoff.id, actor="gina")
        assert rejected.status == HandoffStatus.rejected
        updated_task = svc.get_task(task.id)
        assert updated_task.assignee_type == AssigneeType.agent
        assert updated_task.assignee_id == "design-agent"

    def test_cannot_accept_non_pending_handoff(self, fresh_services):
        audit, svc = fresh_services
        task = svc.create_task(TaskCreate(title="Test", assignee_type=AssigneeType.human, assignee_id="hank"))
        handoff = svc.handoff_task(
            task.id,
            HandoffCreate(to_assignee_type=AssigneeType.agent, to_assignee_id="test-agent", reason="Automate testing"),
            actor="hank",
        )
        svc.accept_handoff(handoff.id)
        result = svc.accept_handoff(handoff.id)
        assert result is None


class TestAuditTrail:
    def test_create_task_logs_audit(self, fresh_services):
        audit, svc = fresh_services
        svc.create_task(TaskCreate(title="Audit test", assignee_type=AssigneeType.human, assignee_id="ivan"))
        trail = audit.get_trail(task_id=None, actor="ivan")
        assert any(e.action == "task_created" for e in trail)

    def test_update_task_logs_audit(self, fresh_services):
        audit, svc = fresh_services
        task = svc.create_task(TaskCreate(title="Update test"))
        svc.update_task(task.id, TaskUpdate(status=TaskStatus.in_progress), actor="system")
        trail = audit.get_trail(task_id=task.id)
        assert any(e.action == "task_updated" for e in trail)

    def test_handoff_logs_audit(self, fresh_services):
        audit, svc = fresh_services
        task = svc.create_task(TaskCreate(title="Handoff audit", assignee_type=AssigneeType.human, assignee_id="jill"))
        svc.handoff_task(
            task.id,
            HandoffCreate(to_assignee_type=AssigneeType.agent, to_assignee_id="agent-x", reason="Test"),
            actor="jill",
        )
        trail = audit.get_trail(task_id=task.id)
        actions = [e.action for e in trail]
        assert "task_created" in actions
        assert "handoff_initiated" in actions

    def test_filter_audit_by_task(self, fresh_services):
        audit, svc = fresh_services
        t1 = svc.create_task(TaskCreate(title="Task 1"))
        t2 = svc.create_task(TaskCreate(title="Task 2"))
        trail1 = audit.get_trail(task_id=t1.id)
        trail2 = audit.get_trail(task_id=t2.id)
        assert all(e.task_id == t1.id for e in trail1)
        assert all(e.task_id == t2.id for e in trail2)


class TestUpdateTaskStatus:
    def test_update_status(self, fresh_services):
        audit, svc = fresh_services
        task = svc.create_task(TaskCreate(title="Status test"))
        updated = svc.update_task(task.id, TaskUpdate(status=TaskStatus.in_progress))
        assert updated.status == TaskStatus.in_progress

    def test_update_context_and_notes(self, fresh_services):
        audit, svc = fresh_services
        task = svc.create_task(TaskCreate(title="Context test"))
        updated = svc.update_task(task.id, TaskUpdate(context="Important context", notes="See doc X"))
        assert updated.context == "Important context"
        assert updated.notes == "See doc X"

    def test_update_nonexistent_task(self, fresh_services):
        audit, svc = fresh_services
        result = svc.update_task("fake", TaskUpdate(status=TaskStatus.done))
        assert result is None


# --- Integration tests (via HTTP client) ---

class TestHTTPEndpoints:
    def test_create_and_list_tasks(self, client):
        res = client.post("/api/v1/tasks", json={
            "title": "Integration test task",
            "description": "Created via HTTP",
            "assignee_type": "agent",
            "assignee_id": "test-agent",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Integration test task"
        assert data["assignee_type"] == "agent"

    def test_get_task_detail(self, client):
        res = client.post("/api/v1/tasks", json={"title": "Detail test", "description": "Check details"})
        task_id = res.json()["id"]
        detail = client.get(f"/api/v1/tasks/{task_id}")
        assert detail.status_code == 200
        assert detail.json()["title"] == "Detail test"

    def test_update_task_via_http(self, client):
        res = client.post("/api/v1/tasks", json={"title": "Update via HTTP"})
        task_id = res.json()["id"]
        updated = client.put(f"/api/v1/tasks/{task_id}?actor=tester", json={
            "status": "in_progress",
            "context": "Now working on it",
        })
        assert updated.status_code == 200
        assert updated.json()["status"] == "in_progress"

    def test_handoff_via_http(self, client):
        res = client.post("/api/v1/tasks", json={
            "title": "Handoff via HTTP",
            "assignee_type": "human",
            "assignee_id": "kate",
        })
        task_id = res.json()["id"]
        handoff = client.post(f"/api/v1/tasks/{task_id}/handoff?actor=kate", json={
            "to_assignee_type": "agent",
            "to_assignee_id": "agent-y",
            "reason": "Needs automation",
        })
        assert handoff.status_code == 201
        handoff_id = handoff.json()["id"]
        accepted = client.put(f"/api/v1/tasks/{task_id}/handoff/{handoff_id}?actor=agent-y", json={
            "decision": "accepted",
        })
        assert accepted.status_code == 200
        assert accepted.json()["status"] == "accepted"

    def test_audit_trail_via_http(self, client):
        client.post("/api/v1/tasks", json={"title": "Audit HTTP"})
        res = client.get("/api/v1/audit")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_404_for_missing_task(self, client):
        res = client.get("/api/v1/tasks/nonexistent-id")
        assert res.status_code == 404

    def test_dashboard_page(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert "Multi-Agent" in res.text

    def test_health_check(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"
