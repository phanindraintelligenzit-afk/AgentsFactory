"""SQLAlchemy models for SRE Incident Automator."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Text, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Incident(Base):
    """Represents a detected incident or alert."""
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="warning")  # critical, warning, info
    source: Mapped[str] = mapped_column(String(50), default="alertmanager")  # alertmanager, pagerduty, manual
    status: Mapped[str] = mapped_column(String(20), default="firing")  # firing, acknowledged, resolved, muted
    classification: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    assigned_runbook: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    remediation_attempted: Mapped[bool] = mapped_column(Boolean, default=False)
    remediation_success: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    auto_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    actions: Mapped[list["IncidentAction"]] = relationship(
        "IncidentAction", back_populates="incident", cascade="all, delete-orphan"
    )


class IncidentAction(Base):
    """Actions taken during incident lifecycle."""
    __tablename__ = "incident_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)  # classify, notify, remediate, escalate
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, running, completed, failed
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    agent_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    incident: Mapped[Incident] = relationship("Incident", back_populates="actions")


class Runbook(Base):
    """Automated runbook definitions."""
    __tablename__ = "runbooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trigger_pattern: Mapped[str] = mapped_column(String(255), nullable=False)  # regex to match incident title
    steps: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array of steps
    auto_execute: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class OnCallSchedule(Base):
    """On-call rotation tracking."""
    __tablename__ = "oncall_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    user_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    escalation_level: Mapped[int] = mapped_column(Integer, default=1)
