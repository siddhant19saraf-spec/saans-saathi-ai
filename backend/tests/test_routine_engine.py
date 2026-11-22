from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.domain.routine import (
    ForecastCoverageError,
    ForecastHour,
    MemberProfile,
    PlannerActivity,
    generate_plan,
)

PLAN_DATE = date(2026, 11, 21)
KOLKATA = "Asia/Kolkata"
NEW_YORK = "America/New_York"


def _hours(
    start: datetime,
    count: int,
    tz: ZoneInfo,
    value: Callable[[datetime], float | None],
) -> list[ForecastHour]:
    return [
        ForecastHour(
            time=start + timedelta(hours=offset),
            pm2_5=value((start + timedelta(hours=offset)).astimezone(tz)),
            pm10=None,
        )
        for offset in range(count)
    ]


def _constant(value: float | None) -> Callable[[datetime], float | None]:
    return lambda _local: value


def _activity(**overrides: object) -> PlannerActivity:
    values: dict[str, object] = {
        "id": "walk",
        "title": "Morning walk",
        "category": "morning_walk",
        "duration_min": 60,
        "preferred_start": "06:30",
        "earliest_start": "06:00",
        "latest_start": "08:00",
        "venue": "outdoor",
        "fixed": False,
        "priority": "medium",
        "intensity": "light",
    }
    values.update(overrides)
    return PlannerActivity(**values)  # type: ignore[arg-type]


def _plan(
    *,
    hours: list[ForecastHour],
    activities: list[PlannerActivity] | None = None,
    members: list[MemberProfile] | None = None,
    plan_date: date = PLAN_DATE,
    timezone: str = KOLKATA,
    issued_at: datetime | None = None,
) -> object:
    return generate_plan(
        plan_date=plan_date,
        timezone=timezone,
        activities=activities or [_activity()],
        members=members or [MemberProfile(age_band="18-59")],
        hours=hours,
        provider="fixture",
        issued_at=issued_at,
        now=datetime(2026, 11, 20, 12, tzinfo=UTC),
    )


def test_timezone_conversion_maps_local_preference_to_utc_instant() -> None:
    tz = ZoneInfo(KOLKATA)
    hours = _hours(datetime(2026, 11, 20, 0, tzinfo=UTC), 48, tz, _constant(40.0))

    plan = _plan(hours=hours)

    block = plan.blocks[0]  # type: ignore[attr-defined]
    assert block.start == "06:30"
    assert block.start_at == "2026-11-21T01:00:00+00:00"
    assert block.end_at == "2026-11-21T02:00:00+00:00"


def test_low_pollution_window_is_chosen_with_explanation_and_alternatives() -> None:
    tz = ZoneInfo(KOLKATA)
    hours = _hours(datetime(2026, 11, 20, 0, tzinfo=UTC), 48, tz, _constant(18.0))

    plan = _plan(hours=hours)

    block = plan.blocks[0]  # type: ignore[attr-defined]
    assert block.venue == "outdoor"
    assert block.data_available is True
    assert block.rationale[0]["template_id"] == "routine.chosen_slot"
    assert plan.alternatives  # type: ignore[attr-defined]
    assert plan.data_status.coverage_ratio == 1.0  # type: ignore[attr-defined]
    assert "safe" in plan.uncertainty[0]  # type: ignore[attr-defined]


def test_higher_pollution_hours_avoided_when_a_lower_slot_exists() -> None:
    tz = ZoneInfo(KOLKATA)

    def value(local: datetime) -> float:
        return 180.0 if local.hour == 7 else 20.0

    hours = _hours(datetime(2026, 11, 20, 0, tzinfo=UTC), 48, tz, value)

    plan = _plan(
        hours=hours,
        activities=[_activity(duration_min=30)],
    )

    block = plan.blocks[0]  # type: ignore[attr-defined]
    assert block.start == "06:30"
    assert block.pm2_5 is not None and block.pm2_5 < 40


def test_high_pollution_swaps_to_saved_indoor_alternative() -> None:
    tz = ZoneInfo(KOLKATA)
    hours = _hours(datetime(2026, 11, 20, 0, tzinfo=UTC), 48, tz, _constant(300.0))

    plan = _plan(
        hours=hours,
        activities=[_activity(indoor_alternative="Indoor stretching")],
        members=[MemberProfile(age_band="6-12", sensitive=True)],
    )

    block = plan.blocks[0]  # type: ignore[attr-defined]
    assert block.venue == "indoor"
    assert block.rationale[0]["template_id"] == "routine.indoor_swap"
    assert any(
        item.kind == "indoor" for item in plan.alternatives  # type: ignore[attr-defined]
    )


def test_fixed_activities_keep_their_time_and_report_overlap() -> None:
    tz = ZoneInfo(KOLKATA)
    hours = _hours(datetime(2026, 11, 20, 0, tzinfo=UTC), 48, tz, _constant(30.0))
    activities = [
        _activity(id="a", title="A", fixed=True, preferred_start="06:00"),
        _activity(
            id="b",
            title="B",
            fixed=True,
            preferred_start="06:30",
            duration_min=60,
        ),
    ]

    plan = _plan(hours=hours, activities=activities)

    assert [block.activity_id for block in plan.blocks] == ["a"]  # type: ignore[attr-defined]
    assert plan.unscheduled[0].reason_code == "FIXED_OVERLAP"  # type: ignore[attr-defined]


def test_flexible_activity_moves_when_preferred_slot_is_taken() -> None:
    tz = ZoneInfo(KOLKATA)
    hours = _hours(datetime(2026, 11, 20, 0, tzinfo=UTC), 48, tz, _constant(30.0))
    activities = [
        _activity(id="a", title="A", fixed=True, preferred_start="06:00"),
        _activity(
            id="b",
            title="B",
            preferred_start="06:00",
            earliest_start="06:00",
            latest_start="08:00",
        ),
    ]

    plan = _plan(hours=hours, activities=activities)

    starts = {block.activity_id: block.start for block in plan.blocks}  # type: ignore[attr-defined]
    assert starts["a"] == "06:00"
    assert starts["b"] != "06:00"


def test_missing_forecast_interval_is_reported_not_invented() -> None:
    tz = ZoneInfo(KOLKATA)

    def value(local: datetime) -> float | None:
        if local.date() == PLAN_DATE and local.hour < 9:
            return None
        return 25.0

    hours = _hours(datetime(2026, 11, 20, 0, tzinfo=UTC), 48, tz, value)

    plan = _plan(hours=hours)

    assert plan.blocks == []  # type: ignore[attr-defined]
    assert plan.unscheduled[0].reason_code == "NO_FORECAST_FOR_WINDOW"  # type: ignore[attr-defined]
    assert plan.data_status.coverage_ratio < 1.0  # type: ignore[attr-defined]


def test_impossible_window_is_unscheduled() -> None:
    tz = ZoneInfo(KOLKATA)
    hours = _hours(datetime(2026, 11, 20, 0, tzinfo=UTC), 48, tz, _constant(25.0))

    plan = _plan(
        hours=hours,
        activities=[_activity(earliest_start="08:00", latest_start="07:00")],
    )

    assert plan.unscheduled[0].reason_code == "IMPOSSIBLE_WINDOW"  # type: ignore[attr-defined]


def test_no_forecast_for_the_date_raises_coverage_error() -> None:
    hours = [
        ForecastHour(time=datetime(2026, 11, 25, hour, tzinfo=UTC), pm2_5=20.0)
        for hour in range(24)
    ]

    with pytest.raises(ForecastCoverageError):
        _plan(hours=hours)


def test_dst_spring_forward_gap_is_reported() -> None:
    tz = ZoneInfo(NEW_YORK)
    hours = _hours(datetime(2026, 3, 8, 0, tzinfo=UTC), 36, tz, _constant(20.0))
    spring_forward = date(2026, 3, 8)

    plan = _plan(
        hours=hours,
        plan_date=spring_forward,
        timezone=NEW_YORK,
        activities=[
            _activity(
                preferred_start="02:30", earliest_start="02:30", latest_start="02:30"
            )
        ],
    )

    assert plan.unscheduled[0].reason_code == "DST_GAP"  # type: ignore[attr-defined]


def test_dst_fall_back_uses_the_first_occurrence() -> None:
    tz = ZoneInfo(NEW_YORK)
    hours = _hours(datetime(2026, 11, 1, 0, tzinfo=UTC), 30, tz, _constant(20.0))
    fall_back = date(2026, 11, 1)

    plan = _plan(
        hours=hours,
        plan_date=fall_back,
        timezone=NEW_YORK,
        activities=[
            _activity(
                preferred_start="07:00",
                earliest_start="06:00",
                latest_start="08:00",
            )
        ],
    )

    # 07:00 on Nov 1 is in EST (after DST fall-back at 02:00 EDT→01:00 EST),
    # so 07:00 EST = 12:00 UTC
    assert plan.blocks[0].start_at == "2026-11-01T12:00:00+00:00"  # type: ignore[attr-defined]


def test_identical_inputs_produce_identical_payloads() -> None:
    tz = ZoneInfo(KOLKATA)
    hours = _hours(datetime(2026, 11, 20, 0, tzinfo=UTC), 48, tz, _constant(35.0))

    first = _plan(hours=hours)
    second = _plan(hours=hours)

    assert first.to_payload() == second.to_payload()  # type: ignore[attr-defined]


def test_priority_breaks_a_contested_fixed_slot() -> None:
    tz = ZoneInfo(KOLKATA)
    hours = _hours(datetime(2026, 11, 20, 0, tzinfo=UTC), 48, tz, _constant(25.0))
    activities = [
        _activity(
            id="low",
            title="Low",
            priority="low",
            preferred_start="06:00",
            earliest_start="06:00",
            latest_start="06:00",
            duration_min=30,
        ),
        _activity(
            id="high",
            title="High",
            priority="high",
            preferred_start="06:00",
            earliest_start="06:00",
            latest_start="06:00",
            duration_min=30,
        ),
    ]

    plan = _plan(hours=hours, activities=activities)

    assert [block.activity_id for block in plan.blocks] == ["high"]  # type: ignore[attr-defined]
    assert plan.unscheduled[0].activity_id == "low"  # type: ignore[attr-defined]


def test_duration_controls_end_time() -> None:
    tz = ZoneInfo(KOLKATA)
    hours = _hours(datetime(2026, 11, 20, 0, tzinfo=UTC), 48, tz, _constant(25.0))

    plan = _plan(
        hours=hours,
        activities=[_activity(duration_min=90, preferred_start="07:00")],
    )

    block = plan.blocks[0]  # type: ignore[attr-defined]
    assert (block.start, block.end) == ("07:00", "08:30")
