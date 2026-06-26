"""Core firewall detection engine."""
import re, time
from typing import Dict, List, Any
from config import FirewallConfig, Severity

class Firewall:
    def __init__(self, config: FirewallConfig = None):
        self.config = config or FirewallConfig.default()
        self.stats = {"total_scans": 0, "total_blocked": 0, "violations_by_type": {}, "blocked_percentage": 0.0}
        self.recent_violations: List[Dict[str, Any]] = []

    def _match_patterns(self, text: str, patterns: List[str]) -> List[str]:
        text_lower = text.lower()
        return [p for p in patterns if re.search(re.escape(p.lower()), text_lower)]

    def detect_prompt_injection(self, text: str) -> List[str]:
        return self._match_patterns(text, self.config.injection_patterns)

    def detect_jailbreak(self, text: str) -> List[str]:
        return self._match_patterns(text, self.config.jailbreak_patterns)

    def detect_data_exfiltration(self, text: str) -> List[str]:
        return self._match_patterns(text, self.config.exfiltration_patterns)

    def detect_instruction_override(self, text: str) -> List[str]:
        return self._match_patterns(text, self.config.override_patterns)

    def scan(self, text: str) -> Dict[str, Any]:
        start = time.time()
        self.stats["total_scans"] += 1
        violations = []
        if not text or not text.strip():
            return {"blocked": False, "severity": "log", "violations": [],
                    "scan_time_ms": 0.0, "input_length": 0, "timestamp": time.time()}
        if len(text) > self.config.max_input_length:
            violations.append({"type": "input_validation", "matches": ["oversized_input"], "severity": Severity.BLOCK})
        for detector, category in [
            (self.detect_prompt_injection, "prompt_injection"),
            (self.detect_jailbreak, "jailbreak"),
            (self.detect_data_exfiltration, "data_exfiltration"),
            (self.detect_instruction_override, "instruction_override"),
        ]:
            matches = detector(text)
            if matches:
                sev = Severity.BLOCK if category in ("jailbreak", "data_exfiltration") else self.config.severity_threshold
                violations.append({"type": category, "matches": matches, "severity": sev})
                self.stats["violations_by_type"][category] = self.stats["violations_by_type"].get(category, 0) + 1
        blocked = any(v["severity"] == Severity.BLOCK for v in violations)
        flagged = any(v["severity"] == Severity.FLAG for v in violations)
        severity = "block" if blocked else ("flag" if flagged else "log")
        if blocked:
            self.stats["total_blocked"] += 1
        self.stats["blocked_percentage"] = round(self.stats["total_blocked"] / self.stats["total_scans"] * 100, 2)
        elapsed = (time.time() - start) * 1000
        result = {"blocked": blocked, "severity": severity, "violations": violations,
                  "scan_time_ms": round(elapsed, 2), "input_length": len(text), "timestamp": time.time()}
        if violations:
            self.recent_violations.append({"text_preview": text[:100], **result})
            if len(self.recent_violations) > 50:
                self.recent_violations = self.recent_violations[-50:]
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {**self.stats}

    def get_recent_violations(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self.recent_violations[-limit:]
