"""IndoorShield assessment, sensor and action-plan orchestration.

Deterministic rules in :mod:`app.domain.indoor_shield` decide every action and
priority. Gemini, when configured, may only rephrase an already validated plan.
All reads and writes are scoped to the authenticated profile's household.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import (
    AppError,
    ConflictError,
    DatabaseUnavailableError,
    NotFoundError,
    UnprocessableEntityError,
)
from app.core.logging import get_logger
from app.domain.facts import Fact, FactPack
from app.domain.indoor_shield import (
    ENGINE_VERSION,
    AssessmentSnapshot,
    OutdoorSnapshot,
    PlanDraft,
    RecommendationDraft,
    RoomSnapshot,
    SensorSnapshot,
    SourceSnapshot,
    recommend,
)
from app.integrations.ai.gemini import GeminiClient, GeminiError
from app.integrations.ai.validation import DraftValidationError, parse_and_validate
from app.models.household import Household
from app.models.indoor import (
    IndoorAssessment,
    IndoorRecommendation,
    IndoorSensor,
    IndoorSensorReading,
    IndoorSource,
)
from app.models.profile import Profile
from app.repositories import households as households_repo, indoor as repo
from app.schemas.indoor import (
    ActionCounts,
    ActionEventOut,
    AssessmentCreate,
    AssessmentList,
    AssessmentOut,
    AssessmentUpdate,
    ExplanationOut,
    IndoorDataStatus,
    IndoorOverview,
    OutdoorSnapshotOut,
    RecommendationList,
    RecommendationOut,
    RoomOut,
    SensorCreate,
    SensorDataStatus,
    SensorList,
    SensorOut,
    SensorReadingCreate,
    SensorReadingList,
    SensorReadingOut,
    SourceOut,
)
from app.services.ai_budget import ai_budget_allows
from app.services.air_quality_service import AirQualityService
from app.utils.time import utc_now

logger = get_logger(__name__)

SENSOR_FRESH_HOURS = 24
READING_LIMIT = 100
SENSOR_READING_PAGE = 60
_FUTURE_SKEW = timedelta(minutes=5)
_DUE_DELAYS = {
    "once": timedelta(days=1),
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=30),
}
_UNIT_ALIASES: dict[str, str] = {
    "ug/m3": "µg/m³",
    "µg/m3": "µg/m³",
    "ug/m³": "µg/m³",
    "mg/m3": "mg/m³",
    "percent": "%",
}
_POLLUTANT_UNITS = {
    "pm2_5": "µg/m³",
    "pm10": "µg/m³",
    "co2": "ppm",
    "co": "mg/m³",
    "tvoc": "ppb",
    "humidity": "%",
}
_POLLUTANT_RANGES = {
    "pm2_5": (0.0, 2000.0),
    "pm10": (0.0, 3000.0),
    "co2": (0.0, 10_000.0),
    "co": (0.0, 100.0),
    "tvoc": (0.0, 10_000.0),
    "humidity": (0.0, 100.0),
}
_SENSITIVE_AGE_BANDS = {"0-5", "6-12", "60+"}

_UNSAFE_EXPLANATION = (
    "safe",
    "guarantee",
    "risk-free",
    "risk free",
    "pollution-free",
    "pollution free",
    "no pollution",
    "will not harm",
    "definitely",
)
_EXPLANATION_SYSTEM = """You explain a pre-computed IndoorShield action plan for a home in India.
Use only the FactPack. Rules:
- Every action, priority and due date is already fixed. Never add, remove or reorder them.
- Never state a measurement that is absent from the facts. Never invent a sensor reading.
- Never say the home is safe, pollution-free or guaranteed, and never diagnose a condition.
- Distinguish self-reported assessment information from measured sensor samples.
- Say that recommendations are general household guidance, not a measurement or medical advice.
- Return JSON matching the schema. The answer must be plain text of at most 3 sentences (600 characters). Actions and avoid must be empty arrays.
FactPack JSON:
"""


@dataclass(frozen=True, slots=True)
class _OutdoorLoad:
    snapshot: OutdoorSnapshot
    out: OutdoorSnapshotOut


@dataclass(frozen=True, slots=True)
class _SensorLoad:
    out: SensorList
    snapshots: tuple[SensorSnapshot, ...]
    status: SensorDataStatus


# -- ownership and household context ---------------------------------------


async def _require_household(session: AsyncSession, profile: Profile) -> Household:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise UnprocessableEntityError(
            "Save a household profile before using IndoorShield.",
            code="NO_HOUSEHOLD",
        )
    return household


async def _has_sensitive_members(session: AsyncSession, household_id: UUID) -> bool:
    members = await households_repo.list_members(session, household_id)
    return any(
        member.age_band in _SENSITIVE_AGE_BANDS or bool(member.health_flags)
        for member in members
    )


# -- outdoor context --------------------------------------------------------


async def _load_outdoor(
    household: Household, air_service: AirQualityService
) -> _OutdoorLoad:
    unavailable_note = (
        "Outdoor air-quality context is unavailable for this location. "
        "No outdoor value was used."
    )
    if household.lat is None or household.lon is None:
        unavailable_note = (
            "Save household coordinates to load outdoor air-quality context. "
            "No outdoor value was used."
        )
        return _OutdoorLoad(
            snapshot=OutdoorSnapshot(available=False),
            out=OutdoorSnapshotOut(note=unavailable_note),
        )

    lat, lon = float(household.lat), float(household.lon)
    current = None
    try:
        current, _cache = await air_service.current(lat, lon)
    except AppError:
        logger.info("indoor_outdoor_current_unavailable")

    forecast = None
    try:
        forecast, _cache = await air_service.forecast(lat, lon, 24)
    except AppError:
        logger.info("indoor_outdoor_forecast_unavailable")

    now = utc_now()
    best_point = None
    if forecast is not None:
        candidates = [
            point
            for point in forecast.hourly
            if point.pm2_5 is not None and point.time >= now - timedelta(minutes=30)
        ]
        if candidates:
            best_point = min(candidates, key=lambda point: point.pm2_5 or 0.0)

    pm2_5 = current.reading.pm2_5 if current is not None else None
    pm10 = current.reading.pm10 if current is not None else None
    stale = bool(current.provenance.stale) if current is not None else False
    available = pm2_5 is not None
    cpcb_aqi = (
        current.cpcb_aqi.value
        if current is not None and current.cpcb_aqi is not None
        else None
    )

    if not available:
        note = (
            "Current outdoor air-quality data is unavailable; no outdoor value "
            "was used. Any forecast shown is a model estimate, not an indoor "
            "measurement."
        )
    elif stale:
        note = (
            "The saved outdoor observation is stale. It is shown with its "
            "timestamp and was not used to time ventilation."
        )
    else:
        note = (
            "Outdoor values are modelled or observed outside the home; they are "
            "not indoor measurements."
        )

    snapshot = OutdoorSnapshot(
        available=available,
        provider=current.provenance.provider if current is not None else None,
        observed_at=current.provenance.observed_at if current is not None else None,
        stale=stale,
        pm2_5=pm2_5,
        pm10=pm10,
        cpcb_aqi=cpcb_aqi,
        forecast_available=best_point is not None,
        forecast_min_pm2_5=best_point.pm2_5 if best_point is not None else None,
        forecast_min_at=best_point.time if best_point is not None else None,
    )
    out = OutdoorSnapshotOut(
        available=available,
        provider=snapshot.provider,
        observed_at=snapshot.observed_at,
        stale=stale,
        pm2_5=pm2_5,
        pm10=pm10,
        cpcb_aqi=cpcb_aqi,
        forecast_available=snapshot.forecast_available,
        forecast_min_pm2_5=snapshot.forecast_min_pm2_5,
        forecast_min_at=snapshot.forecast_min_at,
        attribution=(
            list(current.provenance.attribution) if current is not None else []
        ),
        note=note,
    )
    return _OutdoorLoad(snapshot=snapshot, out=out)


# -- sensors ----------------------------------------------------------------


def _reading_stale(reading: IndoorSensorReading, now: datetime) -> bool:
    measured = reading.measured_at
    if measured.tzinfo is None:
        measured = measured.replace(tzinfo=UTC)
    return measured < now - timedelta(hours=SENSOR_FRESH_HOURS)


def _reading_out(reading: IndoorSensorReading, *, now: datetime) -> SensorReadingOut:
    return SensorReadingOut(
        id=str(reading.id),
        sensor_id=str(reading.sensor_id),
        pollutant=reading.pollutant,
        value=float(reading.value),
        unit=reading.unit,
        measured_at=reading.measured_at,
        received_at=reading.received_at,
        calibration_status=cast(Any, reading.calibration_status),
        quality_status=cast(Any, reading.quality_status),
        stale=_reading_stale(reading, now),
        note=reading.note,
    )


def _latest_per_pollutant(
    readings: list[IndoorSensorReading],
) -> list[IndoorSensorReading]:
    latest: dict[str, IndoorSensorReading] = {}
    for reading in readings:
        current = latest.get(reading.pollutant)
        if current is None or reading.measured_at > current.measured_at:
            latest[reading.pollutant] = reading
    return sorted(latest.values(), key=lambda item: item.pollutant)


def _sensor_out(
    sensor: IndoorSensor,
    *,
    readings: list[IndoorSensorReading],
    now: datetime,
) -> SensorOut:
    latest = _latest_per_pollutant(readings)
    if not latest:
        data_status: SensorDataStatus = "unavailable"
    elif all(_reading_stale(item, now) for item in latest):
        data_status = "stale"
    else:
        data_status = "measured"
    return SensorOut(
        id=str(sensor.id),
        household_id=str(sensor.household_id),
        provider=sensor.provider,
        external_id=sensor.external_id,
        name=sensor.name,
        model=sensor.model,
        room_name=sensor.room_name,
        calibration_status=cast(Any, sensor.calibration_status),
        status=cast(Any, sensor.status),
        last_seen_at=sensor.last_seen_at,
        latest_readings=[_reading_out(item, now=now) for item in latest],
        data_status=data_status,
        created_at=sensor.created_at,
    )


async def _load_sensors(session: AsyncSession, household_id: UUID) -> _SensorLoad:
    sensors = await repo.list_sensors(session, household_id=household_id)
    now = utc_now()
    outputs: list[SensorOut] = []
    all_latest: list[IndoorSensorReading] = []
    for sensor in sensors:
        readings = await repo.list_readings(
            session, sensor_id=sensor.id, limit=SENSOR_READING_PAGE
        )
        outputs.append(_sensor_out(sensor, readings=readings, now=now))
        all_latest.extend(_latest_per_pollutant(readings))

    snapshots: dict[str, SensorSnapshot] = {}
    for reading in all_latest:
        if reading.quality_status != "valid" or _reading_stale(reading, now):
            continue
        existing = snapshots.get(reading.pollutant)
        if existing is not None and existing.measured_at >= reading.measured_at:
            continue
        snapshots[reading.pollutant] = SensorSnapshot(
            pollutant=reading.pollutant,
            value=float(reading.value),
            unit=reading.unit,
            measured_at=reading.measured_at,
            calibration_status=reading.calibration_status,
        )

    if not sensors:
        status: SensorDataStatus = "unavailable"
        message = "Indoor sensor data unavailable."
    elif not outputs or all(item.data_status == "unavailable" for item in outputs):
        status = "unavailable"
        message = "No validated indoor sensor readings have been received."
    elif all(item.data_status == "stale" for item in outputs):
        status = "stale"
        message = (
            "Latest indoor readings are stale and were not used for recommendations."
        )
    else:
        status = "measured"
        message = "Showing the latest validated indoor sensor readings."

    return _SensorLoad(
        out=SensorList(sensors=outputs, available=bool(snapshots), message=message),
        snapshots=tuple(sorted(snapshots.values(), key=lambda item: item.pollutant)),
        status=status,
    )


# -- domain snapshots and persistence --------------------------------------


def _assessment_snapshot(
    assessment: IndoorAssessment,
    rooms: list[Any],
    sources: list[IndoorSource],
    *,
    sensitive: bool,
    sensor_available: bool,
) -> AssessmentSnapshot:
    return AssessmentSnapshot(
        rooms=tuple(
            RoomSnapshot(
                name=room.name,
                room_type=room.room_type,
                area_m2=float(room.area_m2),
                ceiling_m=float(room.ceiling_m),
                ventilation=room.ventilation,
                windows_count=room.windows_count,
                has_purifier=room.has_purifier,
                purifier_cadr=room.purifier_cadr,
                dampness=room.dampness,
            )
            for room in rooms
        ),
        sources=tuple(
            SourceSnapshot(code=source.code, frequency=source.frequency)
            for source in sources
        ),
        cooking_fuel=assessment.cooking_fuel,
        cooking_location=assessment.cooking_location,
        cooking_exhaust=assessment.cooking_exhaust,
        cleaning_frequency=assessment.cleaning_frequency,
        sensor_available=sensor_available,
        sensitive_members=sensitive,
    )


def _due_at(draft: RecommendationDraft, now: datetime) -> datetime | None:
    if draft.due_at is not None and draft.due_at > now:
        return draft.due_at
    return now + _DUE_DELAYS[draft.frequency]


def _recommendation_values(plan: PlanDraft, *, now: datetime) -> list[dict[str, Any]]:
    return [
        {
            "rule_id": item.rule_id,
            "category": item.category,
            "title": item.title,
            "description": item.description,
            "issue": item.issue,
            "action": item.action,
            "priority": item.priority,
            "priority_score": item.priority_score,
            "evidence": item.evidence,
            "expected_benefit": item.expected_benefit,
            "limitations": item.limitations,
            "frequency": item.frequency,
            "source": "deterministic",
            "status": "pending",
            "due_at": _due_at(item, now),
        }
        for item in plan.recommendations
    ]


def _deterministic_explanation(plan: PlanDraft, *, sensor_status: str) -> str:
    high = sum(1 for item in plan.recommendations if item.priority == "high")
    medium = sum(1 for item in plan.recommendations if item.priority == "medium")
    low = len(plan.recommendations) - high - medium
    start = "; ".join(item.title for item in plan.recommendations[:2])
    sensor_text = (
        "Validated indoor sensor readings were used."
        if sensor_status == "measured"
        else "Indoor sensor data is unavailable, so no indoor measurement was used."
    )
    return (
        f"Your assessment produced {len(plan.recommendations)} actions "
        f"({high} high, {medium} medium, {low} low priority). Start with: {start}. "
        f"{sensor_text} These are general household recommendations, not a "
        "measurement or medical advice."
    )


async def _evaluate(
    session: AsyncSession,
    *,
    assessment: IndoorAssessment,
    household: Household,
    air_service: AirQualityService,
) -> PlanDraft:
    rooms = await repo.list_rooms(session, assessment_id=assessment.id)
    sources = await repo.list_sources(session, assessment_id=assessment.id)
    sensitive = await _has_sensitive_members(session, assessment.household_id)
    outdoor = await _load_outdoor(household, air_service)
    sensors = await _load_sensors(session, assessment.household_id)

    snapshot = _assessment_snapshot(
        assessment,
        list(rooms),
        list(sources),
        sensitive=sensitive,
        sensor_available=bool(sensors.snapshots),
    )
    plan = recommend(snapshot, sensors.snapshots, outdoor.snapshot)
    now = utc_now()

    assessment.engine_version = ENGINE_VERSION
    assessment.summary = plan.summary
    assessment.confidence = plan.confidence
    assessment.assumptions = list(plan.assumptions)
    assessment.limitations = list(plan.limitations)
    assessment.outdoor_context = outdoor.out.model_dump(mode="json")
    assessment.completed_at = now
    assessment.status = "completed"
    assessment.updated_at = now
    assessment.explanation = ExplanationOut(
        status="deterministic",
        text=_deterministic_explanation(plan, sensor_status=sensors.status),
        note="Deterministic summary. Request an AI explanation to rephrase it.",
    ).model_dump(mode="json")

    await repo.replace_pending_recommendations(
        session,
        assessment_id=assessment.id,
        household_id=assessment.household_id,
        values=_recommendation_values(plan, now=now),
    )
    await session.flush()
    return plan


def _failure(exc: SQLAlchemyError) -> DatabaseUnavailableError:
    logger.error(
        "indoor_database_error",
        error_type=type(exc).__name__,
    )
    return DatabaseUnavailableError()


# -- serialisation ----------------------------------------------------------


def _recommendation_out(row: IndoorRecommendation) -> RecommendationOut:
    return RecommendationOut(
        id=str(row.id),
        assessment_id=str(row.assessment_id),
        rule_id=row.rule_id,
        category=cast(Any, row.category),
        title=row.title,
        description=row.description,
        issue=row.issue,
        action=row.action,
        priority=cast(Any, row.priority),
        priority_score=row.priority_score,
        evidence=row.evidence,
        expected_benefit=row.expected_benefit,
        limitations=row.limitations,
        frequency=cast(Any, row.frequency),
        source=cast(Any, row.source),
        status=cast(Any, row.status),
        due_at=row.due_at,
        completed_at=row.completed_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _counts(recommendations: list[IndoorRecommendation]) -> ActionCounts:
    return ActionCounts(
        total=len(recommendations),
        pending=sum(1 for item in recommendations if item.status == "pending"),
        completed=sum(1 for item in recommendations if item.status == "completed"),
        dismissed=sum(1 for item in recommendations if item.status == "dismissed"),
        high_priority=sum(
            1
            for item in recommendations
            if item.priority == "high" and item.status == "pending"
        ),
    )


async def _assessment_out(
    session: AsyncSession, assessment: IndoorAssessment
) -> AssessmentOut:
    rooms = await repo.list_rooms(session, assessment_id=assessment.id)
    sources = await repo.list_sources(session, assessment_id=assessment.id)
    recommendations = await repo.list_recommendations(
        session,
        household_id=assessment.household_id,
        assessment_id=assessment.id,
    )
    explanation = ExplanationOut.model_validate(assessment.explanation or {})
    outdoor = OutdoorSnapshotOut.model_validate(assessment.outdoor_context or {})
    return AssessmentOut(
        id=str(assessment.id),
        household_id=str(assessment.household_id),
        status=cast(Any, assessment.status),
        dwelling=cast(Any, assessment.dwelling),
        cooking_fuel=cast(Any, assessment.cooking_fuel),
        cooking_location=cast(Any, assessment.cooking_location),
        cooking_exhaust=assessment.cooking_exhaust,
        cleaning_frequency=cast(Any, assessment.cleaning_frequency),
        sensor_available=assessment.sensor_available,
        notes=assessment.notes,
        engine_version=assessment.engine_version,
        summary=assessment.summary,
        confidence=cast(Any, assessment.confidence),
        assumptions=list(assessment.assumptions),
        limitations=list(assessment.limitations),
        outdoor_context=outdoor,
        explanation=explanation,
        rooms=[
            RoomOut(
                id=str(room.id),
                name=room.name,
                room_type=cast(Any, room.room_type),
                area_m2=float(room.area_m2),
                ceiling_m=float(room.ceiling_m),
                ventilation=cast(Any, room.ventilation),
                windows_count=room.windows_count,
                has_purifier=room.has_purifier,
                purifier_cadr=room.purifier_cadr,
                dampness=cast(Any, room.dampness),
            )
            for room in rooms
        ],
        sources=[
            SourceOut(
                id=str(source.id),
                code=cast(Any, source.code),
                frequency=cast(Any, source.frequency),
                note=source.note,
            )
            for source in sources
        ],
        recommendations=[_recommendation_out(item) for item in recommendations],
        action_counts=_counts(recommendations),
        completed_at=assessment.completed_at,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
    )


async def _require_assessment(
    session: AsyncSession, profile: Profile, assessment_id: UUID
) -> IndoorAssessment:
    household = await _require_household(session, profile)
    assessment = await repo.get_assessment(
        session, household_id=household.id, assessment_id=assessment_id
    )
    if assessment is None:
        raise NotFoundError("Indoor assessment not found.")
    return assessment


# -- assessment workflow ----------------------------------------------------


async def create_assessment(
    session: AsyncSession,
    profile: Profile,
    payload: AssessmentCreate,
    air_service: AirQualityService,
) -> AssessmentOut:
    household = await _require_household(session, profile)
    values = payload.model_dump(exclude={"rooms", "sources"})
    try:
        assessment = await repo.create_assessment(
            session, household_id=household.id, values=values
        )
        await repo.replace_rooms(
            session,
            assessment_id=assessment.id,
            rooms=[room.model_dump() for room in payload.rooms],
        )
        await repo.replace_sources(
            session,
            assessment_id=assessment.id,
            sources=[source.model_dump() for source in payload.sources],
        )
        await _evaluate(
            session,
            assessment=assessment,
            household=household,
            air_service=air_service,
        )
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise _failure(exc) from exc

    logger.info(
        "indoor_assessment_created",
        household_id=str(household.id),
        assessment_id=str(assessment.id),
        rooms=len(payload.rooms),
        sources=len(payload.sources),
    )
    return await _assessment_out(session, assessment)


async def list_assessments(
    session: AsyncSession, profile: Profile, *, limit: int, offset: int
) -> AssessmentList:
    household = await _require_household(session, profile)
    assessments = await repo.list_assessments(
        session, household_id=household.id, limit=limit, offset=offset
    )
    items = [await _assessment_out(session, item) for item in assessments]
    return AssessmentList(assessments=items, count=len(items))


async def get_assessment(
    session: AsyncSession, profile: Profile, assessment_id: UUID
) -> AssessmentOut:
    assessment = await _require_assessment(session, profile, assessment_id)
    return await _assessment_out(session, assessment)


async def update_assessment(
    session: AsyncSession,
    profile: Profile,
    assessment_id: UUID,
    payload: AssessmentUpdate,
    air_service: AirQualityService,
) -> AssessmentOut:
    household = await _require_household(session, profile)
    assessment = await repo.get_assessment(
        session, household_id=household.id, assessment_id=assessment_id
    )
    if assessment is None:
        raise NotFoundError("Indoor assessment not found.")

    values = payload.model_dump(exclude_unset=True, exclude={"rooms", "sources"})
    try:
        for key, value in values.items():
            setattr(assessment, key, value)
        if payload.rooms is not None:
            await repo.replace_rooms(
                session,
                assessment_id=assessment.id,
                rooms=[room.model_dump() for room in payload.rooms],
            )
        if payload.sources is not None:
            await repo.replace_sources(
                session,
                assessment_id=assessment.id,
                sources=[source.model_dump() for source in payload.sources],
            )
        await session.flush()
        await _evaluate(
            session,
            assessment=assessment,
            household=household,
            air_service=air_service,
        )
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise _failure(exc) from exc

    logger.info(
        "indoor_assessment_updated",
        household_id=str(household.id),
        assessment_id=str(assessment.id),
    )
    return await _assessment_out(session, assessment)


async def delete_assessment(
    session: AsyncSession, profile: Profile, assessment_id: UUID
) -> None:
    assessment = await _require_assessment(session, profile, assessment_id)
    try:
        await repo.delete_assessment(session, assessment)
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise _failure(exc) from exc
    logger.info("indoor_assessment_deleted", assessment_id=str(assessment_id))


async def refresh_assessment(
    session: AsyncSession,
    profile: Profile,
    assessment_id: UUID,
    air_service: AirQualityService,
) -> AssessmentOut:
    household = await _require_household(session, profile)
    assessment = await repo.get_assessment(
        session, household_id=household.id, assessment_id=assessment_id
    )
    if assessment is None:
        raise NotFoundError("Indoor assessment not found.")
    try:
        await _evaluate(
            session,
            assessment=assessment,
            household=household,
            air_service=air_service,
        )
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise _failure(exc) from exc
    logger.info("indoor_assessment_refreshed", assessment_id=str(assessment.id))
    return await _assessment_out(session, assessment)


# -- overview and recommendations ------------------------------------------


async def overview(
    session: AsyncSession, profile: Profile, air_service: AirQualityService
) -> IndoorOverview:
    household = await _require_household(session, profile)
    assessment = await repo.latest_assessment(session, household_id=household.id)
    outdoor = await _load_outdoor(household, air_service)
    sensors = await _load_sensors(session, household.id)

    if assessment is not None:
        recommendations = await repo.list_recommendations(
            session,
            household_id=household.id,
            assessment_id=assessment.id,
        )
        assessment_out = await _assessment_out(session, assessment)
    else:
        recommendations = []
        assessment_out = None

    outdoor_status = (
        "unavailable"
        if not outdoor.out.available
        else "stale" if outdoor.out.stale else "available"
    )
    sensor_note = (
        "Indoor sensor data unavailable. Recommendations use your questionnaire "
        "and available outdoor context only."
        if sensors.status == "unavailable"
        else "Indoor recommendations include validated sensor readings."
    )
    return IndoorOverview(
        latest_assessment=assessment_out,
        sensors=sensors.out,
        outdoor=outdoor.out,
        recommendations=[_recommendation_out(item) for item in recommendations],
        action_counts=_counts(recommendations),
        data_status=IndoorDataStatus(
            assessment="completed" if assessment_out is not None else "missing",
            indoor_sensors=sensors.status,
            outdoor=cast(Any, outdoor_status),
            note=sensor_note,
        ),
        disclaimer=(
            "IndoorShield combines self-reported household conditions and, when "
            "available, validated indoor sensor readings. Estimated risk, "
            "priorities and recommendations are not measurements, not a mould or "
            "medical diagnosis, and not a guarantee of cleaner air."
        ),
        generated_at=utc_now(),
    )


async def list_recommendations(
    session: AsyncSession,
    profile: Profile,
    *,
    assessment_id: UUID | None,
    limit: int,
    offset: int,
) -> RecommendationList:
    household = await _require_household(session, profile)
    if assessment_id is not None:
        assessment = await repo.get_assessment(
            session, household_id=household.id, assessment_id=assessment_id
        )
        if assessment is None:
            raise NotFoundError("Indoor assessment not found.")
    else:
        latest = await repo.latest_assessment(session, household_id=household.id)
        assessment_id = latest.id if latest is not None else None

    rows = (
        await repo.list_recommendations(
            session,
            household_id=household.id,
            assessment_id=assessment_id,
            limit=limit,
            offset=offset,
        )
        if assessment_id is not None
        else []
    )
    return RecommendationList(
        recommendations=[_recommendation_out(item) for item in rows],
        counts=_counts(rows),
    )


async def _require_recommendation(
    session: AsyncSession, profile: Profile, recommendation_id: UUID
) -> IndoorRecommendation:
    household = await _require_household(session, profile)
    recommendation = await repo.get_recommendation(
        session,
        household_id=household.id,
        recommendation_id=recommendation_id,
    )
    if recommendation is None:
        raise NotFoundError("Indoor recommendation not found.")
    return recommendation


async def complete_action(
    session: AsyncSession,
    profile: Profile,
    recommendation_id: UUID,
    *,
    note: str | None,
) -> RecommendationOut:
    recommendation = await _require_recommendation(session, profile, recommendation_id)
    if recommendation.status == "completed":
        raise ConflictError(
            "This indoor action is already completed.", code="ACTION_ALREADY_COMPLETED"
        )
    if recommendation.status == "dismissed":
        raise ConflictError(
            "A dismissed indoor action cannot be completed.",
            code="ACTION_DISMISSED",
        )
    now = utc_now()
    previous_due = recommendation.due_at
    recommendation.status = "completed"
    recommendation.completed_at = now
    recommendation.updated_at = now
    try:
        await repo.add_action_event(
            session,
            recommendation_id=recommendation.id,
            household_id=recommendation.household_id,
            event_type="completed",
            previous_due_at=previous_due,
            new_due_at=None,
            note=note,
        )
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise _failure(exc) from exc
    logger.info(
        "indoor_action_completed",
        household_id=str(recommendation.household_id),
        recommendation_id=str(recommendation.id),
    )
    return _recommendation_out(recommendation)


async def reschedule_action(
    session: AsyncSession,
    profile: Profile,
    recommendation_id: UUID,
    *,
    due_at: datetime,
    note: str | None,
) -> RecommendationOut:
    recommendation = await _require_recommendation(session, profile, recommendation_id)
    if recommendation.status != "pending":
        raise ConflictError(
            "Only a pending indoor action can be rescheduled.",
            code="ACTION_NOT_PENDING",
        )
    now = utc_now()
    if due_at <= now:
        raise UnprocessableEntityError(
            "The new due date must be in the future.", code="DUE_AT_IN_PAST"
        )
    previous_due = recommendation.due_at
    recommendation.due_at = due_at
    recommendation.updated_at = now
    try:
        await repo.add_action_event(
            session,
            recommendation_id=recommendation.id,
            household_id=recommendation.household_id,
            event_type="rescheduled",
            previous_due_at=previous_due,
            new_due_at=due_at,
            note=note,
        )
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise _failure(exc) from exc
    logger.info(
        "indoor_action_rescheduled",
        household_id=str(recommendation.household_id),
        recommendation_id=str(recommendation.id),
    )
    return _recommendation_out(recommendation)


async def reopen_action(
    session: AsyncSession,
    profile: Profile,
    recommendation_id: UUID,
) -> RecommendationOut:
    recommendation = await _require_recommendation(session, profile, recommendation_id)
    if recommendation.status != "completed":
        raise ConflictError(
            "Only a completed indoor action can be reopened.",
            code="ACTION_NOT_COMPLETED",
        )
    now = utc_now()
    recommendation.status = "pending"
    recommendation.completed_at = None
    recommendation.due_at = now + _DUE_DELAYS[recommendation.frequency]
    recommendation.updated_at = now
    try:
        await repo.add_action_event(
            session,
            recommendation_id=recommendation.id,
            household_id=recommendation.household_id,
            event_type="reopened",
            previous_due_at=None,
            new_due_at=recommendation.due_at,
            note=None,
        )
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise _failure(exc) from exc
    return _recommendation_out(recommendation)


async def action_events(
    session: AsyncSession, profile: Profile, recommendation_id: UUID
) -> list[ActionEventOut]:
    household = await _require_household(session, profile)
    recommendation = await repo.get_recommendation(
        session,
        household_id=household.id,
        recommendation_id=recommendation_id,
    )
    if recommendation is None:
        raise NotFoundError("Indoor recommendation not found.")
    events = await repo.list_action_events(session, recommendation_id=recommendation.id)
    return [
        ActionEventOut(
            id=str(event.id),
            recommendation_id=str(event.recommendation_id),
            event_type=cast(Any, event.event_type),
            previous_due_at=event.previous_due_at,
            new_due_at=event.new_due_at,
            note=event.note,
            created_at=event.created_at,
        )
        for event in events
    ]


# -- sensor API -------------------------------------------------------------


async def list_sensors(session: AsyncSession, profile: Profile) -> SensorList:
    household = await _require_household(session, profile)
    return (await _load_sensors(session, household.id)).out


async def register_sensor(
    session: AsyncSession, profile: Profile, payload: SensorCreate
) -> SensorOut:
    household = await _require_household(session, profile)
    existing = await repo.get_sensor_by_identity(
        session,
        provider=payload.provider,
        external_id=payload.external_id,
    )
    if existing is not None:
        raise ConflictError(
            "A sensor with this provider and external id is already registered.",
            code="SENSOR_ALREADY_REGISTERED",
        )
    sensor = repo.add_sensor(
        session,
        household_id=household.id,
        values=payload.model_dump(),
    )
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError(
            "A sensor with this provider and external id is already registered.",
            code="SENSOR_ALREADY_REGISTERED",
        ) from exc
    except SQLAlchemyError as exc:
        await session.rollback()
        raise _failure(exc) from exc
    return _sensor_out(sensor, readings=[], now=utc_now())


async def deactivate_sensor(
    session: AsyncSession, profile: Profile, sensor_id: UUID
) -> None:
    household = await _require_household(session, profile)
    sensor = await repo.get_sensor(
        session, household_id=household.id, sensor_id=sensor_id
    )
    if sensor is None:
        raise NotFoundError("Indoor sensor not found.")
    sensor.status = "inactive"
    sensor.updated_at = utc_now()
    try:
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise _failure(exc) from exc
    logger.info("indoor_sensor_deactivated", sensor_id=str(sensor.id))


def _normalise_reading(
    sensor: IndoorSensor, payload: SensorReadingCreate, now: datetime
) -> tuple[str, str, Decimal]:
    pollutant = payload.pollutant
    if pollutant not in _POLLUTANT_UNITS:
        raise UnprocessableEntityError(
            (
                f"Unsupported indoor pollutant '{pollutant}'. Supported values: "
                + ", ".join(sorted(_POLLUTANT_UNITS))
                + "."
            ),
            code="UNSUPPORTED_POLLUTANT",
        )
    unit = _UNIT_ALIASES.get(payload.unit, payload.unit)
    expected = _POLLUTANT_UNITS[pollutant]
    if unit != expected:
        raise UnprocessableEntityError(
            f"{pollutant} readings must use {expected}, not {unit}.",
            code="UNIT_MISMATCH",
        )
    low, high = _POLLUTANT_RANGES[pollutant]
    if not low <= payload.value <= high:
        raise UnprocessableEntityError(
            (
                f"{pollutant} value {payload.value:g} is outside the supported "
                f"range {low:g}-{high:g} {expected}."
            ),
            code="VALUE_OUT_OF_RANGE",
        )
    if payload.measured_at > now + _FUTURE_SKEW:
        raise UnprocessableEntityError(
            "measured_at must not be in the future.", code="FUTURE_MEASUREMENT"
        )
    if sensor.status != "active":
        raise ConflictError(
            "Readings cannot be recorded for an inactive sensor.",
            code="SENSOR_INACTIVE",
        )
    return pollutant, unit, Decimal(str(payload.value))


async def record_reading(
    session: AsyncSession,
    profile: Profile,
    sensor_id: UUID,
    payload: SensorReadingCreate,
) -> SensorReadingOut:
    household = await _require_household(session, profile)
    sensor = await repo.get_sensor(
        session, household_id=household.id, sensor_id=sensor_id
    )
    if sensor is None:
        raise NotFoundError("Indoor sensor not found.")
    now = utc_now()
    pollutant, unit, value = _normalise_reading(sensor, payload, now)
    try:
        reading = await repo.add_reading(
            session,
            values={
                "sensor_id": sensor.id,
                "household_id": household.id,
                "pollutant": pollutant,
                "value": value,
                "unit": unit,
                "measured_at": payload.measured_at,
                "received_at": now,
                "calibration_status": (
                    payload.calibration_status or sensor.calibration_status
                ),
                "quality_status": payload.quality_status,
                "note": payload.note,
            },
        )
        if sensor.last_seen_at is None or payload.measured_at > sensor.last_seen_at:
            sensor.last_seen_at = payload.measured_at
        sensor.updated_at = now
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError(
            "A reading for this pollutant and timestamp already exists.",
            code="DUPLICATE_READING",
        ) from exc
    except SQLAlchemyError as exc:
        await session.rollback()
        raise _failure(exc) from exc
    logger.info(
        "indoor_reading_recorded",
        household_id=str(household.id),
        sensor_id=str(sensor.id),
        pollutant=pollutant,
        quality=payload.quality_status,
    )
    return _reading_out(reading, now=now)


async def sensor_readings(
    session: AsyncSession,
    profile: Profile,
    sensor_id: UUID,
    *,
    limit: int,
) -> SensorReadingList:
    household = await _require_household(session, profile)
    sensor = await repo.get_sensor(
        session, household_id=household.id, sensor_id=sensor_id
    )
    if sensor is None:
        raise NotFoundError("Indoor sensor not found.")
    readings = await repo.list_readings(session, sensor_id=sensor.id, limit=limit)
    now = utc_now()
    return SensorReadingList(
        sensor_id=str(sensor.id),
        readings=[_reading_out(item, now=now) for item in readings],
        message=(
            None
            if readings
            else "No validated readings have been received for this sensor."
        ),
    )


# -- explanation ------------------------------------------------------------


def _explanation_pack(
    plan: PlanDraft, *, sensor_status: str, outdoor: OutdoorSnapshotOut
) -> FactPack:
    facts: list[Fact] = [
        Fact(
            id="assessment.action_count",
            label="Number of deterministic actions",
            value=float(len(plan.recommendations)),
            unit="actions",
            category="assessment",
            source="indoor-shield",
        ),
        Fact(
            id="assessment.high_priority_count",
            label="High-priority actions",
            value=float(
                sum(1 for item in plan.recommendations if item.priority == "high")
            ),
            unit="actions",
            category="assessment",
            source="indoor-shield",
        ),
        Fact(
            id="assessment.confidence",
            label="Plan confidence",
            value=plan.confidence,
            category="assessment",
            source="indoor-shield",
        ),
        Fact(
            id="assessment.sensor_status",
            label="Indoor sensor data status",
            value=sensor_status,
            category="sensor",
            source="indoor-sensor",
        ),
    ]
    if outdoor.pm2_5 is not None:
        facts.append(
            Fact(
                id="outdoor.pm2_5",
                label="Outdoor PM2.5 context",
                value=outdoor.pm2_5,
                unit="µg/m³",
                category="outdoor",
                source=outdoor.provider or "outdoor-provider",
                observed_at=outdoor.observed_at,
            )
        )
    for item in plan.recommendations[:10]:
        facts.append(
            Fact(
                id=f"action.{item.rule_id}",
                label=item.title,
                value=float(item.priority_score),
                unit="priority score",
                category=item.category,
                source="deterministic-rule",
            )
        )
    return FactPack(
        facts=facts[:40],
        context={
            "actions": [
                {
                    "title": item.title,
                    "category": item.category,
                    "priority": item.priority,
                    "frequency": item.frequency,
                }
                for item in plan.recommendations[:8]
            ],
            "limitations": list(plan.limitations),
        },
        engine={"version": ENGINE_VERSION},
    )


def _validate_explanation_text(text: str) -> None:
    lowered = text.casefold()
    for phrase in _UNSAFE_EXPLANATION:
        if phrase in lowered:
            raise DraftValidationError("unsafe_claim")


async def explain_assessment(
    session: AsyncSession,
    profile: Profile,
    assessment_id: UUID,
    *,
    settings: Settings,
    gemini: GeminiClient | None,
) -> AssessmentOut:
    assessment = await _require_assessment(session, profile, assessment_id)
    recommendations = await repo.list_recommendations(
        session,
        household_id=assessment.household_id,
        assessment_id=assessment.id,
    )
    outdoor = OutdoorSnapshotOut.model_validate(assessment.outdoor_context or {})
    sensor_load = await _load_sensors(session, assessment.household_id)
    plan = PlanDraft(
        recommendations=tuple(
            RecommendationDraft(
                rule_id=row.rule_id,
                category=row.category,
                title=row.title,
                description=row.description,
                issue=row.issue,
                action=row.action,
                priority_score=row.priority_score,
                evidence=row.evidence,
                expected_benefit=row.expected_benefit,
                limitations=row.limitations,
                frequency=row.frequency,
            )
            for row in recommendations
        ),
        summary=assessment.summary or "",
        confidence=assessment.confidence or "low",
        assumptions=tuple(assessment.assumptions),
        limitations=tuple(assessment.limitations),
    )
    fallback = _deterministic_explanation(plan, sensor_status=sensor_load.status)

    if gemini is None or settings.gemini_api_key is None:
        explanation = ExplanationOut(
            status="deterministic",
            text=fallback,
            note="AI explanation is not configured.",
        )
        assessment.explanation = explanation.model_dump(mode="json")
        try:
            await session.commit()
        except SQLAlchemyError as exc:
            await session.rollback()
            raise _failure(exc) from exc
        return await _assessment_out(session, assessment)

    if not await ai_budget_allows(session, settings):
        explanation = ExplanationOut(
            status="fallback",
            text=fallback,
            note="The daily AI request budget is exhausted.",
        )
        assessment.explanation = explanation.model_dump(mode="json")
        try:
            await session.commit()
        except SQLAlchemyError as exc:
            await session.rollback()
            raise _failure(exc) from exc
        return await _assessment_out(session, assessment)

    sensor_status = sensor_load.status
    pack = _explanation_pack(plan, sensor_status=sensor_status, outdoor=outdoor)
    try:
        output = await gemini.generate(
            system_instruction=(
                _EXPLANATION_SYSTEM
                + json.dumps(pack.model_dump(mode="json"), separators=(",", ":"))
            ),
            user_text=(
                "Explain this pre-computed indoor action plan in at most three "
                "sentences. Do not add or change actions."
            ),
        )
    except GeminiError as exc:
        logger.warning("indoor_explanation_failed", code=exc.code)
        explanation = ExplanationOut(status="fallback", text=fallback, note=exc.code)
        assessment.explanation = explanation.model_dump(mode="json")
        try:
            await session.commit()
        except SQLAlchemyError as commit_exc:
            await session.rollback()
            raise _failure(commit_exc) from commit_exc
        return await _assessment_out(session, assessment)

    try:
        draft = parse_and_validate(output.text, pack)
        if draft.actions or draft.avoid:
            raise DraftValidationError("unexpected_actions")
        text = draft.answer.strip()
        _validate_explanation_text(text)
    except DraftValidationError as exc:
        logger.warning("indoor_explanation_rejected", reason=exc.reason)
        explanation = ExplanationOut(status="fallback", text=fallback, note=exc.reason)
        assessment.explanation = explanation.model_dump(mode="json")
        try:
            await session.commit()
        except SQLAlchemyError as commit_exc:
            await session.rollback()
            raise _failure(commit_exc) from commit_exc
        return await _assessment_out(session, assessment)

    explanation = ExplanationOut(status="ai", text=text, model=output.model)
    assessment.explanation = explanation.model_dump(mode="json")
    try:
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise _failure(exc) from exc
    return await _assessment_out(session, assessment)
