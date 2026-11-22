"""Deterministic composer used whenever the model is unavailable or rejected."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain.facts import Fact, FactPack
from app.integrations.ai.validation import AiDraft, DraftAction, DraftAvoid

_NO_DATA_ANSWER = (
    "I need an air-quality reading near you before I can answer. "
    "Save a location and ask again."
)


def compose_fallback(pack: FactPack) -> AiDraft:
    if not pack.facts:
        return AiDraft(answer=_NO_DATA_ANSWER, actions=[], avoid=[])

    timezone = str(pack.context.get("timezone") or "UTC")
    current = pack.find("aq.current.pm2_5")
    aqi = pack.find("aq.current.aqi_cpcb")
    best = pack.find("aq.forecast.min_pm2_5")
    worst = pack.find("aq.forecast.max_pm2_5")

    if current is None and aqi is None and best is None:
        return AiDraft(answer=_NO_DATA_ANSWER, actions=[], avoid=[])

    sentences: list[str] = []
    if current is not None:
        sentences.append(f"PM2.5 is currently {_format_value(current)} µg/m³.")
    if aqi is not None:
        category = aqi.category or "unclassified"
        sentences.append(f"The CPCB AQI is {_format_value(aqi)} ({category}).")
    if best is not None and best.at is not None:
        sentences.append(
            f"The lowest forecast PM2.5 in the next 24 hours is "
            f"{_format_value(best)} µg/m³ around {_clock(best.at, timezone)}."
        )

    actions: list[DraftAction] = []
    if best is not None and best.at is not None:
        start = _clock(best.at, timezone)
        end = _clock(best.at, timezone, offset_minutes=30)
        actions.append(
            DraftAction(
                title=f"Plan outdoor time near {start}",
                detail="Forecast PM2.5 is lowest in this window.",
                time_window=f"{start}-{end}",
                fact_refs=[best.id],
                confidence="high",
            )
        )
    if aqi is not None and aqi.category in {"moderate", "poor", "very_poor", "severe"}:
        actions.append(
            DraftAction(
                title="Keep windows closed during peaks",
                detail="Outdoor particles raise indoor concentrations when windows are open.",
                time_window=None,
                fact_refs=[aqi.id],
                confidence="medium",
            )
        )
    if not actions:
        actions.append(
            DraftAction(
                title="Check the current reading before going out",
                detail="Use the air-quality page for the latest modelled value.",
                time_window=None,
                fact_refs=[pack.facts[0].id],
                confidence="low",
            )
        )

    avoid: list[DraftAvoid] = []
    if worst is not None and worst.at is not None:
        avoid.append(
            DraftAvoid(
                title=f"Avoid outdoor exercise around {_clock(worst.at, timezone)}",
                reason_fact_ref=worst.id,
            )
        )

    return AiDraft(
        answer=" ".join(sentences) or _NO_DATA_ANSWER,
        actions=actions,
        avoid=avoid,
    )


def _format_value(fact: Fact) -> str:
    value = fact.value
    if isinstance(value, float):
        return f"{value:.1f}".rstrip("0").rstrip(".")
    return str(value)


def _clock(value: datetime, timezone: str, *, offset_minutes: int = 0) -> str:
    zone: tzinfo
    try:
        zone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        zone = UTC
    local = value.astimezone(zone)
    if offset_minutes:
        local = local + timedelta(minutes=offset_minutes)
    return local.strftime("%H:%M")
