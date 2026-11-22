"""Household error paths and consent rules not covered by the main suite."""

from __future__ import annotations

from uuid import uuid4

from httpx import AsyncClient

HOUSEHOLD = {
    "lat": 28.6139,
    "lon": 77.209,
    "timezone": "Asia/Kolkata",
    "dwelling": "apartment_upper",
    "cooking_fuel": "lpg",
}


async def test_features_require_a_household_first(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    member = await db_client.post(
        "/api/v1/household/members",
        headers=auth_headers,
        json={"age_band": "18-59", "health_flags": []},
    )
    preferences = await db_client.get(
        "/api/v1/household/preferences", headers=auth_headers
    )
    preferences_update = await db_client.put(
        "/api/v1/household/preferences",
        headers=auth_headers,
        json={"locale": "en-IN", "activity_windows": []},
    )
    locations = await db_client.get(
        "/api/v1/household/locations", headers=auth_headers
    )
    location = await db_client.post(
        "/api/v1/household/locations",
        headers=auth_headers,
        json={"label": "Home", "kind": "home", "lat": 28.6, "lon": 77.2},
    )

    for response in (
        member,
        preferences,
        preferences_update,
        locations,
        location,
    ):
        assert response.status_code == 409, response.text
        assert response.json()["code"] == "CONFLICT"


async def test_missing_members_and_locations_are_404(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await db_client.put("/api/v1/household", headers=auth_headers, json=HOUSEHOLD)
    missing = uuid4()

    updated = await db_client.patch(
        f"/api/v1/household/members/{missing}",
        headers=auth_headers,
        json={"age_band": "18-59"},
    )
    removed = await db_client.delete(
        f"/api/v1/household/members/{missing}", headers=auth_headers
    )
    deleted_location = await db_client.delete(
        f"/api/v1/household/locations/{missing}", headers=auth_headers
    )

    assert updated.status_code == 404
    assert removed.status_code == 404
    assert deleted_location.status_code == 404


async def test_updating_to_health_flags_requires_consent(
    db_client: AsyncClient, plain_headers: dict[str, str]
) -> None:
    await db_client.put("/api/v1/household", headers=plain_headers, json=HOUSEHOLD)
    created = await db_client.post(
        "/api/v1/household/members",
        headers=plain_headers,
        json={"age_band": "18-59", "health_flags": []},
    )
    assert created.status_code == 201
    member = created.json()["data"]

    updated = await db_client.patch(
        f"/api/v1/household/members/{member['id']}",
        headers=plain_headers,
        json={"health_flags": ["asthma"]},
    )

    assert updated.status_code == 403
    assert updated.json()["code"] == "CONSENT_REQUIRED"
