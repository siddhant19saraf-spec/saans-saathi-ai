"""Sustainability ledger: factors, activity logging, goals and summaries."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnprocessableEntityError
from app.domain.carbon import activity_co2e
from app.domain.factors import load_factors
from app.models.impact import SustainabilityActivity
from app.models.profile import Profile
from app.repositories import (
    ecoroute as ecoroute_repo,
    households as households_repo,
    impact as impact_repo,
)
from app.schemas.impact import (
    Activity,
    ActivityCreate,
    BaselineSavings,
    FactorOut,
    GoalCreate,
    GoalOut,
    GoalUpdate,
    ImpactSummary,
    ImpactTrends,
    MethodologyOut,
    TrendPoint,
    TypeBreakdown,
    unit_for,
)
from app.utils.time import utc_now

_SUPPORTED = {"walked", "worked-from-home"}

# Baseline assumption: kilometres that would have been driven by car if the
# user had not walked or worked from home. Labelled as an assumption, not a
# measured baseline.
_BASELINE_CAR_KM_PER_DAY = 16.0


def factors() -> list[FactorOut]:
    return [
        FactorOut(
            key=factor.key,
            label=factor.label,
            value=factor.value,
            unit=factor.unit,
            source=factor.source_title,
            source_url=str(factor.source_url),
            version=factor.version,
            retrieved_at=factor.retrieved_on,
        )
        for factor in load_factors()
    ]


async def add_activity(
    session: AsyncSession, profile: Profile, payload: ActivityCreate
) -> Activity:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise UnprocessableEntityError(
            "Create a household profile before logging an activity.",
            code="NO_HOUSEHOLD",
        )
    if payload.activity_type not in _SUPPORTED:
        raise UnprocessableEntityError(
            (
                f"No verified emission factor exists for '{payload.activity_type}'. "
                "The activity is not recorded with a guessed value."
            ),
            code="FACTOR_NOT_AVAILABLE",
        )
    result = activity_co2e(
        activity_type=payload.activity_type, quantity=payload.quantity
    )
    if result is None:
        raise UnprocessableEntityError(
            f"No verified emission factor exists for '{payload.activity_type}'.",
            code="FACTOR_NOT_AVAILABLE",
        )
    unit = unit_for(payload.activity_type)
    if payload.unit is not None and payload.unit != unit:
        raise UnprocessableEntityError(
            f"Activity '{payload.activity_type}' is logged in {unit}.",
            code="UNIT_MISMATCH",
        )
    # Duplicate prevention: reject exact same activity type + date + quantity
    # within the last 24 hours to avoid accidental double-counting.
    existing = await impact_repo.list_activities(
        session,
        household_id=household.id,
        since=utc_now().date(),
        limit=100,
        offset=0,
    )
    for row in existing:
        if (
            row.activity_type == payload.activity_type
            and row.occurred_on == payload.occurred_on
            and abs(float(row.quantity) - payload.quantity) < 1e-9
        ):
            raise ConflictError(
                "A matching activity for this type, date and quantity already exists.",
                code="DUPLICATE_ACTIVITY",
            )
    activity = await impact_repo.add_activity(
        session,
        household_id=household.id,
        activity_type=payload.activity_type,
        occurred_on=payload.occurred_on,
        quantity=Decimal(str(payload.quantity)).quantize(Decimal("0.001")),
        unit=unit,
        co2e_kg=Decimal(str(result.kg_co2e)).quantize(Decimal("0.0001")),
        factor_key=result.factor_key,
        factor_value=Decimal(str(result.factor_value)).quantize(Decimal("0.000001")),
        factor_unit=result.factor_unit,
        factor_version=result.factor_version,
        factor_source_url=result.factor_source_url,
    )
    await session.commit()
    return _activity(activity)


def _activity(activity: SustainabilityActivity) -> Activity:
    return Activity(
        id=activity.id,
        activity_type=activity.activity_type,
        occurred_on=activity.occurred_on,
        quantity=float(activity.quantity),
        unit=activity.unit,
        co2e_kg=float(activity.co2e_kg),
        factor_key=activity.factor_key,
        factor_value=float(activity.factor_value),
        factor_unit=activity.factor_unit,
        factor_version=activity.factor_version,
        factor_source_url=activity.factor_source_url,
        created_at=activity.created_at,
    )


async def list_activities(
    session: AsyncSession,
    profile: Profile,
    *,
    days: int,
    limit: int,
    offset: int = 0,
) -> list[Activity]:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise UnprocessableEntityError(
            "Create a household profile first.", code="NO_HOUSEHOLD"
        )
    since = utc_now().date() - timedelta(days=days - 1)
    rows = await impact_repo.list_activities(
        session,
        household_id=household.id,
        since=since,
        limit=limit,
        offset=offset,
    )
    return [_activity(row) for row in rows]


async def summary(
    session: AsyncSession, profile: Profile, *, days: int
) -> ImpactSummary:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise UnprocessableEntityError(
            "Create a household profile first.", code="NO_HOUSEHOLD"
        )
    since = utc_now().date() - timedelta(days=days - 1)
    rows = await impact_repo.summary(session, household_id=household.id, since=since)
    total = round(sum(row.co2e_kg for row in rows), 4)
    count = sum(row.count for row in rows)
    return ImpactSummary(
        range=f"{days}d",
        total_co2e_kg=total,
        activity_count=count,
        by_type=[
            TypeBreakdown(
                activity_type=row.activity_type,
                co2e_kg=round(row.co2e_kg, 4),
                count=row.count,
            )
            for row in rows
        ],
    )


# -- goals -------------------------------------------------------------------


async def create_goal(
    session: AsyncSession, profile: Profile, payload: GoalCreate
) -> GoalOut:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise UnprocessableEntityError(
            "Create a household profile before setting a goal.",
            code="NO_HOUSEHOLD",
        )
    if payload.unit != unit_for(payload.activity_type):
        raise UnprocessableEntityError(
            f"Goal unit for '{payload.activity_type}' must be {unit_for(payload.activity_type)}.",
            code="UNIT_MISMATCH",
        )
    goal = await ecoroute_repo.create_goal(
        session,
        household_id=household.id,
        title=payload.title,
        description=payload.description,
        activity_type=payload.activity_type,
        unit=payload.unit,
        target_value=Decimal(str(payload.target_value)).quantize(Decimal("0.001")),
        target_date=payload.target_date,
    )
    await session.commit()
    return _goal_out(goal)


async def list_goals(session: AsyncSession, profile: Profile) -> list[GoalOut]:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise UnprocessableEntityError(
            "Create a household profile first.", code="NO_HOUSEHOLD"
        )
    rows = await ecoroute_repo.list_goals(session, household_id=household.id)
    return [_goal_out(row) for row in rows]


async def update_goal(
    session: AsyncSession,
    profile: Profile,
    goal_id: UUID,
    payload: GoalUpdate,
) -> GoalOut:
    from uuid import UUID as _UUID

    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise UnprocessableEntityError(
            "Create a household profile first.", code="NO_HOUSEHOLD"
        )
    goal = await ecoroute_repo.get_goal(
        session, household_id=household.id, goal_id=_UUID(str(goal_id))
    )
    if goal is None:
        raise UnprocessableEntityError("Goal not found.", code="GOAL_NOT_FOUND")
    goal = await ecoroute_repo.update_goal(
        session,
        goal=goal,
        title=payload.title,
        description=payload.description,
        target_value=(
            Decimal(str(payload.target_value)).quantize(Decimal("0.001"))
            if payload.target_value is not None
            else None
        ),
        target_date=payload.target_date,
        is_active=payload.is_active,
    )
    await session.commit()
    return _goal_out(goal)


async def delete_goal(session: AsyncSession, profile: Profile, goal_id: UUID) -> None:
    from uuid import UUID as _UUID

    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise UnprocessableEntityError(
            "Create a household profile first.", code="NO_HOUSEHOLD"
        )
    goal = await ecoroute_repo.get_goal(
        session, household_id=household.id, goal_id=_UUID(str(goal_id))
    )
    if goal is None:
        raise UnprocessableEntityError("Goal not found.", code="GOAL_NOT_FOUND")
    await ecoroute_repo.delete_goal(session, goal)
    await session.commit()


def _goal_out(goal: Any) -> GoalOut:
    return GoalOut(
        id=goal.id,
        title=goal.title,
        description=goal.description,
        activity_type=goal.activity_type,
        unit=goal.unit,
        target_value=float(goal.target_value),
        current_value=float(goal.current_value),
        target_date=goal.target_date,
        is_active=goal.is_active,
        progress_percent=goal.progress_percent,
        is_complete=goal.is_complete,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )


# -- baseline and savings -----------------------------------------------------


async def baseline_and_savings(
    session: AsyncSession,
    profile: Profile,
    *,
    days: int,
) -> BaselineSavings:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise UnprocessableEntityError(
            "Create a household profile first.", code="NO_HOUSEHOLD"
        )
    since = utc_now().date() - timedelta(days=days - 1)
    rows = await impact_repo.summary(session, household_id=household.id, since=since)
    activity_co2e_total = round(sum(row.co2e_kg for row in rows), 4)
    activity_count = sum(row.count for row in rows)

    # Baseline: kilometres that would have been driven by car if the user had
    # not logged low-carbon activities. Labelled as a modelled assumption.
    baseline_km = (
        _BASELINE_CAR_KM_PER_DAY * days * activity_count if activity_count else 0.0
    )
    baseline_co2e = None
    if baseline_km > 0:
        result = activity_co2e(activity_type="walked", quantity=baseline_km)
        if result is not None:
            baseline_co2e = round(result.kg_co2e, 4)

    savings = None
    savings_basis = None
    if baseline_co2e is not None:
        savings = round(baseline_co2e - activity_co2e_total, 4)
        savings_basis = (
            f"Modelled car baseline ({_BASELINE_CAR_KM_PER_DAY} km/day x {days} days "
            f"x {activity_count} activities) minus logged activity emissions. "
            "Baseline is an assumption, not a measured value."
        )

    return BaselineSavings(
        baseline_co2e_kg=baseline_co2e,
        baseline_basis=(
            (
                f"Modelled car travel: {_BASELINE_CAR_KM_PER_DAY} km/day x {days} days x "
                f"{activity_count} logged activities. Not a measured baseline."
            )
            if baseline_co2e is not None
            else None
        ),
        activity_co2e_kg=activity_co2e_total,
        savings_co2e_kg=savings,
        savings_basis=savings_basis,
    )


# -- trends ------------------------------------------------------------------


async def trends(
    session: AsyncSession,
    profile: Profile,
    *,
    days: int,
) -> ImpactTrends:
    household = await households_repo.get_for_profile(session, profile.id)
    if household is None:
        raise UnprocessableEntityError(
            "Create a household profile first.", code="NO_HOUSEHOLD"
        )
    since = utc_now().date() - timedelta(days=days - 1)
    rows = await impact_repo.list_activities(
        session, household_id=household.id, since=since, limit=10_000, offset=0
    )

    weekly: dict[str, tuple[float, int]] = {}
    monthly: dict[str, tuple[float, int]] = {}
    for row in rows:
        d = row.occurred_on
        iso_week = d.isocalendar()
        week_key = f"{iso_week.year}-W{iso_week.week:02d}"
        month_key = f"{d.year}-{d.month:02d}"
        for bucket, key in ((weekly, week_key), (monthly, month_key)):
            co2e, count = bucket.get(key, (0.0, 0))
            bucket[key] = (co2e + float(row.co2e_kg), count + 1)

    weekly_points = [
        TrendPoint(period=k, co2e_kg=round(v[0], 4), activity_count=v[1])
        for k, v in sorted(weekly.items())
    ]
    monthly_points = [
        TrendPoint(period=k, co2e_kg=round(v[0], 4), activity_count=v[1])
        for k, v in sorted(monthly.items())
    ]
    return ImpactTrends(weekly=weekly_points, monthly=monthly_points)


# -- methodology -------------------------------------------------------------


def methodology() -> MethodologyOut:
    return MethodologyOut(
        formula=(
            "Estimated emissions = Activity quantity x Emission factor. "
            "Estimated savings = Modelled baseline emissions - Activity emissions."
        ),
        factors_used=[f.key for f in load_factors()],
        assumptions=[
            f"Car baseline: {_BASELINE_CAR_KM_PER_DAY} km/day per logged activity day.",
            "Baseline is a modelled assumption, never a measured value.",
            "Activity emission factors carry source, version and uncertainty.",
        ],
        limitations=[
            "Savings are estimated against a modelled baseline, not measured real-world reductions.",
            "No claim is made that individual activity changed city-wide air quality.",
            "Unverified activity types are rejected rather than estimated.",
        ],
    )


__all__ = [
    "add_activity",
    "baseline_and_savings",
    "create_goal",
    "delete_goal",
    "factors",
    "list_activities",
    "list_goals",
    "methodology",
    "summary",
    "trends",
    "update_goal",
]
