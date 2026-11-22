"""Family profile, preference and recommendation orchestration.

Safety-critical decisions are made by ``app.domain.family_rules``. The language
model only writes a short explanation of those decisions and never receives
names, coordinates, member rows or free-text alternatives.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Literal, cast
from uuid import UUID
from zoneinfo import ZoneInfoNotFoundError

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import (
    AppError,
    ConflictError,
    ConsentRequiredError,
    DatabaseUnavailableError,
    NotFoundError,
    UnprocessableEntityError,
)
from app.core.logging import get_logger
from app.domain.facts import Fact, FactPack
from app.domain.family_rules import (
    ACTION_LABELS,
    RULES_VERSION,
    ActivityWindow,
    Assessment,
    ForecastHour,
    PollutionSignal,
    Sensitivity,
    Severity,
    assess_activities,
    pm25_band,
)
from app.integrations.ai.gemini import GeminiClient, GeminiError
from app.integrations.ai.validation import DraftValidationError, parse_and_validate
from app.models.household import Household, HouseholdMember, HouseholdPreference
from app.models.profile import Profile
from app.models.routine import Recommendation
from app.repositories import (
    households as households_repo,
    recommendations as recommendations_repo,
)
from app.schemas.air import AirCurrent, AirForecast
from app.schemas.family import (
    AiExplanation,
    Evidence as EvidenceSchema,
    FamilyPreferencesResponse,
    FamilyProfile,
    FamilyProfileCreate,
    FamilyRecommendation,
    FamilyRecommendationBatch,
    FamilyRecommendationList,
    PollutionContext,
)
from app.schemas.household import FamilyPreferences, Member
from app.services import household_service
from app.services.ai_budget import ai_budget_allows
from app.services.air_quality_service import AirQualityService
from app.utils.time import utc_now

logger = get_logger(__name__)

DISCLAIMER = (
    "General air-quality guidance only. This is not medical advice, and it "
    "does not predict an individual health outcome."
)

_CHILD_BANDS = {"0-5", "6-12", "13-17"}
_OLDER_BANDS = {"60+"}
_FORECAST_HOURS = 48

_UNSAFE_CLAIM = re.compile(
    r"\b(safe|safety|guarantee\w*|risk[- ]free|no risk|will not harm|definitely)\b",
    re.IGNORECASE,
)
_NO_DATA_CLAIM = re.compile(
    r"\b(no data|no reading|data (?:is )?unavailable|reading (?:is )?unavailable)\b",
    re.IGNORECASE,
)

_EXPLANATION_SYSTEM = """You explain pre-computed household air-quality guidance for India.
Use only the facts and deterministic recommendations in the FactPack below.
Rules:
- The deterministic rules already chose every action. Never change an action, never add one, and never say that an activity is safe or guaranteed.
- Never invent or estimate a measurement. If a value is absent, do not create one.
- Never give medical advice, diagnose, prescribe or predict an individual outcome.
- Mention that this is general guidance, not medical advice.
- Return JSON matching the schema. The answer must be plain text of at most 3 sentences (500 characters). Actions and avoid must be empty arrays.
FactPack JSON:
"""


# -- profile ---------------------------------------------------------------


def _decimal(value: float | None, digits: str = "0.001") -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal(digits))


def _member_schema(member: HouseholdMember) -> Member:
    return Member(
        id=member.id,
        age_band=member.age_band,
        health_flags=member.health_flags,
        created_at=member.created_at,
    )


def _sensitivity(members: list[HouseholdMember]) -> Sensitivity:
    bands = {member.age_band for member in members}
    return Sensitivity(
        has_children=bool(bands & _CHILD_BANDS),
        has_older_adults=bool(bands & _OLDER_BANDS),
        has_health_flags=any(member.health_flags for member in members),
    )


async def _profile_output(session: AsyncSession, household: Household) -> FamilyProfile:
    members = await households_repo.list_members(session, household.id)
    bands = {member.age_band for member in members}
    return FamilyProfile(
        id=household.id,
        name=household.name,
        size=len(members),
        lat=float(household.lat) if household.lat is not None else None,
        lon=float(household.lon) if household.lon is not None else None,
        city=household.city,
        timezone=household.timezone,
        dwelling=household.dwelling,
        cooking_fuel=household.cooking_fuel,
        has_purifier=household.has_purifier,
        purifier_cadr=household.purifier_cadr,
        room_area_m2=household.room_area_m2,
        ceiling_m=(
            float(household.ceiling_m) if household.ceiling_m is not None else None
        ),
        members=[_member_schema(member) for member in members],
        has_children=bool(bands & _CHILD_BANDS),
        has_older_adults=bool(bands & _OLDER_BANDS),
        has_health_flags=any(member.health_flags for member in members),
        created_at=household.created_at,
        updated_at=household.updated_at,
    )


def _require_health_consent(profile: Profile, payload: FamilyProfileCreate) -> None:
    if profile.health_consent_at is None and any(
        member.health_flags for member in payload.members
    ):
        raise ConsentRequiredError()


def _values(payload: FamilyProfileCreate) -> dict[str, Any]:
    return {
        "name": payload.name,
        "lat": _decimal(payload.lat),
        "lon": _decimal(payload.lon),
        "city": payload.city,
        "timezone": payload.timezone,
        "dwelling": payload.dwelling,
        "cooking_fuel": payload.cooking_fuel,
        "has_purifier": payload.has_purifier,
        "purifier_cadr": payload.purifier_cadr,
        "room_area_m2": payload.room_area_m2,
        "ceiling_m": _decimal(payload.ceiling_m, "0.01"),
    }


def _member_rows(payload: FamilyProfileCreate) -> list[tuple[str, list[str]]]:
    return [(member.age_band, list(member.health_flags)) for member in payload.members]


async def create_profile(
    session: AsyncSession, profile: Profile, payload: FamilyProfileCreate
) -> FamilyProfile:
    if await households_repo.get_for_profile(session, profile.id) is not None:
        raise ConflictError(
            "A family profile already exists for this session. Update it instead."
        )
    _require_health_consent(profile, payload)
    household = await households_repo.create(
        session, profile_id=profile.id, **_values(payload)
    )
    await households_repo.replace_members(
        session, household_id=household.id, members=_member_rows(payload)
    )
    await households_repo.ensure_preferences(session, household.id)
    await session.commit()
    return await _profile_output(session, household)


async def update_profile(
    session: AsyncSession, profile: Profile, payload: FamilyProfileCreate
) -> FamilyProfile:
    household = await household_service.require_household(session, profile)
    _require_health_consent(profile, payload)
    household = await households_repo.update(session, household, **_values(payload))
    await households_repo.replace_members(
        session, household_id=household.id, members=_member_rows(payload)
    )
    await households_repo.ensure_preferences(session, household.id)
    await session.commit()
    return await _profile_output(session, household)


async def get_profile(session: AsyncSession, profile: Profile) -> FamilyProfile:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise NotFoundError("No family profile exists for this session.")
    return await _profile_output(session, household)


async def delete_profile(session: AsyncSession, profile: Profile) -> None:
    household = await household_service.require_household(session, profile)
    await households_repo.delete_all_for_profile(session, household.profile_id)
    await session.commit()
    logger.info("family_profile_deleted", household_id=str(household.id))


# -- preferences -----------------------------------------------------------


def _preferences_dict(preferences: HouseholdPreference) -> dict[str, Any]:
    return {
        "locale": preferences.locale,
        "activity_windows": preferences.activity_windows,
        "alert_threshold_aqi": preferences.alert_threshold_aqi,
        "transport_mode": preferences.transport_mode,
        "notifications_enabled": preferences.notifications_enabled,
        "notify_alerts": preferences.notify_alerts,
        "notify_daily_summary": preferences.notify_daily_summary,
        "quiet_hours_start": preferences.quiet_hours_start,
        "quiet_hours_end": preferences.quiet_hours_end,
    }


def _preferences_output(
    household_id: UUID, preferences: HouseholdPreference
) -> FamilyPreferencesResponse:
    try:
        family = FamilyPreferences.model_validate(_preferences_dict(preferences))
    except ValidationError as exc:
        raise UnprocessableEntityError(
            "Preferences were saved without activity types. Save them from the "
            "Family page first.",
            code="PREFERENCES_INCOMPLETE",
        ) from exc
    return FamilyPreferencesResponse(
        household_id=household_id,
        **family.model_dump(mode="python"),
        created_at=preferences.created_at,
        updated_at=preferences.updated_at,
    )


async def get_preferences(
    session: AsyncSession, profile: Profile
) -> FamilyPreferencesResponse:
    household = await household_service.require_household(session, profile)
    preferences = await households_repo.get_preferences(session, household.id)
    if preferences is None:
        raise NotFoundError("No family preferences exist yet.")
    return _preferences_output(household.id, preferences)


async def update_preferences(
    session: AsyncSession, profile: Profile, payload: FamilyPreferences
) -> FamilyPreferencesResponse:
    household = await household_service.require_household(session, profile)
    preferences = await households_repo.ensure_preferences(session, household.id)
    preferences = await households_repo.update_preferences(
        session,
        preferences,
        locale=payload.locale,
        activity_windows=[
            window.model_dump(mode="json") for window in payload.activity_windows
        ],
        alert_threshold_aqi=payload.alert_threshold_aqi,
        transport_mode=payload.transport_mode,
        notifications_enabled=payload.notifications_enabled,
        notify_alerts=payload.notify_alerts,
        notify_daily_summary=payload.notify_daily_summary,
        quiet_hours_start=payload.quiet_hours_start,
        quiet_hours_end=payload.quiet_hours_end,
    )
    await session.commit()
    return _preferences_output(household.id, preferences)


# -- pollution context -----------------------------------------------------


def _source_type(
    value: str | None,
) -> Literal["ground_observation", "model_forecast", "historical_observation"] | None:
    if value in {
        "ground_observation",
        "model_forecast",
        "historical_observation",
    }:
        return cast(
            Literal["ground_observation", "model_forecast", "historical_observation"],
            value,
        )
    return None


def _signal_from_current(current: AirCurrent) -> PollutionSignal:
    cpcb = current.cpcb_aqi
    pm2_5 = current.reading.pm2_5
    basis: Literal["cpcb_aqi", "pm25_band", "none"]
    if cpcb is not None:
        basis = "cpcb_aqi"
        category: str | None = cpcb.category
    elif pm2_5 is not None:
        basis = "pm25_band"
        category = pm25_band(pm2_5)
    else:
        basis = "none"
        category = None
    return PollutionSignal(
        aqi=cpcb.value if cpcb is not None else None,
        category=category,
        pm2_5=pm2_5,
        pm10=current.reading.pm10,
        provider=current.provenance.provider,
        source_type=current.provenance.source_type,
        observed_at=current.provenance.observed_at,
        fetched_at=current.provenance.fetched_at,
        age_minutes=current.provenance.age_minutes,
        stale=current.provenance.stale,
        aqi_partial=cpcb.partial if cpcb is not None else False,
        unavailable_reason=current.aqi_unavailable_reason,
        forecast_only=False,
        attribution=tuple(current.provenance.attribution),
        guidance_basis=basis,
    )


def _forecast_hours(forecast: AirForecast) -> list[ForecastHour]:
    return [
        ForecastHour(time=point.time, pm2_5=point.pm2_5)
        for point in forecast.hourly
        if point.pm2_5 is not None
    ]


def _nearest_point(points: list[ForecastHour], now: datetime) -> ForecastHour:
    upcoming = [point for point in points if point.time >= now - timedelta(minutes=30)]
    return upcoming[0] if upcoming else points[0]


def _signal_from_forecast(
    *,
    point: ForecastHour,
    forecast: AirForecast,
    current: AirCurrent | None,
    now: datetime,
) -> PollutionSignal:
    provenance = forecast.provenance
    if current is not None and current.provenance.stale:
        reason = (
            "The latest saved current reading was stale, so it was not used; "
            "guidance uses forecast data only."
        )
    elif current is not None:
        reason = (
            "The current reading did not include PM2.5 or an AQI; guidance "
            "uses forecast data only."
        )
    else:
        reason = (
            "Current readings are unavailable for this location; guidance uses "
            "forecast data only."
        )
    return PollutionSignal(
        aqi=None,
        category=pm25_band(point.pm2_5 or 0.0),
        pm2_5=point.pm2_5,
        pm10=None,
        provider=provenance.provider if provenance is not None else None,
        source_type=(
            provenance.source_type if provenance is not None else "model_forecast"
        ),
        observed_at=None,
        fetched_at=provenance.fetched_at if provenance is not None else now,
        age_minutes=provenance.age_minutes if provenance is not None else 0,
        stale=provenance.stale if provenance is not None else False,
        aqi_partial=False,
        unavailable_reason=reason,
        forecast_only=True,
        attribution=(
            tuple(provenance.attribution)
            if provenance is not None and provenance.attribution
            else (provenance.provider if provenance is not None else "Forecast",)
        ),
        guidance_basis="pm25_band",
    )


def _no_data_signal(
    current: AirCurrent | None, current_error: str | None
) -> PollutionSignal:
    if current is not None:
        reason = current.aqi_unavailable_reason or (
            "The reading did not include PM2.5 or an AQI, and no forecast was "
            "available."
        )
        return PollutionSignal(
            aqi=None,
            category=None,
            pm2_5=None,
            pm10=current.reading.pm10,
            provider=current.provenance.provider,
            source_type=current.provenance.source_type,
            observed_at=current.provenance.observed_at,
            fetched_at=current.provenance.fetched_at,
            age_minutes=current.provenance.age_minutes,
            stale=current.provenance.stale,
            aqi_partial=False,
            unavailable_reason=reason,
            forecast_only=False,
            attribution=tuple(current.provenance.attribution),
            guidance_basis="none",
        )
    return PollutionSignal(
        aqi=None,
        category=None,
        pm2_5=None,
        pm10=None,
        provider=None,
        source_type=None,
        observed_at=None,
        fetched_at=None,
        age_minutes=None,
        stale=False,
        aqi_partial=False,
        unavailable_reason=(
            current_error
            or "No current or forecast air-quality data is available for this location."
        ),
        forecast_only=False,
        attribution=(),
        guidance_basis="none",
    )


async def _pollution(
    air_service: AirQualityService, lat: float, lon: float, now: datetime
) -> tuple[PollutionSignal, list[ForecastHour]]:
    current: AirCurrent | None = None
    current_error: str | None = None
    try:
        current, _cache = await air_service.current(lat, lon)
    except AppError:
        current_error = "Current air-quality data is unavailable for this location."

    forecast: AirForecast | None = None
    try:
        forecast, _cache = await air_service.forecast(lat, lon, _FORECAST_HOURS)
    except AppError:
        forecast = None
    points = _forecast_hours(forecast) if forecast is not None else []

    if current is not None and not current.provenance.stale:
        signal = _signal_from_current(current)
        if signal.guidance_basis != "none":
            return signal, points

    if forecast is not None and points:
        point = _nearest_point(points, now)
        return (
            _signal_from_forecast(
                point=point, forecast=forecast, current=current, now=now
            ),
            points,
        )

    return _no_data_signal(current, current_error), points


def _guidance_label(basis: str) -> str:
    if basis == "cpcb_aqi":
        return "CPCB AQI (2014 method)"
    if basis == "pm25_band":
        return "PM2.5 sub-index band (CPCB breakpoints)"
    return "No validated pollution data"


def _context_schema(
    signal: PollutionSignal, *, forecast_used: bool
) -> PollutionContext:
    return PollutionContext(
        provider=signal.provider,
        source_type=_source_type(signal.source_type),
        aqi=signal.aqi,
        category=signal.category,
        pm2_5=signal.pm2_5,
        pm10=signal.pm10,
        observed_at=signal.observed_at,
        fetched_at=signal.fetched_at,
        age_minutes=signal.age_minutes,
        stale=signal.stale,
        forecast_used=forecast_used,
        forecast_only=signal.forecast_only,
        guidance_basis=signal.guidance_basis,
        guidance_basis_label=_guidance_label(signal.guidance_basis),
        aqi_unavailable_reason=signal.unavailable_reason,
        attribution=list(signal.attribution),
    )


def _data_source(signal: PollutionSignal) -> str:
    if signal.provider is None:
        return "No validated current or forecast reading"
    source = (signal.source_type or "provider data").replace("_", " ")
    if signal.guidance_basis == "cpcb_aqi":
        method = "CPCB 2014 AQI"
    elif signal.guidance_basis == "pm25_band":
        method = "CPCB PM2.5 sub-index breakpoints"
    else:
        method = "No AQI method applied"
    return f"{method} from {signal.provider} ({source})"


# -- generation ------------------------------------------------------------


def _windows(preferences: FamilyPreferences) -> list[ActivityWindow]:
    return [
        ActivityWindow(
            id=window.id,
            title=window.title,
            activity=cast(str, window.activity),
            start=window.start,
            duration_min=window.duration_min,
            intensity=window.intensity,
            venue=window.venue,
            days=tuple(window.days),
            flexibility_min=window.flexibility_min,
            indoor_alternative=window.indoor_alternative,
            transport_mode=window.transport_mode or preferences.transport_mode,
        )
        for window in preferences.activity_windows
    ]


def _recommendation(
    assessment: Assessment,
    *,
    recommendation_id: UUID,
    context: PollutionContext,
    signal: PollutionSignal,
    generated_at: datetime,
) -> FamilyRecommendation:
    return FamilyRecommendation(
        recommendation_id=recommendation_id,
        activity=cast(Any, assessment.activity),
        activity_title=assessment.activity_title,
        recommended_action=assessment.action,
        action_label=ACTION_LABELS[assessment.action],
        reason=assessment.reason,
        relevant_pollution_context=context,
        alternative_activity=assessment.alternative_activity,
        suggested_time=assessment.suggested_time,
        suggested_at=assessment.suggested_at,
        data_source=_data_source(signal),
        attribution=list(signal.attribution),
        generated_at=generated_at,
        uncertainty_information=list(assessment.uncertainty),
        evidence=[
            EvidenceSchema(source=item.source, note=item.note)
            for item in assessment.evidence
        ],
        rule_id=assessment.rule_id,
        rule_version=RULES_VERSION,
        severity=assessment.severity,
        confidence=assessment.confidence,
    )


async def generate(
    session: AsyncSession,
    profile: Profile,
    *,
    settings: Settings,
    air_service: AirQualityService,
    gemini: GeminiClient | None,
) -> FamilyRecommendationBatch:
    household = await household_service.require_household(session, profile)
    if household.lat is None or household.lon is None:
        raise UnprocessableEntityError(
            "Add a location to the family profile before generating "
            "recommendations.",
            code="LOCATION_REQUIRED",
        )
    preferences_row = await households_repo.get_preferences(session, household.id)
    if preferences_row is None:
        raise UnprocessableEntityError(
            "Save family preferences before generating recommendations.",
            code="PREFERENCES_REQUIRED",
        )
    try:
        preferences = FamilyPreferences.model_validate(
            _preferences_dict(preferences_row)
        )
    except ValidationError as exc:
        raise UnprocessableEntityError(
            "Preferences were saved without activity types. Save them from the "
            "Family page first.",
            code="PREFERENCES_INCOMPLETE",
        ) from exc
    if not preferences.activity_windows:
        raise UnprocessableEntityError(
            "Add at least one activity preference before generating "
            "recommendations.",
            code="NO_ACTIVITIES",
        )

    members = await households_repo.list_members(session, household.id)
    sensitivity = _sensitivity(members)
    now = utc_now()
    signal, forecast = await _pollution(
        air_service, float(household.lat), float(household.lon), now
    )
    try:
        assessments = assess_activities(
            signal=signal,
            windows=_windows(preferences),
            sensitivity=sensitivity,
            forecast=forecast,
            timezone=household.timezone,
            now=now,
        )
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise UnprocessableEntityError(
            "The household timezone is invalid. Update the profile and try again.",
            code="INVALID_TIMEZONE",
        ) from exc

    forecast_used = signal.forecast_only or any(
        assessment.suggested_at is not None for assessment in assessments
    )
    context = _context_schema(signal, forecast_used=forecast_used)
    valid_until = now + timedelta(hours=24)

    created: list[FamilyRecommendation] = []
    try:
        for assessment in assessments:
            row = await recommendations_repo.create(
                session,
                household_id=household.id,
                module="family",
                severity=assessment.severity,
                title=assessment.activity_title,
                body=assessment.reason[:2000],
                source="deterministic",
                valid_until=valid_until,
                rule_id=assessment.rule_id,
            )
            item = _recommendation(
                assessment,
                recommendation_id=row.id,
                context=context,
                signal=signal,
                generated_at=now,
            )
            row.payload = item.model_dump(mode="json")
            created.append(item)
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise DatabaseUnavailableError() from exc

    logger.info(
        "family_recommendations_generated",
        household_id=str(household.id),
        count=len(created),
        forecast_only=context.forecast_only,
        stale=context.stale,
        rules=sorted({item.rule_id for item in created}),
    )

    ai_explanation = await _explain(
        assessments,
        context,
        sensitivity,
        settings=settings,
        gemini=gemini,
        session=session,
    )
    return FamilyRecommendationBatch(
        household_id=household.id,
        generated_at=now,
        rules_version=RULES_VERSION,
        pollution_context=context,
        recommendations=created,
        ai_explanation=ai_explanation,
        disclaimer=DISCLAIMER,
    )


# -- AI explanation --------------------------------------------------------


def _explanation_pack(
    assessments: list[Assessment],
    context: PollutionContext,
    sensitivity: Sensitivity,
) -> FactPack:
    facts: list[Fact] = []
    source = (
        f"{context.provider or 'provider'} ({context.source_type or 'unknown source'})"
    )
    if context.aqi is not None:
        facts.append(
            Fact(
                id="aq.context.aqi",
                label="CPCB AQI",
                value=float(context.aqi),
                unit="index",
                category=context.category,
                source=f"CPCB 2014 method · {source}",
            )
        )
    if context.pm2_5 is not None:
        facts.append(
            Fact(
                id="aq.context.pm2_5",
                label="PM2.5",
                value=round(float(context.pm2_5), 1),
                unit="µg/m³",
                category=context.category,
                source=source,
            )
        )
    if context.pm10 is not None:
        facts.append(
            Fact(
                id="aq.context.pm10",
                label="PM10",
                value=round(float(context.pm10), 1),
                unit="µg/m³",
                source=source,
            )
        )

    return FactPack(
        facts=facts,
        context={
            "guidance_basis": context.guidance_basis,
            "forecast_only": context.forecast_only,
            "stale": context.stale,
            "sensitive_groups": {
                "children": sensitivity.has_children,
                "older_adults": sensitivity.has_older_adults,
                "health_flags": sensitivity.has_health_flags,
            },
            "recommendations": [
                {
                    "activity": assessment.activity,
                    "action": ACTION_LABELS[assessment.action],
                    "rule_id": assessment.rule_id,
                    "suggested_time": assessment.suggested_time,
                    "severity": assessment.severity,
                }
                for assessment in assessments
            ],
        },
        engine={"rules_version": RULES_VERSION},
    )


def _validate_explanation(text: str, context: PollutionContext) -> None:
    if _UNSAFE_CLAIM.search(text):
        raise DraftValidationError("unsafe_claim")
    if context.guidance_basis != "none" and _NO_DATA_CLAIM.search(text):
        raise DraftValidationError("contradicts_available_data")


async def _explain(
    assessments: list[Assessment],
    context: PollutionContext,
    sensitivity: Sensitivity,
    *,
    settings: Settings,
    gemini: GeminiClient | None,
    session: AsyncSession,
) -> AiExplanation:
    if gemini is None or settings.gemini_api_key is None:
        return AiExplanation(
            status="unavailable", reason="AI explanation is not configured."
        )
    if not await ai_budget_allows(session, settings):
        return AiExplanation(
            status="unavailable", reason="The daily AI request budget is exhausted."
        )

    pack = _explanation_pack(assessments, context, sensitivity)
    try:
        output = await gemini.generate(
            system_instruction=(
                _EXPLANATION_SYSTEM
                + json.dumps(pack.model_dump(mode="json"), separators=(",", ":"))
            ),
            user_text=(
                "Explain the pre-computed recommendations in at most three "
                "sentences. Do not change any action."
            ),
        )
    except GeminiError as exc:
        logger.warning("family_explanation_failed", code=exc.code)
        return AiExplanation(status="unavailable", reason=exc.code)

    try:
        draft = parse_and_validate(output.text, pack)
        if draft.actions or draft.avoid:
            raise DraftValidationError("unexpected_actions")
        text = draft.answer.strip()
        _validate_explanation(text, context)
    except DraftValidationError as exc:
        logger.warning("family_explanation_rejected", reason=exc.reason)
        return AiExplanation(status="rejected", reason=exc.reason)
    return AiExplanation(status="available", text=text, model=output.model)


# -- history ---------------------------------------------------------------


def _stored_recommendation(row: Recommendation) -> FamilyRecommendation:
    try:
        return FamilyRecommendation.model_validate(row.payload)
    except ValidationError:
        logger.warning("family_recommendation_payload_invalid", id=str(row.id))
        return FamilyRecommendation(
            recommendation_id=row.id,
            activity="indoor_activity",
            activity_title=row.title or "Stored recommendation",
            recommended_action="check_back",
            action_label=ACTION_LABELS["check_back"],
            reason=row.body or "This stored recommendation could not be fully read.",
            relevant_pollution_context=PollutionContext(
                provider=None,
                source_type=None,
                aqi=None,
                category=None,
                pm2_5=None,
                pm10=None,
                observed_at=None,
                fetched_at=None,
                age_minutes=None,
                stale=False,
                forecast_used=False,
                forecast_only=False,
                guidance_basis="none",
                guidance_basis_label=_guidance_label("none"),
                aqi_unavailable_reason=None,
                attribution=[],
            ),
            data_source=row.source,
            generated_at=row.created_at,
            uncertainty_information=[
                "This stored record could not be fully reconstructed."
            ],
            rule_id=row.rule_id or "FAM-000",
            rule_version=RULES_VERSION,
            severity=cast(Severity, row.severity),
            confidence="low",
        )


async def list_recommendations(
    session: AsyncSession,
    profile: Profile,
    *,
    limit: int,
    offset: int,
) -> FamilyRecommendationList:
    household = await household_service.require_household(session, profile)
    rows = await recommendations_repo.list_for_household(
        session,
        household_id=household.id,
        limit=limit,
        offset=offset,
        module="family",
    )
    return FamilyRecommendationList(
        items=[_stored_recommendation(row) for row in rows],
        limit=limit,
        offset=offset,
    )


async def get_recommendation(
    session: AsyncSession, profile: Profile, recommendation_id: UUID
) -> FamilyRecommendation:
    household = await household_service.require_household(session, profile)
    row = await recommendations_repo.get(
        session,
        household_id=household.id,
        recommendation_id=recommendation_id,
    )
    if row is None or row.module != "family":
        raise NotFoundError("Recommendation not found for this session.")
    return _stored_recommendation(row)


__all__ = [
    "DISCLAIMER",
    "create_profile",
    "delete_profile",
    "generate",
    "get_preferences",
    "get_profile",
    "get_recommendation",
    "list_recommendations",
    "update_preferences",
    "update_profile",
]
