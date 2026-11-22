from __future__ import annotations

from collections.abc import Callable

from fastapi import FastAPI
from httpx import AsyncClient

from app.integrations.air_quality.base import (
    AirQualityProviderError,
    ProviderReading,
)

LOCATION = {"location": {"lat": 28.61, "lon": 77.21}}


async def test_assessment_returns_an_interval_with_assumptions(
    app: FastAPI,
    client: AsyncClient,
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., ProviderReading],
    forecast_factory: Callable[..., object],
) -> None:
    app.state.air_provider = fake_provider(
        reading=reading_factory(pm2_5=120.0, pm10=190.0),
        forecast=forecast_factory(hours=24, pm2_5=40.0),
    )

    response = await client.post(
        "/api/v1/indoor/assess",
        json={
            **LOCATION,
            "overrides": {
                "purifier_cadr": 200,
                "room_area_m2": 25,
                "ceiling_m": 2.8,
            },
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["outdoor"]["pm2_5"] == 120.0
    assert data["indoor"]["pm2_5_low"] <= data["indoor"]["pm2_5_high"]
    assert data["indoor"]["purifier_cadr"] == 200
    assert data["indoor"]["volume_m3"] == 70.0
    assert data["indoor"]["recommended_cadr"] > 0
    assert data["ventilation"] is not None
    assert data["actions"]
    assert len(data["assumptions"]) >= 3
    assert "not a measurement" in data["disclaimer"] or "not a" in data["disclaimer"]


async def test_assessment_without_location_is_422(client: AsyncClient) -> None:
    response = await client.post("/api/v1/indoor/assess", json={})

    assert response.status_code == 422
    assert response.json()["code"] == "NO_LOCATION"


async def test_missing_pm2_5_is_reported_not_estimated(
    app: FastAPI,
    client: AsyncClient,
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., ProviderReading],
) -> None:
    app.state.air_provider = fake_provider(
        reading=reading_factory(pm2_5=None, pm10=90.0)
    )

    response = await client.post("/api/v1/indoor/assess", json=LOCATION)

    assert response.status_code == 422
    assert response.json()["code"] == "OUTDOOR_PM25_UNAVAILABLE"


async def test_ventilation_is_null_when_forecast_fails(
    app: FastAPI,
    client: AsyncClient,
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., ProviderReading],
) -> None:
    app.state.air_provider = fake_provider(
        reading=reading_factory(),
        forecast_error=AirQualityProviderError("no forecast", kind="timeout"),
    )

    response = await client.post("/api/v1/indoor/assess", json=LOCATION)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["ventilation"] is None
    assert data["outdoor"]["stale"] is False


async def test_household_defaults_can_be_overridden(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., ProviderReading],
) -> None:
    await db_client.put(
        "/api/v1/household",
        headers=auth_headers,
        json={
            "lat": 28.6139,
            "lon": 77.209,
            "timezone": "Asia/Kolkata",
            "dwelling": "independent",
            "cooking_fuel": "png",
            "room_area_m2": 30,
            "ceiling_m": 3.0,
        },
    )
    db_app.state.air_provider = fake_provider(reading=reading_factory(pm2_5=55.0))

    response = await db_client.post(
        "/api/v1/indoor/assess", headers=auth_headers, json={}
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["indoor"]["volume_m3"] == 90.0
    assert data["indoor"]["purifier_cadr"] == 0
