from __future__ import annotations

from datetime import UTC, datetime

from httpx import AsyncClient

HOUSEHOLD = {
    "lat": 28.6139,
    "lon": 77.209,
    "timezone": "Asia/Kolkata",
    "dwelling": "apartment_upper",
    "cooking_fuel": "lpg",
}


async def test_factors_expose_provenance(client: AsyncClient) -> None:
    response = await client.get("/api/v1/impact/factors")

    assert response.status_code == 200
    factors = response.json()["data"]
    # Base factors + bus + train DEFRA-2023 factors
    assert len(factors) == 5
    keys = {factor["key"] for factor in factors}
    assert {"petrol_combustion", "diesel_combustion", "grid_india_cea_v22", "bus_average_uk_defra_2023", "train_national_rail_uk_defra_2023"} <= keys
    for factor in factors:
        assert factor["source_url"].startswith("https://")
        assert factor["version"]
        assert factor["value"] > 0


async def test_activity_requires_a_household(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await db_client.post(
        "/api/v1/impact/activities",
        headers=auth_headers,
        json={
            "activity_type": "walked",
            "quantity": 5,
            "occurred_on": datetime.now(tz=UTC).date().isoformat(),
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "NO_HOUSEHOLD"


async def test_logged_activity_is_summarised(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await db_client.put("/api/v1/household", headers=auth_headers, json=HOUSEHOLD)
    today = datetime.now(tz=UTC).date().isoformat()

    created = await db_client.post(
        "/api/v1/impact/activities",
        headers=auth_headers,
        json={
            "activity_type": "walked",
            "quantity": 10,
            "unit": "km",
            "occurred_on": today,
        },
    )

    assert created.status_code == 201, created.text
    activity = created.json()["data"]
    assert activity["activity_type"] == "walked"
    assert activity["unit"] == "km"
    assert activity["co2e_kg"] > 0
    assert activity["factor_version"] == "IPCC-2006"
    assert activity["factor_source_url"].startswith("https://")

    listed = await db_client.get("/api/v1/impact/activities", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()["data"]) == 1

    summary = await db_client.get("/api/v1/impact/summary", headers=auth_headers)
    assert summary.status_code == 200
    data = summary.json()["data"]
    assert data["range"] == "30d"
    assert data["activity_count"] == 1
    assert data["total_co2e_kg"] > 0
    assert data["by_type"][0]["activity_type"] == "walked"


async def test_unverified_activity_type_is_rejected(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await db_client.put("/api/v1/household", headers=auth_headers, json=HOUSEHOLD)

    response = await db_client.post(
        "/api/v1/impact/activities",
        headers=auth_headers,
        json={
            "activity_type": "public-transport",
            "quantity": 12,
            "occurred_on": datetime.now(tz=UTC).date().isoformat(),
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "FACTOR_NOT_AVAILABLE"
    assert "guessed" in body["detail"]


async def test_unit_mismatch_is_rejected(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await db_client.put("/api/v1/household", headers=auth_headers, json=HOUSEHOLD)

    response = await db_client.post(
        "/api/v1/impact/activities",
        headers=auth_headers,
        json={
            "activity_type": "walked",
            "quantity": 10,
            "unit": "days",
            "occurred_on": datetime.now(tz=UTC).date().isoformat(),
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "UNIT_MISMATCH"
