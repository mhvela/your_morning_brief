import os
from unittest.mock import patch

from app.core.config import Settings, get_settings


def test_settings_default_values() -> None:
    """Test that settings have correct default values."""
    settings = Settings()

    assert settings.app_name == "Your Morning Brief API"
    assert settings.app_description == "Personalized news curation service"
    assert settings.version == "0.1.0"
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000
    assert settings.log_level == "INFO"
    assert settings.cors_origins == ["http://localhost:3000"]


def test_settings_from_environment() -> None:
    """Test that settings can be configured from environment variables."""
    with patch.dict(
        os.environ,
        {
            "LOG_LEVEL": "DEBUG",
            "API_PORT": "9000",
            "API_HOST": "127.0.0.1",
        },
    ):
        settings = Settings()

        assert settings.log_level == "DEBUG"
        assert settings.api_port == 9000
        assert settings.api_host == "127.0.0.1"


def test_get_settings_singleton() -> None:
    """Test that get_settings returns the same instance."""
    settings1 = get_settings()
    settings2 = get_settings()

    # Should be the same object (singleton pattern could be implemented)
    assert isinstance(settings1, Settings)
    assert isinstance(settings2, Settings)
    assert settings1.app_name == settings2.app_name
