from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, Field

from app.core.exceptions import NotFoundError


class _Payload(BaseModel):
    name: str = Field(min_length=3)


@pytest.fixture
async def error_client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    @app.get("/api/v1/_test/not-found")
    async def _raise_not_found() -> None:
        raise NotFoundError("The requested plan does not exist.")

    @app.post("/api/v1/_test/echo")
    async def _echo(payload: _Payload) -> _Payload:
        return payload

    @app.get("/api/v1/_test/crash")
    async def _crash() -> None:
        raise RuntimeError("boom: internal detail that must not leak")

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http


async def test_unknown_route_uses_problem_json(client: AsyncClient) -> None:
    response = await client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["code"] == "NOT_FOUND"
    assert body["status"] == 404
    assert body["instance"] == "/api/v1/does-not-exist"
    assert body["request_id"]
    assert "detail" in body


async def test_application_error_keeps_its_code(error_client: AsyncClient) -> None:
    response = await error_client.get("/api/v1/_test/not-found")

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "NOT_FOUND"
    assert body["detail"] == "The requested plan does not exist."


async def test_validation_error_is_field_scoped(error_client: AsyncClient) -> None:
    response = await error_client.post("/api/v1/_test/echo", json={"name": "x"})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["errors"][0]["field"] == "name"
    assert "input" not in body["errors"][0]
    assert "ctx" not in body["errors"][0]


async def test_unhandled_exception_is_sanitised(error_client: AsyncClient) -> None:
    response = await error_client.get("/api/v1/_test/crash")

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert "boom" not in response.text
    assert "Traceback" not in response.text
    assert body["request_id"]
