"""Step 10: EcoRoute AI + Impact Intelligence tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.domain.carbon import (
    BUS_FACTOR_KEY,
    TRAIN_FACTOR_KEY,
    transport_co2e,
    transport_co2e_per_passenger,
)
from app.domain.factors import get_factor, load_factors
from app.integrations.air_quality.base import AirQualityProviderError

# ============================================================================
# Domain: carbon calculation tests
# ============================================================================


def test_car_emissions_per_passenger() -> None:
    result = transport_co2e_per_passenger(mode="car", distance_km=10.0, passengers=2)
    assert result is not None
    assert result.mode == "car"
    assert result.distance_km == 10.0
    assert result.passengers == 2
    # Per-passenger = total / 2
    assert result.per_passenger_kg_co2e == result.total_kg_co2e / 2
    assert result.factor_key == "petrol_combustion"
    assert (
        result.allocation_method
        == "total vehicle emissions divided equally across passengers"
    )


def test_two_wheeler_emissions_per_passenger() -> None:
    result = transport_co2e_per_passenger(
        mode="two-wheeler", distance_km=5.0, passengers=1
    )
    assert result is not None
    assert result.per_passenger_kg_co2e == result.total_kg_co2e


def test_walk_zero_emissions() -> None:
    result = transport_co2e_per_passenger(mode="walk", distance_km=3.0, passengers=1)
    assert result is not None
    assert result.total_kg_co2e == 0.0
    assert result.per_passenger_kg_co2e == 0.0


def test_cycle_zero_emissions() -> None:
    result = transport_co2e_per_passenger(mode="cycle", distance_km=3.0, passengers=1)
    assert result is not None
    assert result.total_kg_co2e == 0.0
    assert result.per_passenger_kg_co2e == 0.0


def test_bus_emissions_per_passenger_km() -> None:
    result = transport_co2e_per_passenger(mode="bus", distance_km=10.0, passengers=4)
    assert result is not None
    factor = get_factor(BUS_FACTOR_KEY)
    expected_per_passenger = 10.0 * factor.value
    # DEFRA factor is per-passenger-km; passenger count doesn't change rate
    assert result.per_passenger_kg_co2e == round(expected_per_passenger, 4)
    assert result.total_kg_co2e == round(expected_per_passenger * 4, 4)
    assert result.factor_key == BUS_FACTOR_KEY


def test_train_emissions_per_passenger_km() -> None:
    result = transport_co2e_per_passenger(mode="train", distance_km=20.0, passengers=2)
    assert result is not None
    factor = get_factor(TRAIN_FACTOR_KEY)
    expected_per_passenger = 20.0 * factor.value
    assert result.per_passenger_kg_co2e == round(expected_per_passenger, 4)
    assert result.total_kg_co2e == round(expected_per_passenger * 2, 4)
    assert result.factor_key == TRAIN_FACTOR_KEY


def test_metro_no_factor_returns_none() -> None:
    result = transport_co2e_per_passenger(mode="metro", distance_km=10.0, passengers=1)
    assert result is None


def test_shared_mobility_no_factor_returns_none() -> None:
    result = transport_co2e_per_passenger(
        mode="shared-mobility", distance_km=10.0, passengers=1
    )
    assert result is None


def test_negative_distance_rejected() -> None:
    with pytest.raises(ValueError, match="Distance cannot be negative"):
        transport_co2e_per_passenger(mode="car", distance_km=-1.0, passengers=1)


def test_zero_passengers_rejected() -> None:
    with pytest.raises(ValueError, match="Passenger count must be at least 1"):
        transport_co2e_per_passenger(mode="car", distance_km=10.0, passengers=0)


def test_transport_co2e_bus_per_passenger() -> None:
    # transport_co2e returns emissions for one passenger for bus/train
    result = transport_co2e(mode="bus", distance_km=10.0)
    assert result is not None
    factor = get_factor(BUS_FACTOR_KEY)
    assert result.kg_co2e == round(10.0 * factor.value, 4)


def test_factor_registry_has_bus_and_train() -> None:
    keys = {f.key for f in load_factors()}
    assert BUS_FACTOR_KEY in keys
    assert TRAIN_FACTOR_KEY in keys
    bus = get_factor(BUS_FACTOR_KEY)
    train = get_factor(TRAIN_FACTOR_KEY)
    assert bus.verified is True
    assert train.verified is True
    assert str(bus.source_url).startswith("https://")
    assert str(train.source_url).startswith("https://")


# ============================================================================
# API: EcoRoute comparison tests
# ============================================================================


ECO_REQUEST = {
    "origin": {"lat": 28.6139, "lon": 77.209},
    "destination": {"lat": 28.5355, "lon": 77.241},
    "modes": ["walk", "cycle", "car", "bus", "train"],
    "passengers": 2,
}


async def test_compare_includes_bus_and_train(
    app: FastAPI,
    client: AsyncClient,
    fake_provider,
    reading_factory,
) -> None:
    app.state.air_provider = fake_provider(reading=reading_factory(pm2_5=95.0))
    response = await client.post("/api/v1/ecoroute/compare", json=ECO_REQUEST)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    modes = {item["mode"]: item for item in data["modes"]}
    assert "bus" in modes
    assert "train" in modes
    assert modes["bus"]["co2e_kg"] is not None
    assert modes["train"]["co2e_kg"] is not None
    assert modes["bus"]["co2e_per_passenger_kg"] is not None
    assert modes["train"]["co2e_per_passenger_kg"] is not None
    assert modes["walk"]["co2e_kg"] == 0.0
    assert modes["cycle"]["co2e_kg"] == 0.0
    assert modes["car"]["co2e_kg"] > 0
    assert modes["car"]["co2e_per_passenger_kg"] is not None


async def test_compare_filters_by_accessibility(
    app: FastAPI,
    client: AsyncClient,
    fake_provider,
    reading_factory,
) -> None:
    app.state.air_provider = fake_provider(reading=reading_factory(pm2_5=30.0))
    payload = {
        **ECO_REQUEST,
        "accessibility_needs": ["wheelchair"],
        "modes": ["walk", "cycle", "car", "bus", "train"],
    }
    response = await client.post("/api/v1/ecoroute/compare", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    modes = {item["mode"]: item for item in data["modes"]}
    # Car should be filtered out when wheelchair accessibility is required
    assert "car" not in modes
    assert modes.get("bus", {}).get("accessible") is True
    assert modes.get("train", {}).get("accessible") is True


async def test_compare_filters_by_max_duration(
    app: FastAPI,
    client: AsyncClient,
    fake_provider,
    reading_factory,
) -> None:
    app.state.air_provider = fake_provider(reading=reading_factory(pm2_5=30.0))
    payload = {
        **ECO_REQUEST,
        "max_duration_min": 5,  # Very short - should filter out most modes
        "modes": ["walk", "cycle", "car", "bus", "train"],
    }
    response = await client.post("/api/v1/ecoroute/compare", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    # With max 5 min, even walk/cycle at that distance may exceed it
    # At minimum, car with 5 min wait should be excluded
    modes = {item["mode"]: item for item in data["modes"]}
    if "car" in modes:
        assert modes["car"]["duration_min"] <= 5


async def test_compare_rejects_negative_passengers(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/ecoroute/compare",
        json={**ECO_REQUEST, "passengers": 0},
    )
    assert response.status_code == 422


async def test_compare_rejects_duplicate_modes(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/ecoroute/compare",
        json={**ECO_REQUEST, "modes": ["car", "car"]},
    )
    assert response.status_code == 422


async def test_compare_rejects_out_of_range_coordinates(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/ecoroute/compare",
        json={**ECO_REQUEST, "origin": {"lat": -91, "lon": 77}},
    )
    assert response.status_code == 422


async def test_compare_air_unavailable(
    app: FastAPI,
    client: AsyncClient,
    fake_provider,
) -> None:
    app.state.air_provider = fake_provider(
        current_error=AirQualityProviderError("down", kind="http_error")
    )
    response = await client.post("/api/v1/ecoroute/compare", json=ECO_REQUEST)
    assert response.status_code == 200
    data = response.json()["data"]
    assert all(item["exposure_index"] is None for item in data["modes"])


# ============================================================================
# API: Calculate emissions tests
# ============================================================================


async def test_calculate_emissions_car(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/ecoroute/calculate-emissions",
        params={"mode": "car", "distance_km": 10.0, "passengers": 2},
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["mode"] == "car"
    assert data["distance_km"] == 10.0
    assert data["passengers"] == 2
    assert data["total_kg_co2e"] > 0
    assert data["per_passenger_kg_co2e"] == data["total_kg_co2e"] / 2
    assert data["factor_key"] == "petrol_combustion"
    assert data["factor_source_url"].startswith("https://")


async def test_calculate_emissions_bus(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/ecoroute/calculate-emissions",
        params={"mode": "bus", "distance_km": 10.0, "passengers": 4},
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["mode"] == "bus"
    assert data["factor_key"] == BUS_FACTOR_KEY
    # Per-passenger doesn't change with passenger count for bus
    assert data["per_passenger_kg_co2e"] > 0


async def test_calculate_emissions_unsupported_mode(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/ecoroute/calculate-emissions",
        params={"mode": "metro", "distance_km": 10.0, "passengers": 1},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "FACTOR_NOT_AVAILABLE"


async def test_calculate_emissions_invalid_mode(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/ecoroute/calculate-emissions",
        params={"mode": "invalid", "distance_km": 10.0, "passengers": 1},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "UNSUPPORTED_MODE"


# ============================================================================
# API: Provider health test
# ============================================================================


async def test_provider_health(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ecoroute/providers/health")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) >= 1
    haversine = next((p for p in data if p["name"] == "haversine"), None)
    assert haversine is not None
    assert haversine["healthy"] is True


# ============================================================================
# API: Impact goals tests
# ============================================================================


HOUSEHOLD = {
    "lat": 28.6139,
    "lon": 77.209,
    "timezone": "Asia/Kolkata",
    "dwelling": "apartment_upper",
    "cooking_fuel": "lpg",
}


async def test_impact_goals_crud(
    db_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    await db_client.put("/api/v1/household", headers=auth_headers, json=HOUSEHOLD)

    # Create goal
    created = await db_client.post(
        "/api/v1/impact/goals",
        headers=auth_headers,
        json={
            "title": "Walk 100 km this month",
            "description": "Replace short car trips with walking",
            "activity_type": "walked",
            "unit": "km",
            "target_value": 100.0,
            "target_date": (datetime.now(tz=UTC) + timedelta(days=30))
            .date()
            .isoformat(),
        },
    )
    assert created.status_code == 201, created.text
    goal = created.json()["data"]
    assert goal["title"] == "Walk 100 km this month"
    assert goal["target_value"] == 100.0
    assert goal["current_value"] == 0.0
    assert goal["progress_percent"] == 0.0
    assert goal["is_complete"] is False
    goal_id = goal["id"]

    # List goals
    listed = await db_client.get("/api/v1/impact/goals", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()["data"]) == 1

    # Update goal
    updated = await db_client.put(
        f"/api/v1/impact/goals/{goal_id}",
        headers=auth_headers,
        json={"target_value": 150.0},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["target_value"] == 150.0

    # Delete goal
    deleted = await db_client.delete(
        f"/api/v1/impact/goals/{goal_id}", headers=auth_headers
    )
    assert deleted.status_code == 204

    # Verify deletion
    listed2 = await db_client.get("/api/v1/impact/goals", headers=auth_headers)
    assert len(listed2.json()["data"]) == 0


async def test_goal_unit_mismatch_rejected(
    db_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    await db_client.put("/api/v1/household", headers=auth_headers, json=HOUSEHOLD)
    response = await db_client.post(
        "/api/v1/impact/goals",
        headers=auth_headers,
        json={
            "title": "Bad goal",
            "activity_type": "walked",
            "unit": "trees",
            "target_value": 10.0,
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "UNIT_MISMATCH"


# ============================================================================
# API: Baseline and savings tests
# ============================================================================


async def test_baseline_and_savings(
    db_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    await db_client.put("/api/v1/household", headers=auth_headers, json=HOUSEHOLD)
    today = datetime.now(tz=UTC).date().isoformat()

    # Log an activity
    await db_client.post(
        "/api/v1/impact/activities",
        headers=auth_headers,
        json={
            "activity_type": "walked",
            "quantity": 10,
            "unit": "km",
            "occurred_on": today,
        },
    )

    response = await db_client.get(
        "/api/v1/impact/baseline-savings", headers=auth_headers
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["activity_co2e_kg"] > 0
    assert data["baseline_co2e_kg"] is not None
    assert data["baseline_basis"] is not None
    assert "not a measured baseline" in data["baseline_basis"].lower()
    assert data["savings_co2e_kg"] is not None
    assert data["savings_basis"] is not None


# ============================================================================
# API: Trends test
# ============================================================================


async def test_trends(
    db_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    await db_client.put("/api/v1/household", headers=auth_headers, json=HOUSEHOLD)
    today = datetime.now(tz=UTC).date().isoformat()

    await db_client.post(
        "/api/v1/impact/activities",
        headers=auth_headers,
        json={
            "activity_type": "walked",
            "quantity": 5,
            "unit": "km",
            "occurred_on": today,
        },
    )

    response = await db_client.get("/api/v1/impact/trends", headers=auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert "weekly" in data
    assert "monthly" in data
    assert len(data["weekly"]) >= 1
    assert data["weekly"][0]["co2e_kg"] > 0


# ============================================================================
# API: Methodology test
# ============================================================================


async def test_methodology(client: AsyncClient) -> None:
    response = await client.get("/api/v1/impact/methodology")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "formula" in data
    assert "factors_used" in data
    assert "assumptions" in data
    assert "limitations" in data
    assert "petrol_combustion" in data["factors_used"]
    assert BUS_FACTOR_KEY in data["factors_used"]
    assert TRAIN_FACTOR_KEY in data["factors_used"]


# ============================================================================
# API: Duplicate activity prevention
# ============================================================================


async def test_duplicate_activity_rejected(
    db_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    await db_client.put("/api/v1/household", headers=auth_headers, json=HOUSEHOLD)
    today = datetime.now(tz=UTC).date().isoformat()

    await db_client.post(
        "/api/v1/impact/activities",
        headers=auth_headers,
        json={
            "activity_type": "walked",
            "quantity": 10,
            "unit": "km",
            "occurred_on": today,
        },
    )

    response = await db_client.post(
        "/api/v1/impact/activities",
        headers=auth_headers,
        json={
            "activity_type": "walked",
            "quantity": 10,
            "unit": "km",
            "occurred_on": today,
        },
    )
    assert response.status_code == 409
    assert response.json()["code"] == "DUPLICATE_ACTIVITY"


# ============================================================================
# API: Unauthorized access
# ============================================================================


async def test_unauthorized_access(db_client: AsyncClient) -> None:
    response = await db_client.post("/api/v1/impact/goals", json={})
    assert response.status_code == 401


async def test_unauthorized_ecoroute(client: AsyncClient) -> None:
    response = await client.post("/api/v1/ecoroute/compare", json=ECO_REQUEST)
    # ecoroute compare is public rate-limited, no auth required
    assert response.status_code == 200
