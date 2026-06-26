"""FastAPI application entry-point for Multi-Agent Team Workspace."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import config
from app.routers.audit import router as audit_router, set_audit_service
from app.routers.tasks import router as tasks_router, set_task_service
from app.services.audit_service import AuditService
from app.services.task_service import TaskService

# --- Application factory ---

app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    description="A workspace where tasks are assigned to humans OR AI agents -- "
                "with shared context, handoff protocols, and audit trails.",
)

# Wire up services (singletons for the lifetime of the process)
audit_service = AuditService()
task_service = TaskService(audit_service)

set_audit_service(audit_service)
set_task_service(task_service)

# Register routers
app.include_router(tasks_router)
app.include_router(audit_router)

# Serve static files
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# --- Dashboard route ---

@app.get("/", response_class=HTMLResponse)
def dashboard():
    """Serve the Kanban board dashboard."""
    html_path = STATIC_DIR / "dashboard.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return HTMLResponse("<h1>Dashboard not found</h1><p>Place dashboard.html in app/static/</p>")


# --- Health check ---

@app.get("/health")
def health():
    return {"status": "ok", "version": config.app_version}
