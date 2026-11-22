from __future__ import annotations

from httpx import AsyncClient


async def test_create_session_returns_token_once(db_client: AsyncClient) -> None:
    response = await db_client.post(
        "/api/v1/sessions",
        json={"consent_version": "2026-11", "health_consent": False},
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert len(data["token"]) >= 40
    assert data["profile_id"]
    assert data["expires_at"]

    me = await db_client.get(
        "/api/v1/sessions/me",
        headers={"Authorization": f"Bearer {data['token']}"},
    )
    assert me.status_code == 200
    info = me.json()["data"]
    assert info["profile_id"] == data["profile_id"]
    assert info["has_household"] is False
    assert info["consent"]["health_consent_at"] is None


async def test_missing_or_invalid_token_is_401(db_client: AsyncClient) -> None:
    missing = await db_client.get("/api/v1/sessions/me")
    invalid = await db_client.get(
        "/api/v1/sessions/me", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert missing.json()["code"] == "UNAUTHORIZED"


async def test_health_consent_can_be_granted(db_client: AsyncClient) -> None:
    created = await db_client.post(
        "/api/v1/sessions",
        json={"consent_version": "2026-11", "health_consent": False},
    )
    headers = {"Authorization": f"Bearer {created.json()['data']['token']}"}

    response = await db_client.post(
        "/api/v1/sessions/me/consent", json={"health_consent": True}, headers=headers
    )

    assert response.status_code == 200
    consent = response.json()["data"]["consent"]
    assert consent["version"] == "2026-11"
    assert consent["health_consent_at"] is not None


async def test_delete_removes_the_session_and_its_data(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    household = await db_client.put(
        "/api/v1/household",
        headers=auth_headers,
        json={
            "lat": 28.61,
            "lon": 77.21,
            "timezone": "Asia/Kolkata",
            "dwelling": "apartment_upper",
            "cooking_fuel": "lpg",
        },
    )
    assert household.status_code == 200

    deleted = await db_client.delete("/api/v1/sessions/me", headers=auth_headers)

    assert deleted.status_code == 204
    after = await db_client.get("/api/v1/sessions/me", headers=auth_headers)
    assert after.status_code == 401
