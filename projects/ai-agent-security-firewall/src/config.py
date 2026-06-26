"""Configuration for the AI Agent Security Firewall."""
from dataclasses import dataclass, field
from typing import List

class Severity:
    BLOCK = "block"
    FLAG = "flag"
    LOG = "log"

@dataclass
class FirewallConfig:
    severity_threshold: str = Severity.BLOCK
    max_input_length: int = 50000
    injection_patterns: List[str] = field(default_factory=lambda: [
        "ignore previous instructions", "ignore all previous", "disregard your instructions",
        "forget your instructions", "you are now", "from now on you are",
        "system prompt:", "user is the new system", "override safety",
        "jailbreak", "you have no restrictions", "you can do anything", "no rules apply",
    ])
    jailbreak_patterns: List[str] = field(default_factory=lambda: [
        "do anything now", "no restrictions", "unrestricted mode", "developer mode",
        "pretend you are", "roleplay as", "you are free", "no limitations",
        "you have no rules", "you are not bound",
    ])
    exfiltration_patterns: List[str] = field(default_factory=lambda: [
        "reveal your system prompt", "show your instructions", "what are your instructions",
        "print your prompt", "output your system", "leak your prompt",
        "secret instructions", "hidden instructions", "api key", "password", "token is",
    ])
    override_patterns: List[str] = field(default_factory=lambda: [
        "new instructions:", "updated rules:", "replace your instructions",
        "instead of your normal", "behave as if", "act as if you are not an AI",
    ])
    @classmethod
    def default(cls):
        return cls()
