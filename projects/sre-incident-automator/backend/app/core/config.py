"""Configuration management for SRE Incident Automator."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    APP_NAME: str = "SRE Incident Automator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    DATABASE_URL: str = "sqlite+aiosqlite:///./sre_automator.db"
    SECRET_KEY: str = "dev-secret-change-in-production"
    ALERTMANAGER_URL: str = ""
    PAGERDUTY_API_KEY: str = ""
    SLACK_WEBHOOK_URL: str = ""
    RUNBOOK_PATH: str = "./runbooks"
    AUTO_REMEDIATE: bool = False
    REMEDIATION_APPROVAL_REQUIRED: bool = True
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
