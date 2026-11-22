from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest

from app.integrations.air_quality.base import AirQualityProviderError
from app.integrations.air_quality.openaq import OpenAQProvider

Handler = Callable[[httpx.Request], httpx.Response]

_NOW = datetime.now(tz=UTC).replace(microsecond=0)


def _location(
    *,
    latitude: float = 28.628,
    longitude: float = 77.24,
    no2_unit: str = "ppm",
) -> dict[str, Any]:
    return {
        "id": 2178,
        "name": "ITO, Delhi",
        "locality": "Delhi",
        "timezone": "Asia/Kolkata",
        "country": {"code": "IN", "name": "India"},
        "provider": {"id": 119, "name": "CPCB"},
        "owner": {"id": 4, "name": "Central Pollution Control Board"},
        "isMonitor": True,
        "isMobile": False,
        "coordinates": {"latitude": latitude, "longitude": longitude},
        "sensors": [
            {
                "id": 123,
                "name": "pm25",
                "parameter": {"id": 2, "name": "pm25", "units": "µg/m³"},
            },
            {
                "id": 124,
                "name": "pm10",
                "parameter": {"id": 1, "name": "pm10", "units": "µg/m³"},
            },
            {
                "id": 125,
                "name": "no2",
                "parameter": {"id": 7, "name": "no2", "units": no2_unit},
            },
        ],
        "licenses": [
            {
                "name": "CC BY 4.0",
                "attribution": "CPCB",
                "url": "https://creativecommons.org/licenses/by/4.0/",
            }
        ],
    }


def _latest(*, observed_at: datetime | None = None) -> dict[str, Any]:
    when = (observed_at or _NOW).isoformat()
    return {
        "meta": {"name": "openaq-api", "page": 1, "limit": 100, "found": 3},
        "results": [
            {
                "sensorsId": 123,
                "value": 82.0,
                "datetime": {"utc": when, "local": when},
            },
            {
                "sensorsId": 124,
                "value": 140.0,
                "datetime": {"utc": when, "local": when},
            },
            {
                "sensorsId": 125,
                "value": 0.05,
                "datetime": {"utc": when, "local": when},
            },
        ],
    }


def _handler(
    *,
    locations: list[dict[str, Any]] | None = None,
    latest: dict[str, Any] | None = None,
) -> Handler:
    items = locations if locations is not None else [_location()]
    latest_payload = latest if latest is not None else _latest()

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v3/locations":
            return httpx.Response(
                200,
                json={
                    "meta": {
                        "name": "openaq-api",
                        "page": 1,
                        "limit": 20,
                        "found": len(items),
                    },
                    "results": items,
                },
            )
        if request.url.path.endswith("/latest"):
            return httpx.Response(200, json=latest_payload)
        return httpx.Response(404, json={"detail": "not found"})

    return handle


def _provider(handler: Handler, *, api_key: str | None = "test-key") -> OpenAQProvider:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.openaq.org",
    )
    return OpenAQProvider(client, api_key=api_key)


async def test_current_returns_ground_observation_with_station_metadata() -> None:
    provider = _provider(_handler())

    reading = await provider.current(28.61, 77.21)

    assert reading.provider == "openaq"
    assert reading.kind == "measured"
    assert reading.source_type == "ground_observation"
    assert reading.model is None
    assert reading.values["pm2_5"] == 82.0
    assert reading.values["pm10"] == 140.0
    assert reading.values["no2_ug_m3"] == pytest.approx(94.08)
    assert reading.values["so2_ug_m3"] is None
    assert reading.averages == {}
    assert reading.station is not None
    assert reading.station.name == "ITO, Delhi"
    assert reading.station.distance_km is not None
    assert 1.0 < reading.station.distance_km < 4.0
    assert "OpenAQ" in reading.attribution
    assert "Data provider: CPCB" in reading.attribution
    assert any("CC BY 4.0" in item for item in reading.attribution)
    assert reading.units["no2_ug_m3"] == "µg/m³"
    assert reading.raw is not None


async def test_missing_api_key_is_not_configured_without_a_request() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("OpenAQ must not be called without a key")

    provider = _provider(handler, api_key=None)

    health = await provider.health()
    assert health.status == "not_configured"
    with pytest.raises(AirQualityProviderError) as caught:
        await provider.current(28.61, 77.21)
    assert caught.value.kind == "not_configured"
    assert caught.value.retryable is False


async def test_unauthorized_is_not_retried() -> None:
    provider = _provider(lambda _request: httpx.Response(401, json={"detail": "bad"}))

    with pytest.raises(AirQualityProviderError) as caught:
        await provider.current(28.61, 77.21)

    assert caught.value.kind == "unauthorized"
    assert caught.value.retryable is False
    assert caught.value.http_status == 401


async def test_rate_limit_exposes_retry_after() -> None:
    provider = _provider(
        lambda _request: httpx.Response(
            429, json={"detail": "slow"}, headers={"Retry-After": "7"}
        )
    )

    with pytest.raises(AirQualityProviderError) as caught:
        await provider.current(28.61, 77.21)

    assert caught.value.kind == "rate_limited"
    assert caught.value.retryable is True
    assert caught.value.retry_after == 7.0


async def test_no_station_is_not_found() -> None:
    provider = _provider(_handler(locations=[]))

    with pytest.raises(AirQualityProviderError) as caught:
        await provider.current(28.61, 77.21)

    assert caught.value.kind == "not_found"


async def test_unsupported_unit_does_not_invent_a_value() -> None:
    provider = _provider(
        _handler(
            locations=[_location(no2_unit="furlongs")],
            latest={
                "meta": {"page": 1, "limit": 100, "found": 1},
                "results": [
                    {
                        "sensorsId": 125,
                        "value": 0.05,
                        "datetime": {"utc": _NOW.isoformat()},
                    }
                ],
            },
        )
    )

    with pytest.raises(AirQualityProviderError) as caught:
        await provider.current(28.61, 77.21)

    assert caught.value.kind == "not_found"


async def test_stale_station_measurement_is_flagged() -> None:
    yesterday = _NOW - timedelta(days=3)
    provider = _provider(_handler(latest=_latest(observed_at=yesterday)))

    reading = await provider.current(28.61, 77.21)

    assert "stale_measurement" in reading.quality_flags


async def test_multiple_stations_are_disclosed() -> None:
    stations = [
        _location(latitude=28.70, longitude=77.30),
        _location(latitude=28.628, longitude=77.24),
    ]
    provider = _provider(_handler(locations=stations))

    reading = await provider.current(28.61, 77.21)

    assert "multiple_stations_available:2" in reading.quality_flags
    assert reading.station is not None
    assert reading.station.distance_km is not None
    assert reading.station.distance_km < 4.0


async def test_station_listing_is_sorted_by_distance() -> None:
    stations = [
        _location(latitude=28.70, longitude=77.30),
        _location(latitude=28.628, longitude=77.24),
    ]
    provider = _provider(_handler(locations=stations))

    found, attribution = await provider.stations(28.61, 77.21, radius_km=25, limit=10)

    assert len(found) == 2
    assert found[0].distance_km is not None
    assert found[1].distance_km is not None
    assert found[0].distance_km <= found[1].distance_km
    assert "OpenAQ" in attribution


async def test_forecast_is_explicitly_unsupported() -> None:
    provider = _provider(_handler())

    with pytest.raises(AirQualityProviderError) as caught:
        await provider.forecast(28.61, 77.21, 24)

    assert caught.value.kind == "unsupported"
