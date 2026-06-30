"""Agent pipeline runner — executes the 4-agent SRE pipeline."""
import time
import json
from typing import Optional
from app.services.classifier import classify_incident, extract_service_name
from app.services.remediator import execute_runbook_step
from app.services.notifier import format_notification
from app.services.incident_scribe import generate_postmortem_draft


def run_full_pipeline(incident_data: dict) -> dict:
    """Execute the full 4-agent incident pipeline.

    Agents:
    1. Classifier — categorize and assign severity
    2. Remediator — match runbook and suggest/execute fix
    3. Notifier — format alert for Slack/PagerDuty
    4. Incident Scribe — draft postmortem

    Args:
        incident_data: Dict with incident details

    Returns:
        Full pipeline output with each agent's result
    """
    pipeline_start = time.time()
    results = {
        "incident_title": incident_data.get("title", ""),
        "agents": [],
        "total_duration_seconds": 0,
        "auto_remediation_available": False,
    }

    # Agent 1: Classifier
    t1 = time.time()
    category, severity_override, runbook = classify_incident(
        incident_data.get("title", ""),
        incident_data.get("description", ""),
    )
    service_name = extract_service_name(incident_data.get("title", ""))
    source_severity = incident_data.get("severity", "warning")
    severity = severity_override or source_severity

    results["agents"].append({
        "name": "classifier",
        "role": "Categorize and prioritize",
        "output": {
            "category": category,
            "severity": severity,
            "service_name": service_name,
            "runbook_suggested": runbook,
            "confidence": 0.85 if category != "unknown" else 0.4,
        },
        "duration_seconds": round(time.time() - t1, 3),
    })

    # Agent 2: Remediator
    t2 = time.time()
    if runbook:
        remediation = execute_runbook_step(runbook, incident_data)
        results["agents"].append({
            "name": "remediator",
            "role": "Match runbook and execute fix",
            "output": remediation,
            "duration_seconds": round(time.time() - t2, 3),
        })
        results["auto_remediation_available"] = remediation.get("has_runbook", False)
    else:
        results["agents"].append({
            "name": "remediator",
            "role": "Match runbook and execute fix",
            "output": {"has_runbook": False, "message": "No matching runbook found"},
            "duration_seconds": round(time.time() - t2, 3),
        })

    # Agent 3: Notifier
    t3 = time.time()
    notification = format_notification(
        title=incident_data.get("title", ""),
        severity=severity,
        category=category,
        service_name=service_name,
        status=incident_data.get("status", "firing"),
    )
    results["agents"].append({
        "name": "notifier",
        "role": "Format multi-platform alert",
        "output": notification,
        "duration_seconds": round(time.time() - t3, 3),
    })

    # Agent 4: Incident Scribe
    t4 = time.time()
    postmortem = generate_postmortem_draft(
        title=incident_data.get("title", ""),
        category=category,
        severity=severity,
        service_name=service_name,
        actions=results["agents"][1]["output"].get("steps", []) if runbook else [],
    )
    results["agents"].append({
        "name": "incident_scribe",
        "role": "Draft postmortem and timeline",
        "output": postmortem,
        "duration_seconds": round(time.time() - t4, 3),
    })

    results["total_duration_seconds"] = round(time.time() - pipeline_start, 3)
    return results
