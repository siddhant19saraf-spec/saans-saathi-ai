from __future__ import annotations

from httpx import AsyncClient

HOUSEHOLD = {
    "lat": 28.6139,
    "lon": 77.209,
    "city": "New Delhi",
    "timezone": "Asia/Kolkata",
    "dwelling": "apartment_upper",
    "cooking_fuel": "lpg",
    "has_purifier": True,
    "purifier_cadr": 300,
    "room_area_m2": 24,
    "ceiling_m": 2.7,
}


async def test_household_requires_authentication(db_client: AsyncClient) -> None:
    response = await db_client.get("/api/v1/household")

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


async def test_household_is_created_and_replaced(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await db_client.put(
        "/api/v1/household", headers=auth_headers, json=HOUSEHOLD
    )
    assert created.status_code == 200, created.text
    data = created.json()["data"]
    assert data["city"] == "New Delhi"
    assert data["purifier_cadr"] == 300
    assert data["members"] == []

    replaced = await db_client.put(
        "/api/v1/household",
        headers=auth_headers,
        json={**HOUSEHOLD, "city": "Gurugram", "has_purifier": False},
    )
    assert replaced.status_code == 200
    assert replaced.json()["data"]["city"] == "Gurugram"
    assert replaced.json()["data"]["has_purifier"] is False

    read = await db_client.get("/api/v1/household", headers=auth_headers)
    assert read.status_code == 200
    assert read.json()["data"]["id"] == data["id"]


async def test_missing_household_is_404(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await db_client.get("/api/v1/household", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


async def test_health_flags_require_consent(
    db_client: AsyncClient, plain_headers: dict[str, str]
) -> None:
    await db_client.put("/api/v1/household", headers=plain_headers, json=HOUSEHOLD)

    member = await db_client.post(
        "/api/v1/household/members",
        headers=plain_headers,
        json={"age_band": "6-12", "health_flags": ["asthma"]},
    )

    assert member.status_code == 403
    assert member.json()["code"] == "CONSENT_REQUIRED"


async def test_members_can_be_added_updated_and_removed(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await db_client.put("/api/v1/household", headers=auth_headers, json=HOUSEHOLD)

    created = await db_client.post(
        "/api/v1/household/members",
        headers=auth_headers,
        json={"age_band": "6-12", "health_flags": ["asthma"]},
    )
    assert created.status_code == 201, created.text
    member = created.json()["data"]
    assert member["age_band"] == "6-12"
    assert member["health_flags"] == ["asthma"]

    updated = await db_client.patch(
        f"/api/v1/household/members/{member['id']}",
        headers=auth_headers,
        json={"age_band": "13-17"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["age_band"] == "13-17"
    assert updated.json()["data"]["health_flags"] == ["asthma"]

    removed = await db_client.delete(
        f"/api/v1/household/members/{member['id']}", headers=auth_headers
    )
    assert removed.status_code == 204

    household = await db_client.get("/api/v1/household", headers=auth_headers)
    assert household.json()["data"]["members"] == []


async def test_preferences_default_and_update(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await db_client.put("/api/v1/household", headers=auth_headers, json=HOUSEHOLD)

    defaults = await db_client.get(
        "/api/v1/household/preferences", headers=auth_headers
    )
    assert defaults.status_code == 200
    assert defaults.json()["data"]["locale"] == "en-IN"
    assert defaults.json()["data"]["activity_windows"] == []

    window = {
        "id": "morning-walk",
        "title": "Morning walk",
        "start": "06:30",
        "duration_min": 60,
        "intensity": "light",
        "venue": "outdoor",
    }
    updated = await db_client.put(
        "/api/v1/household/preferences",
        headers=auth_headers,
        json={
            "locale": "en-IN",
            "activity_windows": [window],
            "alert_threshold_aqi": 120,
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["alert_threshold_aqi"] == 120
    assert updated.json()["data"]["activity_windows"][0]["id"] == "morning-walk"


async def test_saved_locations_reject_duplicate_labels(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await db_client.put("/api/v1/household", headers=auth_headers, json=HOUSEHOLD)
    payload = {"label": "Home", "kind": "home", "lat": 28.6139, "lon": 77.209}

    created = await db_client.post(
        "/api/v1/household/locations", headers=auth_headers, json=payload
    )
    assert created.status_code == 201
    duplicate = await db_client.post(
        "/api/v1/household/locations", headers=auth_headers, json=payload
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "CONFLICT"

    listed = await db_client.get("/api/v1/household/locations", headers=auth_headers)
    assert len(listed.json()["data"]) == 1

    deleted = await db_client.delete(
        f"/api/v1/household/locations/{created.json()['data']['id']}",
        headers=auth_headers,
    )
    assert deleted.status_code == 204

    empty = await db_client.get("/api/v1/household/locations", headers=auth_headers)
    assert empty.json()["data"] == []
