"""Persistence for saved journeys, emission calculations and sustainability goals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ecoroute import (
    EmissionCalculation,
    SavedJourney,
    SustainabilityGoal,
)
from app.models.household import Household


@dataclass(frozen=True)
class JourneyRow:
    id: UUID
    origin_lat: float
    origin_lon: float
    destination_lat: float
    destination_lon: float
    travel_date: date | None
    modes: list[str]
    selected_mode: str
    passengers: int
    distance_km: float
    duration_min: int
    co2e_kg: float | None
    co2e_per_passenger_kg: float | None
    notes: str | None


async def save_journey(
    session: AsyncSession,
    *,
    household_id: UUID,
    origin_lat: float,
    origin_lon: float,
    destination_lat: float,
    destination_lon: float,
    travel_date: date | None,
    modes: list[str],
    selected_mode: str,
    passengers: int,
    distance_km: float,
    duration_min: int,
    co2e_kg: float | None,
    co2e_per_passenger_kg: float | None,
    notes: str | None,
) -> SavedJourney:
    journey = SavedJourney(
        household_id=household_id,
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        destination_lat=destination_lat,
        destination_lon=destination_lon,
        travel_date=travel_date,
        modes=modes,
        selected_mode=selected_mode,
        passengers=passengers,
        distance_km=distance_km,
        duration_min=duration_min,
        co2e_kg=co2e_kg,
        co2e_per_passenger_kg=co2e_per_passenger_kg,
        notes=notes,
    )
    session.add(journey)
    await session.flush()
    return journey


async def list_journeys(
    session: AsyncSession,
    *,
    household_id: UUID,
    limit: int,
    offset: int = 0,
) -> list[SavedJourney]:
    statement = (
        select(SavedJourney)
        .where(SavedJourney.household_id == household_id)
        .order_by(SavedJourney.created_at.desc(), SavedJourney.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list((await session.scalars(statement)).all())


async def get_journey(
    session: AsyncSession,
    *,
    household_id: UUID,
    journey_id: UUID,
) -> SavedJourney | None:
    return await session.scalar(
        select(SavedJourney).where(
            SavedJourney.id == journey_id,
            SavedJourney.household_id == household_id,
        )
    )


async def delete_journey(
    session: AsyncSession,
    journey: SavedJourney,
) -> None:
    await session.delete(journey)
    await session.flush()


async def add_emission_calculation(
    session: AsyncSession,
    *,
    household_id: UUID,
    activity_type: str,
    quantity: Decimal,
    unit: str,
    result_kg_co2e: Decimal,
    factor_key: str,
    factor_value: Decimal,
    factor_unit: str,
    factor_version: str,
    factor_source_url: str,
    calculation_method: str,
    assumptions: dict[str, Any],
) -> EmissionCalculation:
    calculation = EmissionCalculation(
        household_id=household_id,
        activity_type=activity_type,
        quantity=quantity,
        unit=unit,
        result_kg_co2e=result_kg_co2e,
        factor_key=factor_key,
        factor_value=factor_value,
        factor_unit=factor_unit,
        factor_version=factor_version,
        factor_source_url=factor_source_url,
        calculation_method=calculation_method,
        assumptions=assumptions,
    )
    session.add(calculation)
    await session.flush()
    return calculation


async def list_emission_calculations(
    session: AsyncSession,
    *,
    household_id: UUID,
    limit: int,
    offset: int = 0,
) -> list[EmissionCalculation]:
    statement = (
        select(EmissionCalculation)
        .where(EmissionCalculation.household_id == household_id)
        .order_by(EmissionCalculation.created_at.desc(), EmissionCalculation.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list((await session.scalars(statement)).all())


async def create_goal(
    session: AsyncSession,
    *,
    household_id: UUID,
    title: str,
    description: str | None,
    activity_type: str,
    unit: str,
    target_value: Decimal,
    target_date: date | None,
) -> SustainabilityGoal:
    goal = SustainabilityGoal(
        household_id=household_id,
        title=title,
        description=description,
        activity_type=activity_type,
        unit=unit,
        target_value=target_value,
        current_value=Decimal("0"),
        target_date=target_date,
    )
    session.add(goal)
    await session.flush()
    return goal


async def list_goals(
    session: AsyncSession,
    *,
    household_id: UUID,
) -> list[SustainabilityGoal]:
    statement = (
        select(SustainabilityGoal)
        .where(SustainabilityGoal.household_id == household_id)
        .order_by(SustainabilityGoal.created_at.desc())
    )
    return list((await session.scalars(statement)).all())


async def get_goal(
    session: AsyncSession,
    *,
    household_id: UUID,
    goal_id: UUID,
) -> SustainabilityGoal | None:
    return await session.scalar(
        select(SustainabilityGoal).where(
            SustainabilityGoal.id == goal_id,
            SustainabilityGoal.household_id == household_id,
        )
    )


async def update_goal(
    session: AsyncSession,
    *,
    goal: SustainabilityGoal,
    title: str | None = None,
    description: str | None = None,
    target_value: Decimal | None = None,
    target_date: date | None = None,
    is_active: bool | None = None,
) -> SustainabilityGoal:
    from app.models.profile import utc_now

    if title is not None:
        goal.title = title
    if description is not None:
        goal.description = description
    if target_value is not None:
        goal.target_value = target_value
    if target_date is not None:
        goal.target_date = target_date
    if is_active is not None:
        goal.is_active = is_active
    goal.updated_at = utc_now()
    await session.flush()
    return goal


async def delete_goal(
    session: AsyncSession,
    goal: SustainabilityGoal,
) -> None:
    await session.delete(goal)
    await session.flush()


async def delete_journeys_for_profile(session: AsyncSession, profile_id: UUID) -> None:
    household_ids = select(Household.id).where(Household.profile_id == profile_id)
    await session.execute(
        delete(SavedJourney).where(SavedJourney.household_id.in_(household_ids))
    )
    await session.flush()


async def delete_calculations_for_profile(
    session: AsyncSession, profile_id: UUID
) -> None:
    household_ids = select(Household.id).where(Household.profile_id == profile_id)
    await session.execute(
        delete(EmissionCalculation).where(
            EmissionCalculation.household_id.in_(household_ids)
        )
    )
    await session.flush()


async def delete_goals_for_profile(session: AsyncSession, profile_id: UUID) -> None:
    household_ids = select(Household.id).where(Household.profile_id == profile_id)
    await session.execute(
        delete(SustainabilityGoal).where(
            SustainabilityGoal.household_id.in_(household_ids)
        )
    )
    await session.flush()


__all__ = [
    "JourneyRow",
    "add_emission_calculation",
    "create_goal",
    "delete_calculations_for_profile",
    "delete_goal",
    "delete_goals_for_profile",
    "delete_journey",
    "delete_journeys_for_profile",
    "get_goal",
    "get_journey",
    "list_emission_calculations",
    "list_goals",
    "list_journeys",
    "save_journey",
    "update_goal",
]
