# Multi-Agent Team Workspace

A workspace where tasks are assigned to **humans OR AI agents** — with shared context, handoff protocols, and audit trails. Think Linear/Asana for mixed human-agent teams.

## Architecture

```
+-----------------------------------------------+
|                  FastAPI App                    |
|                                                 |
|  +--------------+    +--------------+           |
|  | Tasks Router  |    | Audit Router  |           |
|  | /api/v1/tasks |    | /api/v1/audit |           |
|  +------+-------+    +------+-------+           |
|         |                   |                    |
|  +------v-------+    +------v-------+           |
|  |  TaskService   |--->| AuditService  |           |
|  | (CRUD,         |    | (log_action,  |           |
|  |  handoffs)     |    |  get_trail)   |           |
|  +---------------+    +--------------+           |
|                                                 |
|  +-------------------------------+              |
|  | Pydantic Models                |              |
|  | Task, TaskCreate, TaskUpdate,  |              |
|  | Handoff, HandoffCreate,        |              |
|  | HandoffDecision, AuditEntry    |              |
|  +-------------------------------+              |
+-----------------------------------------------+
```

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| **Config** | `app/config.py` | App settings from env vars |
| **Models** | `app/models/models.py` | Pydantic schemas for Tasks, Handoffs, Audit |
| **TaskService** | `app/services/task_service.py` | Business logic: CRUD, assignment, handoffs |
| **AuditService** | `app/services/audit_service.py` | Immutable audit log for all actions |
| **Tasks Router** | `app/routers/tasks.py` | REST endpoints for tasks & handoffs |
| **Audit Router** | `app/routers/audit.py` | REST endpoints for audit trail |
| **Dashboard** | `app/static/dashboard.html` | Kanban board UI |
| **Main** | `app/main.py` | FastAPI app assembly |

## Quick Start

### Local (Python)

```bash
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open **http://localhost:8000** for the dashboard.

### Docker

```bash
docker compose up --build
```

## API Documentation

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/tasks` | List tasks (filter by `status`, `assignee_id`, `assignee_type`) |
| `POST` | `/api/v1/tasks` | Create a task |
| `GET` | `/api/v1/tasks/{task_id}` | Get task detail |
| `PUT` | `/api/v1/tasks/{task_id}` | Update task (status, context, notes) |
| `POST` | `/api/v1/tasks/{task_id}/handoff` | Initiate handoff |
| `PUT` | `/api/v1/tasks/{task_id}/handoff/{handoff_id}` | Accept or reject handoff |

### Audit

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/audit` | Get audit trail (filter by `task_id`, `actor`) |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |

### Example: Create a task assigned to an agent

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Review pull request",
    "description": "Check code quality and test coverage",
    "assignee_type": "agent",
    "assignee_id": "code-reviewer-agent"
  }'
```

### Example: Initiate a handoff

```bash
curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/handoff?actor=alice \
  -H "Content-Type: application/json" \
  -d '{
    "to_assignee_type": "agent",
    "to_assignee_id": "ml-train-agent",
    "reason": "Needs machine learning expertise for model training"
  }'
```

### Example: Accept a handoff

```bash
curl -X PUT http://localhost:8000/api/v1/tasks/{task_id}/handoff/{handoff_id}?actor=ml-train-agent \
  -H "Content-Type: application/json" \
  -d '{"decision": "accepted"}'
```

## Handoff Protocol

The handoff protocol enables smooth task transfer between humans and AI agents:

### Flow

1. **Initiate**: The current assignee (or a manager) creates a handoff, specifying the target assignee type (human/agent), target assignee ID, and a reason.

2. **Pending**: The handoff sits in a `pending` state, visible in the audit trail and on the dashboard via a handoff indicator.

3. **Accept**: The receiving assignee accepts the handoff. The task is automatically reassigned to the new assignee, and the audit trail records the transfer.

4. **Reject**: The receiving assignee rejects the handoff. The task remains with the original assignee, and the rejection is recorded.

### Why Handoffs Matter

- **Accountability**: Every transfer is logged with a reason and timestamp.
- **Context preservation**: The `reason` field carries why a handoff happened, and the task's `context` and `notes` fields carry working state.
- **Human-in-the-loop**: Humans can accept or reject requests from agents, maintaining oversight.
- **Agent collaboration**: Agents can hand off to other agents or to humans when they encounter tasks outside their capabilities.

## Task Statuses

| Status | Description |
|--------|-------------|
| `backlog` | Not yet started |
| `in_progress` | Currently being worked on |
| `in_review` | Awaiting review |
| `done` | Completed |

## Running Tests

```bash
pip install pytest httpx
pytest tests/ -v
```

## License

MIT
