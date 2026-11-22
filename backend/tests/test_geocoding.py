from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from app.integrations.geocoding.client import GeocodingClient, GeocodingError

Handler = Callable[[httpx.Request], httpx.Response]


def _client(handler: Handler) -> GeocodingClient:
    return GeocodingClient(
        httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://geocoding-api.open-meteo.com/v1",
        )
    )


async def test_search_returns_every_candidate_without_choosing() -> None:
    payload = {
        "results": [
            {
                "id": 1264527,
                "name": "Chennai",
                "latitude": 13.08784,
                "longitude": 80.27847,
                "country": "India",
                "country_code": "IN",
                "admin1": "Tamil Nadu",
                "timezone": "Asia/Kolkata",
                "population": 4328063,
            },
            {
                "id": 1258526,
                "name": "Chennai",
                "latitude": 15.0,
                "longitude": 80.0,
                "country": "India",
                "country_code": "IN",
                "admin1": "Andhra Pradesh",
                "timezone": "Asia/Kolkata",
            },
        ]
    }
    client = _client(lambda _request: httpx.Response(200, json=payload))

    results = await client.search(query="Chennai", count=10, country_code="in")

    assert [place.id for place in results] == ["1264527", "1258526"]
    assert results[0].admin1 == "Tamil Nadu"
    assert results[1].population is None


async def test_missing_results_is_an_empty_list() -> None:
    client = _client(lambda _request: httpx.Response(200, json={}))

    assert await client.search(query="Nowhere", count=5) == ()


async def test_invalid_coordinates_are_skipped() -> None:
    payload = {
        "results": [
            {"id": 1, "name": "Broken", "latitude": 200, "longitude": 10},
            {
                "id": 2,
                "name": "Delhi",
                "latitude": 28.61,
                "longitude": 77.21,
                "country_code": "IN",
            },
        ]
    }
    client = _client(lambda _request: httpx.Response(200, json=payload))

    results = await client.search(query="Delhi", count=5)

    assert [place.name for place in results] == ["Delhi"]


async def test_server_error_is_retryable() -> None:
    client = _client(lambda _request: httpx.Response(500, json={"error": True}))

    with pytest.raises(GeocodingError) as caught:
        await client.search(query="Delhi", count=5)

    assert caught.value.kind == "http_error"
    assert caught.value.retryable is True


async def test_rate_limit_is_reported_separately() -> None:
    client = _client(lambda _request: httpx.Response(429, json={}))

    with pytest.raises(GeocodingError) as caught:
        await client.search(query="Delhi", count=5)

    assert caught.value.kind == "rate_limited"
