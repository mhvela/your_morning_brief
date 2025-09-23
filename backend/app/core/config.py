from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment-based configuration."""

    # Application info
    app_name: str = "Your Morning Brief API"
    app_description: str = "Personalized news curation service"
    version: str = "0.1.0"

    # Server configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Logging
    log_level: str = "INFO"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database settings
    database_url: str | None = None
    postgres_user: str = "mb_user"
    postgres_password: str = "mb_dev_password"
    postgres_host: str = "localhost"
    postgres_port: str = "5432"
    postgres_db: str = "morning_brief"

    # Database connection pool settings
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30
    database_echo: bool = False

    # Test database (use SQLite file by default for CI/local tests)
    test_database_url: str | None = "sqlite:///./test.db"

    # RSS Ingestion settings
    ingestion_user_agent: str = "YourMorningBriefBot/0.1 (+contact: dev@local)"
    ingestion_timeout_sec: int = 10
    ingestion_max_retries: int = 2
    retry_backoff_base_sec: float = 0.5
    retry_backoff_jitter_sec: float = 0.3
    ingestion_total_retry_cap_sec: float = 8.0
    summary_max_len: int = 4000
    max_response_size_mb: int = 10
    blocked_networks: list[str] = [
        "10.0.0.0/8",      # Private Class A
        "172.16.0.0/12",   # Private Class B
        "192.168.0.0/16",  # Private Class C
        "127.0.0.0/8",     # Loopback
        "169.254.0.0/16",  # Link-local
        "::1/128",         # IPv6 loopback
        "fc00::/7",        # IPv6 unique local
        "fe80::/10",       # IPv6 link-local
    ]
    allowed_url_schemes: list[str] = ["http", "https"]

    # Build info (populated at runtime)
    build_date: str = ""
    commit_hash: str = ""
    python_version: str = ""

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Any, info: ValidationInfo) -> str:
        if isinstance(v, str):
            return v
        # Build from components if not provided
        values: Mapping[str, Any] = info.data if hasattr(info, "data") else {}
        user = values.get("postgres_user", "mb_user")
        password = values.get("postgres_password", "mb_dev_password")
        host = values.get("postgres_host", "localhost")
        port = values.get("postgres_port", "5432")
        db = values.get("postgres_db", "morning_brief")
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"

    model_config = {"env_file": ".env", "case_sensitive": False}


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()


# Global settings instance
settings = get_settings()
