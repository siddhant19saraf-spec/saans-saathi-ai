"""Household, member, preference and saved-location persistence."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.household import (
    Household,
    HouseholdMember,
    HouseholdPreference,
    SavedLocation,
)
from app.models.profile import utc_now


async def get_for_profile(session: AsyncSession, profile_id: UUID) -> Household | None:
    return await session.scalar(
        select(Household).where(Household.profile_id == profile_id)
    )


async def create(
    session: AsyncSession,
    *,
    profile_id: UUID,
    name: str = "Household",
    lat: Decimal | None,
    lon: Decimal | None,
    city: str | None,
    timezone: str,
    dwelling: str,
    cooking_fuel: str,
    has_purifier: bool,
    purifier_cadr: int | None,
    room_area_m2: int | None,
    ceiling_m: Decimal | None,
) -> Household:
    household = Household(
        profile_id=profile_id,
        name=name,
        lat=lat,
        lon=lon,
        city=city,
        timezone=timezone,
        dwelling=dwelling,
        cooking_fuel=cooking_fuel,
        has_purifier=has_purifier,
        purifier_cadr=purifier_cadr,
        room_area_m2=room_area_m2,
        ceiling_m=ceiling_m,
    )
    session.add(household)
    await session.flush()
    return household


async def update(
    session: AsyncSession,
    household: Household,
    **values: object,
) -> Household:
    for key, value in values.items():
        setattr(household, key, value)
    household.updated_at = utc_now()
    await session.flush()
    return household


async def list_members(
    session: AsyncSession, household_id: UUID
) -> list[HouseholdMember]:
    statement = (
        select(HouseholdMember)
        .where(HouseholdMember.household_id == household_id)
        .order_by(HouseholdMember.created_at)
    )
    return list((await session.scalars(statement)).all())


async def get_member(
    session: AsyncSession, *, household_id: UUID, member_id: UUID
) -> HouseholdMember | None:
    return await session.scalar(
        select(HouseholdMember).where(
            HouseholdMember.id == member_id,
            HouseholdMember.household_id == household_id,
        )
    )


async def add_member(
    session: AsyncSession,
    *,
    household_id: UUID,
    age_band: str,
    health_flags: list[str],
) -> HouseholdMember:
    member = HouseholdMember(
        household_id=household_id,
        age_band=age_band,
        health_flags=health_flags,
    )
    session.add(member)
    await session.flush()
    return member


async def update_member(
    session: AsyncSession,
    member: HouseholdMember,
    *,
    age_band: str | None,
    health_flags: list[str] | None,
) -> HouseholdMember:
    if age_band is not None:
        member.age_band = age_band
    if health_flags is not None:
        member.health_flags = health_flags
    await session.flush()
    return member


async def delete_member(session: AsyncSession, member: HouseholdMember) -> None:
    await session.delete(member)
    await session.flush()


async def replace_members(
    session: AsyncSession,
    *,
    household_id: UUID,
    members: list[tuple[str, list[str]]],
) -> list[HouseholdMember]:
    """Replace every member row in one transaction.

    Member rows carry no external references, so replacing them keeps the
    household size and age bands consistent with the submitted profile.
    """
    await session.execute(
        delete(HouseholdMember).where(HouseholdMember.household_id == household_id)
    )
    rows = [
        HouseholdMember(
            household_id=household_id,
            age_band=age_band,
            health_flags=health_flags,
        )
        for age_band, health_flags in members
    ]
    session.add_all(rows)
    await session.flush()
    return rows


async def get_preferences(
    session: AsyncSession, household_id: UUID
) -> HouseholdPreference | None:
    return await session.get(HouseholdPreference, household_id)


async def ensure_preferences(
    session: AsyncSession, household_id: UUID
) -> HouseholdPreference:
    preferences = await get_preferences(session, household_id)
    if preferences is None:
        preferences = HouseholdPreference(household_id=household_id)
        session.add(preferences)
        await session.flush()
    return preferences


async def update_preferences(
    session: AsyncSession,
    preferences: HouseholdPreference,
    *,
    locale: str,
    activity_windows: list[dict[str, Any]],
    alert_threshold_aqi: int,
    transport_mode: str,
    notifications_enabled: bool,
    notify_alerts: bool,
    notify_daily_summary: bool,
    quiet_hours_start: str | None,
    quiet_hours_end: str | None,
) -> HouseholdPreference:
    preferences.locale = locale
    preferences.activity_windows = activity_windows
    preferences.alert_threshold_aqi = alert_threshold_aqi
    preferences.transport_mode = transport_mode
    preferences.notifications_enabled = notifications_enabled
    preferences.notify_alerts = notify_alerts
    preferences.notify_daily_summary = notify_daily_summary
    preferences.quiet_hours_start = quiet_hours_start
    preferences.quiet_hours_end = quiet_hours_end
    preferences.updated_at = utc_now()
    await session.flush()
    return preferences


async def list_locations(
    session: AsyncSession, household_id: UUID
) -> list[SavedLocation]:
    statement = (
        select(SavedLocation)
        .where(SavedLocation.household_id == household_id)
        .order_by(SavedLocation.created_at)
    )
    return list((await session.scalars(statement)).all())


async def get_location(
    session: AsyncSession, *, household_id: UUID, location_id: UUID
) -> SavedLocation | None:
    return await session.scalar(
        select(SavedLocation).where(
            SavedLocation.id == location_id,
            SavedLocation.household_id == household_id,
        )
    )


async def find_location_by_label(
    session: AsyncSession, *, household_id: UUID, label: str
) -> SavedLocation | None:
    return await session.scalar(
        select(SavedLocation).where(
            SavedLocation.household_id == household_id,
            SavedLocation.label == label,
        )
    )


async def add_location(
    session: AsyncSession,
    *,
    household_id: UUID,
    label: str,
    kind: str,
    lat: Decimal,
    lon: Decimal,
) -> SavedLocation:
    location = SavedLocation(
        household_id=household_id,
        label=label,
        kind=kind,
        lat=lat,
        lon=lon,
    )
    session.add(location)
    await session.flush()
    return location


async def delete_location(session: AsyncSession, location: SavedLocation) -> None:
    await session.delete(location)
    await session.flush()


async def delete_all_for_profile(session: AsyncSession, profile_id: UUID) -> None:
    household_ids = select(Household.id).where(Household.profile_id == profile_id)
    await session.execute(
        delete(SavedLocation).where(SavedLocation.household_id.in_(household_ids))
    )
    await session.execute(
        delete(HouseholdMember).where(HouseholdMember.household_id.in_(household_ids))
    )
    await session.execute(
        delete(HouseholdPreference).where(
            HouseholdPreference.household_id.in_(household_ids)
        )
    )
    await session.execute(delete(Household).where(Household.profile_id == profile_id))
    await session.flush()


__all__ = [
    "add_location",
    "add_member",
    "create",
    "delete_all_for_profile",
    "delete_location",
    "delete_member",
    "ensure_preferences",
    "find_location_by_label",
    "get_for_profile",
    "get_location",
    "get_member",
    "get_preferences",
    "list_locations",
    "list_members",
    "replace_members",
    "update",
    "update_member",
    "update_preferences",
]
