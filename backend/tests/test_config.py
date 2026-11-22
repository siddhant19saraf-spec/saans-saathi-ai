from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_development_allows_missing_database() -> None:
    settings = Settings(_env_file=None, app_env="development", database_url=None)

    assert settings.database_url is None
    assert settings.json_logs is False


def test_production_requires_database() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_env="production", database_url=None)


def test_production_enables_json_logs() -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        database_url="postgresql+psycopg://user:pass@localhost:5432/saans",
    )

    assert settings.json_logs is True
    assert settings.docs_enabled is False


def test_blank_database_url_is_treated_as_missing() -> None:
    settings = Settings(_env_file=None, app_env="development", database_url="   ")

    assert settings.database_url is None


def test_non_postgres_database_scheme_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_env="development",
            database_url="mysql://user:pass@localhost:3306/saans",
        )


def test_database_url_requires_database_name() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_env="development",
            database_url="postgresql+psycopg://user:pass@localhost:5432/",
        )


def test_trailing_slashes_are_removed_from_urls() -> None:
    settings = Settings(_env_file=None, frontend_url="http://localhost:3000/")

    assert settings.frontend_url == "http://localhost:3000"


def test_relative_urls_are_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, frontend_url="not-a-url")


def test_allowed_hosts_are_parsed_and_trimmed() -> None:
    settings = Settings(_env_file=None, allowed_hosts=" localhost, example.com , ")

    assert settings.host_allowlist == ["localhost", "example.com"]


def test_invalid_log_level_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, log_level="LOUD")


def test_secret_values_are_masked_in_repr() -> None:
    settings = Settings(_env_file=None, gemini_api_key="super-secret-value")

    assert settings.ai_configured is True
    assert "super-secret-value" not in repr(settings)
