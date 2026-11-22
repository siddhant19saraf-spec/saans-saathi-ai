"""Household, member, preference and saved-location operations."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ConsentRequiredError,
    NotFoundError,
)
from app.models.household import Household, HouseholdMember, HouseholdPreference
from app.models.profile import Profile
from app.repositories import households as repo
from app.schemas.household import (
    ActivityWindow,
    Household as HouseholdOut,
    HouseholdUpsert,
    Member,
    MemberCreate,
    MemberUpdate,
    Preferences,
    PreferencesResponse,
)
from app.schemas.locations import SavedLocation, SavedLocationCreate


def _decimal(value: float | None, digits: str = "0.001") -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal(digits))


def _member(member: HouseholdMember) -> Member:
    return Member(
        id=member.id,
        age_band=member.age_band,
        health_flags=member.health_flags,
        created_at=member.created_at,
    )


async def _output(session: AsyncSession, household: Household) -> HouseholdOut:
    members = await repo.list_members(session, household.id)
    return HouseholdOut(
        id=household.id,
        name=household.name,
        lat=float(household.lat) if household.lat is not None else None,
        lon=float(household.lon) if household.lon is not None else None,
        city=household.city,
        timezone=household.timezone,
        dwelling=household.dwelling,
        cooking_fuel=household.cooking_fuel,
        has_purifier=household.has_purifier,
        purifier_cadr=household.purifier_cadr,
        room_area_m2=household.room_area_m2,
        ceiling_m=(
            float(household.ceiling_m) if household.ceiling_m is not None else None
        ),
        members=[_member(member) for member in members],
        created_at=household.created_at,
        updated_at=household.updated_at,
    )


async def get(session: AsyncSession, profile: Profile) -> HouseholdOut:
    household = await repo.get_for_profile(session, profile.id)
    if household is None:
        raise NotFoundError("No household profile exists for this session.")
    return await _output(session, household)


async def require_household(session: AsyncSession, profile: Profile) -> Household:
    household = await repo.get_for_profile(session, profile.id)
    if household is None:
        raise ConflictError("Create a household profile before using this feature.")
    return household


async def upsert(
    session: AsyncSession, profile: Profile, payload: HouseholdUpsert
) -> HouseholdOut:
    values: dict[str, Any] = {
        "name": payload.name,
        "lat": _decimal(payload.lat),
        "lon": _decimal(payload.lon),
        "city": payload.city,
        "timezone": payload.timezone,
        "dwelling": payload.dwelling,
        "cooking_fuel": payload.cooking_fuel,
        "has_purifier": payload.has_purifier,
        "purifier_cadr": payload.purifier_cadr,
        "room_area_m2": payload.room_area_m2,
        "ceiling_m": _decimal(payload.ceiling_m, "0.01"),
    }
    household = await repo.get_for_profile(session, profile.id)
    if household is None:
        household = await repo.create(session, profile_id=profile.id, **values)
    else:
        household = await repo.update(session, household, **values)
    await repo.ensure_preferences(session, household.id)
    await session.commit()
    return await _output(session, household)


async def add_member(
    session: AsyncSession,
    profile: Profile,
    *,
    household: Household,
    payload: MemberCreate,
) -> Member:
    if payload.health_flags and profile.health_consent_at is None:
        raise ConsentRequiredError()
    member = await repo.add_member(
        session,
        household_id=household.id,
        age_band=payload.age_band,
        health_flags=list(payload.health_flags),
    )
    await session.commit()
    return _member(member)


async def update_member(
    session: AsyncSession,
    profile: Profile,
    *,
    household: Household,
    member_id: UUID,
    payload: MemberUpdate,
) -> Member:
    if payload.health_flags and profile.health_consent_at is None:
        raise ConsentRequiredError()
    member = await repo.get_member(
        session, household_id=household.id, member_id=member_id
    )
    if member is None:
        raise NotFoundError("Household member not found.")
    member = await repo.update_member(
        session,
        member,
        age_band=payload.age_band,
        health_flags=(
            list(payload.health_flags) if payload.health_flags is not None else None
        ),
    )
    await session.commit()
    return _member(member)


async def delete_member(
    session: AsyncSession,
    *,
    household: Household,
    member_id: UUID,
) -> None:
    member = await repo.get_member(
        session, household_id=household.id, member_id=member_id
    )
    if member is None:
        raise NotFoundError("Household member not found.")
    await repo.delete_member(session, member)
    await session.commit()


def _preferences(
    household_id: UUID, preferences: HouseholdPreference
) -> PreferencesResponse:
    return PreferencesResponse(
        household_id=household_id,
        locale=preferences.locale,
        activity_windows=[
            ActivityWindow.model_validate(window)
            for window in preferences.activity_windows
        ],
        alert_threshold_aqi=preferences.alert_threshold_aqi,
        transport_mode=preferences.transport_mode,
        notifications_enabled=preferences.notifications_enabled,
        notify_alerts=preferences.notify_alerts,
        notify_daily_summary=preferences.notify_daily_summary,
        quiet_hours_start=preferences.quiet_hours_start,
        quiet_hours_end=preferences.quiet_hours_end,
        created_at=preferences.created_at,
        updated_at=preferences.updated_at,
    )


async def get_preferences(
    session: AsyncSession, profile: Profile
) -> PreferencesResponse:
    household = await require_household(session, profile)
    preferences = await repo.get_preferences(session, household.id)
    if preferences is None:
        raise NotFoundError("No preferences exist for this household yet.")
    return _preferences(household.id, preferences)


async def update_preferences(
    session: AsyncSession, profile: Profile, payload: Preferences
) -> PreferencesResponse:
    household = await require_household(session, profile)
    preferences = await repo.ensure_preferences(session, household.id)
    preferences = await repo.update_preferences(
        session,
        preferences,
        locale=payload.locale,
        activity_windows=[
            window.model_dump(mode="json") for window in payload.activity_windows
        ],
        alert_threshold_aqi=payload.alert_threshold_aqi,
        transport_mode=payload.transport_mode,
        notifications_enabled=payload.notifications_enabled,
        notify_alerts=payload.notify_alerts,
        notify_daily_summary=payload.notify_daily_summary,
        quiet_hours_start=payload.quiet_hours_start,
        quiet_hours_end=payload.quiet_hours_end,
    )
    await session.commit()
    return _preferences(household.id, preferences)


def _location(location: Any) -> SavedLocation:
    return SavedLocation(
        id=location.id,
        label=location.label,
        kind=location.kind,
        lat=float(location.lat),
        lon=float(location.lon),
        created_at=location.created_at,
    )


async def list_locations(
    session: AsyncSession, profile: Profile
) -> list[SavedLocation]:
    household = await require_household(session, profile)
    return [
        _location(item) for item in await repo.list_locations(session, household.id)
    ]


async def add_location(
    session: AsyncSession, profile: Profile, payload: SavedLocationCreate
) -> SavedLocation:
    household = await require_household(session, profile)
    existing = await repo.find_location_by_label(
        session, household_id=household.id, label=payload.label
    )
    if existing is not None:
        raise ConflictError("A saved location with this label already exists.")
    try:
        location = await repo.add_location(
            session,
            household_id=household.id,
            label=payload.label,
            kind=payload.kind,
            lat=_decimal(payload.lat) or Decimal("0"),
            lon=_decimal(payload.lon) or Decimal("0"),
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("A saved location with this label already exists.") from exc
    return _location(location)


async def delete_location(
    session: AsyncSession, profile: Profile, location_id: UUID
) -> None:
    household = await require_household(session, profile)
    location = await repo.get_location(
        session, household_id=household.id, location_id=location_id
    )
    if location is None:
        raise NotFoundError("Saved location not found.")
    await repo.delete_location(session, location)
    await session.commit()
