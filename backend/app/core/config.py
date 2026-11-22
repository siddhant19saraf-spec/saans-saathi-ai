"""Typed runtime configuration with fail-fast validation."""

from __future__ import annotations

from datetime import timedelta
from functools import lru_cache
from typing import Literal, Self
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]

_SUPPORTED_DATABASE_SCHEMES = frozenset({"postgresql+psycopg", "postgresql+asyncpg"})
_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


class Settings(BaseSettings):
    """Application settings loaded from environment variables and `.env`.

    Production requires a database URL. Development and test may run without
    one, in which case the health endpoint reports the database as
    ``not_configured`` instead of pretending it is healthy.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "SAANS SAATHI API"
    app_version: str = "0.1.0"
    app_env: Environment = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    database_url: str | None = None
    db_pool_size: int = Field(default=5, ge=1, le=20)
    db_max_overflow: int = Field(default=5, ge=0, le=20)
    db_pool_timeout_seconds: int = Field(default=10, ge=1, le=60)

    gemini_api_key: SecretStr | None = None
    gemini_api_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_model: str = "gemini-2.5-flash-lite"
    ai_daily_request_budget: int = Field(default=300, ge=0, le=100_000)
    ai_request_timeout_seconds: float = Field(default=12.0, ge=1.0, le=60.0)

    air_quality_api_base_url: str = "https://air-quality-api.open-meteo.com/v1"
    openmeteo_daily_call_budget: int = Field(default=8_000, ge=0, le=100_000)
    air_current_ttl_seconds: int = Field(default=30 * 60, ge=60, le=86_400)
    air_forecast_ttl_seconds: int = Field(default=3 * 3600, ge=60, le=86_400)
    air_history_ttl_seconds: int = Field(default=24 * 3600, ge=60, le=7 * 86_400)
    air_stale_max_age_seconds: int = Field(default=24 * 3600, ge=60, le=7 * 86_400)

    openaq_api_base_url: str = "https://api.openaq.org"
    openaq_api_key: SecretStr | None = None
    openaq_daily_call_budget: int = Field(default=2_000, ge=0, le=100_000)
    openaq_station_radius_km: int = Field(default=25, ge=1, le=25)
    openaq_stations_per_page: int = Field(default=20, ge=1, le=100)

    geocoding_api_base_url: str = "https://geocoding-api.open-meteo.com/v1"
    geocoding_cache_ttl_seconds: int = Field(default=24 * 3600, ge=60, le=30 * 86_400)
    location_search_max_results: int = Field(default=10, ge=1, le=20)

    cpcb_enabled: bool = False
    cpcb_api_base_url: str | None = None
    cpcb_api_key: SecretStr | None = None

    frontend_url: str = "http://localhost:3000"
    allowed_origins: str = ""
    allowed_hosts: str = "localhost,127.0.0.1,testserver"

    request_max_bytes: int = Field(default=32_768, ge=1_024, le=1_048_576)
    session_ttl_days: int = Field(default=90, ge=1, le=365)
    rate_limit_public_per_minute: int = Field(default=30, ge=1, le=10_000)
    rate_limit_session_per_minute: int = Field(default=100, ge=1, le=10_000)
    copilot_messages_per_hour: int = Field(default=20, ge=1, le=10_000)
    family_generations_per_hour: int = Field(default=30, ge=1, le=10_000)
    indoor_explanations_per_hour: int = Field(default=20, ge=1, le=10_000)

    @field_validator("database_url", mode="before")
    @classmethod
    def _blank_database_url_is_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        parsed = urlparse(value)
        if parsed.scheme not in _SUPPORTED_DATABASE_SCHEMES:
            raise ValueError("DATABASE_URL must use the postgresql+psycopg scheme.")
        if not parsed.hostname or not parsed.path.strip("/"):
            raise ValueError("DATABASE_URL must include a host and a database name.")
        return value

    @field_validator(
        "air_quality_api_base_url",
        "frontend_url",
        "gemini_api_base_url",
        "openaq_api_base_url",
        "geocoding_api_base_url",
    )
    @classmethod
    def _validate_http_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("must be an absolute http(s) URL")
        return value.rstrip("/")

    @field_validator("cpcb_api_base_url")
    @classmethod
    def _validate_optional_http_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("must be an absolute http(s) URL")
        return value.rstrip("/")

    @field_validator("allowed_origins")
    @classmethod
    def _validate_allowed_origins(cls, value: str) -> str:
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        for origin in origins:
            if origin == "*":
                raise ValueError("ALLOWED_ORIGINS must not contain a wildcard")
            parsed = urlparse(origin)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError("ALLOWED_ORIGINS entries must be absolute origins")
        return ",".join(origins)

    @field_validator("gemini_model")
    @classmethod
    def _validate_model_name(cls, value: str) -> str:
        model = value.strip()
        if not model or len(model) > 80 or any(char.isspace() for char in model):
            raise ValueError("GEMINI_MODEL must be a single model identifier")
        return model

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        level = value.upper()
        if level not in _LOG_LEVELS:
            raise ValueError(f"LOG_LEVEL must be one of {sorted(_LOG_LEVELS)}")
        return level

    @model_validator(mode="after")
    def _require_database_in_production(self) -> Self:
        if self.app_env == "production" and self.database_url is None:
            raise ValueError("DATABASE_URL is required when APP_ENV=production.")
        return self

    @property
    def host_allowlist(self) -> list[str]:
        hosts = [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]
        return hosts or ["localhost"]

    @property
    def cors_origins(self) -> list[str]:
        origins = [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]
        return origins or [self.frontend_url]

    @property
    def session_ttl(self) -> timedelta:
        return timedelta(days=self.session_ttl_days)

    @property
    def json_logs(self) -> bool:
        return self.app_env == "production"

    @property
    def ai_configured(self) -> bool:
        return self.gemini_api_key is not None

    @property
    def openaq_configured(self) -> bool:
        return self.openaq_api_key is not None

    @property
    def cpcb_configured(self) -> bool:
        return self.cpcb_enabled and self.cpcb_api_base_url is not None

    @property
    def docs_enabled(self) -> bool:
        return self.app_env != "production"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings()
