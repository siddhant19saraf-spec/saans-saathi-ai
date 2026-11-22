"""Tool executor for Copilot Gemini requests.

Maps tool names to backend-side implementations. Each function validates
arguments, applies authorisation, and returns a plain-data dict that the model
can reference in its next response.

All tool output is treated as untrusted; the model must re-ground any cited
values in the FactPack. Tool handlers never return coordinates, names,
free-text household notes or individual health conditions.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.models.profile import Profile
from app.repositories import households as households_repo
from app.services import (
    ecoroute_service,
    family_service,
    impact_service,
    indoor_shield_service,
    routine_service,
)
from app.services.air_quality_service import AirQualityService

logger = get_logger(__name__)

_MAX_FORECAST_HOURS = 72


async def execute_tool(
    *,
    tool_name: str,
    arguments: dict[str, Any],
    profile: Profile | None,
    session: AsyncSession | None,
    air_service: AirQualityService | None = None,
) -> dict[str, Any]:
    """Run a registered tool and return its result dict.

    Raises KeyError if the tool is not registered.
    """
    handlers = {
        "get_air_quality": _tool_get_air_quality,
        "get_air_quality_forecast": _tool_get_air_quality_forecast,
        "get_household_profile": _tool_get_household_profile,
        "get_family_recommendations": _tool_get_family_recommendations,
        "get_daily_routine": _tool_get_daily_routine,
        "get_indoor_assessment": _tool_get_indoor_assessment,
        "get_indoor_recommendations": _tool_get_indoor_recommendations,
        "compare_transport_options": _tool_compare_transport_options,
        "get_impact_summary": _tool_get_impact_summary,
        "get_sustainability_goals": _tool_get_sustainability_goals,
    }
    handler = handlers.get(tool_name)
    if handler is None:
        raise KeyError(f"Unknown tool: {tool_name}")
    return await handler(arguments, profile, session, air_service)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _error(tool: str, message: str, *, status: str = "error") -> dict[str, Any]:
    return {"tool": tool, "status": status, "message": message}


def _number(arguments: dict[str, Any], key: str) -> float | None:
    value = arguments.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _uuid(arguments: dict[str, Any], key: str) -> UUID | None:
    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return UUID(value.strip())
    except ValueError:
        return None


async def _coordinates(
    arguments: dict[str, Any],
    session: AsyncSession | None,
    profile: Profile | None,
) -> tuple[float, float] | None:
    """Resolve coordinates from arguments, then from the saved household.

    Coordinates are used only for provider reads and are never returned in a
    tool result.
    """
    lat = _number(arguments, "lat")
    lon = _number(arguments, "lon")
    if lat is not None and lon is not None:
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        return lat, lon
    if session is not None and profile is not None:
        household = await households_repo.get_for_profile(session, profile.id)
        if (
            household is not None
            and household.lat is not None
            and household.lon is not None
        ):
            return float(household.lat), float(household.lon)
    return None


# ---------------------------------------------------------------------------
# Individual tool implementations
# ---------------------------------------------------------------------------


async def _tool_get_air_quality(
    arguments: dict[str, Any],
    profile: Profile | None,
    session: AsyncSession | None,
    air_service: AirQualityService | None,
) -> dict[str, Any]:
    tool = "get_air_quality"
    if air_service is None:
        return _error(
            tool, "Air-quality service is not available.", status="unavailable"
        )
    coordinates = await _coordinates(arguments, session, profile)
    if coordinates is None:
        return _error(
            tool,
            "No location is available. Provide lat and lon, or save a household location.",
        )
    try:
        current, _cache = await air_service.current(*coordinates)
    except AppError as exc:
        return _error(tool, exc.detail, status="unavailable")
    reading = current.reading
    aqi = current.cpcb_aqi
    return {
        "tool": tool,
        "status": "ok",
        "data": {
            "aqi": aqi.value if aqi is not None else None,
            "aqi_category": aqi.category if aqi is not None else None,
            "aqi_method": aqi.method if aqi is not None else None,
            "pm2_5": reading.pm2_5,
            "pm10": reading.pm10,
            "no2_ug_m3": reading.no2_ug_m3,
            "so2_ug_m3": reading.so2_ug_m3,
            "o3_ug_m3": reading.o3_ug_m3,
            "co_ug_m3": reading.co_ug_m3,
            "provider": current.provenance.provider,
            "source_type": current.provenance.source_type,
            "observed_at": (
                current.provenance.observed_at.isoformat()
                if current.provenance.observed_at is not None
                else None
            ),
            "fetched_at": current.provenance.fetched_at.isoformat(),
            "stale": current.provenance.stale,
        },
    }


async def _tool_get_air_quality_forecast(
    arguments: dict[str, Any],
    profile: Profile | None,
    session: AsyncSession | None,
    air_service: AirQualityService | None,
) -> dict[str, Any]:
    tool = "get_air_quality_forecast"
    if air_service is None:
        return _error(
            tool, "Air-quality service is not available.", status="unavailable"
        )
    coordinates = await _coordinates(arguments, session, profile)
    if coordinates is None:
        return _error(
            tool,
            "No location is available. Provide lat and lon, or save a household location.",
        )
    hours = _number(arguments, "hours")
    horizon = min(max(int(hours), 1), _MAX_FORECAST_HOURS) if hours is not None else 24
    try:
        forecast, _cache = await air_service.forecast(*coordinates, horizon)
    except AppError as exc:
        return _error(tool, exc.detail, status="unavailable")
    provenance = forecast.provenance
    return {
        "tool": tool,
        "status": "ok",
        "data": {
            "hours": horizon,
            "source_type": provenance.source_type if provenance else "model_forecast",
            "provider": provenance.provider if provenance else None,
            "hourly": [
                {
                    "time": point.time.isoformat(),
                    "pm2_5": point.pm2_5,
                    "pm10": point.pm10,
                }
                for point in forecast.hourly[:horizon]
            ],
            "note": "Forecast values are model estimates, not measured station data.",
        },
    }


async def _tool_get_household_profile(
    arguments: dict[str, Any],
    profile: Profile | None,
    session: AsyncSession | None,
    air_service: AirQualityService | None,
) -> dict[str, Any]:
    tool = "get_household_profile"
    profile_id: str = str(arguments.get("profile_id", ""))
    if profile is None:
        return _error(tool, "No profile provided.")
    if profile_id and profile.id.__str__() != profile_id:
        return _error(
            tool,
            "Profile ID mismatch: you do not own this profile.",
            status="unauthorized",
        )
    if session is None:
        return _error(tool, "Database session required.")
    try:
        family = await family_service.get_profile(session, profile)
    except AppError as exc:
        return _error(tool, exc.detail, status="not_found")
    except Exception:
        logger.warning("tool_get_household_profile_failed", exc_info=True)
        return _error(tool, "Failed to retrieve the household profile.")
    return {
        "tool": tool,
        "status": "ok",
        "data": {
            "dwelling": family.dwelling,
            "cooking_fuel": family.cooking_fuel,
            "has_purifier": family.has_purifier,
            "timezone": family.timezone,
            "member_count": family.size,
            "age_bands": [member.age_band for member in family.members],
            "has_children": family.has_children,
            "has_older_adults": family.has_older_adults,
            "has_health_flags": family.has_health_flags,
        },
    }


async def _tool_get_family_recommendations(
    arguments: dict[str, Any],
    profile: Profile | None,
    session: AsyncSession | None,
    air_service: AirQualityService | None,
) -> dict[str, Any]:
    tool = "get_family_recommendations"
    profile_id: str = str(arguments.get("profile_id", ""))
    if profile is None:
        return _error(tool, "No profile provided.")
    if profile_id and profile.id.__str__() != profile_id:
        return _error(
            tool,
            "Profile ID mismatch: you do not own this profile.",
            status="unauthorized",
        )
    if session is None:
        return _error(tool, "Database session required.")
    try:
        recommendations = await family_service.list_recommendations(
            session, profile, limit=10, offset=0
        )
    except AppError as exc:
        return _error(tool, exc.detail, status="not_found")
    except Exception:
        logger.warning("tool_get_family_recommendations_failed", exc_info=True)
        return _error(tool, "Failed to retrieve family recommendations.")
    return {
        "tool": tool,
        "status": "ok",
        "data": [
            {
                "activity_title": item.activity_title,
                "action_label": item.action_label,
                "severity": item.severity,
                "confidence": item.confidence,
                "suggested_time": item.suggested_time,
                "data_source": item.data_source,
            }
            for item in recommendations.items
        ],
    }


async def _tool_get_daily_routine(
    arguments: dict[str, Any],
    profile: Profile | None,
    session: AsyncSession | None,
    air_service: AirQualityService | None,
) -> dict[str, Any]:
    tool = "get_daily_routine"
    date_str: str = str(arguments.get("date", ""))
    target_date: date | None = None
    if date_str:
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            return _error(tool, f"Invalid date format: '{date_str}'. Use YYYY-MM-DD.")
    if profile is None:
        return _error(tool, "No profile provided.")
    if session is None:
        return _error(tool, "Database session required.")
    try:
        routine = await routine_service.get(session, profile, plan_date=target_date)
    except AppError as exc:
        return _error(tool, exc.detail, status="not_found")
    except Exception:
        logger.warning("tool_get_daily_routine_failed", exc_info=True)
        return _error(tool, "Failed to retrieve the routine.")
    return {
        "tool": tool,
        "status": "ok",
        "data": {
            "date": routine.date.isoformat(),
            "timezone": routine.timezone,
            "confidence": routine.confidence,
            "data_status": routine.data_status.model_dump(mode="json"),
            "blocks": [
                {
                    "title": block.title,
                    "start": block.start,
                    "end": block.end,
                    "venue": block.venue,
                    "status": block.status,
                    "pm2_5": block.pm2_5,
                    "aqi": block.aqi,
                    "basis": block.basis,
                }
                for block in routine.blocks[:10]
            ],
            "unscheduled_count": len(routine.unscheduled),
        },
    }


async def _tool_get_indoor_assessment(
    arguments: dict[str, Any],
    profile: Profile | None,
    session: AsyncSession | None,
    air_service: AirQualityService | None,
) -> dict[str, Any]:
    tool = "get_indoor_assessment"
    assessment_id = _uuid(arguments, "assessment_id")
    if assessment_id is None:
        return _error(tool, "A valid assessment_id is required.")
    if profile is None:
        return _error(tool, "No profile provided.")
    if session is None:
        return _error(tool, "Database session required.")
    try:
        assessment = await indoor_shield_service.get_assessment(
            session, profile, assessment_id
        )
    except AppError as exc:
        return _error(tool, exc.detail, status="not_found")
    except Exception:
        logger.warning("tool_get_indoor_assessment_failed", exc_info=True)
        return _error(tool, "Failed to retrieve the indoor assessment.")
    # Free-text notes are deliberately excluded from tool output.
    return {
        "tool": tool,
        "status": "ok",
        "data": {
            "id": assessment.id,
            "status": assessment.status,
            "summary": assessment.summary,
            "confidence": assessment.confidence,
            "action_counts": assessment.action_counts.model_dump(mode="json"),
            "outdoor_context": {
                "available": assessment.outdoor_context.available,
                "provider": assessment.outdoor_context.provider,
                "observed_at": (
                    assessment.outdoor_context.observed_at.isoformat()
                    if assessment.outdoor_context.observed_at is not None
                    else None
                ),
                "stale": assessment.outdoor_context.stale,
                "pm2_5": assessment.outdoor_context.pm2_5,
            },
        },
    }


async def _tool_get_indoor_recommendations(
    arguments: dict[str, Any],
    profile: Profile | None,
    session: AsyncSession | None,
    air_service: AirQualityService | None,
) -> dict[str, Any]:
    tool = "get_indoor_recommendations"
    assessment_id = _uuid(arguments, "assessment_id")
    if profile is None:
        return _error(tool, "No profile provided.")
    if session is None:
        return _error(tool, "Database session required.")
    try:
        result = await indoor_shield_service.list_recommendations(
            session,
            profile,
            assessment_id=assessment_id,
            limit=10,
            offset=0,
        )
    except AppError as exc:
        return _error(tool, exc.detail, status="not_found")
    except Exception:
        logger.warning("tool_get_indoor_recommendations_failed", exc_info=True)
        return _error(tool, "Failed to retrieve indoor recommendations.")
    return {
        "tool": tool,
        "status": "ok",
        "data": {
            "counts": result.counts.model_dump(mode="json"),
            "recommendations": [
                {
                    "title": item.title,
                    "action": item.action,
                    "priority": item.priority,
                    "status": item.status,
                    "category": item.category,
                    "source": item.source,
                    "due_at": item.due_at.isoformat() if item.due_at else None,
                }
                for item in result.recommendations
            ],
        },
    }


async def _tool_compare_transport_options(
    arguments: dict[str, Any],
    profile: Profile | None,
    session: AsyncSession | None,
    air_service: AirQualityService | None,
) -> dict[str, Any]:
    tool = "compare_transport_options"
    journey_id = _uuid(arguments, "journey_id")
    if profile is None:
        return _error(tool, "No profile provided.")
    if session is None:
        return _error(tool, "Database session required.")
    if journey_id is None:
        return _error(tool, "A valid journey_id is required.")
    try:
        journeys = await ecoroute_service.list_journeys(
            session, profile, limit=100, offset=0
        )
    except AppError as exc:
        return _error(tool, exc.detail, status="not_found")
    except Exception:
        logger.warning("tool_compare_transport_options_failed", exc_info=True)
        return _error(tool, "Failed to retrieve saved journeys.")
    journey = next((item for item in journeys if item.id == str(journey_id)), None)
    if journey is None:
        return _error(tool, "Journey not found for this profile.", status="not_found")
    return {
        "tool": tool,
        "status": "ok",
        "data": {
            "journey_id": journey.id,
            "selected_mode": journey.selected_mode,
            "distance_km": journey.distance_km,
            "duration_min": journey.duration_min,
            "passengers": journey.passengers,
            "co2e_kg": journey.co2e_kg,
            "co2e_per_passenger_kg": journey.co2e_per_passenger_kg,
            "modes_compared": list(journey.modes),
            "note": "Emissions are estimates using sourced per-passenger factors.",
        },
    }


async def _tool_get_impact_summary(
    arguments: dict[str, Any],
    profile: Profile | None,
    session: AsyncSession | None,
    air_service: AirQualityService | None,
) -> dict[str, Any]:
    tool = "get_impact_summary"
    if profile is None:
        return _error(tool, "No profile provided.")
    if session is None:
        return _error(tool, "Database session required.")
    days = 30
    date_range = arguments.get("date_range", "30d")
    if isinstance(date_range, str) and date_range.endswith("d"):
        try:
            days = min(max(int(date_range[:-1]), 1), 365)
        except ValueError:
            days = 30
    try:
        summary = await impact_service.summary(session, profile, days=days)
        trends = await impact_service.trends(session, profile, days=days)
        savings = await impact_service.baseline_and_savings(session, profile, days=days)
    except AppError as exc:
        return _error(tool, exc.detail, status="not_found")
    except Exception:
        logger.warning("tool_get_impact_summary_failed", exc_info=True)
        return _error(tool, "Failed to retrieve the impact summary.")
    return {
        "tool": tool,
        "status": "ok",
        "data": {
            "range": summary.range,
            "total_co2e_kg": summary.total_co2e_kg,
            "activity_count": summary.activity_count,
            "by_type": [item.model_dump(mode="json") for item in summary.by_type],
            "weekly": [item.model_dump(mode="json") for item in trends.weekly[-8:]],
            "monthly": [item.model_dump(mode="json") for item in trends.monthly[-6:]],
            "baseline": savings.model_dump(mode="json"),
        },
    }


async def _tool_get_sustainability_goals(
    arguments: dict[str, Any],
    profile: Profile | None,
    session: AsyncSession | None,
    air_service: AirQualityService | None,
) -> dict[str, Any]:
    tool = "get_sustainability_goals"
    profile_id: str = str(arguments.get("profile_id", ""))
    if profile is None:
        return _error(tool, "No profile provided.")
    if profile_id and profile.id.__str__() != profile_id:
        return _error(
            tool,
            "Profile ID mismatch: you do not own this profile.",
            status="unauthorized",
        )
    if session is None:
        return _error(tool, "Database session required.")
    try:
        goals = await impact_service.list_goals(session, profile)
    except AppError as exc:
        return _error(tool, exc.detail, status="not_found")
    except Exception:
        logger.warning("tool_get_sustainability_goals_failed", exc_info=True)
        return _error(tool, "Failed to retrieve sustainability goals.")
    return {
        "tool": tool,
        "status": "ok",
        "data": [goal.model_dump(mode="json") for goal in goals],
    }
