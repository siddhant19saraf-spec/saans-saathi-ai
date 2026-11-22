"""Indoor PM2.5 assessment with explicit intervals and assumptions."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ProviderUnavailableError,
    UnprocessableEntityError,
)
from app.domain.indoor import (
    DEFAULT_CEILING_M,
    DEFAULT_ROOM_AREA_M2,
    estimate_indoor_pm25,
    recommended_cadr,
    room_volume_m3,
)
from app.models.profile import Profile
from app.repositories import households as households_repo
from app.schemas.indoor import (
    IndoorAction,
    IndoorAssessment,
    IndoorAssessmentRequest,
    IndoorInterval,
    OutdoorContext,
    VentilationWindow,
)
from app.services.air_quality_service import AirQualityService

DISCLAIMER = (
    "This is a modelled estimate from outdoor concentration and standard "
    "building-physics ranges, not a measurement from a sensor in your home."
)


async def assess(
    session: AsyncSession | None,
    profile: Profile | None,
    payload: IndoorAssessmentRequest,
    air_service: AirQualityService,
) -> IndoorAssessment:
    household = (
        await households_repo.get_for_profile(session, profile.id)
        if profile is not None and session is not None
        else None
    )
    overrides = payload.overrides

    lat: float | None = None
    lon: float | None = None
    if payload.location is not None:
        lat, lon = payload.location.lat, payload.location.lon
    elif (
        household is not None
        and household.lat is not None
        and household.lon is not None
    ):
        lat, lon = float(household.lat), float(household.lon)
    if lat is None or lon is None:
        raise UnprocessableEntityError(
            "Provide a location or save a household location first.",
            code="NO_LOCATION",
        )

    current, _cache = await air_service.current(lat, lon)
    outdoor_pm2_5 = current.reading.pm2_5
    if outdoor_pm2_5 is None:
        raise UnprocessableEntityError(
            "The provider did not report PM2.5 for this location.",
            code="OUTDOOR_PM25_UNAVAILABLE",
        )

    area = (
        overrides.room_area_m2
        if overrides and overrides.room_area_m2 is not None
        else (
            float(household.room_area_m2)
            if household is not None and household.room_area_m2 is not None
            else DEFAULT_ROOM_AREA_M2
        )
    )
    ceiling = (
        overrides.ceiling_m
        if overrides and overrides.ceiling_m is not None
        else (
            float(household.ceiling_m)
            if household is not None and household.ceiling_m is not None
            else DEFAULT_CEILING_M
        )
    )
    purifier = (
        overrides.purifier_cadr
        if overrides and overrides.purifier_cadr is not None
        else (
            household.purifier_cadr
            if household is not None and household.has_purifier
            else 0
        )
    ) or 0
    windows_open = bool(overrides.windows_open) if overrides else False
    cooking_fuel = (
        overrides.cooking_fuel
        if overrides and overrides.cooking_fuel is not None
        else household.cooking_fuel if household is not None else None
    )

    volume = room_volume_m3(area_m2=area, ceiling_m=ceiling)
    estimate = estimate_indoor_pm25(
        outdoor_pm2_5=outdoor_pm2_5,
        volume_m3=volume,
        purifier_cadr=purifier,
        windows_open=windows_open,
    )
    target_cadr = recommended_cadr(volume)

    ventilation = await _ventilation(air_service, lat, lon)
    actions = _actions(
        purifier_cadr=purifier,
        recommended=target_cadr,
        windows_open=windows_open,
        cooking_fuel=cooking_fuel,
    )
    return IndoorAssessment(
        outdoor=OutdoorContext(
            pm2_5=outdoor_pm2_5,
            provider=current.provenance.provider,
            observed_at=current.provenance.observed_at,
            stale=current.provenance.stale,
        ),
        indoor=IndoorInterval(
            pm2_5_low=estimate.pm2_5_low,
            pm2_5_high=estimate.pm2_5_high,
            volume_m3=estimate.volume_m3,
            purifier_cadr=purifier,
            recommended_cadr=target_cadr,
        ),
        ventilation=ventilation,
        actions=actions,
        assumptions=[
            "Windows-closed air exchange: 0.3-1.0 changes per hour; "
            "windows-open: 3-10 changes per hour.",
            "Particle penetration with windows closed: 0.3-0.8; "
            "windows open: 0.7-0.9.",
            "Deposition loss: 0.2-0.5 per hour.",
            "Room volume assumes the stated area and ceiling height "
            "(defaults 20 m² and 2.7 m).",
            "Indoor combustion sources are not quantified; the estimate "
            "covers outdoor particles only.",
        ],
        disclaimer=DISCLAIMER,
    )


async def _ventilation(
    air_service: AirQualityService, lat: float, lon: float
) -> VentilationWindow | None:
    try:
        forecast, _cache = await air_service.forecast(lat, lon, 24)
    except ProviderUnavailableError:
        return None
    candidates = [point for point in forecast.hourly if point.pm2_5 is not None]
    if not candidates:
        return None
    best = min(candidates, key=lambda point: point.pm2_5 or 0.0)
    return VentilationWindow(
        start=best.time,
        end=best.time + timedelta(hours=1),
        pm2_5=float(best.pm2_5 or 0.0),
    )


def _actions(
    *,
    purifier_cadr: int,
    recommended: int,
    windows_open: bool,
    cooking_fuel: str | None,
) -> list[IndoorAction]:
    actions: list[IndoorAction] = []
    if recommended > purifier_cadr:
        actions.append(
            IndoorAction(
                id="purifier-sizing",
                title="Match purifier CADR to the room",
                detail=(
                    f"About {recommended} m³/h is roughly five air changes per "
                    f"hour for this room; the current setting is {purifier_cadr} m³/h."
                ),
            )
        )
    if not windows_open:
        actions.append(
            IndoorAction(
                id="windows-closed-peak",
                title="Keep windows closed during outdoor peaks",
                detail="Ventilate during the lowest-forecast window instead.",
            )
        )
    else:
        actions.append(
            IndoorAction(
                id="windows-open-check",
                title="Re-check the outdoor reading before keeping windows open",
                detail="Open-window air exchange lets a large share of outdoor particles inside.",
            )
        )
    if cooking_fuel in {"lpg", "png", "biomass", "mixed"}:
        actions.append(
            IndoorAction(
                id="cooking-ventilation",
                title="Ventilate during and after cooking",
                detail="Cooking adds particles that the outdoor estimate does not include.",
            )
        )
    actions.append(
        IndoorAction(
            id="damp-wipe",
            title="Damp-wipe surfaces and use entrance mats",
            detail="Captures settled dust before it is resuspended.",
        )
    )
    return actions[:4]
