from __future__ import annotations

from collections.abc import Callable

from fastapi import FastAPI
from httpx import AsyncClient

from app.integrations.air_quality.base import AirQualityProviderError

REQUEST = {
    "origin": {"lat": 28.6139, "lon": 77.209},
    "destination": {"lat": 28.5355, "lon": 77.241},
    "modes": ["walk", "cycle", "car", "bus", "train", "metro"],
}


async def test_compare_reports_carbon_and_exposure(
    app: FastAPI,
    client: AsyncClient,
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., object],
) -> None:
    app.state.air_provider = fake_provider(reading=reading_factory(pm2_5=95.0))

    response = await client.post("/api/v1/ecoroute/compare", json=REQUEST)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["route"]["distance_km"] > 0
    assert data["route"]["is_estimate"] is True
    modes = {item["mode"]: item for item in data["modes"]}

    assert modes["walk"]["co2e_kg"] == 0.0
    assert modes["cycle"]["co2e_kg"] == 0.0
    assert modes["car"]["co2e_kg"] > 0
    # Bus and train now have verified DEFRA-2023 per-passenger-km factors.
    assert modes["bus"]["co2e_kg"] is not None
    assert modes["train"]["co2e_kg"] is not None
    assert modes["bus"]["co2e_per_passenger_kg"] is not None
    assert modes["train"]["co2e_per_passenger_kg"] is not None
    assert modes["metro"]["co2e_kg"] is None
    assert modes["car"]["exposure_index"] is not None
    assert all(item["duration_min"] > 0 for item in data["modes"])
    assert data["tradeoff_note"]
    assert any(item["key"] == "circuity_factor" for item in data["assumptions"])


async def test_compare_still_returns_when_air_data_is_unavailable(
    app: FastAPI,
    client: AsyncClient,
    fake_provider: Callable[..., object],
) -> None:
    app.state.air_provider = fake_provider(
        current_error=AirQualityProviderError("down", kind="http_error")
    )

    response = await client.post("/api/v1/ecoroute/compare", json=REQUEST)

    assert response.status_code == 200
    data = response.json()["data"]
    assert all(item["exposure_index"] is None for item in data["modes"])
    assert all(
        item["co2e_kg"] is not None for item in data["modes"] if item["mode"] == "car"
    )


async def test_duplicate_modes_are_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/ecoroute/compare", json={**REQUEST, "modes": ["car", "car"]}
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["errors"][0]["field"] == "modes"


async def test_out_of_range_coordinates_are_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/ecoroute/compare",
        json={**REQUEST, "origin": {"lat": -91, "lon": 77}},
    )

    assert response.status_code == 422
