from __future__ import annotations

from fastapi import FastAPI
from httpx import AsyncClient


class _UnreachableDatabase:
    """Duck-typed stand-in for a configured database that cannot answer."""

    is_configured = True

    async def check(self) -> bool:
        return False

    async def dispose(self) -> None:
        return None


async def test_health_returns_structured_payload(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["service"] == "SAANS SAATHI API"
    assert body["version"] == "0.1.0"
    assert body["environment"] == "test"
    assert body["checks"] == {
        "database": "not_configured",
        "ai_provider": "not_configured",
        "air_quality_provider": "configured",
    }
    assert "timestamp" in body


async def test_health_does_not_leak_infrastructure_details(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/health")
    text = response.text.lower()

    assert "postgresql" not in text
    assert "password" not in text
    assert "traceback" not in text
    assert "gemini" not in text


async def test_health_sets_request_id_header(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    request_id = response.headers.get("x-request-id")
    assert request_id is not None
    assert len(request_id) >= 8


async def test_valid_request_id_is_echoed(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/health",
        headers={"X-Request-ID": "client-supplied-1234"},
    )

    assert response.headers["x-request-id"] == "client-supplied-1234"


async def test_unsafe_request_id_is_replaced(client: AsyncClient) -> None:
    unsafe = "bad id with spaces and $cript"
    response = await client.get("/api/v1/health", headers={"X-Request-ID": unsafe})

    assert response.headers["x-request-id"] != unsafe


async def test_database_failure_yields_503_without_internals(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    app.state.database = _UnreachableDatabase()

    response = await client.get("/api/v1/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unhealthy"
    assert body["checks"]["database"] == "unavailable"
    text = response.text.lower()
    assert "postgresql" not in text
    assert "traceback" not in text
