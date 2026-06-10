"""Configuration management via Pydantic Settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    agentsfactory_env: str = "development"
    agentsfactory_log_level: str = "INFO"

    # LLM
    openrouter_api_key: str = ""

    # Database
    agentsfactory_database_url: str = "sqlite+aiosqlite:///./agentsfactory.db"

    # Observability
    enable_tracing: bool = True
    log_format: str = "json"  # json | text

    # Safety
    max_tokens_per_run: int = 100_000
    max_cost_per_run_usd: float = 5.0
    max_pipeline_duration_seconds: int = 300

    @property
    def is_development(self) -> bool:
        return self.agentsfactory_env == "development"

    @property
    def is_production(self) -> bool:
        return self.agentsfactory_env == "production"


# Singleton
settings = Settings()
