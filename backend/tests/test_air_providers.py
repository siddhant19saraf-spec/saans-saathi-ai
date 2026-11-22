from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import httpx
from fastapi import FastAPI
from httpx import AsyncClient

from app.integrations.air_quality.circuit import CircuitBreaker
from app.integrations.air_quality.openaq import OpenAQProvider
from app.integrations.geocoding.client import GeocodingClient
from app.services.air_quality_service import ProviderBinding

READING = {"lat": 28.61, "lon": 77.21}


def _openaq_provider(
    handler: Callable[[httpx.Request], httpx.Response],
) -> OpenAQProvider:
    return OpenAQProvider(
        httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://api.openaq.org",
        ),
        api_key="test-key",
    )


def _location_payload() -> dict[str, object]:
    return {
        "meta": {"name": "openaq-api", "page": 1, "limit": 20, "found": 1},
        "results": [
            {
                "id": 2178,
                "name": "ITO, Delhi",
                "timezone": "Asia/Kolkata",
                "country": {"code": "IN", "name": "India"},
                "provider": {"id": 119, "name": "CPCB"},
                "owner": {"id": 4, "name": "CPCB"},
                "isMonitor": True,
                "coordinates": {"latitude": 28.628, "longitude": 77.24},
                "sensors": [
                    {
                        "id": 123,
                        "parameter": {"id": 2, "name": "pm25", "units": "µg/m³"},
                    },
                    {
                        "id": 124,
                        "parameter": {"id": 1, "name": "pm10", "units": "µg/m³"},
                    },
                    {
                        "id": 125,
                        "parameter": {"id": 7, "name": "no2", "units": "ppm"},
                    },
                ],
                "licenses": [{"name": "CC BY 4.0", "attribution": "CPCB"}],
            }
        ],
    }


def _openaq_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/v3/locations":
        return httpx.Response(200, json=_location_payload())
    if request.url.path.endswith("/latest"):
        when = datetime.now(tz=UTC).isoformat()
        return httpx.Response(
            200,
            json={
                "meta": {"page": 1, "limit": 100, "found": 2},
                "results": [
                    {
                        "sensorsId": 123,
                        "value": 82.0,
                        "datetime": {"utc": when},
                    },
                    {
                        "sensorsId": 124,
                        "value": 140.0,
                        "datetime": {"utc": when},
                    },
                ],
            },
        )
    return httpx.Response(404, json={"detail": "not found"})


def _install_openaq(app: FastAPI) -> None:
    app.state.air_bindings["openaq"] = ProviderBinding(
        provider=_openaq_provider(_openaq_handler),
        breaker=CircuitBreaker(),
        budget_key="openaq",
        budget=100,
    )


async def test_air_quality_current_reports_source_type_and_windows(
    app: FastAPI,
    client: AsyncClient,
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., object],
) -> None:
    app.state.air_provider = fake_provider(reading=reading_factory())

    response = await client.get("/api/v1/air-quality/current", params=READING)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["provenance"]["source_type"] == "model_forecast"
    assert data["provenance"]["freshness"] == "fresh"
    assert data["cpcb_aqi"]["value"] >= 0
    assert data["cpcb_aqi"]["basis"]
    assert data["cpcb_aqi"]["averaging"]
    assert data["aqi_unavailable_reason"] is None


async def test_legacy_air_path_still_resolves(
    app: FastAPI,
    client: AsyncClient,
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., object],
) -> None:
    app.state.air_provider = fake_provider(reading=reading_factory())

    response = await client.get("/api/v1/air/current", params=READING)

    assert response.status_code == 200, response.text
    assert response.json()["data"]["reading"]["pm2_5"] == 82.0


async def test_openaq_current_is_labelled_ground_observation(
    app: FastAPI, client: AsyncClient
) -> None:
    _install_openaq(app)

    response = await client.get(
        "/api/v1/air-quality/current", params={**READING, "provider": "openaq"}
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["provenance"]["provider"] == "openaq"
    assert data["provenance"]["source_type"] == "ground_observation"
    assert data["provenance"]["station"]["name"] == "ITO, Delhi"
    assert data["cpcb_aqi"] is None
    assert "averaging windows" in data["aqi_unavailable_reason"]
    assert "OpenAQ" in data["provenance"]["attribution"]


async def test_cpcb_reports_an_explicit_unavailable_status(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/air-quality/current", params={**READING, "provider": "cpcb"}
    )

    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "PROVIDER_UNAVAILABLE"
    assert "could not be verified" in body["detail"]


async def test_openaq_without_a_key_is_unavailable(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/air-quality/current", params={**READING, "provider": "openaq"}
    )

    assert response.status_code == 503
    assert "coverage is incomplete" in response.json()["detail"]


async def test_provider_health_keeps_providers_separate(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/air-quality/providers/health")

    assert response.status_code == 200, response.text
    providers = {item["name"]: item for item in response.json()["data"]["providers"]}
    assert set(providers) == {"open-meteo", "openaq", "cpcb"}
    assert providers["open-meteo"]["status"] == "ok"
    assert providers["open-meteo"]["source_type"] == "model_forecast"
    assert providers["openaq"]["status"] == "not_configured"
    assert providers["openaq"]["configured"] is False
    assert providers["cpcb"]["status"] == "unavailable"
    assert "could not be verified" in providers["cpcb"]["detail"]


async def test_station_listing_returns_provider_metadata(
    app: FastAPI, client: AsyncClient
) -> None:
    _install_openaq(app)

    response = await client.get(
        "/api/v1/air-quality/stations",
        params={**READING, "provider": "openaq", "radius_km": 10, "limit": 5},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["provider"] == "openaq"
    assert data["stations"][0]["name"] == "ITO, Delhi"
    assert data["stations"][0]["distance_km"] is not None
    assert any("CC BY 4.0" in item for item in data["attribution"])


async def test_unknown_provider_is_rejected_by_validation(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/air-quality/current", params={**READING, "provider": "unknown"}
    )

    assert response.status_code == 422


async def test_location_search_returns_candidates_and_hits_cache(
    app: FastAPI, client: AsyncClient
) -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": 1,
                        "name": "Pune",
                        "latitude": 18.51957,
                        "longitude": 73.85535,
                        "country": "India",
                        "country_code": "IN",
                        "admin1": "Maharashtra",
                        "timezone": "Asia/Kolkata",
                    },
                    {
                        "id": 2,
                        "name": "Pune",
                        "latitude": 18.0,
                        "longitude": 74.0,
                        "country": "India",
                        "country_code": "IN",
                    },
                ]
            },
        )

    app.state.geocoding_client = GeocodingClient(
        httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://geocoding-api.open-meteo.com/v1",
        )
    )

    first = await client.get(
        "/api/v1/locations/search", params={"q": "Pune", "country_code": "IN"}
    )
    second = await client.get(
        "/api/v1/locations/search", params={"q": "Pune", "country_code": "IN"}
    )

    assert first.status_code == 200, first.text
    results = first.json()["data"]["results"]
    assert [item["id"] for item in results] == ["1", "2"]
    assert results[0]["admin1"] == "Maharashtra"
    assert first.headers["x-data-cache"] == "miss"
    assert second.headers["x-data-cache"] == "hit"
    assert len(calls) == 1


async def test_location_search_requires_a_query(client: AsyncClient) -> None:
    response = await client.get("/api/v1/locations/search", params={"q": "P"})

    assert response.status_code == 422
