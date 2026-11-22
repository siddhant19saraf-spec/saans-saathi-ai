"""Sustainability ledger, aggregate queries and privacy audit events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.household import Household
from app.models.impact import PrivacyEvent, SustainabilityActivity


@dataclass(frozen=True)
class ActivityRow:
    activity_type: str
    co2e_kg: float
    count: int


async def add_activity(
    session: AsyncSession,
    *,
    household_id: UUID,
    activity_type: str,
    occurred_on: date,
    quantity: Decimal,
    unit: str,
    co2e_kg: Decimal,
    factor_key: str,
    factor_value: Decimal,
    factor_unit: str,
    factor_version: str,
    factor_source_url: str,
) -> SustainabilityActivity:
    activity = SustainabilityActivity(
        household_id=household_id,
        activity_type=activity_type,
        occurred_on=occurred_on,
        quantity=quantity,
        unit=unit,
        co2e_kg=co2e_kg,
        factor_key=factor_key,
        factor_value=factor_value,
        factor_unit=factor_unit,
        factor_version=factor_version,
        factor_source_url=factor_source_url,
    )
    session.add(activity)
    await session.flush()
    return activity


async def list_activities(
    session: AsyncSession,
    *,
    household_id: UUID,
    since: date,
    limit: int,
    offset: int = 0,
) -> list[SustainabilityActivity]:
    statement = (
        select(SustainabilityActivity)
        .where(
            SustainabilityActivity.household_id == household_id,
            SustainabilityActivity.occurred_on >= since,
        )
        .order_by(
            SustainabilityActivity.occurred_on.desc(),
            SustainabilityActivity.created_at.desc(),
            SustainabilityActivity.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )
    return list((await session.scalars(statement)).all())


async def summary(
    session: AsyncSession, *, household_id: UUID, since: date
) -> tuple[ActivityRow, ...]:
    statement = (
        select(
            SustainabilityActivity.activity_type,
            func.coalesce(func.sum(SustainabilityActivity.co2e_kg), 0),
            func.count(SustainabilityActivity.id),
        )
        .where(
            SustainabilityActivity.household_id == household_id,
            SustainabilityActivity.occurred_on >= since,
        )
        .group_by(SustainabilityActivity.activity_type)
        .order_by(SustainabilityActivity.activity_type)
    )
    rows = (await session.execute(statement)).all()
    return tuple(
        ActivityRow(
            activity_type=str(row[0]),
            co2e_kg=float(row[1]),
            count=int(row[2]),
        )
        for row in rows
    )


async def log_privacy_event(
    session: AsyncSession,
    *,
    profile_id: UUID | None,
    event: str,
    meta: dict[str, Any] | None = None,
) -> None:
    session.add(PrivacyEvent(profile_id=profile_id, event=event, meta=meta or {}))
    await session.flush()


async def delete_activities_for_profile(
    session: AsyncSession, profile_id: UUID
) -> None:
    household_ids = select(Household.id).where(Household.profile_id == profile_id)
    await session.execute(
        delete(SustainabilityActivity).where(
            SustainabilityActivity.household_id.in_(household_ids)
        )
    )
    await session.flush()
