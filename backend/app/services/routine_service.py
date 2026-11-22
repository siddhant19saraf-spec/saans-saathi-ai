"""SmartRoutine activity management, plan generation and replanning.

All scheduling is deterministic in ``app.domain.routine``. The language model,
when configured, may only rephrase an already generated plan; its output is
validated and any failure falls back to a deterministic summary.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import ValidationError
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
from app.domain.routine import (
    ENGINE_VERSION,
    ForecastCoverageError,
    ForecastHour,
    MemberProfile,
    PlannerActivity,
    RoutinePlan as DomainPlan,
    generate_plan,
    scoring_payload,
)
from app.integrations.ai.gemini import GeminiClient, GeminiError
from app.integrations.ai.validation import DraftValidationError, parse_and_validate
from app.models.household import Household, HouseholdMember
from app.models.profile import Profile
from app.models.routine import Routine, RoutineActivity
from app.repositories import households as households_repo, routines as repo
from app.schemas.routines import (
    ActivityLocation,
    ForecastStatus,
    ObservationStatus,
    RoutineActivity as RoutineActivitySchema,
    RoutineActivityChange,
    RoutineActivityCreate,
    RoutineActivityUpdate,
    RoutineAlternative,
    RoutineBlock,
    RoutineDataStatus,
    RoutineExplanation,
    RoutineHistory,
    RoutineItemUpdate,
    RoutinePlan,
    RoutineScoring,
    RoutineUnscheduled,
    RoutineVersionSummary,
)
from app.services.ai_budget import ai_budget_allows
from app.services.air_quality_service import AirQualityService
from app.utils.time import utc_now

logger = get_logger(__name__)

PLAN_TTL_HOURS = 6
MAX_ACTIVITIES = 20
HISTORY_DEFAULT = 20
HISTORY_MAX = 50
FORECAST_HOURS = 48
PLAN_OPEN_MINUTE = 5 * 60
PLAN_CLOSE_MINUTE = 22 * 60
_INDOOR_ONLY = {"indoor_exercise", "household_activity"}
_OUTDOOR_ONLY = {"morning_walk", "outdoor_sports", "outdoor_recreation", "gardening"}

_UNSAFE_CLAIM = re.compile(
    r"\b(safe|safety|guarantee\w*|risk[- ]free|no risk|will not harm|definitely)\b",
    re.IGNORECASE,
)
_CLOCK_CLAIM = re.compile(r"\b\d{1,2}:\d{2}\b")
_NO_DATA_CLAIM = re.compile(
    r"\b(no data|no forecast|forecast (?:is )?unavailable|data (?:is )?unavailable)\b",
    re.IGNORECASE,
)

_EXPLANATION_SYSTEM = """You explain a pre-computed, deterministic daily schedule for India.
Use only the FactPack. Rules:
- Every time, activity and venue is already fixed. Never change or add one.
- Never state a clock time. Never state a concentration or AQI value that is absent from the facts.
- Never say a time slot or activity is safe, guaranteed, risk-free or medically advisable.
- Never diagnose, prescribe or predict an individual health outcome.
- Say that concentrations are forecast estimates, not measurements, when relevant.
- Return JSON matching the schema. The answer must be plain text of at most 3 sentences (500 characters). Actions and avoid must be empty arrays.
FactPack JSON:
"""


def local_today(timezone: str) -> date:
    return datetime.now(tz=ZoneInfo(timezone)).date()


# -- activity management ---------------------------------------------------


def _clock(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def _activity_schema(row: RoutineActivity) -> RoutineActivitySchema:
    return RoutineActivitySchema(
        id=row.id,
        title=row.title,
        category=row.category,
        duration_min=row.duration_min,
        preferred_start=row.preferred_start,
        earliest_start=row.earliest_start,
        latest_start=row.latest_start,
        venue=row.venue,
        fixed=row.fixed,
        priority=row.priority,
        intensity=row.intensity,
        member_ids=list(row.member_ids),
        location=row.location,
        indoor_alternative=row.indoor_alternative,
        notes=row.notes,
        active=row.active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _require_household(household: Household | None) -> Household:
    if household is None:
        raise UnprocessableEntityError(
            "Save a household profile before using SmartRoutine.",
            code="NO_HOUSEHOLD",
        )
    if household.lat is None or household.lon is None:
        raise UnprocessableEntityError(
            "Add coordinates to the household profile before generating a routine.",
            code="NO_LOCATION",
        )
    return household


def _member_ids(members: list[HouseholdMember]) -> set[str]:
    return {str(member.id) for member in members}


def _validate_category_venue(category: str, venue: str) -> None:
    if category in _INDOOR_ONLY and venue != "indoor":
        raise UnprocessableEntityError(
            f"{category} must be an indoor activity.", code="INVALID_VENUE"
        )
    if category in _OUTDOOR_ONLY and venue != "outdoor":
        raise UnprocessableEntityError(
            f"{category} must be an outdoor activity.", code="INVALID_VENUE"
        )


def _validate_values(values: dict[str, Any], member_ids: set[str]) -> None:
    preferred = _clock(values["preferred_start"])
    duration = int(values["duration_min"])
    earliest = (
        _clock(values["earliest_start"])
        if values.get("earliest_start") is not None
        else preferred
    )
    latest = (
        _clock(values["latest_start"])
        if values.get("latest_start") is not None
        else preferred
    )
    if not (earliest <= preferred <= latest):
        raise UnprocessableEntityError(
            "earliest_start must be at or before preferred_start, and "
            "preferred_start at or before latest_start.",
            code="INVALID_WINDOW",
        )
    if earliest < PLAN_OPEN_MINUTE:
        raise UnprocessableEntityError(
            "earliest_start cannot be before 05:00.", code="INVALID_WINDOW"
        )
    if latest > PLAN_CLOSE_MINUTE:
        raise UnprocessableEntityError(
            "latest_start cannot be after 22:00.", code="INVALID_WINDOW"
        )
    if preferred + duration > PLAN_CLOSE_MINUTE:
        raise UnprocessableEntityError(
            "The activity must end by 22:00.", code="INVALID_WINDOW"
        )
    unknown = sorted(set(values["member_ids"]) - member_ids)
    if unknown:
        raise UnprocessableEntityError(
            "One or more selected members do not belong to this household.",
            code="UNKNOWN_MEMBER",
        )
    _validate_category_venue(str(values["category"]), str(values["venue"]))


def _overlaps_fixed(
    *,
    preferred_start: str,
    duration_min: int,
    others: list[RoutineActivity],
) -> str | None:
    start = _clock(preferred_start)
    end = start + duration_min
    for other in others:
        if not other.fixed or not other.active:
            continue
        other_start = _clock(other.preferred_start)
        other_end = other_start + other.duration_min
        if start < other_end and end > other_start:
            return other.title
    return None


def _values_from_create(payload: RoutineActivityCreate) -> dict[str, Any]:
    return {
        "title": payload.title,
        "category": payload.category,
        "duration_min": payload.duration_min,
        "preferred_start": payload.preferred_start,
        "earliest_start": payload.earliest_start,
        "latest_start": payload.latest_start,
        "venue": payload.venue,
        "fixed": payload.fixed,
        "priority": payload.priority,
        "intensity": payload.intensity,
        "member_ids": [str(member_id) for member_id in payload.member_ids],
        "location": (
            payload.location.model_dump(exclude_none=True)
            if payload.location is not None
            else None
        ),
        "indoor_alternative": payload.indoor_alternative,
        "notes": payload.notes,
    }


def _values_from_update(
    row: RoutineActivity, payload: RoutineActivityUpdate
) -> dict[str, Any]:
    values: dict[str, Any] = {
        "title": row.title,
        "category": row.category,
        "duration_min": row.duration_min,
        "preferred_start": row.preferred_start,
        "earliest_start": row.earliest_start,
        "latest_start": row.latest_start,
        "venue": row.venue,
        "fixed": row.fixed,
        "priority": row.priority,
        "intensity": row.intensity,
        "member_ids": list(row.member_ids),
        "location": row.location,
        "indoor_alternative": row.indoor_alternative,
        "notes": row.notes,
    }
    clearable = {
        "earliest_start",
        "latest_start",
        "indoor_alternative",
        "notes",
        "location",
    }
    for field in payload.model_fields_set:
        if field == "active":
            continue
        value = getattr(payload, field)
        if field == "member_ids" and value is not None:
            values[field] = [str(member_id) for member_id in value]
        elif field == "location":
            location = value
            values[field] = (
                location.model_dump(exclude_none=True)
                if isinstance(location, ActivityLocation)
                else None
            )
        elif value is not None or field in clearable:
            values[field] = value
    return values


async def list_activities(
    session: AsyncSession, profile: Profile
) -> list[RoutineActivitySchema]:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        return []
    rows = await repo.list_activities(session, household_id=household.id)
    return [_activity_schema(row) for row in rows]


async def create_activity(
    session: AsyncSession, profile: Profile, payload: RoutineActivityCreate
) -> RoutineActivitySchema:
    household = _require_household(
        await households_repo.get_for_profile(session, profile.id)
    )
    members = await households_repo.list_members(session, household.id)
    values = _values_from_create(payload)
    _validate_values(values, _member_ids(members))

    existing = await repo.list_activities(session, household_id=household.id)
    if len(existing) >= MAX_ACTIVITIES:
        raise UnprocessableEntityError(
            f"SmartRoutine supports at most {MAX_ACTIVITIES} active activities.",
            code="TOO_MANY_ACTIVITIES",
        )
    if values["fixed"]:
        overlap = _overlaps_fixed(
            preferred_start=values["preferred_start"],
            duration_min=values["duration_min"],
            others=existing,
        )
        if overlap is not None:
            raise UnprocessableEntityError(
                f"This fixed activity overlaps '{overlap}'.",
                code="FIXED_ACTIVITY_OVERLAP",
            )

    row = repo.add_activity(session, household_id=household.id, values=values)
    try:
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise DatabaseUnavailableError() from exc
    await session.refresh(row)
    return _activity_schema(row)


async def update_activity(
    session: AsyncSession,
    profile: Profile,
    activity_id: UUID,
    payload: RoutineActivityUpdate,
) -> RoutineActivitySchema:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise NotFoundError("No household profile exists for this session.")
    row = await repo.get_activity(
        session, household_id=household.id, activity_id=activity_id
    )
    if row is None:
        raise NotFoundError("Activity not found.")
    members = await households_repo.list_members(session, household.id)
    values = _values_from_update(row, payload)
    _validate_values(values, _member_ids(members))

    active = payload.active if payload.active is not None else row.active
    if values["fixed"] and active:
        others = await repo.list_activities(session, household_id=household.id)
        overlap = _overlaps_fixed(
            preferred_start=values["preferred_start"],
            duration_min=values["duration_min"],
            others=[other for other in others if other.id != row.id],
        )
        if overlap is not None:
            raise UnprocessableEntityError(
                f"This fixed activity overlaps '{overlap}'.",
                code="FIXED_ACTIVITY_OVERLAP",
            )

    for field, value in values.items():
        setattr(row, field, value)
    row.active = active
    try:
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise DatabaseUnavailableError() from exc
    await session.refresh(row)
    return _activity_schema(row)


async def delete_activity(
    session: AsyncSession, profile: Profile, activity_id: UUID
) -> None:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise NotFoundError("No household profile exists for this session.")
    row = await repo.get_activity(
        session, household_id=household.id, activity_id=activity_id
    )
    if row is None:
        raise NotFoundError("Activity not found.")
    await repo.delete_activity(session, row)
    try:
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise DatabaseUnavailableError() from exc


# -- plan generation -------------------------------------------------------


def _planner_activities(rows: list[RoutineActivity]) -> list[PlannerActivity]:
    return [
        PlannerActivity(
            id=str(row.id),
            title=row.title,
            category=row.category,
            duration_min=row.duration_min,
            preferred_start=row.preferred_start,
            earliest_start=row.earliest_start,
            latest_start=row.latest_start,
            venue=row.venue,
            fixed=row.fixed,
            priority=row.priority,
            intensity=row.intensity,  # type: ignore[arg-type]
            indoor_alternative=row.indoor_alternative,
            member_ids=tuple(str(value) for value in row.member_ids),
            notes=row.notes,
        )
        for row in rows
    ]


def _member_profiles(members: list[HouseholdMember]) -> list[MemberProfile]:
    return [
        MemberProfile(
            age_band=member.age_band,  # type: ignore[arg-type]
            sensitive=bool(member.health_flags) or member.age_band in {"0-5", "60+"},
            id=str(member.id),
        )
        for member in members
    ]


async def _observation(
    air_service: AirQualityService, lat: float, lon: float
) -> dict[str, Any] | None:
    try:
        current, _cache = await air_service.current(lat, lon)
    except AppError:
        logger.info("routine_observation_unavailable")
        return None
    return ObservationStatus(
        provider=current.provenance.provider,
        source_type=str(current.provenance.source_type),
        observed_at=current.provenance.observed_at,
        age_minutes=current.provenance.age_minutes,
        stale=current.provenance.stale,
        cpcb_aqi=(current.cpcb_aqi.value if current.cpcb_aqi is not None else None),
        pm2_5=current.reading.pm2_5,
    ).model_dump(mode="json")


def _inputs_hash(
    *,
    plan_date: date,
    timezone: str,
    activities: list[PlannerActivity],
    members: list[MemberProfile],
    hours: list[ForecastHour],
    provider: str,
    issued_at: datetime | None,
    stale: bool,
) -> str:
    canonical = {
        "engine": ENGINE_VERSION,
        "date": plan_date.isoformat(),
        "timezone": timezone,
        "provider": provider,
        "issued_at": issued_at.isoformat() if issued_at is not None else None,
        "stale": stale,
        "activities": [
            {
                "id": activity.id,
                "title": activity.title,
                "category": activity.category,
                "duration_min": activity.duration_min,
                "preferred_start": activity.preferred_start,
                "earliest_start": activity.earliest_start,
                "latest_start": activity.latest_start,
                "venue": activity.venue,
                "fixed": activity.fixed,
                "priority": activity.priority,
                "intensity": activity.intensity,
                "indoor_alternative": activity.indoor_alternative,
                "member_ids": list(activity.member_ids),
            }
            for activity in activities
        ],
        "members": [
            {
                "id": member.id,
                "age_band": member.age_band,
                "sensitive": member.sensitive,
            }
            for member in members
        ],
        "hours": [
            [
                hour.time.isoformat(),
                hour.pm2_5,
                hour.pm10,
                hour.no2_ug_m3,
                hour.o3_ug_m3,
            ]
            for hour in hours
        ],
    }
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _deterministic_explanation(plan: DomainPlan) -> str:
    total = len(plan.blocks) + len(plan.unscheduled)
    parts = [
        f"{plan.plan_date.isoformat()}: {len(plan.blocks)} of {total} activities "
        "could be scheduled."
    ]
    for block in plan.blocks[:3]:
        if block.data_available:
            parts.append(
                f"{block.title} is at {block.start}-{block.end} "
                f"({block.venue}, estimated dose {block.dose_ug:g} µg; "
                f"CPCB AQI {block.aqi if block.aqi is not None else 'not available'})."
            )
        else:
            parts.append(
                f"{block.title} is fixed at {block.start}-{block.end} without "
                "forecast coverage for that window."
            )
    forecast = plan.data_status
    parts.append(
        f"The forecast covers {forecast.coverage_hours} of "
        f"{forecast.expected_hours} hourly slots "
        f"({forecast.coverage_ratio:.0%}), confidence is {forecast.confidence}."
    )
    if plan.unscheduled:
        parts.append(
            "Not scheduled: "
            + "; ".join(
                f"{item.title} ({item.reason_code})" for item in plan.unscheduled
            )
            + "."
        )
    parts.append(
        "Estimated doses are planning estimates from forecast data, not "
        "measurements, and this plan does not certify that any slot is safe."
    )
    return " ".join(parts)[:900]


def _explanation_pack(plan: DomainPlan) -> FactPack:
    facts: list[Fact] = [
        Fact(
            id="routine.scheduled_count",
            label="Scheduled activities",
            value=float(len(plan.blocks)),
            unit="count",
            source="deterministic SmartRoutine engine",
        ),
        Fact(
            id="routine.unscheduled_count",
            label="Unscheduled activities",
            value=float(len(plan.unscheduled)),
            unit="count",
            source="deterministic SmartRoutine engine",
        ),
        Fact(
            id="routine.forecast_coverage",
            label="Forecast PM2.5 hour coverage",
            value=float(plan.data_status.coverage_hours),
            unit="hours",
            source=f"{plan.data_status.provider} forecast",
        ),
        Fact(
            id="routine.forecast_expected",
            label="Planning horizon hours",
            value=float(plan.data_status.expected_hours),
            unit="hours",
            source="deterministic SmartRoutine engine",
        ),
    ]
    for index, block in enumerate(plan.blocks[:5], start=1):
        if block.pm2_5 is not None:
            facts.append(
                Fact(
                    id=f"routine.block.{index}.pm2_5",
                    label=f"Forecast PM2.5 for {block.title}",
                    value=float(block.pm2_5),
                    unit="µg/m³",
                    category=block.category,
                    source=f"{plan.data_status.provider} forecast",
                )
            )
        if block.aqi is not None:
            facts.append(
                Fact(
                    id=f"routine.block.{index}.aqi",
                    label=f"CPCB AQI for {block.title}",
                    value=float(block.aqi),
                    unit="index",
                    category="CPCB 2014",
                    source=f"{plan.data_status.provider} forecast",
                )
            )
    return FactPack(
        facts=facts,
        context={
            "date": plan.plan_date.isoformat(),
            "timezone": plan.timezone,
            "confidence": plan.data_status.confidence,
            "stale": plan.data_status.stale,
            "scheduled": [
                {
                    "title": block.title,
                    "category": block.category,
                    "venue": block.venue,
                    "fixed": block.fixed,
                }
                for block in plan.blocks
            ],
            "unscheduled": [
                {"title": item.title, "reason_code": item.reason_code}
                for item in plan.unscheduled
            ],
            "instruction": (
                "Explain why this deterministic schedule looks this way. Do not "
                "state clock times and do not call any slot safe."
            ),
        },
        engine={"engine_version": ENGINE_VERSION},
    )


def _validate_explanation(text: str, plan: DomainPlan) -> None:
    if _UNSAFE_CLAIM.search(text):
        raise DraftValidationError("unsafe_claim")
    if _CLOCK_CLAIM.search(text):
        raise DraftValidationError("ungrounded_clock_time")
    if plan.data_status.coverage_hours > 0 and _NO_DATA_CLAIM.search(text):
        raise DraftValidationError("contradicts_available_data")


async def _explain(
    plan: DomainPlan,
    *,
    settings: Settings,
    gemini: GeminiClient | None,
    session: AsyncSession,
) -> RoutineExplanation:
    fallback = _deterministic_explanation(plan)
    if gemini is None or settings.gemini_api_key is None:
        return RoutineExplanation(
            status="deterministic",
            text=fallback,
            note="AI explanation is not configured.",
        )
    if not await ai_budget_allows(session, settings):
        return RoutineExplanation(
            status="deterministic",
            text=fallback,
            note="The daily AI request budget is exhausted.",
        )

    pack = _explanation_pack(plan)
    try:
        output = await gemini.generate(
            system_instruction=(
                _EXPLANATION_SYSTEM
                + json.dumps(pack.model_dump(mode="json"), separators=(",", ":"))
            ),
            user_text=(
                "Explain why this pre-computed schedule looks this way in at "
                "most three sentences. Do not change times or activities."
            ),
        )
    except GeminiError as exc:
        logger.warning("routine_explanation_failed", code=exc.code)
        return RoutineExplanation(status="deterministic", text=fallback, note=exc.code)

    try:
        draft = parse_and_validate(output.text, pack)
        if draft.actions or draft.avoid:
            raise DraftValidationError("unexpected_actions")
        text = draft.answer.strip()
        _validate_explanation(text, plan)
    except DraftValidationError as exc:
        logger.warning("routine_explanation_rejected", reason=exc.reason)
        return RoutineExplanation(
            status="deterministic", text=fallback, note=exc.reason
        )
    return RoutineExplanation(status="ai", text=text, model=output.model)


def _payload(
    plan: DomainPlan,
    *,
    household: Household,
    explanation: RoutineExplanation,
    override_activity_id: str | None,
) -> dict[str, Any]:
    payload = plan.to_payload()
    payload["location"] = {
        "lat": float(household.lat) if household.lat is not None else None,
        "lon": float(household.lon) if household.lon is not None else None,
        "city": household.city,
    }
    payload["explanation"] = explanation.model_dump(mode="json")
    if override_activity_id is not None:
        for block in payload["blocks"]:
            if block["activity_id"] == override_activity_id:
                block["override"] = True
                block["status"] = "overridden"
                block["rationale"].append(
                    {
                        "template_id": "routine.manual_change",
                        "params": {"changed": True},
                    }
                )
    return payload


def _items(
    session: AsyncSession,
    *,
    routine_id: UUID,
    payload: dict[str, Any],
    previous: Routine | None,
) -> None:
    previous_status: dict[str, str] = {}
    if previous is not None:
        for block in previous.plan.get("blocks", []):
            if block.get("status") in {"done", "skipped"}:
                previous_status[str(block.get("activity_id"))] = str(
                    block.get("status")
                )
    alternatives = payload.get("alternatives", [])
    for block in payload.get("blocks", []):
        activity_id = str(block["activity_id"])
        repo.add_item(
            session,
            routine_id=routine_id,
            activity_id=UUID(activity_id),
            title=str(block["title"]),
            category=str(block["category"]),
            venue=str(block["venue"]),
            priority=str(block["priority"]),
            fixed=bool(block["fixed"]),
            status=previous_status.get(activity_id, "scheduled"),
            start_at=datetime.fromisoformat(block["start_at"]),
            end_at=datetime.fromisoformat(block["end_at"]),
            duration_min=int(block["duration_min"]),
            override=bool(block["override"]),
            rationale=list(block.get("rationale", [])),
            context={
                "aqi": block.get("aqi"),
                "aqi_basis": block.get("aqi_basis"),
                "pm2_5": block.get("pm2_5"),
                "threshold": block.get("threshold"),
                "data_available": block.get("data_available"),
                "basis": block.get("basis"),
                "provider": payload["data_status"]["forecast"]["provider"],
                "issued_at": payload["data_status"]["forecast"]["issued_at"],
            },
            alternatives=[
                alternative
                for alternative in alternatives
                if alternative["activity_id"] == activity_id
            ],
        )
    for item in payload.get("unscheduled", []):
        repo.add_item(
            session,
            routine_id=routine_id,
            activity_id=UUID(str(item["activity_id"])),
            title=str(item["title"]),
            category=str(item["category"]),
            venue="unknown",
            priority=str(item["priority"]),
            fixed=False,
            status="unscheduled",
            start_at=None,
            end_at=None,
            duration_min=None,
            override=False,
            rationale=list(item.get("rationale", [])),
            context={
                "reason_code": item["reason_code"],
                "reason": item["reason"],
            },
            alternatives=[],
        )


def _output(routine: Routine) -> RoutinePlan:
    plan = routine.plan
    if plan.get("engine_version") != ENGINE_VERSION:
        raise ConflictError(
            "This plan version was generated by an earlier engine. Generate a "
            "new plan for this date.",
            code="STALE_ENGINE_VERSION",
        )
    blocks = [RoutineBlock.model_validate(raw) for raw in plan.get("blocks", [])]
    unscheduled = [
        RoutineUnscheduled.model_validate(raw) for raw in plan.get("unscheduled", [])
    ]
    data_status_raw = plan.get("data_status", {})
    forecast_raw = data_status_raw.get("forecast", {})
    observation_raw = data_status_raw.get("observation")
    explanation_raw = plan.get("explanation")
    if isinstance(explanation_raw, dict):
        try:
            explanation = RoutineExplanation.model_validate(explanation_raw)
        except ValidationError:
            explanation = RoutineExplanation(
                status="deterministic",
                text="The stored explanation could not be read.",
                note="invalid_stored_explanation",
            )
    else:
        explanation = RoutineExplanation(
            status="deterministic",
            text="This plan predates stored explanations; regenerate to create one.",
            note="missing_stored_explanation",
        )
    return RoutinePlan(
        id=routine.id,
        date=routine.plan_date,
        timezone=routine.timezone,
        location=plan.get("location"),
        engine_version=routine.engine_version,
        version=routine.version,
        status=routine.status,
        parent_routine_id=routine.parent_routine_id,
        confidence=str(
            plan.get("confidence", data_status_raw.get("confidence", "low"))
        ),
        blocks=blocks,
        unscheduled=unscheduled,
        alternatives=[
            RoutineAlternative.model_validate(raw)
            for raw in plan.get("alternatives", [])
        ],
        data_status=RoutineDataStatus(
            forecast=ForecastStatus.model_validate(forecast_raw),
            observation=(
                ObservationStatus.model_validate(observation_raw)
                if isinstance(observation_raw, dict)
                else None
            ),
            confidence=str(data_status_raw.get("confidence", "low")),
            notes=[str(note) for note in data_status_raw.get("notes", [])],
        ),
        scoring=RoutineScoring.model_validate(plan.get("scoring") or scoring_payload()),
        uncertainty=[str(note) for note in plan.get("uncertainty", [])],
        explanation=explanation,
        generated_at=routine.generated_at,
        expires_at=routine.expires_at,
    )


async def _generate(
    session: AsyncSession,
    profile: Profile,
    *,
    plan_date: date | None,
    refresh: bool,
    force_new: bool,
    override_activity_id: str | None,
    air_service: AirQualityService,
    settings: Settings,
    gemini: GeminiClient | None,
) -> RoutinePlan:
    household = _require_household(
        await households_repo.get_for_profile(session, profile.id)
    )
    members = await households_repo.list_members(session, household.id)
    if not members:
        raise UnprocessableEntityError(
            "Add at least one household member before generating a routine.",
            code="NO_MEMBERS",
        )
    rows = await repo.list_activities(session, household_id=household.id)
    if not rows:
        raise UnprocessableEntityError(
            "Add at least one activity before generating a routine.",
            code="NO_ACTIVITIES",
        )
    for row in rows:
        if row.fixed:
            overlap = _overlaps_fixed(
                preferred_start=row.preferred_start,
                duration_min=row.duration_min,
                others=[other for other in rows if other.id != row.id],
            )
            if overlap is not None:
                raise UnprocessableEntityError(
                    f"Fixed activities '{row.title}' and '{overlap}' overlap. "
                    "Edit one of them before generating a plan.",
                    code="FIXED_ACTIVITY_OVERLAP",
                )

    activities = _planner_activities(rows)
    member_profiles = _member_profiles(members)
    target = plan_date or local_today(household.timezone)

    lat = float(household.lat)  # type: ignore[arg-type]
    lon = float(household.lon)  # type: ignore[arg-type]
    forecast, _cache = await air_service.forecast(lat, lon, FORECAST_HOURS)
    hours = [
        ForecastHour(
            time=point.time,
            pm2_5=point.pm2_5,
            pm10=point.pm10,
            no2_ug_m3=point.no2_ug_m3,
            o3_ug_m3=point.o3_ug_m3,
        )
        for point in forecast.hourly
    ]
    provenance = forecast.provenance
    provider = provenance.provider if provenance is not None else "unknown"
    source_type = (
        str(provenance.source_type) if provenance is not None else "model_forecast"
    )
    issued_at = provenance.fetched_at if provenance is not None else None
    stale = bool(provenance.stale) if provenance is not None else False
    observation = await _observation(air_service, lat, lon)

    try:
        domain_plan = generate_plan(
            plan_date=target,
            timezone=household.timezone,
            activities=activities,
            members=member_profiles,
            hours=hours,
            provider=provider,
            source_type=source_type,
            issued_at=issued_at,
            stale=stale,
            observation=observation,
            now=utc_now(),
        )
    except ForecastCoverageError as exc:
        raise UnprocessableEntityError(
            "The forecast does not cover this date yet. Try tomorrow or a nearer date.",
            code="FORECAST_COVERAGE",
        ) from exc
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise UnprocessableEntityError(str(exc), code="INVALID_ROUTINE_INPUT") from exc

    inputs_hash = _inputs_hash(
        plan_date=target,
        timezone=household.timezone,
        activities=activities,
        members=member_profiles,
        hours=hours,
        provider=provider,
        issued_at=issued_at,
        stale=stale,
    )
    previous = await repo.latest_active_for_date(
        session, household_id=household.id, plan_date=target
    )
    if (
        previous is not None
        and previous.inputs_hash == inputs_hash
        and not refresh
        and not force_new
    ):
        return _output(previous)

    explanation = await _explain(
        domain_plan, settings=settings, gemini=gemini, session=session
    )
    payload = _payload(
        domain_plan,
        household=household,
        explanation=explanation,
        override_activity_id=override_activity_id,
    )
    latest = await repo.latest_version_for_date(
        session, household_id=household.id, plan_date=target
    )
    version = latest.version + 1 if latest is not None else 1
    now = utc_now()
    try:
        await repo.supersede_active(
            session, household_id=household.id, plan_date=target
        )
        routine = repo.add(
            session,
            household_id=household.id,
            plan_date=target,
            timezone=household.timezone,
            engine_version=ENGINE_VERSION,
            inputs_hash=inputs_hash,
            plan=payload,
            version=version,
            parent_routine_id=previous.id if previous is not None else None,
            expires_at=now + timedelta(hours=PLAN_TTL_HOURS),
        )
        await session.flush()
        _items(
            session,
            routine_id=routine.id,
            payload=payload,
            previous=previous,
        )
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing = await repo.find_active_by_inputs(
            session,
            household_id=household.id,
            plan_date=target,
            inputs_hash=inputs_hash,
        )
        if existing is not None:
            return _output(existing)
        raise
    except SQLAlchemyError as exc:
        await session.rollback()
        raise DatabaseUnavailableError() from exc

    logger.info(
        "routine_generated",
        household_id=str(household.id),
        routine_id=str(routine.id),
        date=target.isoformat(),
        version=version,
        scheduled=len(payload["blocks"]),
        unscheduled=len(payload["unscheduled"]),
        confidence=domain_plan.data_status.confidence,
        provider=provider,
        explanation=explanation.status,
    )
    return _output(routine)


async def generate(
    session: AsyncSession,
    profile: Profile,
    *,
    plan_date: date | None,
    refresh: bool,
    air_service: AirQualityService,
    settings: Settings,
    gemini: GeminiClient | None,
) -> RoutinePlan:
    return await _generate(
        session,
        profile,
        plan_date=plan_date,
        refresh=refresh,
        force_new=False,
        override_activity_id=None,
        air_service=air_service,
        settings=settings,
        gemini=gemini,
    )


async def get(
    session: AsyncSession,
    profile: Profile,
    *,
    plan_date: date | None = None,
    routine_id: UUID | None = None,
) -> RoutinePlan:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise NotFoundError("No household profile exists for this session.")
    if routine_id is not None:
        routine = await repo.get(
            session, household_id=household.id, routine_id=routine_id
        )
        if routine is None:
            raise NotFoundError("Routine not found.")
        return _output(routine)
    target = plan_date or local_today(household.timezone)
    routine = await repo.latest_active_for_date(
        session, household_id=household.id, plan_date=target
    )
    if routine is None:
        raise NotFoundError("No routine has been generated for this date yet.")
    return _output(routine)


async def history(
    session: AsyncSession,
    profile: Profile,
    *,
    plan_date: date | None,
    limit: int,
    offset: int,
) -> RoutineHistory:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise NotFoundError("No household profile exists for this session.")
    rows, total = await repo.history(
        session,
        household_id=household.id,
        plan_date=plan_date,
        limit=limit,
        offset=offset,
    )
    return RoutineHistory(
        items=[
            RoutineVersionSummary(
                id=row.id,
                date=row.plan_date,
                version=row.version,
                status=row.status,
                confidence=str(
                    row.plan.get(
                        "confidence",
                        row.plan.get("data_status", {}).get("confidence", "low"),
                    )
                ),
                scheduled_count=len(row.plan.get("blocks", [])),
                unscheduled_count=len(row.plan.get("unscheduled", [])),
                engine_version=row.engine_version,
                generated_at=row.generated_at,
            )
            for row in rows
        ],
        limit=limit,
        offset=offset,
        total=total,
    )


def _apply_change(
    row: RoutineActivity, change: RoutineActivityChange
) -> dict[str, Any]:
    payload = RoutineActivityUpdate(
        **{
            field: getattr(change, field)
            for field in change.model_fields_set
            if field != "cancel" and getattr(change, field) is not None
        }
    )
    return _values_from_update(row, payload)


async def update_routine_activity(
    session: AsyncSession,
    profile: Profile,
    *,
    routine_id: UUID,
    activity_id: UUID,
    change: RoutineActivityChange,
    air_service: AirQualityService,
    settings: Settings,
    gemini: GeminiClient | None,
) -> RoutinePlan:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise NotFoundError("No household profile exists for this session.")
    routine = await repo.get(session, household_id=household.id, routine_id=routine_id)
    if routine is None:
        raise NotFoundError("Routine not found.")
    if routine.status != "active":
        raise ConflictError(
            "Only the active routine version can be changed.",
            code="ROUTINE_SUPERSEDED",
        )
    row = await repo.get_activity(
        session, household_id=household.id, activity_id=activity_id
    )
    if row is None or not row.active:
        raise NotFoundError("Activity not found in this household.")
    if str(activity_id) not in {
        str(block.get("activity_id")) for block in routine.plan.get("blocks", [])
    } and str(activity_id) not in {
        str(item.get("activity_id")) for item in routine.plan.get("unscheduled", [])
    }:
        raise NotFoundError("Activity not found in this routine version.")

    members = await households_repo.list_members(session, household.id)
    if change.cancel:
        row.active = False
    else:
        values = _apply_change(row, change)
        _validate_values(values, _member_ids(members))
        if values["fixed"]:
            others = await repo.list_activities(session, household_id=household.id)
            overlap = _overlaps_fixed(
                preferred_start=values["preferred_start"],
                duration_min=values["duration_min"],
                others=[other for other in others if other.id != row.id],
            )
            if overlap is not None:
                raise UnprocessableEntityError(
                    f"This fixed activity overlaps '{overlap}'.",
                    code="FIXED_ACTIVITY_OVERLAP",
                )
        for field, value in values.items():
            setattr(row, field, value)
    await session.flush()
    plan = await _generate(
        session,
        profile,
        plan_date=routine.plan_date,
        refresh=True,
        force_new=True,
        override_activity_id=str(activity_id),
        air_service=air_service,
        settings=settings,
        gemini=gemini,
    )
    logger.info(
        "routine_activity_changed",
        household_id=str(household.id),
        routine_id=str(routine.id),
        activity_id=str(activity_id),
        cancelled=change.cancel,
        new_version=plan.version,
    )
    return plan


async def replan(
    session: AsyncSession,
    profile: Profile,
    *,
    routine_id: UUID,
    plan_date: date | None,
    air_service: AirQualityService,
    settings: Settings,
    gemini: GeminiClient | None,
) -> RoutinePlan:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise NotFoundError("No household profile exists for this session.")
    routine = await repo.get(session, household_id=household.id, routine_id=routine_id)
    if routine is None:
        raise NotFoundError("Routine not found.")
    if routine.status != "active":
        raise ConflictError(
            "Only the active routine version can be replanned.",
            code="ROUTINE_SUPERSEDED",
        )
    if plan_date is not None and plan_date != routine.plan_date:
        raise UnprocessableEntityError(
            "The replan date must match the routine date.",
            code="DATE_MISMATCH",
        )
    return await _generate(
        session,
        profile,
        plan_date=routine.plan_date,
        refresh=True,
        force_new=False,
        override_activity_id=None,
        air_service=air_service,
        settings=settings,
        gemini=gemini,
    )


async def update_item(
    session: AsyncSession,
    profile: Profile,
    *,
    routine_id: UUID,
    block_id: str,
    payload: RoutineItemUpdate,
) -> RoutinePlan:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise NotFoundError("No household profile exists for this session.")
    routine = await repo.get(session, household_id=household.id, routine_id=routine_id)
    if routine is None:
        raise NotFoundError("Routine not found.")
    plan = dict(routine.plan)
    blocks = [dict(raw) for raw in plan.get("blocks", [])]
    matched: dict[str, Any] | None = None
    for block in blocks:
        if block.get("id") == block_id:
            block["status"] = payload.status
            matched = block
            break
    if matched is None:
        raise NotFoundError("Routine item not found.")
    plan["blocks"] = blocks
    await repo.replace_plan(session, routine, plan)
    item = await repo.get_item_by_activity(
        session,
        routine_id=routine.id,
        activity_id=UUID(str(matched["activity_id"])),
    )
    if item is not None:
        item.status = payload.status
    try:
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise DatabaseUnavailableError() from exc
    return _output(routine)
