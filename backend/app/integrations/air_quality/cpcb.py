"""CPCB / data.gov.in provider status.

The official mechanism for retrieving CPCB station data could not be verified
during implementation: the data.gov.in catalogue pages returned access errors,
and no officially documented resource endpoint could be confirmed. Per the
project constraints this provider therefore reports an explicit unavailable
status and never substitutes another provider's forecast for CPCB observations.
"""

from __future__ import annotations

from app.integrations.air_quality.base import (
    AirQualityProviderError,
    ProviderForecast,
    ProviderHealth,
    ProviderHistory,
    ProviderReading,
)

_DETAIL = (
    "CPCB ground-station access is not enabled: the official data.gov.in "
    "resource endpoint and its parameters could not be verified, so no CPCB "
    "observations are requested or relabelled. Use OpenAQ for verified "
    "ground-station data or Open-Meteo for labelled model data."
)


class CPCBProvider:
    name = "cpcb"
    source_type = "ground_observation"
    supports_forecast = False
    supports_history = False
    supports_stations = False
    attribution = ("CPCB", "data.gov.in")

    def __init__(self, *, enabled: bool, base_url: str | None) -> None:
        self._enabled = enabled
        self._base_url = base_url

    async def health(self) -> ProviderHealth:
        return ProviderHealth(
            name=self.name,
            status="unavailable",
            configured=self._enabled and self._base_url is not None,
            source_type="ground_observation",
            supports_forecast=False,
            supports_history=False,
            supports_stations=False,
            attribution=self.attribution,
            detail=_DETAIL,
        )

    async def current(self, lat: float, lon: float) -> ProviderReading:
        raise AirQualityProviderError(_DETAIL, kind="unsupported")

    async def forecast(self, lat: float, lon: float, hours: int) -> ProviderForecast:
        raise AirQualityProviderError(
            "CPCB does not provide forecasts through a verified endpoint.",
            kind="unsupported",
        )

    async def history(self, lat: float, lon: float, days: int) -> ProviderHistory:
        raise AirQualityProviderError(_DETAIL, kind="unsupported")
