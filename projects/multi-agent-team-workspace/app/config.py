"""Configuration for Multi-Agent Team Workspace."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Multi-Agent Team Workspace"
    version: str = "1.0.0"
    database_url: str = "sqlite:///./workspace.db"
    class Config:
        env_prefix = "WORKSPACE_"

config = Settings()
