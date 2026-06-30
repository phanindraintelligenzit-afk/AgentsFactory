"""Incident classifier agent — analyzes alerts and categorizes them."""
import re
from typing import Optional


# Classification rules: pattern → (category, severity_override, runbook)
CLASSIFICATION_RULES = [
    # Critical patterns
    (r"(?i)(outage|down|crash|panic|fatal|oom.?kill|host.?down)", "infrastructure", "critical", "host-recovery"),
    (r"(?i)(database.*(?:down|fail|corrupt)|postgres.*down|mysql.*down|mongo.*down)", "database", "critical", "database-recovery"),
    (r"(?i)(disk.*full|no.*space|storage.*exhausted)", "storage", "critical", "disk-cleanup"),
    (r"(?i)(memory.*leak|high.?memory|ram.*exhausted)", "memory", "critical", "memory-remediation"),

    # Warning patterns
    (r"(?i)(high.?cpu|cpu.*spike|load.*average)", "performance", "warning", "cpu-investigation"),
    (r"(?i)(high.?latency|slow.*response|p99.*latency)", "performance", "warning", "latency-debug"),
    (r"(?i)(error.?rate.*spike|5xx.*spike|requests?.*failing)", "reliability", "warning", "error-rate-debug"),
    (r"(?i)(cert.*expir|ssl.*expir|tls.*expir)", "security", "warning", "cert-renewal"),
    (r"(?i)(backup.*fail|snapshot.*fail)", "backup", "warning", "backup-retry"),
    (r"(?i)(queue.*full|queue.*backlog|consumer.*lag)", "messaging", "warning", "queue-drain"),

    # Info patterns
    (r"(?i)(deploy.*comple|deploy.*succ|release.*done)", "deployment", "info", None),
    (r"(?i)(scale.*up|scale.*out|autoscal)", "scaling", "info", None),

    # Network
    (r"(?i)(network.*unreachable|connection.*refused|timeout|dns.*fail)", "network", "warning", "network-diagnostics"),
    (r"(?i)(lb.*fail|load.?balancer.*error|ingress.*fail)", "network", "warning", "lb-recovery"),
]


def classify_incident(title: str, description: str = "") -> tuple[str, Optional[str], Optional[str]]:
    """Classify an incident based on its title and description.

    Returns: (category, severity_override, runbook_name)
    """
    text = f"{title} {description}".strip()

    for pattern, category, severity, runbook in CLASSIFICATION_RULES:
        if re.search(pattern, text):
            return category, severity, runbook

    # Default: unknown category, keep source severity, no auto-runbook
    return "unknown", None, None


def extract_service_name(title: str) -> Optional[str]:
    """Try to extract a service/component name from the alert title."""
    # Common patterns: "Service X is down", "[Service] Alert", etc.
    patterns = [
        r"\[([^\]]+)\]",
        r"(?:service|pod|container|node|host)\s+[\"']?([^\s\"',.]+)",
        r"([a-zA-Z0-9_-]+)\s+(?:is\s+)?(?:down|unhealthy|failing|error)",
    ]
    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None
