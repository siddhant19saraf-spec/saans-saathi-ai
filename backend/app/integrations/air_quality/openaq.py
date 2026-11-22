"""OpenAQ v3 adapter for ground-station observations.

OpenAQ coverage is incomplete. This adapter searches stations near the
requested point, reports the station it used (including distance and owner),
and returns only measurements the provider actually supplies. It never fills
missing pollutants, never treats a model value as an observation and never
invents an AQI.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.integrations.air_quality.base import (
    AirQualityProviderError,
    ProviderForecast,
    ProviderHealth,
    ProviderHistory,
    ProviderReading,
    StationInfo,
)

_POLLUTANTS: dict[str, tuple[str, str]] = {
    "pm25": ("pm2_5", "PM2.5"),
    "pm2.5": ("pm2_5", "PM2.5"),
    "pm2_5": ("pm2_5", "PM2.5"),
    "pm10": ("pm10", "PM10"),
    "no2": ("no2_ug_m3", "Nitrogen dioxide"),
    "so2": ("so2_ug_m3", "Sulphur dioxide"),
    "co": ("co_ug_m3", "Carbon monoxide"),
    "o3": ("o3_ug_m3", "Ozone"),
}
_MOLAR_MASS = {
    "no2_ug_m3": 46.0055,
    "so2_ug_m3": 64.066,
    "co_ug_m3": 28.0101,
    "o3_ug_m3": 47.9982,
}
_MICROGRAM_UNITS = frozenset({"µg/m3", "μg/m3", "ug/m3", "µg/m³", "μg/m³"})
_STALE_AFTER = timedelta(hours=24)
_MAX_PAGES = 3


@dataclass(frozen=True)
class _Sensor:
    id: str
    pollutant: str | None
    unit: str | None


@dataclass(frozen=True)
class _Station:
    info: StationInfo
    provider_name: str | None
    owner_name: str | None
    licenses: tuple[str, ...]
    sensors: dict[str, _Sensor]
    raw: dict[str, Any]


class OpenAQProvider:
    name = "openaq"
    source_type = "ground_observation"
    supports_forecast = False
    supports_history = False
    supports_stations = True
    attribution = ("OpenAQ",)

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        api_key: str | None,
        station_radius_km: int = 25,
        page_size: int = 20,
    ) -> None:
        self._client = client
        self._api_key = api_key
        self._radius_km = max(1, min(25, station_radius_km))
        self._page_size = max(1, min(100, page_size))

    async def health(self) -> ProviderHealth:
        configured = self._api_key is not None
        return ProviderHealth(
            name=self.name,
            status="ok" if configured else "not_configured",
            configured=configured,
            source_type="ground_observation",
            supports_forecast=False,
            supports_history=False,
            supports_stations=True,
            attribution=self.attribution,
            detail=(
                "Ground-station observations with station metadata and source "
                "attribution. Coverage is incomplete; only stations near the "
                "requested point are used."
                if configured
                else "OPENAQ_API_KEY is not set; station observations are unavailable."
            ),
        )

    async def current(self, lat: float, lon: float) -> ProviderReading:
        stations = await self._locations(
            lat, lon, radius_km=self._radius_km, limit=self._page_size
        )
        if not stations:
            raise AirQualityProviderError(
                "No OpenAQ monitoring station is within the configured radius.",
                kind="not_found",
            )
        station = stations[0]
        rows = await self._latest(station.info.id)
        flags: list[str] = []
        if len(stations) > 1:
            flags.append(f"multiple_stations_available:{len(stations)}")
        values: dict[str, float | None] = {
            pollutant: None for pollutant, _label in _POLLUTANTS.values()
        }
        units: dict[str, str] = {}
        original_units: dict[str, str] = {}
        observed: dict[str, datetime] = {}
        compact: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            sensor_id = _identifier(row.get("sensorsId")) or _identifier(
                row.get("sensors_id")
            )
            sensor = station.sensors.get(sensor_id or "")
            if sensor is None or sensor.pollutant is None:
                continue
            when = _time(row.get("datetime"))
            raw_value = row.get("value")
            value = _non_negative(raw_value)
            if when is None or value is None:
                flags.append(f"invalid_value:{sensor.pollutant}")
                continue
            converted = _to_micrograms(value, sensor.unit, sensor.pollutant)
            if converted is None:
                flags.append(f"unsupported_unit:{sensor.pollutant}")
                continue
            previous = observed.get(sensor.pollutant)
            if previous is not None and when <= previous:
                continue
            observed[sensor.pollutant] = when
            values[sensor.pollutant] = converted
            units[sensor.pollutant] = "µg/m³"
            original_units[sensor.pollutant] = sensor.unit or "unknown"
            compact.append(
                {
                    "sensor_id": sensor.id,
                    "pollutant": sensor.pollutant,
                    "value": value,
                    "unit": sensor.unit,
                    "observed_at": when.isoformat(),
                }
            )
        if not observed:
            raise AirQualityProviderError(
                "The nearest OpenAQ station returned no usable measurements.",
                kind="not_found",
            )
        observed_at = max(observed.values())
        if observed_at < datetime.now(tz=UTC) - _STALE_AFTER:
            flags.append("stale_measurement")
        return ProviderReading(
            provider=self.name,
            kind="measured",
            source_type="ground_observation",
            values=values,
            observed_at=observed_at,
            model=None,
            us_aqi=None,
            european_aqi=None,
            attribution=self._attribution(station),
            quality_flags=tuple(flags),
            station_id=station.info.id,
            station_distance_km=station.info.distance_km,
            latitude=station.info.latitude,
            longitude=station.info.longitude,
            timezone=station.info.timezone,
            units=units,
            station=station.info,
            raw={
                "station": station.raw,
                "latest": compact,
                "original_units": original_units,
            },
        )

    async def forecast(self, lat: float, lon: float, hours: int) -> ProviderForecast:
        raise AirQualityProviderError(
            "OpenAQ does not provide forecasts.", kind="unsupported"
        )

    async def history(self, lat: float, lon: float, days: int) -> ProviderHistory:
        raise AirQualityProviderError(
            "OpenAQ history is not exposed by this endpoint.", kind="unsupported"
        )

    async def stations(
        self, lat: float, lon: float, *, radius_km: int, limit: int
    ) -> tuple[tuple[StationInfo, ...], tuple[str, ...]]:
        found = await self._locations(
            lat,
            lon,
            radius_km=max(1, min(25, radius_km)),
            limit=max(1, min(50, limit)),
        )
        if not found:
            return (), self.attribution
        attribution = self._attribution(found[0])
        return tuple(station.info for station in found), attribution

    async def _locations(
        self, lat: float, lon: float, *, radius_km: int, limit: int
    ) -> list[_Station]:
        page = 1
        found: list[_Station] = []
        page_size = min(100, max(limit, 1))
        while page <= _MAX_PAGES and len(found) < limit:
            payload = await self._request(
                "/v3/locations",
                {
                    "coordinates": f"{lat:.4f},{lon:.4f}",
                    "radius": min(25_000, radius_km * 1000),
                    "limit": page_size,
                    "page": page,
                },
            )
            items = payload.get("results")
            if not isinstance(items, list):
                raise AirQualityProviderError(
                    "OpenAQ locations response is malformed.", kind="parse_error"
                )
            for item in items:
                station = _station(item, lat, lon)
                if station is not None:
                    found.append(station)
            meta = payload.get("meta")
            total = _positive_int(meta.get("found")) if isinstance(meta, dict) else None
            if not items or (total is not None and page * page_size >= total):
                break
            page += 1
        found.sort(
            key=lambda station: (
                (
                    station.info.distance_km
                    if station.info.distance_km is not None
                    else float("inf")
                ),
                0 if station.info.is_monitor else 1,
                station.info.name,
            )
        )
        return found[:limit]

    async def _latest(self, location_id: str) -> list[Any]:
        payload = await self._request(
            f"/v3/locations/{location_id}/latest", {"limit": 100}
        )
        rows = payload.get("results")
        if not isinstance(rows, list):
            raise AirQualityProviderError(
                "OpenAQ latest response is malformed.", kind="parse_error"
            )
        return rows

    async def _request(self, path: str, params: dict[str, str | int]) -> dict[str, Any]:
        if self._api_key is None:
            raise AirQualityProviderError(
                "OpenAQ is not configured.", kind="not_configured"
            )
        try:
            response = await self._client.get(
                path,
                params=params,
                headers={"X-API-Key": self._api_key},
            )
        except httpx.TimeoutException as exc:
            raise AirQualityProviderError(
                "OpenAQ request timed out.", kind="timeout"
            ) from exc
        except httpx.HTTPError as exc:
            raise AirQualityProviderError(
                "OpenAQ request failed.", kind="http_error"
            ) from exc
        if response.status_code != 200:
            if response.status_code in {401, 403}:
                kind: str = "unauthorized"
            elif response.status_code == 429:
                kind = "rate_limited"
            elif response.status_code == 404:
                kind = "not_found"
            else:
                kind = "http_error"
            raise AirQualityProviderError(
                f"OpenAQ returned HTTP {response.status_code}.",
                kind=kind,  # type: ignore[arg-type]
                retryable=response.status_code == 429 or response.status_code >= 500,
                http_status=response.status_code,
                retry_after=_retry_after(response),
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise AirQualityProviderError(
                "OpenAQ response was not JSON.", kind="parse_error"
            ) from exc
        if not isinstance(payload, dict):
            raise AirQualityProviderError(
                "OpenAQ response shape is invalid.", kind="parse_error"
            )
        return payload

    @staticmethod
    def _attribution(station: _Station) -> tuple[str, ...]:
        items = ["OpenAQ"]
        if station.provider_name:
            items.append(f"Data provider: {station.provider_name}")
        if station.owner_name and station.owner_name != station.provider_name:
            items.append(f"Station owner: {station.owner_name}")
        items.extend(station.licenses)
        return tuple(dict.fromkeys(items))


def _station(value: object, request_lat: float, request_lon: float) -> _Station | None:
    if not isinstance(value, dict):
        return None
    raw_id = value.get("id")
    name = _text(value.get("name"))
    coordinates = value.get("coordinates")
    if (
        isinstance(raw_id, bool)
        or not isinstance(raw_id, (int, str))
        or name is None
        or not isinstance(coordinates, dict)
    ):
        return None
    lat = _coordinate(coordinates.get("latitude"), 90.0)
    lon = _coordinate(coordinates.get("longitude"), 180.0)
    if lat is None or lon is None:
        return None
    provider = value.get("provider")
    owner = value.get("owner")
    countries = value.get("country")
    sensors = _sensors(value.get("sensors"))
    info = StationInfo(
        id=str(raw_id),
        name=name,
        provider=(_text(provider.get("name")) if isinstance(provider, dict) else None)
        or "OpenAQ",
        latitude=lat,
        longitude=lon,
        distance_km=round(_distance_km(request_lat, request_lon, lat, lon), 2),
        timezone=_text(value.get("timezone")),
        is_monitor=(
            value.get("isMonitor") if isinstance(value.get("isMonitor"), bool) else None
        ),
    )
    return _Station(
        info=info,
        provider_name=(
            _text(provider.get("name")) if isinstance(provider, dict) else None
        ),
        owner_name=_text(owner.get("name")) if isinstance(owner, dict) else None,
        licenses=_licenses(value.get("licenses")),
        sensors=sensors,
        raw={
            "id": info.id,
            "name": info.name,
            "locality": _text(value.get("locality")),
            "country": (
                _text(countries.get("name")) if isinstance(countries, dict) else None
            ),
            "country_code": (
                _text(countries.get("code")) if isinstance(countries, dict) else None
            ),
            "timezone": info.timezone,
            "provider": info.provider,
            "owner": _text(owner.get("name")) if isinstance(owner, dict) else None,
            "licenses": list(_licenses(value.get("licenses"))),
            "coordinates": {"latitude": lat, "longitude": lon},
            "is_monitor": info.is_monitor,
            "sensor_count": len(sensors),
        },
    )


def _sensors(value: object) -> dict[str, _Sensor]:
    if not isinstance(value, list):
        return {}
    sensors: dict[str, _Sensor] = {}
    for item in value:
        if not isinstance(item, dict):
            continue
        raw_id = item.get("id")
        parameter = item.get("parameter")
        if (
            isinstance(raw_id, bool)
            or not isinstance(raw_id, (int, str))
            or not isinstance(parameter, dict)
        ):
            continue
        name = _text(parameter.get("name"))
        mapped = _POLLUTANTS.get(name.lower()) if name else None
        sensors[str(raw_id)] = _Sensor(
            id=str(raw_id),
            pollutant=mapped[0] if mapped else None,
            unit=_text(parameter.get("units")),
        )
    return sensors


def _licenses(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    items: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        name = _text(item.get("name"))
        attribution = _text(item.get("attribution"))
        url = _text(item.get("url"))
        if name and attribution:
            items.append(f"Licence: {name} ({attribution})")
        elif name:
            items.append(f"Licence: {name}")
        elif attribution:
            items.append(f"Licence attribution: {attribution}")
        if url:
            items.append(url)
    return tuple(dict.fromkeys(items))


def _to_micrograms(value: float, unit: str | None, pollutant: str) -> float | None:
    if unit is None:
        return None
    normalised = unit.strip().lower().replace("μ", "µ").replace("³", "3")
    if normalised in _MICROGRAM_UNITS:
        return round(value, 2)
    if normalised == "mg/m3":
        return round(value * 1000.0, 2)
    mass = _MOLAR_MASS.get(pollutant)
    if mass is None:
        return None
    if normalised == "ppm":
        return round(value * 1000.0 * mass / 24.45, 2)
    if normalised == "ppb":
        return round(value * mass / 24.45, 2)
    return None


def _time(value: object) -> datetime | None:
    if not isinstance(value, dict):
        return None
    raw = value.get("utc") or value.get("local")
    if not isinstance(raw, str):
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _retry_after(response: httpx.Response) -> float | None:
    raw = response.headers.get("retry-after")
    if raw is None:
        return None
    try:
        return max(0.0, float(raw))
    except ValueError:
        return None


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * radius * math.asin(min(1.0, math.sqrt(a)))


def _coordinate(value: object, limit: float) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number) or abs(number) > limit:
        return None
    return number


def _non_negative(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number) or number < 0:
        return None
    return number


def _positive_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _identifier(value: object) -> str | None:
    # Resource ids arrive as integers in the JSON, but are keys as text.
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None
    return str(value)
