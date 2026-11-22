from __future__ import annotations

from httpx import AsyncClient


async def test_preflight_allows_configured_frontend_origin(
    client: AsyncClient,
) -> None:
    response = await client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


async def test_preflight_rejects_unknown_origin(client: AsyncClient) -> None:
    response = await client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers
