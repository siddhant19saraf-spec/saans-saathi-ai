"""Deterministic, explainable daily schedule optimisation.

The engine is a pure function over validated inputs:

* household activities (fixed or flexible, earliest/latest start, priority),
* household members (age band and sensitivity),
* hourly forecast concentrations in UTC,
* optional current observation metadata (context only, never scheduling).

It enumerates candidate starts inside each allowed window, estimates inhaled
dose with the shared exposure model, and chooses the lowest planning score that
does not overlap a fixed or already scheduled activity. Identical inputs always
produce an identical plan; ``ENGINE_VERSION`` is stored with every plan.

Nothing here certifies that a slot is safe. The dose figure is a planning
estimate from an exposure model, not a measurement or a clinical prediction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain.aqi import evaluate_cpcb_aqi, rolling_averages, sub_index
from app.domain.exposure import AgeBand, Intensity, Pathway, exposure_dose_ug

ENGINE_VERSION = "routine-2.0.0"
SCORING_VERSION = "routine-score-1.0.0"

PLAN_START = time(5, 0)
PLAN_END = time(22, 0)
SLOT_STEP_MIN = 15
DEFAULT_FLEX_MIN = 120
VIGOROUS_BUFFER_MIN = 30

SENSITIVE_AQI_THRESHOLD = 150
GENERAL_AQI_THRESHOLD = 250

SCORE_DOSE_WEIGHT = 1.0
SCORE_AQI_EXCESS_WEIGHT = 0.2
SCORE_PREFERENCE_WEIGHT = 0.5
SCORE_PRIORITY_ADJUSTMENT = {"high": 2.0, "medium": 0.0, "low": -2.0}
MAX_SLOT_ALTERNATIVES = 2

_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}

DOSE_ASSUMPTION = (
    "Estimated dose uses the SAANS SAATHI exposure model (concentration x "
    "inhalation rate x infiltration x duration). It is a planning estimate, "
    "not a measurement and not a clinical prediction."
)
SAFETY_STATEMENT = (
    "The planner does not certify that any time slot is safe; it compares "
    "forecast conditions and explains the choice."
)


class ForecastCoverageError(Exception):
    """No forecast hours overlap the requested plan date."""


@dataclass(frozen=True)
class ForecastHour:
    """One hourly forecast value. ``time`` may be naive (treated as UTC)."""

    time: datetime
    pm2_5: float | None
    pm10: float | None = None
    no2_ug_m3: float | None = None
    o3_ug_m3: float | None = None


@dataclass(frozen=True)
class PlannerActivity:
    id: str
    title: str
    category: str
    duration_min: int
    preferred_start: str
    venue: str
    earliest_start: str | None = None
    latest_start: str | None = None
    fixed: bool = False
    priority: str = "medium"
    intensity: Intensity = "light"
    indoor_alternative: str | None = None
    member_ids: tuple[str, ...] = ()
    notes: str | None = None


@dataclass(frozen=True)
class MemberProfile:
    age_band: AgeBand
    sensitive: bool = False
    id: str | None = None


@dataclass(frozen=True)
class Block:
    activity_id: str
    title: str
    category: str
    start: str
    end: str
    start_at: str
    end_at: str
    duration_min: int
    venue: str
    priority: str
    intensity: str
    fixed: bool
    status: str
    override: bool
    basis: str
    dose_ug: float
    score: float
    index: int
    pm2_5: float | None
    aqi: int | None
    aqi_basis: str
    threshold: int
    data_available: bool
    rationale: list[dict[str, Any]]
    fact_refs: list[str]
    indoor_alternative: str | None
    member_ids: list[str]

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": f"item-{self.activity_id}",
            "activity_id": self.activity_id,
            "title": self.title,
            "category": self.category,
            "start": self.start,
            "end": self.end,
            "start_at": self.start_at,
            "end_at": self.end_at,
            "duration_min": self.duration_min,
            "venue": self.venue,
            "priority": self.priority,
            "intensity": self.intensity,
            "fixed": self.fixed,
            "status": self.status,
            "override": self.override,
            "basis": self.basis,
            "exposure": {"dose_ug": self.dose_ug, "index": self.index},
            "score": self.score,
            "pm2_5": self.pm2_5,
            "aqi": self.aqi,
            "aqi_basis": self.aqi_basis,
            "threshold": self.threshold,
            "data_available": self.data_available,
            "rationale": self.rationale,
            "fact_refs": self.fact_refs,
            "indoor_alternative": self.indoor_alternative,
            "member_ids": self.member_ids,
        }


@dataclass(frozen=True)
class Alternative:
    activity_id: str
    kind: str
    start: str
    end: str
    start_at: str
    end_at: str
    venue: str
    dose_ug: float
    score: float
    pm2_5: float | None
    aqi: int | None
    aqi_basis: str
    rationale: list[dict[str, Any]]

    @property
    def block_id(self) -> str:
        return f"item-{self.activity_id}"

    def to_payload(self) -> dict[str, Any]:
        return {
            "block_id": self.block_id,
            "activity_id": self.activity_id,
            "kind": self.kind,
            "start": self.start,
            "end": self.end,
            "start_at": self.start_at,
            "end_at": self.end_at,
            "venue": self.venue,
            "dose_ug": self.dose_ug,
            "score": self.score,
            "pm2_5": self.pm2_5,
            "aqi": self.aqi,
            "aqi_basis": self.aqi_basis,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class UnscheduledActivity:
    activity_id: str
    title: str
    category: str
    priority: str
    reason_code: str
    reason: str
    rationale: list[dict[str, Any]]

    def to_payload(self) -> dict[str, Any]:
        return {
            "activity_id": self.activity_id,
            "title": self.title,
            "category": self.category,
            "priority": self.priority,
            "reason_code": self.reason_code,
            "reason": self.reason,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class DataStatus:
    provider: str
    source_type: str
    issued_at: str | None
    stale: bool
    coverage_hours: int
    expected_hours: int
    coverage_ratio: float
    pm2_5_hours: int
    age_minutes: int | None
    observation: dict[str, Any] | None
    confidence: str
    notes: list[str]

    def to_payload(self) -> dict[str, Any]:
        return {
            "forecast": {
                "available": self.coverage_hours > 0,
                "provider": self.provider,
                "source_type": self.source_type,
                "issued_at": self.issued_at,
                "stale": self.stale,
                "coverage_hours": self.coverage_hours,
                "expected_hours": self.expected_hours,
                "coverage_ratio": self.coverage_ratio,
                "pm2_5_hours": self.pm2_5_hours,
                "age_minutes": self.age_minutes,
                "basis": "forecast",
            },
            "observation": self.observation,
            "confidence": self.confidence,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class RoutinePlan:
    plan_date: date
    timezone: str
    blocks: list[Block]
    unscheduled: list[UnscheduledActivity]
    alternatives: list[Alternative]
    data_status: DataStatus
    uncertainty: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return {
            "date": self.plan_date.isoformat(),
            "timezone": self.timezone,
            "engine_version": ENGINE_VERSION,
            "confidence": self.data_status.confidence,
            "blocks": [block.to_payload() for block in self.blocks],
            "unscheduled": [item.to_payload() for item in self.unscheduled],
            "alternatives": [
                alternative.to_payload() for alternative in self.alternatives
            ],
            "data_status": self.data_status.to_payload(),
            "scoring": scoring_payload(),
            "uncertainty": self.uncertainty,
        }


def scoring_payload() -> dict[str, Any]:
    return {
        "version": SCORING_VERSION,
        "formula": (
            "score = 1.0 x estimated_dose_ug"
            " + 0.2 x max(0, CPCB_AQI - threshold)"
            " + 0.5 x hours_from_preferred_start"
            " - priority_adjustment (high 2.0, medium 0, low -2.0)"
        ),
        "lower_is_better": True,
        "weights": {
            "estimated_dose_ug": SCORE_DOSE_WEIGHT,
            "aqi_excess_per_point": SCORE_AQI_EXCESS_WEIGHT,
            "hours_from_preferred": SCORE_PREFERENCE_WEIGHT,
            "priority_adjustment": SCORE_PRIORITY_ADJUSTMENT,
        },
        "thresholds": {
            "sensitive_aqi": SENSITIVE_AQI_THRESHOLD,
            "general_aqi": GENERAL_AQI_THRESHOLD,
            "source": (
                "CPCB National Air Quality Index (2014) categories; the "
                "sensitive threshold follows the existing household rule set."
            ),
            "partial_data": (
                "When fewer than three pollutants have complete CPCB averaging "
                "windows, the CPCB PM2.5 sub-index is used and labelled as such "
                "instead of an overall AQI."
            ),
        },
        "assumptions": [
            DOSE_ASSUMPTION,
            "Forecast concentrations are modelled values converted to the "
            "household timezone; they are not measurements at the home.",
            "The dose weight is in estimated micrograms; other terms are "
            "planner points that break ties, not physical quantities.",
            "Priority can shift the choice by at most a few dose micrograms; "
            "it never overrides an overlap constraint.",
        ],
    }


@dataclass(frozen=True)
class _Candidate:
    start: datetime
    end: datetime
    dose: float
    score: float
    pm2_5: float | None
    aqi: int | None
    aqi_basis: str


def _parse_clock(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def _format_clock(value: datetime) -> str:
    return value.strftime("%H:%M")


def local_datetime(plan_date: date, clock: time, tz: ZoneInfo) -> datetime | None:
    """Return an aware local time, or ``None`` for a DST spring-forward gap.

    Ambiguous fall-back times resolve to the first occurrence (fold 0). Both
    cases are deterministic and reported in the plan uncertainty notes.
    """
    naive = datetime.combine(plan_date, clock)
    aware = naive.replace(tzinfo=tz, fold=0)
    roundtrip = aware.astimezone(UTC).astimezone(tz)
    if roundtrip.replace(tzinfo=None) != naive:
        return None
    return aware


def _local_hours(hours: list[ForecastHour], tz: ZoneInfo) -> list[ForecastHour]:
    converted: list[ForecastHour] = []
    for hour in hours:
        source = (
            hour.time if hour.time.tzinfo is not None else hour.time.replace(tzinfo=UTC)
        )
        converted.append(
            ForecastHour(
                time=source.astimezone(tz),
                pm2_5=hour.pm2_5,
                pm10=hour.pm10,
                no2_ug_m3=hour.no2_ug_m3,
                o3_ug_m3=hour.o3_ug_m3,
            )
        )
    return sorted(converted, key=lambda item: item.time)


def _window_values(
    hours: list[ForecastHour], start: datetime, end: datetime
) -> dict[str, list[float]]:
    collected: dict[str, list[float]] = {
        "pm2_5": [],
        "pm10": [],
        "no2_ug_m3": [],
        "o3_ug_m3": [],
    }
    for hour in hours:
        hour_end = hour.time + timedelta(hours=1)
        if hour.time < end and hour_end > start:
            for key in collected:
                value = getattr(hour, key)
                if value is not None:
                    collected[key].append(float(value))
    return collected


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _trailing_series(
    hours: list[ForecastHour], start: datetime
) -> dict[str, list[float | None]]:
    series: dict[str, list[float | None]] = {
        "pm2_5": [],
        "pm10": [],
        "no2_ug_m3": [],
        "o3_ug_m3": [],
    }
    for hour in hours:
        if hour.time >= start:
            continue
        for key in series:
            series[key].append(getattr(hour, key))
    return series


def _pollution_signal(
    hours: list[ForecastHour], start: datetime
) -> tuple[int | None, str]:
    averages = rolling_averages(_trailing_series(hours, start))
    assessment = evaluate_cpcb_aqi(
        {pollutant: value for pollutant, (value, _info) in averages.items()},
        averaging=[info for _value, info in averages.values()],
    )
    if assessment.aqi is not None:
        return assessment.aqi.value, "cpcb_aqi"
    pm2_5_value, pm2_5_info = averages["pm2_5"]
    if pm2_5_value is not None and pm2_5_info.complete:
        # CPCB requires at least three complete pollutants for an overall AQI.
        # With only PM2.5 available, its published sub-index is a transparent
        # fallback, not an overall AQI.
        return round(sub_index("pm2_5", pm2_5_value)), "pm25_subindex"
    return None, "none"


def _score(
    *,
    dose: float,
    aqi: int | None,
    threshold: int,
    offset: timedelta,
    priority: str,
) -> float:
    excess = max(0, aqi - threshold) if aqi is not None else 0
    preference = abs(offset.total_seconds()) / 3600 * SCORE_PREFERENCE_WEIGHT
    return round(
        dose * SCORE_DOSE_WEIGHT
        + excess * SCORE_AQI_EXCESS_WEIGHT
        + preference
        - SCORE_PRIORITY_ADJUSTMENT.get(priority, 0.0),
        3,
    )


def _evaluate(
    *,
    start: datetime,
    preferred: datetime,
    duration_min: int,
    intensity: Intensity,
    venue: str,
    priority: str,
    members: list[MemberProfile],
    threshold: int,
    hours: list[ForecastHour],
) -> _Candidate:
    end = start + timedelta(minutes=duration_min)
    values = _window_values(hours, start, end)
    pm2_5 = _mean(values["pm2_5"])
    pathway: Pathway = "outdoor" if venue == "outdoor" else "indoor"
    dose = 0.0
    if pm2_5 is not None:
        for member in members:
            dose += exposure_dose_ug(
                concentration_ug_m3=pm2_5,
                duration_min=duration_min,
                intensity=intensity,
                age_band=member.age_band,
                pathway=pathway,
            )
    aqi, aqi_basis = _pollution_signal(hours, start)
    return _Candidate(
        start=start,
        end=end,
        dose=dose,
        score=_score(
            dose=dose,
            aqi=aqi,
            threshold=threshold,
            offset=start - preferred,
            priority=priority,
        ),
        pm2_5=pm2_5,
        aqi=aqi,
        aqi_basis=aqi_basis,
    )


def _candidate_starts(
    *,
    plan_date: date,
    activity: PlannerActivity,
    tz: ZoneInfo,
) -> tuple[list[datetime], str | None]:
    preferred_clock = _parse_clock(activity.preferred_start)
    preferred = local_datetime(plan_date, preferred_clock, tz)
    if preferred is None:
        return [], "DST_GAP"

    earliest_clock = (
        _parse_clock(activity.earliest_start)
        if activity.earliest_start is not None
        else None
    )
    latest_clock = (
        _parse_clock(activity.latest_start)
        if activity.latest_start is not None
        else None
    )
    if activity.fixed:
        earliest_clock = preferred_clock
        latest_clock = preferred_clock

    earliest_clock = earliest_clock or max(
        PLAN_START,
        (
            datetime.combine(plan_date, preferred_clock)
            - timedelta(minutes=DEFAULT_FLEX_MIN)
        ).time(),
    )
    latest_clock = latest_clock or min(
        PLAN_END,
        (
            datetime.combine(plan_date, preferred_clock)
            + timedelta(minutes=DEFAULT_FLEX_MIN)
        ).time(),
    )
    if earliest_clock < PLAN_START:
        earliest_clock = PLAN_START
    if latest_clock > PLAN_END:
        latest_clock = PLAN_END
    if (
        earliest_clock > latest_clock
        or preferred_clock < earliest_clock
        or (preferred_clock > latest_clock)
    ):
        return [], "IMPOSSIBLE_WINDOW"

    duration = timedelta(minutes=activity.duration_min)
    horizon_end = datetime.combine(plan_date, PLAN_END).replace(tzinfo=tz)
    if preferred + duration > horizon_end:
        return [], "IMPOSSIBLE_WINDOW"

    earliest = local_datetime(plan_date, earliest_clock, tz)
    latest = local_datetime(plan_date, latest_clock, tz)
    if earliest is None or latest is None:
        return [], "DST_GAP"
    if latest + duration > horizon_end:
        latest = horizon_end - duration

    starts: set[datetime] = set()
    step = timedelta(minutes=SLOT_STEP_MIN)
    slot = earliest
    while slot <= latest:
        starts.add(slot)
        slot += step
    if earliest <= preferred <= latest:
        starts.add(preferred)
    return sorted(starts), None


def _blocked(
    start: datetime, end: datetime, scheduled: list[tuple[datetime, datetime, bool]]
) -> bool:
    for other_start, other_end, vigorous in scheduled:
        buffer = timedelta(minutes=VIGOROUS_BUFFER_MIN if vigorous else 0)
        if start < other_end + buffer and end > other_start:
            return True
    return False


def _split_activity(
    activity: PlannerActivity, members: list[MemberProfile]
) -> tuple[list[MemberProfile], str | None]:
    if not activity.member_ids:
        return members, None
    known = {member.id: member for member in members if member.id is not None}
    selected = [
        known[member_id] for member_id in activity.member_ids if member_id in known
    ]
    if not selected:
        return members, "UNKNOWN_MEMBERS"
    return selected, None


def _unscheduled(
    activity: PlannerActivity,
    *,
    reason_code: str,
    reason: str,
    params: dict[str, Any] | None = None,
) -> UnscheduledActivity:
    return UnscheduledActivity(
        activity_id=activity.id,
        title=activity.title,
        category=activity.category,
        priority=activity.priority,
        reason_code=reason_code,
        reason=reason,
        rationale=[
            {
                "template_id": "routine.unscheduled",
                "params": {"reason_code": reason_code, **(params or {})},
            }
        ],
    )


def _data_status(
    *,
    plan_date: date,
    tz: ZoneInfo,
    hours: list[ForecastHour],
    provider: str,
    source_type: str,
    issued_at: datetime | None,
    stale: bool,
    observation: dict[str, Any] | None,
    now: datetime,
) -> DataStatus:
    day_start = local_datetime(plan_date, PLAN_START, tz)
    day_end = local_datetime(plan_date, PLAN_END, tz)
    expected = 0
    if day_start is not None and day_end is not None:
        expected = max(0, int((day_end - day_start).total_seconds() // 3600))

    in_day = [
        hour
        for hour in hours
        if day_start is not None
        and day_end is not None
        and day_start <= hour.time < day_end
    ]
    coverage = sum(1 for hour in in_day if hour.pm2_5 is not None)
    ratio = round(coverage / expected, 3) if expected else 0.0

    age_minutes: int | None = None
    if issued_at is not None:
        issued = (
            issued_at if issued_at.tzinfo is not None else issued_at.replace(tzinfo=UTC)
        )
        age_minutes = max(0, int((now - issued).total_seconds() // 60))

    notes: list[str] = []
    if ratio < 1:
        notes.append(
            f"PM2.5 forecast covers {coverage} of {expected} hourly slots in "
            f"the {PLAN_START.strftime('%H:%M')}-{PLAN_END.strftime('%H:%M')} "
            f"planning horizon."
        )
    if stale:
        notes.append("The provider marked the forecast as stale.")
    if age_minutes is not None and age_minutes > 360:
        notes.append(
            f"The forecast was issued {age_minutes // 60} hours before this plan."
        )
    if ratio >= 0.9 and not stale and (age_minutes is None or age_minutes <= 360):
        confidence = "high"
    elif ratio >= 0.5 and not stale:
        confidence = "medium"
    else:
        confidence = "low"

    return DataStatus(
        provider=provider,
        source_type=source_type,
        issued_at=issued_at.isoformat() if issued_at is not None else None,
        stale=stale,
        coverage_hours=coverage,
        expected_hours=expected,
        coverage_ratio=ratio,
        pm2_5_hours=coverage,
        age_minutes=age_minutes,
        observation=observation,
        confidence=confidence,
        notes=notes,
    )


def generate_plan(
    *,
    plan_date: date,
    timezone: str,
    activities: list[PlannerActivity],
    members: list[MemberProfile],
    hours: list[ForecastHour],
    provider: str,
    source_type: str = "model_forecast",
    issued_at: datetime | None = None,
    stale: bool = False,
    observation: dict[str, Any] | None = None,
    sensitive_threshold: int = SENSITIVE_AQI_THRESHOLD,
    now: datetime | None = None,
) -> RoutinePlan:
    if not activities:
        raise ValueError("At least one activity is required.")
    if not members:
        raise ValueError("At least one household member is required.")
    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown timezone: {timezone}") from exc

    current = now or datetime.now(tz=UTC)
    local_hours = _local_hours(hours, tz)
    day_start = local_datetime(plan_date, PLAN_START, tz)
    day_end = local_datetime(plan_date, PLAN_END, tz)
    if (
        day_start is None
        or day_end is None
        or not any(day_start <= hour.time < day_end for hour in local_hours)
    ):
        raise ForecastCoverageError("No forecast data covers the requested date.")

    threshold = (
        sensitive_threshold
        if any(member.sensitive for member in members)
        else GENERAL_AQI_THRESHOLD
    )
    status = _data_status(
        plan_date=plan_date,
        tz=tz,
        hours=local_hours,
        provider=provider,
        source_type=source_type,
        issued_at=issued_at,
        stale=stale,
        observation=observation,
        now=current,
    )

    scheduled: list[tuple[datetime, datetime, bool]] = []
    blocks: list[Block] = []
    unscheduled: list[UnscheduledActivity] = []
    alternatives: list[Alternative] = []

    fixed = sorted(
        (activity for activity in activities if activity.fixed),
        key=lambda activity: (
            _PRIORITY_RANK.get(activity.priority, 1),
            activity.preferred_start,
            activity.id,
        ),
    )
    flexible = sorted(
        (activity for activity in activities if not activity.fixed),
        key=lambda activity: (
            _PRIORITY_RANK.get(activity.priority, 1),
            activity.preferred_start,
            activity.id,
        ),
    )

    for activity in [*fixed, *flexible]:
        selected_members, member_error = _split_activity(activity, members)
        if member_error is not None:
            unscheduled.append(
                _unscheduled(
                    activity,
                    reason_code=member_error,
                    reason=(
                        "The selected household members no longer exist. Edit "
                        "the activity and choose current members."
                    ),
                )
            )
            continue

        starts, window_error = _candidate_starts(
            plan_date=plan_date, activity=activity, tz=tz
        )
        if window_error is not None:
            reason = (
                "The preferred time falls in a daylight-saving clock change."
                if window_error == "DST_GAP"
                else "The allowed start window is empty or ends after 22:00."
            )
            unscheduled.append(
                _unscheduled(activity, reason_code=window_error, reason=reason)
            )
            continue

        preferred = local_datetime(
            plan_date, _parse_clock(activity.preferred_start), tz
        )
        if preferred is None:
            unscheduled.append(
                _unscheduled(
                    activity,
                    reason_code="DST_GAP",
                    reason=(
                        "The preferred time falls in a daylight-saving clock " "change."
                    ),
                )
            )
            continue

        candidates = [
            _evaluate(
                start=start,
                preferred=preferred,
                duration_min=activity.duration_min,
                intensity=activity.intensity,
                venue=activity.venue,
                priority=activity.priority,
                members=selected_members,
                threshold=threshold,
                hours=local_hours,
            )
            for start in starts
        ]
        with_data = [
            candidate for candidate in candidates if candidate.pm2_5 is not None
        ]
        feasible = [
            candidate
            for candidate in with_data
            if not _blocked(candidate.start, candidate.end, scheduled)
        ]

        if activity.fixed:
            chosen = candidates[0] if candidates else None
            if chosen is None:
                unscheduled.append(
                    _unscheduled(
                        activity,
                        reason_code="NO_SLOT",
                        reason="The fixed start is outside the planning horizon.",
                    )
                )
                continue
            if _blocked(chosen.start, chosen.end, scheduled):
                unscheduled.append(
                    _unscheduled(
                        activity,
                        reason_code="FIXED_OVERLAP",
                        reason=(
                            "This fixed activity overlaps another fixed activity "
                            "or its vigorous-activity buffer."
                        ),
                    )
                )
                continue
        else:
            if not with_data:
                unscheduled.append(
                    _unscheduled(
                        activity,
                        reason_code="NO_FORECAST_FOR_WINDOW",
                        reason=(
                            "No PM2.5 forecast covers this activity's allowed "
                            "window, so the planner cannot compare slots."
                        ),
                    )
                )
                continue
            if not feasible:
                unscheduled.append(
                    _unscheduled(
                        activity,
                        reason_code="NO_FEASIBLE_SLOT",
                        reason=(
                            "Every allowed slot overlaps a fixed activity, an "
                            "already scheduled activity, or its buffer."
                        ),
                    )
                )
                continue
            chosen = min(
                feasible,
                key=lambda candidate: (
                    candidate.score,
                    abs((candidate.start - preferred).total_seconds()),
                    candidate.start,
                ),
            )

        venue = activity.venue
        rationale: list[dict[str, Any]] = []
        data_available = chosen.pm2_5 is not None

        if chosen.aqi is not None and chosen.aqi > threshold and venue == "outdoor":
            if activity.indoor_alternative:
                venue = "indoor"
                rationale.append(
                    {
                        "template_id": "routine.indoor_swap",
                        "params": {
                            "aqi": chosen.aqi,
                            "threshold": threshold,
                            "alternative": activity.indoor_alternative,
                            "time": _format_clock(chosen.start),
                        },
                    }
                )
            else:
                rationale.append(
                    {
                        "template_id": "routine.elevated_aqi",
                        "params": {
                            "aqi": chosen.aqi,
                            "threshold": threshold,
                            "note": (
                                "No indoor alternative is saved for this "
                                "activity; treat the slot as a comparison, not "
                                "a safety clearance."
                            ),
                        },
                    }
                )

        if venue != activity.venue:
            chosen = _evaluate(
                start=chosen.start,
                preferred=preferred,
                duration_min=activity.duration_min,
                intensity=activity.intensity,
                venue=venue,
                priority=activity.priority,
                members=selected_members,
                threshold=threshold,
                hours=local_hours,
            )

        if activity.fixed:
            rationale.append(
                {
                    "template_id": "routine.fixed_slot",
                    "params": {"time": _format_clock(chosen.start)},
                }
            )
        elif data_available:
            rationale.append(
                {
                    "template_id": "routine.chosen_slot",
                    "params": {
                        "score": chosen.score,
                        "time": _format_clock(chosen.start),
                        "pm2_5": (
                            round(chosen.pm2_5, 1) if chosen.pm2_5 is not None else None
                        ),
                        "aqi": chosen.aqi,
                        "aqi_basis": chosen.aqi_basis,
                        "threshold": threshold,
                    },
                }
            )
        else:
            rationale.append(
                {
                    "template_id": "routine.forecast_gap_fixed",
                    "params": {"time": _format_clock(chosen.start)},
                }
            )

        block = Block(
            activity_id=activity.id,
            title=activity.title,
            category=activity.category,
            start=_format_clock(chosen.start),
            end=_format_clock(chosen.end),
            start_at=chosen.start.astimezone(UTC).isoformat(),
            end_at=chosen.end.astimezone(UTC).isoformat(),
            duration_min=activity.duration_min,
            venue=venue,
            priority=activity.priority,
            intensity=activity.intensity,
            fixed=activity.fixed,
            status="fixed" if activity.fixed else "recommended",
            override=False,
            basis="forecast",
            dose_ug=round(chosen.dose, 1),
            score=chosen.score,
            index=0,
            pm2_5=round(chosen.pm2_5, 1) if chosen.pm2_5 is not None else None,
            aqi=chosen.aqi,
            aqi_basis=chosen.aqi_basis,
            threshold=threshold,
            data_available=data_available,
            rationale=rationale,
            fact_refs=[
                "aq.forecast.hourly",
                f"aq.forecast.window_{_format_clock(chosen.start).replace(':', '')}",
                "exposure.planning_estimate",
            ],
            indoor_alternative=activity.indoor_alternative,
            member_ids=list(activity.member_ids),
        )
        blocks.append(block)
        scheduled.append(
            (
                chosen.start,
                chosen.end,
                activity.intensity == "vigorous" and venue == "outdoor",
            )
        )

        others = [
            candidate for candidate in feasible if candidate.start != chosen.start
        ]
        slot_alternatives = sorted(others, key=lambda item: (item.score, item.start))[
            :MAX_SLOT_ALTERNATIVES
        ]
        for candidate in slot_alternatives:
            alternatives.append(
                Alternative(
                    activity_id=activity.id,
                    kind="slot",
                    start=_format_clock(candidate.start),
                    end=_format_clock(candidate.end),
                    start_at=candidate.start.astimezone(UTC).isoformat(),
                    end_at=candidate.end.astimezone(UTC).isoformat(),
                    venue=venue,
                    dose_ug=round(candidate.dose, 1),
                    score=candidate.score,
                    pm2_5=(
                        round(candidate.pm2_5, 1)
                        if candidate.pm2_5 is not None
                        else None
                    ),
                    aqi=candidate.aqi,
                    aqi_basis=candidate.aqi_basis,
                    rationale=[
                        {
                            "template_id": "routine.alternative_slot",
                            "params": {
                                "score": candidate.score,
                                "time": _format_clock(candidate.start),
                            },
                        }
                    ],
                )
            )
        worst = max(with_data, key=lambda item: (item.score, item.start), default=None)
        if worst is not None and worst.start != chosen.start:
            alternatives.append(
                Alternative(
                    activity_id=activity.id,
                    kind="higher_pollution",
                    start=_format_clock(worst.start),
                    end=_format_clock(worst.end),
                    start_at=worst.start.astimezone(UTC).isoformat(),
                    end_at=worst.end.astimezone(UTC).isoformat(),
                    venue=venue,
                    dose_ug=round(worst.dose, 1),
                    score=worst.score,
                    pm2_5=round(worst.pm2_5, 1) if worst.pm2_5 is not None else None,
                    aqi=worst.aqi,
                    aqi_basis=worst.aqi_basis,
                    rationale=[
                        {
                            "template_id": "routine.higher_pollution",
                            "params": {
                                "score": worst.score,
                                "time": _format_clock(worst.start),
                                "pm2_5": (
                                    round(worst.pm2_5, 1)
                                    if worst.pm2_5 is not None
                                    else None
                                ),
                            },
                        }
                    ],
                )
            )
        if activity.venue == "outdoor" and activity.indoor_alternative:
            indoor = _evaluate(
                start=chosen.start,
                preferred=preferred,
                duration_min=activity.duration_min,
                intensity=activity.intensity,
                venue="indoor",
                priority=activity.priority,
                members=selected_members,
                threshold=threshold,
                hours=local_hours,
            )
            alternatives.append(
                Alternative(
                    activity_id=activity.id,
                    kind="indoor",
                    start=_format_clock(indoor.start),
                    end=_format_clock(indoor.end),
                    start_at=indoor.start.astimezone(UTC).isoformat(),
                    end_at=indoor.end.astimezone(UTC).isoformat(),
                    venue="indoor",
                    dose_ug=round(indoor.dose, 1),
                    score=indoor.score,
                    pm2_5=round(indoor.pm2_5, 1) if indoor.pm2_5 is not None else None,
                    aqi=indoor.aqi,
                    aqi_basis=indoor.aqi_basis,
                    rationale=[
                        {
                            "template_id": "routine.indoor_offer",
                            "params": {"alternative": activity.indoor_alternative},
                        }
                    ],
                )
            )

    worst_dose = max(
        [block.dose_ug for block in blocks]
        + [alternative.dose_ug for alternative in alternatives]
        + [0.0]
    )
    blocks = [
        Block(
            activity_id=block.activity_id,
            title=block.title,
            category=block.category,
            start=block.start,
            end=block.end,
            start_at=block.start_at,
            end_at=block.end_at,
            duration_min=block.duration_min,
            venue=block.venue,
            priority=block.priority,
            intensity=block.intensity,
            fixed=block.fixed,
            status=block.status,
            override=block.override,
            basis=block.basis,
            dose_ug=block.dose_ug,
            score=block.score,
            index=round(block.dose_ug / worst_dose * 100) if worst_dose else 0,
            pm2_5=block.pm2_5,
            aqi=block.aqi,
            aqi_basis=block.aqi_basis,
            threshold=block.threshold,
            data_available=block.data_available,
            rationale=block.rationale,
            fact_refs=block.fact_refs,
            indoor_alternative=block.indoor_alternative,
            member_ids=block.member_ids,
        )
        for block in blocks
    ]

    uncertainty = [
        SAFETY_STATEMENT,
        DOSE_ASSUMPTION,
        "Forecast values are modelled estimates, not measured concentrations "
        "at the household.",
        *status.notes,
    ]
    if any(not block.data_available for block in blocks):
        uncertainty.append(
            "At least one fixed activity is listed without forecast-based "
            "context because the forecast does not cover its time."
        )
    if any(block.aqi_basis == "pm25_subindex" for block in blocks):
        uncertainty.append(
            "An overall CPCB AQI was unavailable because fewer than three "
            "pollutants had complete averaging windows; the CPCB PM2.5 "
            "sub-index was used instead and is labelled per activity."
        )
    if len(unscheduled) > 0:
        uncertainty.append(
            f"{len(unscheduled)} activity or activities could not be scheduled; "
            "see the unscheduled list for the reason."
        )

    return RoutinePlan(
        plan_date=plan_date,
        timezone=timezone,
        blocks=blocks,
        unscheduled=unscheduled,
        alternatives=alternatives,
        data_status=status,
        uncertainty=uncertainty,
    )
