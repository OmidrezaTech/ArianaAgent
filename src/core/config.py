import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Company MVP"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "super-secret-jwt-signing-key-for-mvp-company"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database Settings (SQLite for local/tests, Postgres for Docker/Production)
    DATABASE_URL: str = "sqlite+aiosqlite:///./aicompany.db"
    SYNC_DATABASE_URL: str = "sqlite:///./aicompany.db"

    # LLM & AI Providers (mock, gemini, openai)
    GEMINI_API_KEY: str = "mock-key"
    OPENAI_API_KEY: str = "mock-key"
    LLM_PROVIDER: str = "mock"  # mock, gemini, openai
    DEFAULT_FAST_MODEL: str = "gemini-1.5-flash"
    DEFAULT_SMART_MODEL: str = "gemini-1.5-pro"
    DEFAULT_DEV_MODEL: str = "gemini-1.5-pro"

    # Workspace for repositories and generated code
    WORKSPACE_ROOT: str = "./workspace_repos"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def is_postgres(self) -> bool:
        return self.DATABASE_URL.startswith("postgresql")


settings = Settings()

# Ensure workspace root exists
Path(settings.WORKSPACE_ROOT).mkdir(parents=True, exist_ok=True)
