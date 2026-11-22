"""Open-Meteo air-quality adapter (CAMS ensemble model data).

Open-Meteo serves model output, never ground-station observations. The adapter
labels every reading ``model_forecast`` and also computes CPCB-compatible
rolling averages from the hourly series so the AQI service never treats a
single hourly value as a 24-hour mean.

The adapter fails loudly when the provider changes units: silently mis-scaling
CO by 1000 would turn a moderate reading into a severe one.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

import httpx

from app.domain.aqi import AveragingInfo, rolling_averages
from app.integrations.air_quality.base import (
    AirQualityProviderError,
    AveragingDetail,
    FailureKind,
    ProviderForecast,
    ProviderForecastPoint,
    ProviderHealth,
    ProviderHistory,
    ProviderHistoryDay,
    ProviderReading,
)

_MICROGRAM_UNITS = frozenset({"μg/m³", "µg/m³", "ug/m3"})
_CONCENTRATION_FIELDS = {
    "pm2_5": "pm2_5",
    "pm10": "pm10",
    "carbon_monoxide": "co_ug_m3",
    "nitrogen_dioxide": "no2_ug_m3",
    "sulphur_dioxide": "so2_ug_m3",
    "ozone": "o3_ug_m3",
    "dust": "dust_ug_m3",
}
_FORECAST_FIELDS = (
    "pm2_5",
    "pm10",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
)


class OpenMeteoProvider:
    name = "open-meteo"
    model = "CAMS ENSEMBLE"
    attribution = ("CAMS ENSEMBLE (Copernicus)", "Open-Meteo.com")
    source_type = "model_forecast"
    supports_forecast = True
    supports_history = True
    supports_stations = False

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def health(self) -> ProviderHealth:
        return ProviderHealth(
            name=self.name,
            status="ok",
            configured=True,
            source_type="model_forecast",
            supports_forecast=True,
            supports_history=True,
            supports_stations=False,
            attribution=self.attribution,
            detail=(
                "CAMS ensemble model data via Open-Meteo. Values are modelled "
                "grid output, not monitoring-station measurements."
            ),
        )

    async def current(self, lat: float, lon: float) -> ProviderReading:
        payload = await self._get(
            {
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "current": ",".join(_CONCENTRATION_FIELDS) + ",us_aqi,european_aqi",
                "hourly": ",".join(_CONCENTRATION_FIELDS),
                "timezone": "UTC",
                "past_days": 2,
                "forecast_days": 1,
            }
        )
        current = payload.get("current")
        current_units = payload.get("current_units")
        hourly = payload.get("hourly")
        hourly_units = payload.get("hourly_units")
        if (
            not isinstance(current, dict)
            or not isinstance(current_units, dict)
            or not isinstance(hourly, dict)
            or not isinstance(hourly_units, dict)
        ):
            raise AirQualityProviderError(
                "Open-Meteo response is missing current values or the hourly "
                "series required for CPCB averages.",
                kind="parse_error",
            )
        self._assert_units(current_units)
        self._assert_units(hourly_units)
        observed_at = _parse_time(current.get("time"))
        flags: list[str] = []
        values = {
            output: _number(current.get(source), flags, source)
            for source, output in _CONCENTRATION_FIELDS.items()
        }
        series = _series(hourly, observed_at, flags)
        averages = rolling_averages(series)
        average_windows: dict[str, AveragingDetail] = {
            pollutant: _detail(value, info)
            for pollutant, (value, info) in averages.items()
        }
        return ProviderReading(
            provider=self.name,
            kind="modelled",
            source_type="model_forecast",
            values=values,
            averages={
                pollutant: value for pollutant, (value, _info) in averages.items()
            },
            average_windows=average_windows,
            observed_at=observed_at,
            model=self.model,
            us_aqi=_integer(current.get("us_aqi")),
            european_aqi=_integer(current.get("european_aqi")),
            attribution=self.attribution,
            quality_flags=tuple(flags),
            latitude=_coordinate(payload.get("latitude")),
            longitude=_coordinate(payload.get("longitude")),
            timezone=_string(payload.get("timezone")),
            units={
                output: str(current_units.get(source))
                for source, output in _CONCENTRATION_FIELDS.items()
                if current_units.get(source) is not None
            },
            raw={
                "current": current,
                "current_units": current_units,
                "hourly_units": hourly_units,
            },
        )

    async def forecast(self, lat: float, lon: float, hours: int) -> ProviderForecast:
        payload = await self._get(
            {
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "hourly": ",".join(_FORECAST_FIELDS),
                "timezone": "UTC",
                "forecast_days": min(7, max(1, math.ceil(hours / 24) + 1)),
            }
        )
        hourly = payload.get("hourly")
        units = payload.get("hourly_units")
        if not isinstance(hourly, dict) or not isinstance(units, dict):
            raise AirQualityProviderError(
                "Open-Meteo response is missing hourly values.", kind="parse_error"
            )
        self._assert_units(units, _FORECAST_FIELDS)
        times = hourly.get("time")
        if not isinstance(times, list):
            raise AirQualityProviderError(
                "Open-Meteo hourly time series is malformed.", kind="parse_error"
            )

        flags: list[str] = []
        points: list[ProviderForecastPoint] = []
        floor = datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
        for index, time_value in enumerate(times):
            if not isinstance(time_value, str):
                continue
            point_time = _parse_time(time_value)
            if point_time < floor:
                continue
            if len(points) >= hours:
                break
            points.append(
                ProviderForecastPoint(
                    time=point_time,
                    pm2_5=_number(_at(hourly, "pm2_5", index), flags, "pm2_5"),
                    pm10=_number(_at(hourly, "pm10", index), flags, "pm10"),
                    co_ug_m3=_number(
                        _at(hourly, "carbon_monoxide", index), flags, "carbon_monoxide"
                    ),
                    no2_ug_m3=_number(
                        _at(hourly, "nitrogen_dioxide", index),
                        flags,
                        "nitrogen_dioxide",
                    ),
                    so2_ug_m3=_number(
                        _at(hourly, "sulphur_dioxide", index),
                        flags,
                        "sulphur_dioxide",
                    ),
                    o3_ug_m3=_number(_at(hourly, "ozone", index), flags, "ozone"),
                )
            )

        if not points:
            raise AirQualityProviderError(
                "Open-Meteo returned no usable forecast points.", kind="parse_error"
            )
        return ProviderForecast(
            provider=self.name,
            points=tuple(points),
            issued_at=datetime.now(tz=UTC),
            attribution=self.attribution,
            model=self.model,
            source_type="model_forecast",
        )

    async def history(self, lat: float, lon: float, days: int) -> ProviderHistory:
        fields = ("pm2_5", "pm10")
        payload = await self._get(
            {
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "hourly": ",".join(fields),
                "timezone": "UTC",
                "past_days": min(92, max(1, days + 1)),
                "forecast_days": 1,
            }
        )
        hourly = payload.get("hourly")
        units = payload.get("hourly_units")
        if not isinstance(hourly, dict) or not isinstance(units, dict):
            raise AirQualityProviderError(
                "Open-Meteo response is missing hourly history.", kind="parse_error"
            )
        self._assert_units(units, fields)
        times = hourly.get("time")
        if not isinstance(times, list):
            raise AirQualityProviderError(
                "Open-Meteo history time series is malformed.", kind="parse_error"
            )

        today = datetime.now(tz=UTC).date()
        buckets: dict[str, dict[str, list[float]]] = {}
        for index, time_value in enumerate(times):
            if not isinstance(time_value, str):
                continue
            day = _parse_time(time_value).date()
            if day >= today:
                continue
            key = day.isoformat()
            bucket = buckets.setdefault(key, {"pm2_5": [], "pm10": []})
            for field in fields:
                value = _number(_at(hourly, field, index), [], field)
                if value is not None:
                    bucket[field].append(value)

        result: list[ProviderHistoryDay] = []
        for key in sorted(buckets)[-days:]:
            bucket = buckets[key]
            result.append(
                ProviderHistoryDay(
                    date=key,
                    pm2_5=_rounded_mean(bucket["pm2_5"]),
                    pm10=_rounded_mean(bucket["pm10"]),
                )
            )
        return ProviderHistory(
            provider=self.name,
            days=tuple(result),
            issued_at=datetime.now(tz=UTC),
            attribution=self.attribution,
            model=self.model,
            source_type="model_forecast",
        )

    async def _get(self, params: dict[str, str | int | float]) -> dict[str, Any]:
        try:
            response = await self._client.get("/air-quality", params=params)
        except httpx.TimeoutException as exc:
            raise AirQualityProviderError(
                "Open-Meteo request timed out.", kind="timeout"
            ) from exc
        except httpx.HTTPError as exc:
            raise AirQualityProviderError(
                "Open-Meteo request failed.", kind="http_error"
            ) from exc

        if response.status_code != 200:
            kind: FailureKind = (
                "rate_limited" if response.status_code == 429 else "http_error"
            )
            raise AirQualityProviderError(
                f"Open-Meteo returned HTTP {response.status_code}.",
                kind=kind,
                retryable=response.status_code == 429 or response.status_code >= 500,
                http_status=response.status_code,
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise AirQualityProviderError(
                "Open-Meteo response was not JSON.", kind="parse_error"
            ) from exc
        if not isinstance(payload, dict):
            raise AirQualityProviderError(
                "Open-Meteo response shape is invalid.", kind="parse_error"
            )
        return payload

    @staticmethod
    def _assert_units(
        units: dict[str, Any],
        fields: tuple[str, ...] | None = None,
    ) -> None:
        checked = fields or tuple(_CONCENTRATION_FIELDS)
        for field in checked:
            unit = units.get(field)
            if unit is None:
                if field == "dust":
                    continue
                raise AirQualityProviderError(
                    f"Open-Meteo omitted units for {field}.", kind="parse_error"
                )
            if str(unit) not in _MICROGRAM_UNITS:
                raise AirQualityProviderError(
                    f"Open-Meteo changed units for {field} to {unit!r}; refusing to guess.",
                    kind="parse_error",
                )


def _series(
    hourly: dict[str, Any],
    observed_at: datetime,
    flags: list[str],
) -> dict[str, list[float | None]]:
    times = hourly.get("time")
    if not isinstance(times, list):
        raise AirQualityProviderError(
            "Open-Meteo hourly time series is malformed.", kind="parse_error"
        )
    stop = -1
    for index, time_value in enumerate(times):
        if isinstance(time_value, str) and _parse_time(time_value) <= observed_at:
            stop = index
    if stop < 0:
        raise AirQualityProviderError(
            "Open-Meteo hourly series does not cover the observation time.",
            kind="parse_error",
        )
    series: dict[str, list[float | None]] = {}
    for source, output in _CONCENTRATION_FIELDS.items():
        if output == "dust_ug_m3":
            continue
        series[output] = [
            _number(_at(hourly, source, index), flags, source)
            for index in range(stop + 1)
        ]
    return series


def _detail(value: float | None, info: AveragingInfo) -> AveragingDetail:
    return AveragingDetail(
        window=info.window,
        hours=info.hours,
        valid_hours=info.valid_hours,
        required_hours=info.required_hours,
        value=value,
        method=info.method,
    )


def _parse_time(value: object) -> datetime:
    if not isinstance(value, str):
        raise AirQualityProviderError(
            "Open-Meteo response contains an invalid timestamp.", kind="parse_error"
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AirQualityProviderError(
            "Open-Meteo response contains an invalid timestamp.", kind="parse_error"
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _number(value: object, flags: list[str], field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        flags.append(f"invalid_{field}")
        return None
    number = float(value)
    if not math.isfinite(number) or number < 0:
        flags.append(f"invalid_{field}")
        return None
    return round(number, 2)


def _integer(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return round(float(value))


def _coordinate(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _at(hourly: dict[str, Any], field: str, index: int) -> object:
    series = hourly.get(field)
    if not isinstance(series, list) or index >= len(series):
        return None
    return series[index]


def _rounded_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 2)
