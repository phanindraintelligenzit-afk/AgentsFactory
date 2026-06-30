"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# --- Incident schemas ---

class IncidentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    severity: str = Field(default="warning", pattern="^(critical|warning|info)$")
    source: str = Field(default="alertmanager")
    external_id: Optional[str] = None
    metadata_json: Optional[str] = None


class IncidentCreate(IncidentBase):
    pass


class IncidentResponse(IncidentBase):
    id: int
    status: str
    classification: Optional[str] = None
    assigned_runbook: Optional[str] = None
    remediation_attempted: bool
    remediation_success: Optional[bool] = None
    auto_resolved: bool
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IncidentActionResponse(BaseModel):
    id: int
    incident_id: int
    action_type: str
    status: str
    result: Optional[str] = None
    agent_name: Optional[str] = None
    duration_seconds: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Runbook schemas ---

class RunbookBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    trigger_pattern: str = Field(..., min_length=1, max_length=255)
    steps: str = Field(..., description="JSON array of remediation steps")
    auto_execute: bool = False
    requires_approval: bool = True


class RunbookCreate(RunbookBase):
    pass


class RunbookResponse(RunbookBase):
    id: int
    success_count: int
    fail_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- OnCall schemas ---

class OnCallCreate(BaseModel):
    user_name: str
    user_email: str
    user_phone: Optional[str] = None
    start_time: datetime
    end_time: datetime
    is_primary: bool = False
    escalation_level: int = 1


class OnCallResponse(OnCallCreate):
    id: int

    class Config:
        from_attributes = True


# --- Alert webhook schema ---

class AlertmanagerAlert(BaseModel):
    """Incoming Alertmanager webhook payload."""
    receiver: str = ""
    status: str = "firing"
    labels: dict = Field(default_factory=dict)
    annotations: dict = Field(default_factory=dict)
    startsAt: Optional[str] = None
    endsAt: Optional[str] = None
    fingerprint: Optional[str] = None


class AlertmanagerWebhook(BaseModel):
    version: str = "4"
    groupKey: str = ""
    status: str = "firing"
    receiver: str = ""
    groupLabels: dict = Field(default_factory=dict)
    commonLabels: dict = Field(default_factory=dict)
    commonAnnotations: dict = Field(default_factory=dict)
    alerts: list[AlertmanagerAlert] = Field(default_factory=list)


# --- Dashboard stats ---

class DashboardStats(BaseModel):
    total_incidents: int
    active_incidents: int
    auto_resolved: int
    avg_resolution_minutes: float
    remediation_success_rate: float
    incidents_by_severity: dict[str, int]
    top_classifications: list[dict]
