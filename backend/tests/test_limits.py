from __future__ import annotations

from httpx import AsyncClient


async def test_oversized_body_is_rejected_before_the_handler(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/copilot/chat",
        content=b"x" * 40_000,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 413
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["code"] == "PAYLOAD_TOO_LARGE"
    assert body["request_id"]


async def test_responses_carry_defensive_headers(client: AsyncClient) -> None:
    response = await client.get("/api/v1/meta")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-request-id"]


async def test_database_backed_endpoint_reports_unavailable_storage(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/household", headers={"Authorization": "Bearer a-token"}
    )

    assert response.status_code == 503
    assert response.json()["code"] == "SERVICE_UNAVAILABLE"
    assert "not configured" in response.json()["detail"]


async def test_meta_does_not_leak_secrets(client: AsyncClient) -> None:
    response = await client.get("/api/v1/meta")

    assert response.status_code == 200
    text = response.text.lower()
    assert "api_key" not in text
    assert "postgresql" not in text
    assert "password" not in text
    data = response.json()["data"]
    assert data["ai_configured"] is False
    assert data["air_provider"]["name"] == "open-meteo"
