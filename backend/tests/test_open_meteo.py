from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest

from app.integrations.air_quality.base import AirQualityProviderError
from app.integrations.air_quality.open_meteo import OpenMeteoProvider

Handler = Callable[[httpx.Request], httpx.Response]


def _provider(handler: Handler) -> OpenMeteoProvider:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://air-quality-api.open-meteo.com/v1",
    )
    return OpenMeteoProvider(client)


def _base_time() -> datetime:
    return datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)


def _current_payload(
    *,
    pm2_5: float = 82.0,
    pm2_5_unit: str = "µg/m³",
) -> dict[str, Any]:
    base = _base_time()
    times = [(base - timedelta(hours=23 - index)).isoformat() for index in range(24)]
    series = [60.0 + index for index in range(24)]
    return {
        "latitude": 28.61,
        "longitude": 77.21,
        "timezone": "GMT",
        "current_units": {
            "time": "iso8601",
            "pm2_5": pm2_5_unit,
            "pm10": "µg/m³",
            "carbon_monoxide": "µg/m³",
            "nitrogen_dioxide": "µg/m³",
            "sulphur_dioxide": "µg/m³",
            "ozone": "µg/m³",
        },
        "current": {
            "time": base.isoformat(),
            "pm2_5": pm2_5,
            "pm10": 140.0,
            "carbon_monoxide": 900.0,
            "nitrogen_dioxide": 46.0,
            "sulphur_dioxide": 9.0,
            "ozone": 55.0,
            "us_aqi": 165,
            "european_aqi": 110,
        },
        "hourly_units": {
            "time": "iso8601",
            "pm2_5": "µg/m³",
            "pm10": "µg/m³",
            "carbon_monoxide": "µg/m³",
            "nitrogen_dioxide": "µg/m³",
            "sulphur_dioxide": "µg/m³",
            "ozone": "µg/m³",
        },
        "hourly": {
            "time": times,
            "pm2_5": series,
            "pm10": [value * 1.6 for value in series],
            "carbon_monoxide": [900.0] * 24,
            "nitrogen_dioxide": [46.0] * 24,
            "sulphur_dioxide": [9.0] * 24,
            "ozone": [55.0] * 24,
        },
    }


async def test_current_is_labelled_model_data_and_has_rolling_averages() -> None:
    provider = _provider(lambda _request: httpx.Response(200, json=_current_payload()))

    reading = await provider.current(28.61, 77.21)

    assert reading.provider == "open-meteo"
    assert reading.kind == "modelled"
    assert reading.source_type == "model_forecast"
    assert reading.model == "CAMS ENSEMBLE"
    assert reading.values["pm2_5"] == 82.0
    assert reading.averages["pm2_5"] == pytest.approx(71.5)
    window = reading.average_windows["pm2_5"]
    assert window.complete is True
    assert window.valid_hours == 24
    assert window.required_hours == 16
    assert reading.average_windows["o3_ug_m3"].hours == 8
    assert reading.units["pm2_5"] == "µg/m³"
    assert reading.quality_flags == ()
    assert reading.attribution == ("CAMS ENSEMBLE (Copernicus)", "Open-Meteo.com")


async def test_current_refuses_changed_units() -> None:
    payload = _current_payload(pm2_5_unit="mg/m3")
    provider = _provider(lambda _request: httpx.Response(200, json=payload))

    with pytest.raises(AirQualityProviderError) as caught:
        await provider.current(28.61, 77.21)

    assert caught.value.kind == "parse_error"
    assert caught.value.retryable is False


async def test_invalid_values_are_dropped_and_flagged() -> None:
    payload = _current_payload(pm2_5=-4.0)
    provider = _provider(lambda _request: httpx.Response(200, json=payload))

    reading = await provider.current(28.61, 77.21)

    assert reading.values["pm2_5"] is None
    assert "invalid_pm2_5" in reading.quality_flags


async def test_rate_limit_is_retryable_and_preserves_status() -> None:
    provider = _provider(lambda _request: httpx.Response(429, json={"error": True}))

    with pytest.raises(AirQualityProviderError) as caught:
        await provider.current(28.61, 77.21)

    assert caught.value.kind == "rate_limited"
    assert caught.value.retryable is True
    assert caught.value.http_status == 429


async def test_timeout_is_normalised() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("slow", request=request)

    provider = _provider(handler)

    with pytest.raises(AirQualityProviderError) as caught:
        await provider.current(28.61, 77.21)

    assert caught.value.kind == "timeout"


async def test_forecast_includes_all_supported_pollutants() -> None:
    base = _base_time()
    times = [(base + timedelta(hours=index)).isoformat() for index in range(24)]
    payload = {
        "hourly_units": {
            "time": "iso8601",
            "pm2_5": "µg/m³",
            "pm10": "µg/m³",
            "carbon_monoxide": "µg/m³",
            "nitrogen_dioxide": "µg/m³",
            "sulphur_dioxide": "µg/m³",
            "ozone": "µg/m³",
        },
        "hourly": {
            "time": times,
            "pm2_5": [60.0] * 24,
            "pm10": [96.0] * 24,
            "carbon_monoxide": [900.0] * 24,
            "nitrogen_dioxide": [46.0] * 24,
            "sulphur_dioxide": [9.0] * 24,
            "ozone": [55.0] * 24,
        },
    }
    provider = _provider(lambda _request: httpx.Response(200, json=payload))

    forecast = await provider.forecast(28.61, 77.21, 12)

    assert len(forecast.points) == 12
    assert forecast.source_type == "model_forecast"
    assert forecast.points[0].co_ug_m3 == 900.0
    assert forecast.points[0].so2_ug_m3 == 9.0
    assert forecast.points[0].pm2_5 == 60.0
