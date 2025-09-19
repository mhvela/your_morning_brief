from __future__ import annotations

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

    # Build info (populated at runtime)
    build_date: str = ""
    commit_hash: str = ""
    python_version: str = ""

    model_config = {"env_file": ".env", "case_sensitive": False}


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()


# Global settings instance
settings = get_settings()
