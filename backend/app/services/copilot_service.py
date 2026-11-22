"""Copilot orchestration: FactPack, model call, fail-closed validation, fallback.

The assistant is grounded in server-built FactPack data only. It never receives
names, coordinates or free-text household notes directly. Citations are always
rebuilt from the FactPack server-side. Without a model key, or when model output
fails validation, a deterministic answer is returned and source is 'deterministic'.

Anonymous calls are accepted but not persisted; a posted conversation_id must belong
to the bearer-token profile or the request returns 404.
"""

from __future__ import annotations

import json
import re
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AppError, NotFoundError
from app.core.logging import get_logger
from app.domain.facts import Fact, FactPack
from app.integrations.ai.fallback import compose_fallback
from app.integrations.ai.gemini import GeminiClient, GeminiError
from app.integrations.ai.tool_executor import execute_tool
from app.integrations.ai.validation import (
    AiDraft,
    DraftValidationError,
    parse_and_validate,
)
from app.models.household import Household, HouseholdMember
from app.models.profile import Profile
from app.repositories import (
    air as air_repo,
    conversations as conversations_repo,
    households as households_repo,
    usage as usage_repo,
)
from app.schemas.copilot import (
    CopilotAction,
    CopilotAnswer,
    CopilotAvoid,
    CopilotCitation,
    CopilotRequest,
)
from app.services import (
    ecoroute_service,
    family_service,
    impact_service,
    indoor_shield_service,
    routine_service,
)
from app.services.ai_budget import AI_BUDGET_KEY, ai_budget_allows
from app.services.air_quality_service import AirQualityService
from app.utils.time import utc_now

logger = get_logger(__name__)

_CONVERSATION_TTL_DAYS = 7
_DISCLAIMER = "General air-quality guidance only. This is not medical advice."
_SYSTEM_INSTRUCTION = (
    "You are a grounded environmental intelligence assistant. "
    "Answer based on the provided FactPack data only. "
    "Do not invent AQI values, sensor readings, or environmental measurements. "
    "Cite fact ids for any numeric claims. "
    "Distinguish observed measurements, forecasts, calculations, and educational information. "
    "If the FactPack has no relevant data, say so. "
    "Never provide medical diagnoses or medical advice. "
    "Disclaimer: General air-quality guidance only. This is not medical advice."
)

# ---------------------------------------------------------------------------
# Helper: build a FactPack enriched with context from all services.
# ---------------------------------------------------------------------------


async def _build_fact_pack(
    air_service: AirQualityService,
    *,
    session: AsyncSession | None,
    profile: Profile | None,
    lat: float | None,
    lon: float | None,
    timezone: str,
    members: list[HouseholdMember] | None = None,
) -> FactPack:
    """Build a FactPack enriched with data from all integrated services.

    Only grounded, server-produced values are included. Names, coordinates,
    free-text notes and individual health conditions never enter the pack.
    """
    age_bands: set[str] = {m.age_band for m in (members or []) if m.age_band}

    context: dict[str, Any] = {
        "timezone": timezone,
        "sensitive_group": bool(age_bands & {"0-5", "60+"}),
        "has_children": bool(age_bands & {"0-5", "6-12", "13-17"}),
    }

    facts: list[Fact] = []

    # --- Air quality (current + forecast) ---
    # A request without a saved location has no coordinates. Fetching by
    # ``None`` previously raised a TypeError; absence of coordinates is an
    # honest "no reading" state, not a crash.
    if lat is not None and lon is not None:
        try:
            current, _cache = await air_service.current(lat, lon)
        except AppError:
            current = None
        if current is not None:
            source = f"{current.provenance.provider} (modelled)"
            observed_at = current.provenance.observed_at
            for key, label, unit in (
                ("pm2_5", "PM2.5", "µg/m³"),
                ("pm10", "PM10", "µg/m³"),
                ("no2_ug_m3", "Nitrogen dioxide", "µg/m³"),
                ("so2_ug_m3", "Sulphur dioxide", "µg/m³"),
                ("o3_ug_m3", "Ozone", "µg/m³"),
                ("co_ug_m3", "Carbon monoxide", "µg/m³"),
            ):
                value = getattr(current.reading, key)
                if value is not None:
                    facts.append(
                        Fact(
                            id=f"aq.current.{key}",
                            label=label,
                            value=round(float(value), 1),
                            unit=unit,
                            category="air",
                            source=source,
                            observed_at=observed_at,
                        )
                    )
            if current.cpcb_aqi is not None:
                facts.append(
                    Fact(
                        id="aq.current.aqi_cpcb",
                        label="CPCB AQI (computed)",
                        value=float(current.cpcb_aqi.value),
                        unit="index",
                        category=current.cpcb_aqi.category,
                        source="CPCB 2014 method applied to modelled values",
                        observed_at=observed_at,
                    )
                )
            if current.provenance.stale:
                facts.append(
                    Fact(
                        id="aq.current.staleness",
                        label="Data is stale",
                        value="saved data",
                        source="Air-quality cache",
                        observed_at=current.provenance.fetched_at,
                    )
                )

        try:
            forecast, _cache = await air_service.forecast(lat, lon, 24)
        except AppError:
            forecast = None
        if forecast is not None:
            points = [point for point in forecast.hourly if point.pm2_5 is not None]
            if points:
                best = min(points, key=lambda point: point.pm2_5 or 0.0)
                worst = max(points, key=lambda point: point.pm2_5 or 0.0)
                facts.extend(
                    [
                        Fact(
                            id="aq.forecast.min_pm2_5",
                            label="Lowest forecast PM2.5 (24 h)",
                            value=round(float(best.pm2_5 or 0.0), 1),
                            unit="µg/m³",
                            category="forecast",
                            source="CAMS forecast via Open-Meteo",
                            at=best.time,
                        ),
                        Fact(
                            id="aq.forecast.max_pm2_5",
                            label="Highest forecast PM2.5 (24 h)",
                            value=round(float(worst.pm2_5 or 0.0), 1),
                            unit="µg/m³",
                            category="forecast",
                            source="CAMS forecast via Open-Meteo",
                            at=worst.time,
                        ),
                    ]
                )

    # --- Family intelligence ---
    family_recommendations: list[str] = []
    if session is not None and profile is not None:
        try:
            family = await family_service.get_profile(session, profile)
            context["has_children"] = family.has_children
            context["sensitive_group"] = (
                context["sensitive_group"]
                or family.has_health_flags
                or family.has_older_adults
            )
            recommendations = await family_service.list_recommendations(
                session, profile, limit=3, offset=0
            )
            family_recommendations = [
                f"{item.activity_title}: {item.action_label}"
                for item in recommendations.items
            ]
        except Exception:
            logger.warning("family_context_unavailable", profile_id=profile.id)

    # --- SmartRoutine ---
    routine_blocks: list[str] = []
    if session is not None and profile is not None:
        try:
            routine = await routine_service.get(session, profile)
            context["routine_date"] = routine.date.isoformat()
            routine_blocks = [
                f"{block.title} {block.start}-{block.end} ({block.venue})"
                for block in routine.blocks[:3]
            ]
        except Exception:
            logger.warning("routine_context_unavailable", profile_id=profile.id)

    # --- Impact Intelligence ---
    if session is not None and profile is not None:
        try:
            impact_summary = await impact_service.summary(session, profile, days=30)
            savings = await impact_service.baseline_and_savings(
                session, profile, days=30
            )
            facts.extend(
                [
                    Fact(
                        id="impact.total_co2e_30d",
                        label="Logged activity CO2e (30 days)",
                        value=round(float(impact_summary.total_co2e_kg), 4),
                        unit="kgCO2e",
                        category="impact",
                        source="Impact Intelligence activity ledger",
                    ),
                    Fact(
                        id="impact.activity_count_30d",
                        label="Logged activities (30 days)",
                        value=impact_summary.activity_count,
                        unit="activities",
                        category="impact",
                        source="Impact Intelligence activity ledger",
                    ),
                ]
            )
            if savings.savings_co2e_kg is not None:
                facts.append(
                    Fact(
                        id="impact.modelled_savings_30d",
                        label="Estimated savings vs modelled car baseline (30 days)",
                        value=round(float(savings.savings_co2e_kg), 4),
                        unit="kgCO2e",
                        category="impact",
                        source=(
                            "Impact Intelligence modelled baseline "
                            "(assumption, not a measured value)"
                        ),
                    )
                )
            goals = await impact_service.list_goals(session, profile)
            active_goals = [goal for goal in goals if goal.is_active]
            if active_goals:
                progress = "; ".join(
                    f"{goal.title} {float(goal.progress_percent or 0):.0f}%"
                    for goal in active_goals[:3]
                )
                facts.extend(
                    [
                        Fact(
                            id="impact.active_goals",
                            label="Active sustainability goals",
                            value=len(active_goals),
                            unit="goals",
                            category="impact",
                            source="Impact Intelligence goals",
                        ),
                        Fact(
                            id="impact.goal_progress",
                            label="Sustainability goal progress",
                            value=progress,
                            category="impact",
                            source="Impact Intelligence goals",
                        ),
                    ]
                )
        except Exception:
            logger.warning("impact_context_unavailable", profile_id=profile.id)

    # --- IndoorShield (latest assessment only; free-text notes excluded) ---
    if session is not None and profile is not None:
        try:
            assessments = await indoor_shield_service.list_assessments(
                session, profile, limit=1, offset=0
            )
            if assessments.assessments:
                latest = assessments.assessments[0]
                facts.extend(
                    [
                        Fact(
                            id="indoor.latest_assessment",
                            label="Latest IndoorShield assessment",
                            value=latest.status,
                            category="indoor",
                            source="IndoorShield deterministic assessment",
                        ),
                        Fact(
                            id="indoor.action_counts",
                            label="Indoor action counts",
                            value=(
                                f"{latest.action_counts.pending} pending, "
                                f"{latest.action_counts.completed} completed"
                            ),
                            category="indoor",
                            source="IndoorShield action ledger",
                        ),
                    ]
                )
        except Exception:
            logger.warning("indoor_context_unavailable", profile_id=profile.id)

    # --- EcoRoute (latest saved journey; coordinates and notes excluded) ---
    if session is not None and profile is not None:
        try:
            journeys = await ecoroute_service.list_journeys(
                session, profile, limit=1, offset=0
            )
            if journeys:
                journey = journeys[0]
                per_passenger = (
                    "unavailable"
                    if journey.co2e_per_passenger_kg is None
                    else f"{float(journey.co2e_per_passenger_kg):.3f} kgCO2e/passenger"
                )
                facts.append(
                    Fact(
                        id="ecoroute.latest_journey",
                        label="Latest saved journey",
                        value=(
                            f"{journey.selected_mode}; {journey.distance_km} km; "
                            f"{per_passenger}"
                        ),
                        category="transport",
                        source="EcoRoute saved journey",
                    )
                )
        except Exception:
            logger.warning("ecoroute_context_unavailable", profile_id=profile.id)

    if family_recommendations:
        facts.append(
            Fact(
                id="family.recommendations",
                label="Family guidance",
                value="; ".join(family_recommendations[:3]),
                category="family",
                source="Family Intelligence deterministic rules",
            )
        )
    if routine_blocks:
        facts.append(
            Fact(
                id="routine.schedule",
                label="Today's routine blocks",
                value="; ".join(routine_blocks),
                category="routine",
                source="SmartRoutine deterministic plan",
            )
        )

    return FactPack(facts=facts, context=context, engine={"facts": len(facts)})


# ---------------------------------------------------------------------------
# Core chat logic.
# ---------------------------------------------------------------------------


async def chat(
    session: AsyncSession | None,
    profile: Profile | None,
    payload: CopilotRequest,
    *,
    settings: Settings,
    air_service: AirQualityService,
    gemini: GeminiClient | None,
) -> CopilotAnswer:
    household = (
        await households_repo.get_for_profile(session, profile.id)
        if session is not None and profile is not None
        else None
    )
    members: list[HouseholdMember] = (
        await households_repo.list_members(session, household.id)
        if session is not None and household is not None
        else []
    )
    lat, lon = _location(payload, household)
    timezone = household.timezone if household is not None else "UTC"

    conversation_id: UUID | None = None
    if profile is not None and session is not None:
        conversation_id = await _resolve_conversation(
            session, profile, payload, lat=lat, lon=lon
        )
    history = (
        await conversations_repo.recent_user_messages(session, conversation_id)
        if session is not None and conversation_id is not None
        else []
    )

    pack = await _build_fact_pack(
        air_service,
        session=session,
        profile=profile,
        lat=lat,
        lon=lon,
        timezone=timezone,
        members=members,
    )

    (
        draft,
        source,
        model,
        latency_ms,
        input_tokens,
        output_tokens,
        validation,
        error_code,
    ) = await _answer(pack, history, payload.message, settings, gemini, session)

    citations = _citations(draft, pack)
    severity = _severity(pack)
    actions = [
        CopilotAction(
            title=action.title,
            detail=action.detail,
            time_window=action.time_window,
            fact_refs=list(action.fact_refs),
            confidence=action.confidence,
        )
        for action in draft.actions
    ]
    avoid = [
        CopilotAvoid(title=item.title, reason_fact_ref=item.reason_fact_ref)
        for item in draft.avoid
    ]
    citations_out = [
        CopilotCitation(
            fact_id=citation.fact_id,
            label=citation.label,
            value=citation.value,
            unit=citation.unit,
            source=citation.source,
            observed_at=citation.observed_at,
        )
        for citation in citations
    ]
    message_id = uuid4()
    if session is not None and profile is not None and conversation_id is not None:
        structured: dict[str, object] = {
            "severity": severity,
            "actions": [item.model_dump(mode="json") for item in actions],
            "avoid": [item.model_dump(mode="json") for item in avoid],
            "citations": [item.model_dump(mode="json") for item in citations_out],
            "source": source,
            "model": model,
            "latency_ms": latency_ms,
            "disclaimer": _DISCLAIMER,
        }
        message_id = await _persist(
            session,
            conversation_id=conversation_id,
            user_text=payload.message,
            draft=draft,
            structured=structured,
            pack=pack,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            validation=validation,
            error_code=error_code,
        )

    return CopilotAnswer(
        conversation_id=str(conversation_id or uuid4()),
        message_id=str(message_id),
        answer=draft.answer,
        severity=severity,
        actions=actions,
        avoid=avoid,
        citations=citations_out,
        source=source,
        model=model,
        latency_ms=latency_ms,
        disclaimer=_DISCLAIMER,
    )


# ---------------------------------------------------------------------------
# _answer - model call or fallback.
# ---------------------------------------------------------------------------


async def _answer(
    pack: FactPack,
    history: list[str],
    message: str,
    settings: Settings,
    gemini: GeminiClient | None,
    session: AsyncSession | None,
) -> tuple[
    AiDraft,
    str,
    str | None,
    int | None,
    int | None,
    int | None,
    str,
    str | None,
]:
    budget_ok = await ai_budget_allows(session, settings)
    if gemini is None or not budget_ok:
        error_code = "budget_exhausted" if gemini is not None else None
        return (
            compose_fallback(pack),
            "deterministic",
            None,
            None,
            None,
            None,
            "fallback",
            error_code,
        )

    try:
        output = await gemini.generate(
            system_instruction=(
                _SYSTEM_INSTRUCTION
                + json.dumps(pack.model_dump(mode="json"), separators=(",", ":"))
            ),
            user_text=_user_text(history, message),
        )
    except GeminiError as exc:
        logger.warning("copilot_model_failed", code=exc.code)
        return (
            compose_fallback(pack),
            "deterministic",
            None,
            None,
            None,
            None,
            "fallback",
            exc.code,
        )

    try:
        draft = parse_and_validate(output.text, pack)
    except DraftValidationError as exc:
        logger.warning("copilot_output_rejected", reason=exc.reason)
        return (
            compose_fallback(pack),
            "deterministic",
            None,
            output.latency_ms,
            output.input_tokens,
            output.output_tokens,
            "rejected",
            exc.reason,
        )
    return (
        draft,
        "ai",
        output.model,
        output.latency_ms,
        output.input_tokens,
        output.output_tokens,
        "valid",
        None,
    )


# ---------------------------------------------------------------------------
# Helpers: _location, _resolve_conversation, _citations, _severity, _persist,
# _user_text - kept from the original implementation.
# ---------------------------------------------------------------------------


def _location(
    payload: CopilotRequest, household: Household | None
) -> tuple[float | None, float | None]:
    if payload.context is not None:
        return payload.context.lat, payload.context.lon
    if household is None or household.lat is None or household.lon is None:
        return None, None
    return float(household.lat), float(household.lon)


async def _resolve_conversation(
    session: AsyncSession,
    profile: Profile,
    payload: CopilotRequest,
    *,
    lat: float | None,
    lon: float | None,
) -> UUID:
    if payload.conversation_id is not None:
        conversation = await conversations_repo.get_conversation(
            session, conversation_id=payload.conversation_id, profile_id=profile.id
        )
        if conversation is None:
            raise NotFoundError("Conversation not found for this session.")
        return conversation.id
    conversation = await conversations_repo.create_conversation(
        session,
        profile_id=profile.id,
        expires_at=utc_now() + timedelta(days=_CONVERSATION_TTL_DAYS),
        lat_key=air_repo.key_for(lat) if lat is not None else None,
        lon_key=air_repo.key_for(lon) if lon is not None else None,
    )
    await session.commit()
    return conversation.id


def _user_text(history: list[str], message: str) -> str:
    if not history:
        return message
    _NUMBER_PATTERN = re.compile(r"\d+(?:[.,]\d+)?")
    cleaned = [_NUMBER_PATTERN.sub("", item)[:400] for item in history if item.strip()]
    joinable = "\n".join(f"- {item}" for item in cleaned)
    return (
        "Recent questions in this session (numbers removed):\n"
        f"{joinable}\n\nCurrent question:\n{message}"
    )


def _citations(draft: AiDraft, pack: FactPack) -> list[CopilotCitation]:
    referenced: list[str] = []
    for action in draft.actions:
        referenced.extend(action.fact_refs)
    for item in draft.avoid:
        if item.reason_fact_ref is not None:
            referenced.append(item.reason_fact_ref)
    citations: list[CopilotCitation] = []
    seen: set[str] = set()
    for fact_id in referenced:
        if fact_id in seen:
            continue
        seen.add(fact_id)
        fact = pack.find(fact_id)
        if fact is None:
            continue
        citations.append(
            CopilotCitation(
                fact_id=fact.id,
                label=fact.label,
                value=fact.value,
                unit=fact.unit,
                source=fact.source,
                observed_at=fact.observed_at or fact.at,
            )
        )
    return citations


def _severity(pack: FactPack) -> str | None:
    fact = pack.find("aq.current.aqi_cpcb")
    if fact is None or fact.category is None:
        return None
    return fact.category


async def _persist(
    session: AsyncSession,
    *,
    conversation_id: UUID,
    user_text: str,
    draft: AiDraft,
    structured: dict[str, object],
    pack: FactPack,
    model: str | None,
    input_tokens: int | None,
    output_tokens: int | None,
    latency_ms: int | None,
    validation: str,
    error_code: str | None,
) -> UUID:
    await conversations_repo.add_message(
        session,
        conversation_id=conversation_id,
        role="user",
        content=user_text,
    )
    stored = await conversations_repo.add_message(
        session,
        conversation_id=conversation_id,
        role="assistant",
        content=draft.answer,
        structured=structured,
        fact_pack_hash=pack.sha256(),
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        validation=validation,
        error_code=error_code,
    )
    conversation = await conversations_repo.get_conversation_by_id(
        session, conversation_id
    )
    if conversation is not None:
        await conversations_repo.touch_conversation(session, conversation, utc_now())
    await usage_repo.record_tokens(
        session,
        key=AI_BUDGET_KEY,
        day=utc_now().date(),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    await session.commit()
    return stored.id


# ---------------------------------------------------------------------------
# Tool dispatch - the model may request tools; the backend executes them and
# returns results so the model can incorporate them into its next response.
# ---------------------------------------------------------------------------


async def request_tool(
    tool_name: str,
    arguments: dict[str, Any],
    profile: Profile | None,
    session: AsyncSession | None,
    *,
    air_service: AirQualityService | None = None,
) -> dict[str, Any]:
    """Ask the backend to execute a tool and return its result.

    The model sends ``tool_name`` and ``arguments``; the backend runs the
    registered handler and returns a plain-data dict.
    """
    return await execute_tool(
        tool_name=tool_name,
        arguments=arguments,
        profile=profile,
        session=session,
        air_service=air_service,
    )
