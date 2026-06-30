"""Remediator agent — matches runbooks and generates fix steps."""
import json
from typing import Optional


# Pre-built runbook library
RUNBOOKS = {
    "host-recovery": {
        "description": "Recover a downed host or node",
        "steps": [
            {"order": 1, "action": "ping_check", "command": "ping -c 3 {{service_name}}", "type": "diagnostic", "auto": True},
            {"order": 2, "action": "ssh_check", "command": "ssh {{service_name}} 'uptime'", "type": "diagnostic", "auto": False},
            {"order": 3, "action": "restart_service", "command": "systemctl restart {{service_name}}", "type": "remediation", "auto": False},
            {"order": 4, "action": "verify_health", "command": "curl -sf http://{{service_name}}:8080/health", "type": "verify", "auto": False},
        ],
    },
    "database-recovery": {
        "description": "Respond to database failure",
        "steps": [
            {"order": 1, "action": "check_connections", "command": "SELECT count(*) FROM pg_stat_activity", "type": "diagnostic", "auto": True},
            {"order": 2, "action": "check_replication", "command": "SHOW SLAVE STATUS", "type": "diagnostic", "auto": True},
            {"order": 3, "action": "restart_pooler", "command": "systemctl restart pgbouncer", "type": "remediation", "auto": False},
            {"order": 4, "action": "failover_check", "command": "patronictl list", "type": "verify", "auto": False},
        ],
    },
    "disk-cleanup": {
        "description": "Free disk space on a node",
        "steps": [
            {"order": 1, "action": "identify_usage", "command": "df -h && du -sh /var/log/* | sort -rh | head -10", "type": "diagnostic", "auto": True},
            {"order": 2, "action": "clean_logs", "command": "find /var/log -name '*.gz' -mtime +7 -delete", "type": "remediation", "auto": True},
            {"order": 3, "action": "clean_docker", "command": "docker system prune -af --volumes", "type": "remediation", "auto": True},
            {"order": 4, "action": "verify_space", "command": "df -h / | tail -1", "type": "verify", "auto": True},
        ],
    },
    "cert-renewal": {
        "description": "Renew expiring TLS certificates",
        "steps": [
            {"order": 1, "action": "check_expiry", "command": "openssl s_client -connect {{service_name}}:443 2>/dev/null | openssl x509 -noout -dates", "type": "diagnostic", "auto": True},
            {"order": 2, "action": "renew_cert", "command": "certbot renew --cert-name {{service_name}}", "type": "remediation", "auto": False},
            {"order": 3, "action": "reload_nginx", "command": "nginx -s reload", "type": "remediation", "auto": False},
            {"order": 4, "action": "verify_cert", "command": "echo | openssl s_client -connect {{service_name}}:443 2>/dev/null | openssl x509 -noout -dates", "type": "verify", "auto": False},
        ],
    },
    "cpu-investigation": {
        "description": "Investigate high CPU usage",
        "steps": [
            {"order": 1, "action": "top_processes", "command": "ps aux --sort=-%cpu | head -20", "type": "diagnostic", "auto": True},
            {"order": 2, "action": "check_load", "command": "uptime", "type": "diagnostic", "auto": True},
            {"order": 3, "action": "thread_dump", "command": "jstack $(pgrep java) > /tmp/thread_dump_$(date +%s).txt", "type": "diagnostic", "auto": False},
            {"order": 4, "action": "scale_up", "command": "kubectl scale deployment {{service_name}} --replicas=+1", "type": "remediation", "auto": False},
        ],
    },
    "queue-drain": {
        "description": "Fix message queue backlog",
        "steps": [
            {"order": 1, "action": "check_depth", "command": "kafka-consumer-groups --describe --group {{service_name}}", "type": "diagnostic", "auto": True},
            {"order": 2, "action": "restart_consumers", "command": "kubectl rollout restart deployment/{{service_name}}-consumer", "type": "remediation", "auto": False},
            {"order": 3, "action": "scale_consumers", "command": "kubectl scale deployment {{service_name}}-consumer --replicas=5", "type": "remediation", "auto": False},
            {"order": 4, "action": "verify_drain", "command": "kafka-consumer-groups --describe --group {{service_name}} | grep LAG", "type": "verify", "auto": False},
        ],
    },
}


def execute_runbook_step(runbook_name: str, incident_data: dict) -> dict:
    """Get remediation steps for a given runbook."""
    runbook = RUNBOOKS.get(runbook_name)

    if not runbook:
        return {
            "has_runbook": False,
            "runbook_name": runbook_name,
            "message": f"Runbook '{runbook_name}' not found in library",
            "steps": [],
            "auto_steps_available": 0,
        }

    service_name = incident_data.get("service_name", "unknown")
    steps = []
    auto_count = 0

    for step in runbook["steps"]:
        step_copy = dict(step)
        # Template substitution
        step_copy["command"] = step_copy["command"].replace("{{service_name}}", service_name)
        if step.get("auto", False):
            auto_count += 1
        steps.append(step_copy)

    return {
        "has_runbook": True,
        "runbook_name": runbook_name,
        "runbook_description": runbook["description"],
        "total_steps": len(steps),
        "auto_steps_available": auto_count,
        "manual_steps": len(steps) - auto_count,
        "steps": steps,
    }


def list_runbooks() -> list[dict]:
    """List all available runbooks."""
    return [
        {"name": name, "description": rb["description"], "total_steps": len(rb["steps"])}
        for name, rb in RUNBOOKS.items()
    ]

