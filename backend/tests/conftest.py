"""Shared fixtures.

Tests never read the developer's backend/.env: settings are constructed
explicitly so results are identical locally and in CI.

Database-backed tests use TEST_DATABASE_URL when it is set and are skipped
otherwise. They create the schema with the ORM metadata (the Alembic chain is
verified separately) and truncate every table around each test.
"""

from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.integrations.air_quality.base import (
    AirQualityProviderError,
    AveragingDetail,
    ProviderForecast,
    ProviderForecastPoint,
    ProviderHistory,
    ProviderHistoryDay,
    ProviderReading,
)
from app.main import create_app
from app.models import Base

if sys.platform == "win32":
    # psycopg's async driver cannot run on the Proactor loop. pytest-asyncio
    # creates loops through the policy, so set it before any test runs.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

_TABLE_NAMES = tuple(table.name for table in Base.metadata.sorted_tables)


@pytest.fixture
def settings() -> Settings:
    # Every field that could vary between machines is pinned explicitly: the
    # developer's shell may export real keys, and tests must not depend on them.
    return Settings(
        _env_file=None,
        app_env="test",
        database_url=None,
        gemini_api_key=None,
        log_level="WARNING",
    )


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http


@pytest.fixture(scope="session")
def test_database_url() -> str:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set; database-backed tests skipped.")
    return url


@pytest.fixture(scope="session")
def database_schema(test_database_url: str) -> str:
    async def prepare() -> None:
        engine = create_async_engine(test_database_url, poolclass=NullPool)
        try:
            async with engine.begin() as connection:
                # The database persists between runs, and create_all never
                # alters existing tables. Rebuild from metadata so schema
                # changes in this branch are applied.
                await connection.run_sync(Base.metadata.drop_all)
                await connection.run_sync(Base.metadata.create_all)
        finally:
            await engine.dispose()

    asyncio.run(prepare())
    return test_database_url


@pytest.fixture
def db_settings(database_schema: str) -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        database_url=database_schema,
        gemini_api_key=None,
        log_level="WARNING",
    )


async def _truncate(app: FastAPI) -> None:
    engine = app.state.database.engine
    if engine is None:
        raise RuntimeError("Database is not configured for this test.")
    statement = (
        "TRUNCATE TABLE " + ", ".join(_TABLE_NAMES) + " RESTART IDENTITY CASCADE"
    )
    async with engine.begin() as connection:
        await connection.execute(text(statement))


@pytest.fixture
async def db_app(db_settings: Settings) -> AsyncIterator[FastAPI]:
    application = create_app(db_settings)
    await _truncate(application)
    try:
        yield application
    finally:
        await application.state.database.dispose()


@pytest.fixture
async def db_client(db_app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=db_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http


@pytest.fixture
async def auth_headers(db_client: AsyncClient) -> dict[str, str]:
    response = await db_client.post(
        "/api/v1/sessions",
        json={"consent_version": "2026-11-test", "health_consent": True},
    )
    assert response.status_code == 201, response.text
    token = response.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def plain_headers(db_client: AsyncClient) -> dict[str, str]:
    """Session without health-data consent."""
    response = await db_client.post(
        "/api/v1/sessions",
        json={"consent_version": "2026-11-test", "health_consent": False},
    )
    assert response.status_code == 201, response.text
    token = response.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


class FakeAirProvider:
    """Deterministic provider used to exercise behaviour without the network."""

    name = "fake"

    def __init__(
        self,
        *,
        reading: ProviderReading | None = None,
        forecast: ProviderForecast | None = None,
        history: ProviderHistory | None = None,
        current_error: AirQualityProviderError | None = None,
        forecast_error: AirQualityProviderError | None = None,
        history_error: AirQualityProviderError | None = None,
    ) -> None:
        self._reading = reading
        self._forecast = forecast
        self._history = history
        self._current_error = current_error
        self._forecast_error = forecast_error
        self._history_error = history_error
        self.calls: list[tuple[str, float, float]] = []

    async def current(self, lat: float, lon: float) -> ProviderReading:
        self.calls.append(("current", lat, lon))
        if self._current_error is not None:
            raise self._current_error
        if self._reading is None:
            raise AirQualityProviderError("No reading configured.", kind="http_error")
        return self._reading

    async def forecast(self, lat: float, lon: float, hours: int) -> ProviderForecast:
        self.calls.append(("forecast", lat, lon))
        if self._forecast_error is not None:
            raise self._forecast_error
        if self._forecast is None:
            raise AirQualityProviderError("No forecast configured.", kind="http_error")
        return self._forecast

    async def history(self, lat: float, lon: float, days: int) -> ProviderHistory:
        self.calls.append(("history", lat, lon))
        if self._history_error is not None:
            raise self._history_error
        if self._history is None:
            raise AirQualityProviderError("No history configured.", kind="http_error")
        return self._history


def make_reading(
    *,
    pm2_5: float | None = 82.0,
    pm10: float | None = 140.0,
    observed_at: datetime | None = None,
) -> ProviderReading:
    averages = {
        "pm2_5": pm2_5,
        "pm10": pm10,
        "co_ug_m3": 900.0,
        "no2_ug_m3": 46.0,
        "so2_ug_m3": 9.0,
        "o3_ug_m3": 55.0,
    }
    windows = {
        pollutant: AveragingDetail(
            window="8h" if pollutant in {"co_ug_m3", "o3_ug_m3"} else "24h",
            hours=8 if pollutant in {"co_ug_m3", "o3_ug_m3"} else 24,
            valid_hours=8 if pollutant in {"co_ug_m3", "o3_ug_m3"} else 24,
            required_hours=6 if pollutant in {"co_ug_m3", "o3_ug_m3"} else 16,
            value=value,
        )
        for pollutant, value in averages.items()
    }
    return ProviderReading(
        provider=FakeAirProvider.name,
        kind="modelled",
        source_type="model_forecast",
        values={
            "pm2_5": pm2_5,
            "pm10": pm10,
            "co_ug_m3": 900.0,
            "no2_ug_m3": 46.0,
            "so2_ug_m3": 9.0,
            "o3_ug_m3": 55.0,
            "dust_ug_m3": 12.0,
        },
        averages=averages,
        average_windows=windows,
        observed_at=observed_at or datetime.now(tz=UTC),
        model="TEST-MODEL",
        us_aqi=165,
        european_aqi=110,
        attribution=("Fake provider",),
        latitude=28.61,
        longitude=77.21,
        timezone="UTC",
    )


def make_forecast(
    *,
    start: datetime | None = None,
    hours: int = 48,
    pm2_5: float = 60.0,
) -> ProviderForecast:
    base = start or datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
    points = tuple(
        ProviderForecastPoint(
            time=base + timedelta(hours=offset),
            pm2_5=pm2_5 + offset * 0.5,
            pm10=pm2_5 * 1.6 + offset,
            no2_ug_m3=35.0,
            o3_ug_m3=48.0,
        )
        for offset in range(hours)
    )
    return ProviderForecast(
        provider=FakeAirProvider.name,
        points=points,
        issued_at=datetime.now(tz=UTC),
        attribution=("Fake provider",),
        model="TEST-MODEL",
    )


def make_history(days: int = 7) -> ProviderHistory:
    base = datetime.now(tz=UTC).date()
    return ProviderHistory(
        provider=FakeAirProvider.name,
        days=tuple(
            ProviderHistoryDay(
                date=(base - timedelta(days=offset)).isoformat(),
                pm2_5=70.0 + offset,
                pm10=110.0 + offset,
            )
            for offset in range(days, 0, -1)
        ),
        issued_at=datetime.now(tz=UTC),
        attribution=("Fake provider",),
        model="TEST-MODEL",
    )


@pytest.fixture
def fake_provider() -> Callable[..., FakeAirProvider]:
    return FakeAirProvider


@pytest.fixture
def reading_factory() -> Callable[..., ProviderReading]:
    return make_reading


@pytest.fixture
def forecast_factory() -> Callable[..., ProviderForecast]:
    return make_forecast


@pytest.fixture
def history_factory() -> Callable[..., ProviderHistory]:
    return make_history
