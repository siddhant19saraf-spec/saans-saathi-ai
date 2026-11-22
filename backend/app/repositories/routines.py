"""Routine activity, plan-version and item persistence."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.routine import Routine, RoutineActivity, RoutineItem

# -- activity preferences --------------------------------------------------


async def list_activities(
    session: AsyncSession, *, household_id: UUID, include_inactive: bool = False
) -> list[RoutineActivity]:
    statement = select(RoutineActivity).where(
        RoutineActivity.household_id == household_id
    )
    if not include_inactive:
        statement = statement.where(RoutineActivity.active.is_(True))
    statement = statement.order_by(
        RoutineActivity.preferred_start, RoutineActivity.created_at
    )
    return list((await session.scalars(statement)).all())


async def get_activity(
    session: AsyncSession, *, household_id: UUID, activity_id: UUID
) -> RoutineActivity | None:
    return await session.scalar(
        select(RoutineActivity).where(
            RoutineActivity.id == activity_id,
            RoutineActivity.household_id == household_id,
        )
    )


async def count_activities(session: AsyncSession, *, household_id: UUID) -> int:
    return int(
        await session.scalar(
            select(func.count())
            .select_from(RoutineActivity)
            .where(
                RoutineActivity.household_id == household_id,
                RoutineActivity.active.is_(True),
            )
        )
        or 0
    )


def add_activity(
    session: AsyncSession,
    *,
    household_id: UUID,
    values: dict[str, Any],
) -> RoutineActivity:
    activity = RoutineActivity(household_id=household_id, **values)
    session.add(activity)
    return activity


async def delete_activity(session: AsyncSession, activity: RoutineActivity) -> None:
    activity.active = False
    await session.flush()


# -- plans -----------------------------------------------------------------


async def latest_active_for_date(
    session: AsyncSession, *, household_id: UUID, plan_date: date
) -> Routine | None:
    return await session.scalar(
        select(Routine)
        .where(
            Routine.household_id == household_id,
            Routine.plan_date == plan_date,
            Routine.status == "active",
        )
        .order_by(Routine.version.desc())
        .limit(1)
    )


async def latest_version_for_date(
    session: AsyncSession, *, household_id: UUID, plan_date: date
) -> Routine | None:
    return await session.scalar(
        select(Routine)
        .where(
            Routine.household_id == household_id,
            Routine.plan_date == plan_date,
        )
        .order_by(Routine.version.desc())
        .limit(1)
    )


async def find_active_by_inputs(
    session: AsyncSession,
    *,
    household_id: UUID,
    plan_date: date,
    inputs_hash: str,
) -> Routine | None:
    return await session.scalar(
        select(Routine).where(
            Routine.household_id == household_id,
            Routine.plan_date == plan_date,
            Routine.inputs_hash == inputs_hash,
            Routine.status == "active",
        )
    )


async def get(
    session: AsyncSession, *, household_id: UUID, routine_id: UUID
) -> Routine | None:
    return await session.scalar(
        select(Routine).where(
            Routine.id == routine_id, Routine.household_id == household_id
        )
    )


async def supersede_active(
    session: AsyncSession, *, household_id: UUID, plan_date: date
) -> None:
    await session.execute(
        update(Routine)
        .where(
            Routine.household_id == household_id,
            Routine.plan_date == plan_date,
            Routine.status == "active",
        )
        .values(status="superseded")
    )


def add(
    session: AsyncSession,
    *,
    household_id: UUID,
    plan_date: date,
    timezone: str,
    engine_version: str,
    inputs_hash: str,
    plan: dict[str, Any],
    version: int,
    parent_routine_id: UUID | None,
    expires_at: datetime,
) -> Routine:
    routine = Routine(
        household_id=household_id,
        plan_date=plan_date,
        timezone=timezone,
        engine_version=engine_version,
        inputs_hash=inputs_hash,
        plan=plan,
        version=version,
        status="active",
        parent_routine_id=parent_routine_id,
        expires_at=expires_at,
    )
    session.add(routine)
    return routine


async def replace_plan(
    session: AsyncSession, routine: Routine, plan: dict[str, Any]
) -> Routine:
    routine.plan = plan
    await session.flush()
    return routine


async def history(
    session: AsyncSession,
    *,
    household_id: UUID,
    plan_date: date | None,
    limit: int,
    offset: int,
) -> tuple[list[Routine], int]:
    filters = [Routine.household_id == household_id]
    if plan_date is not None:
        filters.append(Routine.plan_date == plan_date)
    total = int(
        await session.scalar(select(func.count()).select_from(Routine).where(*filters))
        or 0
    )
    rows = await session.scalars(
        select(Routine)
        .where(*filters)
        .order_by(Routine.plan_date.desc(), Routine.version.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(rows), total


# -- items -----------------------------------------------------------------


def add_item(
    session: AsyncSession,
    *,
    routine_id: UUID,
    activity_id: UUID,
    title: str,
    category: str,
    venue: str,
    priority: str,
    fixed: bool,
    status: str,
    start_at: datetime | None,
    end_at: datetime | None,
    duration_min: int | None,
    override: bool,
    rationale: list[dict[str, Any]],
    context: dict[str, Any],
    alternatives: list[dict[str, Any]],
) -> RoutineItem:
    item = RoutineItem(
        routine_id=routine_id,
        activity_id=activity_id,
        title=title,
        category=category,
        venue=venue,
        priority=priority,
        fixed=fixed,
        status=status,
        start_at=start_at,
        end_at=end_at,
        duration_min=duration_min,
        override=override,
        rationale=rationale,
        context=context,
        alternatives=alternatives,
    )
    session.add(item)
    return item


async def get_item_by_activity(
    session: AsyncSession, *, routine_id: UUID, activity_id: UUID
) -> RoutineItem | None:
    return await session.scalar(
        select(RoutineItem).where(
            RoutineItem.routine_id == routine_id,
            RoutineItem.activity_id == activity_id,
        )
    )
