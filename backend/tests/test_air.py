from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from fastapi import FastAPI
from httpx import AsyncClient

from app.integrations.air_quality.base import (
    AirQualityProviderError,
    ProviderReading,
)

READING = {
    "lat": 28.61,
    "lon": 77.21,
}


async def test_current_returns_cpcb_aqi_with_provenance(
    app: FastAPI,
    client: AsyncClient,
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., ProviderReading],
) -> None:
    app.state.air_provider = fake_provider(reading=reading_factory())

    response = await client.get("/api/v1/air/current", params=READING)

    assert response.status_code == 200, response.text
    body = response.json()
    data = body["data"]
    assert data["reading"]["pm2_5"] == 82.0
    assert data["reading"]["dust_ug_m3"] == 12.0
    assert data["cpcb_aqi"]["method"] == "CPCB-2014"
    assert data["cpcb_aqi"]["value"] >= 0
    assert data["cpcb_aqi"]["dominant_pollutant"]
    assert data["provenance"]["provider"] == "fake"
    assert data["provenance"]["stale"] is False
    assert data["location"]["requested"] == READING
    assert body["meta"]["request_id"]
    assert response.headers["x-data-cache"] == "miss"
    assert response.headers["x-data-expires-at"]


async def test_second_current_call_hits_memory_cache(
    app: FastAPI,
    client: AsyncClient,
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., ProviderReading],
) -> None:
    provider = fake_provider(reading=reading_factory())
    app.state.air_provider = provider

    first = await client.get("/api/v1/air/current", params=READING)
    second = await client.get("/api/v1/air/current", params=READING)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.headers["x-data-cache"] == "hit"
    assert provider.calls == [("current", 28.61, 77.21)]


async def test_provider_failure_returns_503_without_invented_values(
    app: FastAPI,
    client: AsyncClient,
    fake_provider: Callable[..., object],
) -> None:
    app.state.air_provider = fake_provider(
        current_error=AirQualityProviderError("upstream down", kind="http_error")
    )

    response = await client.get("/api/v1/air/current", params=READING)

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["code"] == "PROVIDER_UNAVAILABLE"
    assert "pm2_5" not in body
    assert "upstream down" not in response.text


async def test_forecast_returns_only_supplied_hours(
    app: FastAPI,
    client: AsyncClient,
    fake_provider: Callable[..., object],
    forecast_factory: Callable[..., object],
) -> None:
    app.state.air_provider = fake_provider(forecast=forecast_factory(hours=48))

    response = await client.get("/api/v1/air/forecast", params={**READING, "hours": 24})

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]["hourly"]) == 24
    assert body["data"]["provenance"]["provider"] == "fake"
    assert body["data"]["location"]["requested"] == READING


async def test_history_returns_daily_points(
    app: FastAPI,
    client: AsyncClient,
    fake_provider: Callable[..., object],
    history_factory: Callable[..., object],
) -> None:
    app.state.air_provider = fake_provider(history=history_factory(days=7))

    response = await client.get("/api/v1/air/history", params={**READING, "days": 7})

    assert response.status_code == 200
    daily = response.json()["data"]["daily"]
    assert len(daily) == 7
    assert all(point["pm2_5"] is not None for point in daily)


async def test_invalid_coordinates_are_rejected(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/air/current", params={"lat": 100, "lon": 77.21}
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["errors"][0]["field"] == "lat"


async def test_public_rate_limit_returns_retry_after(
    app: FastAPI,
    client: AsyncClient,
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., ProviderReading],
) -> None:
    app.state.air_provider = fake_provider(reading=reading_factory())
    app.state.settings.rate_limit_public_per_minute = 1

    first = await client.get("/api/v1/air/current", params=READING)
    second = await client.get("/api/v1/air/current", params=READING)

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["retry-after"]
    assert second.json()["code"] == "RATE_LIMITED"


async def test_stale_snapshot_is_labelled_and_never_hidden(
    db_app: FastAPI,
    db_client: AsyncClient,
    fake_provider: Callable[..., object],
) -> None:
    from app.models.air import AirQualitySnapshot
    from app.repositories.air import key_for

    now = datetime.now(tz=UTC)
    async with db_app.state.database.session() as session:
        session.add(
            AirQualitySnapshot(
                provider="fake",
                lat_key=key_for(READING["lat"]),
                lon_key=key_for(READING["lon"]),
                kind="modelled",
                observed_at=now - timedelta(hours=2),
                fetched_at=now - timedelta(hours=1),
                expires_at=now - timedelta(minutes=30),
                pm2_5=91.0,
                pm10=150.0,
            )
        )
        await session.commit()

    db_app.state.air_provider = fake_provider(
        current_error=AirQualityProviderError("upstream down", kind="timeout")
    )

    response = await db_client.get("/api/v1/air/current", params=READING)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["reading"]["pm2_5"] == 91.0
    assert data["provenance"]["stale"] is True


async def test_fresh_snapshot_is_served_without_calling_the_provider(
    db_app: FastAPI,
    db_client: AsyncClient,
    fake_provider: Callable[..., object],
) -> None:
    from app.models.air import AirQualitySnapshot
    from app.repositories.air import key_for

    provider = fake_provider()
    now = datetime.now(tz=UTC)
    async with db_app.state.database.session() as session:
        session.add(
            AirQualitySnapshot(
                provider="fake",
                lat_key=key_for(READING["lat"]),
                lon_key=key_for(READING["lon"]),
                kind="modelled",
                observed_at=now - timedelta(minutes=5),
                fetched_at=now - timedelta(minutes=5),
                expires_at=now + timedelta(minutes=25),
                pm2_5=44.0,
                pm10=70.0,
            )
        )
        await session.commit()

    db_app.state.air_provider = provider

    response = await db_client.get("/api/v1/air/current", params=READING)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["reading"]["pm2_5"] == 44.0
    assert data["provenance"]["stale"] is False
    assert provider.calls == []
