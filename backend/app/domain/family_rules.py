"""Deterministic family activity rules.

This module is the safety-critical part of the family engine. It contains no
language-model calls: the same inputs always produce the same assessment.

Evidence policy
---------------
* CPCB 2014 supplies the AQI categories and the PM2.5 sub-index breakpoints.
* WHO 2021 supplies the PM2.5 24-hour guideline value (15 µg/m³) as context,
  not as an AQI category.
* Public activity guidance for sensitive groups (US EPA AQI programme) is
  mapped conservatively onto CPCB categories. This mapping is a product
  decision, not an official CPCB activity guideline.
* Nothing here diagnoses a condition, predicts an individual outcome or
  guarantees safety.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Literal, cast
from zoneinfo import ZoneInfo

Action = Literal[
    "proceed",
    "reduce_exposure",
    "reschedule",
    "move_indoor",
    "avoid_outdoor",
    "check_back",
]
Confidence = Literal["high", "medium", "low"]
GuidanceBasis = Literal["cpcb_aqi", "pm25_band", "none"]
Severity = Literal[
    "good",
    "satisfactory",
    "moderate",
    "poor",
    "very_poor",
    "severe",
    "info",
]
EvidenceStatus = Literal["official", "public_guidance", "product_policy", "none"]

RULES_VERSION = "family-rules-1.0.0"
FORECAST_IMPROVEMENT_RATIO = 0.8
MIN_SUGGESTION_LEAD_MIN = 30


@dataclass(frozen=True)
class Evidence:
    source: str
    note: str


_CPCB_SOURCE = Evidence(
    source="CPCB National Air Quality Index (2014), Central Pollution Control Board",
    note=(
        "AQI categories (good ≤50, satisfactory ≤100, moderate ≤200, poor "
        "≤300, very poor ≤400, severe >400) and PM2.5 sub-index breakpoints."
    ),
)
_WHO_SOURCE = Evidence(
    source="WHO global air quality guidelines (2021)",
    note=(
        "PM2.5 24-hour guideline value of 15 µg/m³; used as context for "
        "concentration bands, not as a categorical AQI."
    ),
)
_EPA_SOURCE = Evidence(
    source=(
        "US EPA Air Quality Index activity guidance for sensitive groups "
        "(public health guidance)"
    ),
    note=(
        "Public guidance to reduce prolonged or heavy outdoor exertion when "
        "air quality is unhealthy. Mapped conservatively onto CPCB categories; "
        "this mapping is a SAANS SAATHI product decision."
    ),
)


@dataclass(frozen=True)
class RuleDefinition:
    identifier: str
    trigger: str
    recommended_action: Action
    explanation: str
    data_requirements: tuple[str, ...]
    evidence: tuple[Evidence, ...]
    evidence_status: EvidenceStatus
    confidence: Confidence


RULES: dict[str, RuleDefinition] = {
    "FAM-000": RuleDefinition(
        identifier="FAM-000",
        trigger="The preferred activity is already indoors.",
        recommended_action="proceed",
        explanation=(
            "Outdoor readings do not describe indoor air. Keep ventilation "
            "and filtration appropriate for the room."
        ),
        data_requirements=("activity venue",),
        evidence=(),
        evidence_status="product_policy",
        confidence="medium",
    ),
    "FAM-001": RuleDefinition(
        identifier="FAM-001",
        trigger="No validated current or forecast pollution value is available.",
        recommended_action="check_back",
        explanation=(
            "Without a reading, no claim about outdoor safety can be made. "
            "Check again before the activity."
        ),
        data_requirements=("current pm2.5 or CPCB AQI", "or forecast pm2.5"),
        evidence=(_CPCB_SOURCE,),
        evidence_status="none",
        confidence="low",
    ),
    "FAM-002": RuleDefinition(
        identifier="FAM-002",
        trigger="The only available reading is marked stale.",
        recommended_action="check_back",
        explanation=(
            "Stale data cannot describe current conditions. A fresh reading is "
            "required before acting on it."
        ),
        data_requirements=("freshness timestamp",),
        evidence=(_CPCB_SOURCE,),
        evidence_status="none",
        confidence="low",
    ),
    "FAM-003": RuleDefinition(
        identifier="FAM-003",
        trigger="CPCB AQI category is good or the PM2.5 band is low.",
        recommended_action="proceed",
        explanation="Air quality is in the lowest CPCB category.",
        data_requirements=("CPCB AQI or PM2.5",),
        evidence=(_CPCB_SOURCE,),
        evidence_status="official",
        confidence="high",
    ),
    "FAM-004": RuleDefinition(
        identifier="FAM-004",
        trigger="CPCB AQI is satisfactory and the household has no sensitivity flag.",
        recommended_action="proceed",
        explanation=(
            "The CPCB satisfactory category does not require a change for the "
            "general population."
        ),
        data_requirements=("CPCB AQI", "household sensitivity"),
        evidence=(_CPCB_SOURCE,),
        evidence_status="official",
        confidence="high",
    ),
    "FAM-005": RuleDefinition(
        identifier="FAM-005",
        trigger=(
            "CPCB AQI is satisfactory; a child, older adult or health flag is "
            "present and the activity is long or vigorous."
        ),
        recommended_action="reduce_exposure",
        explanation=(
            "Public guidance for sensitive groups is to reduce prolonged or "
            "heavy outdoor exertion when air quality is not in the lowest band."
        ),
        data_requirements=("CPCB AQI", "activity duration/intensity", "sensitivity"),
        evidence=(_CPCB_SOURCE, _EPA_SOURCE),
        evidence_status="public_guidance",
        confidence="medium",
    ),
    "FAM-006": RuleDefinition(
        identifier="FAM-006",
        trigger="CPCB AQI is moderate and the household has no sensitivity flag.",
        recommended_action="reduce_exposure",
        explanation=(
            "Moderate conditions warrant shorter or lighter outdoor activity "
            "when it is vigorous or prolonged."
        ),
        data_requirements=("CPCB AQI", "activity duration/intensity"),
        evidence=(_CPCB_SOURCE, _EPA_SOURCE),
        evidence_status="public_guidance",
        confidence="medium",
    ),
    "FAM-007": RuleDefinition(
        identifier="FAM-007",
        trigger="CPCB AQI is moderate and a household sensitivity flag is present.",
        recommended_action="reduce_exposure",
        explanation=(
            "Sensitive groups are advised to reduce prolonged or heavy outdoor "
            "exertion in this category."
        ),
        data_requirements=("CPCB AQI", "household sensitivity"),
        evidence=(_CPCB_SOURCE, _EPA_SOURCE),
        evidence_status="public_guidance",
        confidence="medium",
    ),
    "FAM-008": RuleDefinition(
        identifier="FAM-008",
        trigger="CPCB AQI is poor and the household has no sensitivity flag.",
        recommended_action="reduce_exposure",
        explanation=(
            "Poor conditions warrant avoiding prolonged outdoor exertion and "
            "shortening outdoor tasks."
        ),
        data_requirements=("CPCB AQI",),
        evidence=(_CPCB_SOURCE, _EPA_SOURCE),
        evidence_status="public_guidance",
        confidence="medium",
    ),
    "FAM-009": RuleDefinition(
        identifier="FAM-009",
        trigger="CPCB AQI is poor and a household sensitivity flag is present.",
        recommended_action="move_indoor",
        explanation=(
            "Sensitive groups are advised to avoid outdoor exertion and use an "
            "indoor alternative where one exists."
        ),
        data_requirements=("CPCB AQI", "household sensitivity", "indoor alternative"),
        evidence=(_CPCB_SOURCE, _EPA_SOURCE),
        evidence_status="public_guidance",
        confidence="medium",
    ),
    "FAM-010": RuleDefinition(
        identifier="FAM-010",
        trigger="CPCB AQI is very poor.",
        recommended_action="avoid_outdoor",
        explanation=(
            "Very poor conditions warrant avoiding outdoor activity; use an "
            "indoor alternative and follow local health advisories."
        ),
        data_requirements=("CPCB AQI", "indoor alternative"),
        evidence=(_CPCB_SOURCE, _EPA_SOURCE),
        evidence_status="public_guidance",
        confidence="medium",
    ),
    "FAM-011": RuleDefinition(
        identifier="FAM-011",
        trigger="CPCB AQI is severe.",
        recommended_action="avoid_outdoor",
        explanation=(
            "Severe conditions warrant staying indoors and following local "
            "health advisories. This is not a medical assessment."
        ),
        data_requirements=("CPCB AQI",),
        evidence=(_CPCB_SOURCE, _EPA_SOURCE),
        evidence_status="public_guidance",
        confidence="medium",
    ),
    "FAM-012": RuleDefinition(
        identifier="FAM-012",
        trigger=(
            "A school or office commute uses walking or cycling while air "
            "quality is moderate or worse."
        ),
        recommended_action="reduce_exposure",
        explanation=(
            "Active travel increases breathing rate on busy routes; a "
            "lower-exposure mode or time is preferable."
        ),
        data_requirements=("activity type", "transport mode", "CPCB AQI"),
        evidence=(_EPA_SOURCE,),
        evidence_status="public_guidance",
        confidence="medium",
    ),
    "FAM-013": RuleDefinition(
        identifier="FAM-013",
        trigger=(
            "The forecast contains a window at least 20% lower in PM2.5 within "
            "the activity's stated flexibility."
        ),
        recommended_action="reduce_exposure",
        explanation=(
            "A model forecast suggests a lower-exposure time. Forecast values "
            "are not station measurements and can change."
        ),
        data_requirements=("hourly forecast PM2.5", "activity flexibility"),
        evidence=(_CPCB_SOURCE,),
        evidence_status="public_guidance",
        confidence="low",
    ),
}

ACTION_LABELS: dict[Action, str] = {
    "proceed": "Proceed as planned",
    "reduce_exposure": "Reduce exposure",
    "reschedule": "Reschedule to a lower-pollution time",
    "move_indoor": "Move this activity indoors",
    "avoid_outdoor": "Avoid outdoor activity",
    "check_back": "Check again before going outside",
}

_DEFAULT_INDOOR: dict[str, str] = {
    "morning_exercise": "Indoor stretching or a home workout",
    "evening_exercise": "Indoor stretching or a home workout",
    "walking": "Walk indoors or use a treadmill",
    "cycling": "Indoor cycling or a shorter low-traffic ride later",
    "outdoor_play": "Indoor play in a room away from open windows",
    "shopping": "Delay non-essential shopping or use a nearby indoor market",
    "school_commute": "Use public transport or a vehicle with recirculated air",
    "office_commute": "Use public transport or a vehicle with recirculated air",
    "public_transport": "Keep the trip essential and wait in a sheltered area",
    "indoor_activity": "Continue the indoor activity",
}

_WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


@dataclass(frozen=True)
class PollutionSignal:
    aqi: int | None
    category: str | None
    pm2_5: float | None
    pm10: float | None
    provider: str | None
    source_type: str | None
    observed_at: datetime | None
    fetched_at: datetime | None
    age_minutes: int | None
    stale: bool
    aqi_partial: bool
    unavailable_reason: str | None
    forecast_only: bool
    attribution: tuple[str, ...]
    guidance_basis: GuidanceBasis


@dataclass(frozen=True)
class ForecastHour:
    time: datetime
    pm2_5: float | None


@dataclass(frozen=True)
class ActivityWindow:
    id: str
    title: str
    activity: str
    start: str
    duration_min: int
    intensity: str
    venue: str
    days: tuple[str, ...]
    flexibility_min: int
    indoor_alternative: str | None
    transport_mode: str | None


@dataclass(frozen=True)
class Sensitivity:
    has_children: bool
    has_older_adults: bool
    has_health_flags: bool

    @property
    def cautious(self) -> bool:
        return self.has_children or self.has_older_adults or self.has_health_flags


@dataclass(frozen=True)
class Assessment:
    activity: str
    activity_title: str
    action: Action
    severity: Severity
    rule_id: str
    reason: str
    alternative_activity: str | None
    suggested_time: str | None
    suggested_at: datetime | None
    uncertainty: tuple[str, ...]
    confidence: Confidence
    evidence: tuple[Evidence, ...]


def pm25_band(value: float) -> Severity:
    """Map PM2.5 to the CPCB PM2.5 sub-index band.

    These are sub-index breakpoints, not an overall CPCB AQI; callers must label
    the result accordingly.
    """
    if value <= 30:
        return "good"
    if value <= 60:
        return "satisfactory"
    if value <= 90:
        return "moderate"
    if value <= 120:
        return "poor"
    if value <= 250:
        return "very_poor"
    return "severe"


def _severity(signal: PollutionSignal) -> Severity:
    if signal.aqi is not None and signal.category is not None:
        return cast(Severity, signal.category)
    if signal.pm2_5 is not None:
        return pm25_band(signal.pm2_5)
    return "info"


def _confidence(signal: PollutionSignal) -> Confidence:
    if signal.stale or signal.guidance_basis == "none":
        return "low"
    if (
        signal.guidance_basis == "cpcb_aqi"
        and signal.source_type == "ground_observation"
    ):
        return "high"
    return "medium"


def _source_label(signal: PollutionSignal) -> str:
    if signal.source_type == "ground_observation":
        return "ground-station observation"
    if signal.source_type == "historical_observation":
        return "historical observation"
    if signal.source_type == "model_forecast":
        return "model-based forecast"
    return "provider data"


def _pollution_sentence(signal: PollutionSignal) -> str:
    if signal.aqi is not None and signal.category is not None:
        category = signal.category.replace("_", " ")
        sentence = (
            f"CPCB AQI is {signal.aqi} ({category}) from "
            f"{signal.provider or 'the provider'} {_source_label(signal)}."
        )
    elif signal.pm2_5 is not None:
        band = pm25_band(signal.pm2_5).replace("_", " ")
        sentence = (
            f"PM2.5 is {signal.pm2_5:.1f} µg/m³ ({band} PM2.5 sub-index band). "
            "An overall CPCB AQI is not available."
        )
    else:
        return "No validated pollution reading is available for this location."
    if signal.stale:
        sentence += " This reading is stale and is not treated as current."
    return sentence


def _uncertainty(signal: PollutionSignal, *, scheduled_today: bool) -> tuple[str, ...]:
    notes: list[str] = []
    if signal.guidance_basis == "none":
        notes.append("No current or forecast pollution value was available.")
    if signal.stale:
        notes.append(
            "The latest reading is stale and cannot describe current conditions."
        )
    if signal.forecast_only:
        notes.append("Only forecast data was available; no current reading was used.")
    if signal.source_type == "model_forecast" and not signal.forecast_only:
        notes.append(
            "The current value is model-based, not a monitoring-station measurement."
        )
    if signal.guidance_basis == "pm25_band":
        notes.append(
            "An overall CPCB AQI is unavailable; guidance uses PM2.5 concentration "
            "bands only."
        )
    if signal.aqi_partial:
        notes.append("The CPCB AQI is based on a partial set of pollutants.")
    if signal.unavailable_reason:
        notes.append(signal.unavailable_reason)
    if not scheduled_today:
        notes.append("This activity is not scheduled for today; no time was suggested.")
    return tuple(notes)


def _choose_rule(
    severity: Severity,
    *,
    sensitive: bool,
    window: ActivityWindow,
    transport_mode: str | None,
) -> tuple[Action, str]:
    vigorous_or_long = window.intensity == "vigorous" or window.duration_min >= 90
    active_commute = window.activity in {
        "school_commute",
        "office_commute",
    } and transport_mode in {"walk", "cycle"}
    if severity == "good":
        return "proceed", "FAM-003"
    if severity == "satisfactory":
        if sensitive and vigorous_or_long:
            return "reduce_exposure", "FAM-005"
        return "proceed", "FAM-004"
    if severity == "moderate":
        if active_commute:
            return "reduce_exposure", "FAM-012"
        if sensitive:
            return "reduce_exposure", "FAM-007"
        if vigorous_or_long:
            return "reduce_exposure", "FAM-006"
        return "proceed", "FAM-006"
    if severity == "poor":
        if active_commute:
            return "reduce_exposure", "FAM-012"
        if sensitive:
            return "move_indoor", "FAM-009"
        return "reduce_exposure", "FAM-008"
    if severity == "very_poor":
        if active_commute:
            return "reduce_exposure", "FAM-012"
        return "avoid_outdoor", "FAM-010"
    if severity == "severe":
        if active_commute:
            return "reduce_exposure", "FAM-012"
        return "avoid_outdoor", "FAM-011"
    return "check_back", "FAM-001"


def _action_reason(action: Action, rule_id: str) -> str:
    if action == "proceed":
        return (
            "Outdoor conditions do not call for a change to this activity for "
            "the household as configured."
        )
    if action == "reduce_exposure":
        if rule_id == "FAM-012":
            return (
                "Walking or cycling during the commute increases outdoor "
                "breathing time; use a lower-exposure mode or a later window."
            )
        return (
            "Shorten the activity, lower its intensity, or move it to a lower-"
            "pollution time."
        )
    if action == "move_indoor":
        return (
            "Use the indoor alternative or postpone the activity until the "
            "outdoor reading improves."
        )
    if action == "avoid_outdoor":
        return (
            "Avoid outdoor activity for now and follow local health advisories. "
            "Indoor air may still need ventilation or filtration."
        )
    if action == "reschedule":
        return "Move the activity to the suggested lower-pollution time."
    if action == "check_back":
        return (
            "Check the air-quality reading again shortly before the activity; "
            "no safety claim is possible without current data."
        )
    return "Review the current guidance."


def _alternative(
    window: ActivityWindow, action: Action, *, transport_mode: str | None
) -> str | None:
    if action == "proceed":
        return None
    if window.indoor_alternative:
        return window.indoor_alternative
    if window.activity in {"school_commute", "office_commute"}:
        if transport_mode in {"walk", "cycle"}:
            return (
                "Use public transport or a vehicle with recirculated air, or "
                "shift the trip to a lower-pollution time."
            )
        return "Keep the trip essential and wait indoors where possible."
    return _DEFAULT_INDOOR.get(
        window.activity, "Choose an indoor alternative or postpone the activity"
    )


def _parse_clock(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _next_window(
    *,
    window: ActivityWindow,
    tz: ZoneInfo,
    forecast: list[ForecastHour],
    current_pm2_5: float | None,
    now: datetime,
) -> tuple[datetime | None, float | None]:
    """Find the lowest-mean forecast window within the stated flexibility."""
    if current_pm2_5 is None or not forecast:
        return None, None
    if window.flexibility_min <= 0:
        return None, None

    local_now = now.astimezone(tz)
    preferred = _parse_clock(window.start)
    best_start: datetime | None = None
    best_mean: float | None = None

    for day_offset in (0, 1):
        base_date: date = local_now.date() + timedelta(days=day_offset)
        preferred_dt = datetime.combine(base_date, preferred, tzinfo=tz)
        earliest = preferred_dt - timedelta(minutes=window.flexibility_min)
        latest = preferred_dt + timedelta(minutes=window.flexibility_min)
        if day_offset == 0:
            earliest = max(
                earliest, local_now + timedelta(minutes=MIN_SUGGESTION_LEAD_MIN)
            )
        candidate = earliest.replace(minute=0, second=0, microsecond=0)
        if candidate < earliest:
            candidate += timedelta(hours=1)
        while candidate <= latest:
            end = candidate + timedelta(minutes=window.duration_min)
            values = [
                point.pm2_5
                for point in forecast
                if point.pm2_5 is not None and candidate <= point.time < end
            ]
            mean = _mean([float(value) for value in values])
            if mean is not None and (best_mean is None or mean < best_mean):
                best_start = candidate
                best_mean = mean
            candidate += timedelta(hours=1)

    if best_start is None or best_mean is None:
        return None, None
    if best_mean > current_pm2_5 * FORECAST_IMPROVEMENT_RATIO:
        return None, None
    return best_start, round(best_mean, 1)


def assess_activities(
    *,
    signal: PollutionSignal,
    windows: list[ActivityWindow],
    sensitivity: Sensitivity,
    forecast: list[ForecastHour],
    timezone: str,
    now: datetime,
) -> list[Assessment]:
    tz = ZoneInfo(timezone)
    severity = _severity(signal)
    base_confidence = _confidence(signal)
    local_today = now.astimezone(tz).date()
    today_code = _WEEKDAYS[local_today.weekday()]
    assessments: list[Assessment] = []

    for window in windows:
        scheduled_today = today_code in window.days if window.days else True
        uncertainty = list(_uncertainty(signal, scheduled_today=scheduled_today))

        if window.venue == "indoor" or window.activity == "indoor_activity":
            definition = RULES["FAM-000"]
            assessments.append(
                Assessment(
                    activity=window.activity,
                    activity_title=window.title,
                    action="proceed",
                    severity=severity,
                    rule_id=definition.identifier,
                    reason=definition.explanation,
                    alternative_activity=None,
                    suggested_time=None,
                    suggested_at=None,
                    uncertainty=tuple(uncertainty),
                    confidence="medium",
                    evidence=(),
                )
            )
            continue

        if signal.guidance_basis == "none":
            definition = RULES["FAM-001"]
            action: Action = "check_back"
            rule_id = definition.identifier
        elif signal.stale:
            definition = RULES["FAM-002"]
            action = "check_back"
            rule_id = definition.identifier
        else:
            transport_mode = window.transport_mode
            action, rule_id = _choose_rule(
                severity,
                sensitive=sensitivity.cautious,
                window=window,
                transport_mode=transport_mode,
            )
            definition = RULES[rule_id]

        alternative = _alternative(window, action, transport_mode=window.transport_mode)
        suggested_at: datetime | None = None
        if (
            action in {"reduce_exposure", "reschedule", "avoid_outdoor"}
            and scheduled_today
        ):
            suggested_at, _mean_pm = _next_window(
                window=window,
                tz=tz,
                forecast=forecast,
                current_pm2_5=signal.pm2_5,
                now=now,
            )
            if suggested_at is not None:
                uncertainty.append(
                    "The suggested time uses forecast data, not a station measurement."
                )

        reason_parts = [_pollution_sentence(signal)]
        if sensitivity.cautious and definition.evidence_status == "public_guidance":
            reason_parts.append(
                "A household member is in a group that public health guidance "
                "treats as more sensitive."
            )
        reason_parts.append(_action_reason(action, rule_id))
        reason_parts.append("General guidance, not medical advice.")

        evidence = definition.evidence
        if signal.guidance_basis == "pm25_band" and _WHO_SOURCE not in evidence:
            evidence = (*evidence, _WHO_SOURCE)

        confidence = base_confidence
        if rule_id == "FAM-013" or definition.evidence_status == "none":
            confidence = "low"

        assessments.append(
            Assessment(
                activity=window.activity,
                activity_title=window.title,
                action=action,
                severity=severity,
                rule_id=rule_id,
                reason=" ".join(reason_parts),
                alternative_activity=alternative,
                suggested_time=(
                    suggested_at.astimezone(tz).strftime("%H:%M")
                    if suggested_at is not None
                    else None
                ),
                suggested_at=suggested_at,
                uncertainty=tuple(uncertainty),
                confidence=confidence,
                evidence=evidence,
            )
        )
    return assessments
