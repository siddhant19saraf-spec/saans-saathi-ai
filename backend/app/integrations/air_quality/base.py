"""Provider-neutral air-quality contracts.

Missing pollutants are represented as ``None``, never as zero. Every reading
also states how it was produced: model output, a ground-station observation or
a historical observation. Providers with different semantics are never merged
into a single measurement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Protocol

ReadingKind = Literal["modelled", "measured"]
SourceType = Literal[
    "ground_observation",
    "model_forecast",
    "historical_observation",
]
FailureKind = Literal[
    "timeout",
    "http_error",
    "parse_error",
    "circuit_open",
    "rate_limited",
    "unauthorized",
    "not_configured",
    "not_found",
    "unsupported",
]

_NON_RETRYABLE: frozenset[str] = frozenset(
    {"parse_error", "unauthorized", "not_configured", "not_found", "unsupported"}
)


@dataclass(frozen=True)
class StationInfo:
    """Station metadata exactly as the provider describes it."""

    id: str
    name: str
    provider: str
    latitude: float
    longitude: float
    distance_km: float | None = None
    timezone: str | None = None
    is_monitor: bool | None = None


@dataclass(frozen=True)
class AveragingDetail:
    """How a concentration average was formed and how complete it is."""

    window: str
    hours: int
    valid_hours: int
    required_hours: int
    value: float | None
    method: str = "rolling_mean"

    @property
    def complete(self) -> bool:
        return self.valid_hours >= self.required_hours


@dataclass(frozen=True)
class ProviderReading:
    provider: str
    kind: ReadingKind
    values: dict[str, float | None]
    observed_at: datetime
    model: str | None
    us_aqi: int | None
    european_aqi: int | None
    attribution: tuple[str, ...]
    quality_flags: tuple[str, ...] = ()
    station_id: str | None = None
    station_distance_km: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = None
    raw: dict[str, Any] | None = None
    source_type: SourceType | None = None
    station: StationInfo | None = None
    units: dict[str, str] = field(default_factory=dict)
    averages: dict[str, float | None] = field(default_factory=dict)
    average_windows: dict[str, AveragingDetail] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderForecastPoint:
    time: datetime
    pm2_5: float | None
    pm10: float | None
    no2_ug_m3: float | None
    o3_ug_m3: float | None
    co_ug_m3: float | None = None
    so2_ug_m3: float | None = None


@dataclass(frozen=True)
class ProviderForecast:
    provider: str
    points: tuple[ProviderForecastPoint, ...]
    issued_at: datetime
    attribution: tuple[str, ...]
    model: str | None = None
    source_type: SourceType = "model_forecast"


@dataclass(frozen=True)
class ProviderHistoryDay:
    date: str
    pm2_5: float | None
    pm10: float | None


@dataclass(frozen=True)
class ProviderHistory:
    provider: str
    days: tuple[ProviderHistoryDay, ...]
    issued_at: datetime
    attribution: tuple[str, ...]
    model: str | None = None
    source_type: SourceType = "model_forecast"


@dataclass(frozen=True)
class ProviderHealth:
    name: str
    status: Literal["ok", "degraded", "unavailable", "not_configured"]
    configured: bool
    source_type: SourceType
    supports_forecast: bool
    supports_history: bool
    supports_stations: bool
    attribution: tuple[str, ...]
    detail: str


class AirQualityProviderError(Exception):
    """Normalised provider failure. Detail is safe to log, not to expose."""

    def __init__(
        self,
        message: str,
        *,
        kind: FailureKind = "http_error",
        retryable: bool | None = None,
        http_status: int | None = None,
        retry_after: float | None = None,
    ) -> None:
        self.kind = kind
        self.retryable = kind not in _NON_RETRYABLE if retryable is None else retryable
        self.http_status = http_status
        self.retry_after = retry_after
        super().__init__(message)


class AirQualityStationProvider(Protocol):
    async def stations(
        self, lat: float, lon: float, *, radius_km: int, limit: int
    ) -> tuple[tuple[StationInfo, ...], tuple[str, ...]]: ...


class AirQualityProvider(Protocol):
    name: str

    async def current(self, lat: float, lon: float) -> ProviderReading: ...

    async def forecast(
        self, lat: float, lon: float, hours: int
    ) -> ProviderForecast: ...

    async def history(self, lat: float, lon: float, days: int) -> ProviderHistory: ...
