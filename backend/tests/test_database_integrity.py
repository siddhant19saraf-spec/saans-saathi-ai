"""Database-level invariants that Pydantic cannot enforce alone.

Every test here talks to PostgreSQL through the ORM with API validation
bypassed, so a failure proves the constraint exists in the database itself.
"""

from __future__ import annotations

import asyncio
import secrets
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.ai import AiConversation, AiMessage
from app.models.air import AirQualitySnapshot
from app.models.household import (
    Household,
    HouseholdMember,
    HouseholdPreference,
    SavedLocation,
)
from app.models.impact import PrivacyEvent, SustainabilityActivity, UsageDaily
from app.models.profile import Profile
from app.models.routine import Recommendation, Routine
from app.repositories import (
    air as air_repo,
    conversations as conversations_repo,
    impact as impact_repo,
    recommendations as recommendations_repo,
)


def _profile_values(**overrides: Any) -> dict[str, Any]:
    now = datetime.now(tz=UTC)
    values: dict[str, Any] = {
        "token_hash": secrets.token_bytes(32),
        "consent_version": "2026-11-test",
        "expires_at": now + timedelta(days=90),
    }
    values.update(overrides)
    return values


async def _profile(session: AsyncSession) -> Profile:
    profile = Profile(**_profile_values())
    session.add(profile)
    await session.flush()
    return profile


async def _household(session: AsyncSession, profile_id: Any) -> Household:
    household = Household(
        profile_id=profile_id,
        timezone="Asia/Kolkata",
        dwelling="apartment_upper",
        cooking_fuel="lpg",
    )
    session.add(household)
    await session.flush()
    return household


async def _activity(
    session: AsyncSession, household_id: Any, **overrides: Any
) -> SustainabilityActivity:
    values: dict[str, Any] = {
        "household_id": household_id,
        "activity_type": "walked",
        "occurred_on": datetime.now(tz=UTC).date(),
        "quantity": Decimal("5.000"),
        "unit": "km",
        "co2e_kg": Decimal("0.0000"),
        "factor_key": "walking_avoided_car",
        "factor_value": Decimal("0.000000"),
        "factor_unit": "kg_co2e/km",
        "factor_version": "IPCC-2006",
        "factor_source_url": "https://example.com/factor",
    }
    values.update(overrides)
    activity = SustainabilityActivity(**values)
    session.add(activity)
    await session.flush()
    return activity


@pytest.fixture
async def session(db_app: FastAPI) -> AsyncIterator[AsyncSession]:
    async with db_app.state.database.session() as database_session:
        yield database_session


async def test_foreign_key_violation_is_rejected(session: AsyncSession) -> None:
    conversation = AiConversation(
        profile_id=uuid4(), expires_at=datetime.now(tz=UTC) + timedelta(days=1)
    )
    session.add(conversation)

    with pytest.raises(IntegrityError, match="fk_ai_conversations_profile_id_profiles"):
        await session.flush()
    await session.rollback()


async def test_expiry_must_follow_creation(session: AsyncSession) -> None:
    session.add(
        Profile(
            token_hash=secrets.token_bytes(32),
            consent_version="2026-11-test",
            expires_at=datetime.now(tz=UTC) - timedelta(days=1),
        )
    )

    with pytest.raises(IntegrityError, match="ck_profiles_expiry_after_created"):
        await session.flush()
    await session.rollback()


async def test_unique_session_token_hash_is_enforced(session: AsyncSession) -> None:
    first = await _profile(session)
    await session.commit()

    session.add(
        Profile(
            token_hash=first.token_hash,
            consent_version="2026-11-test",
            expires_at=datetime.now(tz=UTC) + timedelta(days=90),
        )
    )
    with pytest.raises(IntegrityError, match="uq_profiles_token_hash"):
        await session.flush()
    await session.rollback()


async def test_invalid_coordinates_are_rejected(session: AsyncSession) -> None:
    profile = await _profile(session)
    household = await _household(session, profile.id)
    await session.commit()

    location = SavedLocation(
        household_id=household.id,
        label="Out of range",
        kind="home",
        lat=Decimal("91.000"),
        lon=Decimal("77.000"),
    )
    session.add(location)

    with pytest.raises(IntegrityError, match="ck_saved_locations_lat_range"):
        await session.flush()
    await session.rollback()


async def test_negative_measurements_are_rejected(session: AsyncSession) -> None:
    now = datetime.now(tz=UTC)
    snapshot = AirQualitySnapshot(
        provider="integrity-test",
        lat_key=Decimal("28.61"),
        lon_key=Decimal("77.21"),
        kind="modelled",
        observed_at=now,
        fetched_at=now,
        expires_at=now + timedelta(minutes=30),
        pm2_5=-1.0,
    )
    session.add(snapshot)

    with pytest.raises(
        IntegrityError, match="ck_air_quality_snapshots_pollutants_non_negative"
    ):
        await session.flush()
    await session.rollback()


async def test_invalid_activity_unit_is_rejected(session: AsyncSession) -> None:
    profile = await _profile(session)
    household = await _household(session, profile.id)
    await session.commit()

    with pytest.raises(
        IntegrityError, match="ck_sustainability_activities_unit_allowed"
    ):
        await _activity(session, household.id, unit="miles")
    await session.rollback()


async def test_blank_location_label_is_rejected(session: AsyncSession) -> None:
    profile = await _profile(session)
    household = await _household(session, profile.id)
    await session.commit()

    session.add(
        SavedLocation(
            household_id=household.id,
            label="   ",
            kind="other",
            lat=Decimal("28.610"),
            lon=Decimal("77.210"),
        )
    )

    with pytest.raises(IntegrityError, match="ck_saved_locations_label_present"):
        await session.flush()
    await session.rollback()


async def test_negative_token_usage_is_rejected(session: AsyncSession) -> None:
    profile = await _profile(session)
    conversation = await conversations_repo.create_conversation(
        session,
        profile_id=profile.id,
        expires_at=datetime.now(tz=UTC) + timedelta(days=1),
        lat_key=None,
        lon_key=None,
    )
    await session.commit()

    with pytest.raises(
        IntegrityError, match="ck_ai_messages_input_tokens_non_negative"
    ):
        await conversations_repo.add_message(
            session,
            conversation_id=conversation.id,
            role="assistant",
            content="answer",
            input_tokens=-1,
        )
    await session.rollback()


async def test_profile_delete_cascades_and_keeps_audit_event(
    session: AsyncSession,
) -> None:
    profile = await _profile(session)
    household = await _household(session, profile.id)
    member = HouseholdMember(household_id=household.id, age_band="18-59")
    preference = HouseholdPreference(household_id=household.id)
    location = SavedLocation(
        household_id=household.id,
        label="Home",
        kind="home",
        lat=Decimal("28.610"),
        lon=Decimal("77.210"),
    )
    routine = Routine(
        household_id=household.id,
        plan_date=date(2026, 11, 19),
        timezone="Asia/Kolkata",
        engine_version="routine-1.0.0",
        inputs_hash="a" * 64,
        plan={},
        expires_at=datetime.now(tz=UTC) + timedelta(days=1),
    )
    session.add_all([member, preference, location, routine])
    await session.flush()

    recommendation = Recommendation(
        household_id=household.id,
        routine_id=routine.id,
        module="routine",
        severity="good",
        title="Walk early",
        body="Air is cleaner before 9am.",
        source="deterministic",
    )
    conversation = await conversations_repo.create_conversation(
        session,
        profile_id=profile.id,
        expires_at=datetime.now(tz=UTC) + timedelta(days=1),
        lat_key=None,
        lon_key=None,
    )
    message = AiMessage(
        conversation_id=conversation.id, role="user", content="When should I walk?"
    )
    audit = PrivacyEvent(profile_id=profile.id, event="consent")
    await _activity(session, household.id)
    session.add_all([recommendation, message, audit])
    await session.commit()

    await session.delete(profile)
    await session.commit()
    # The audit row is updated by the database (ON DELETE SET NULL), so drop
    # the cached instance before asserting on it.
    session.expire_all()

    for model in (
        Household,
        HouseholdMember,
        HouseholdPreference,
        SavedLocation,
        Routine,
        Recommendation,
        SustainabilityActivity,
        AiConversation,
        AiMessage,
    ):
        count = await session.scalar(select(func.count()).select_from(model))
        assert count == 0, f"{model.__name__} rows survived profile deletion"

    events = list((await session.scalars(select(PrivacyEvent))).all())
    assert len(events) == 1
    assert events[0].event == "consent"
    assert events[0].profile_id is None


async def test_routine_delete_sets_recommendation_link_to_null(
    session: AsyncSession,
) -> None:
    profile = await _profile(session)
    household = await _household(session, profile.id)
    routine = Routine(
        household_id=household.id,
        plan_date=date(2026, 11, 19),
        timezone="Asia/Kolkata",
        engine_version="routine-1.0.0",
        inputs_hash="b" * 64,
        plan={},
        expires_at=datetime.now(tz=UTC) + timedelta(days=1),
    )
    session.add(routine)
    await session.flush()
    recommendation = Recommendation(
        household_id=household.id,
        routine_id=routine.id,
        module="routine",
        severity="good",
        title="Walk early",
        body="Air is cleaner before 9am.",
        source="deterministic",
    )
    session.add(recommendation)
    await session.commit()
    recommendation_id = recommendation.id

    await session.delete(routine)
    await session.commit()

    stored = await session.get(Recommendation, recommendation_id)
    assert stored is not None
    await session.refresh(stored)
    assert stored.routine_id is None


async def test_transaction_rollback_discards_all_writes(
    session: AsyncSession,
) -> None:
    profile = await _profile(session)
    await _household(session, profile.id)
    await session.flush()

    await session.rollback()

    for model in (Profile, Household):
        count = await session.scalar(select(func.count()).select_from(model))
        assert count == 0


async def test_activity_pagination_uses_stable_offset(
    session: AsyncSession,
) -> None:
    profile = await _profile(session)
    household = await _household(session, profile.id)
    await session.commit()

    today = datetime.now(tz=UTC).date()
    for offset in range(5):
        await _activity(
            session,
            household.id,
            occurred_on=today - timedelta(days=offset),
        )
    await session.commit()

    first_page = await impact_repo.list_activities(
        session, household_id=household.id, since=today - timedelta(days=30), limit=2
    )
    second_page = await impact_repo.list_activities(
        session,
        household_id=household.id,
        since=today - timedelta(days=30),
        limit=2,
        offset=2,
    )

    assert [row.occurred_on for row in first_page] == [today, today - timedelta(days=1)]
    assert [row.occurred_on for row in second_page] == [
        today - timedelta(days=2),
        today - timedelta(days=3),
    ]


async def test_expired_conversation_is_not_readable(
    session: AsyncSession,
) -> None:
    profile = await _profile(session)
    now = datetime.now(tz=UTC)
    conversation = await conversations_repo.create_conversation(
        session,
        profile_id=profile.id,
        expires_at=now + timedelta(seconds=5),
        lat_key=None,
        lon_key=None,
    )
    await session.commit()

    assert (
        await conversations_repo.get_conversation(
            session,
            conversation_id=conversation.id,
            profile_id=profile.id,
            now=now,
        )
        is not None
    )
    later = now + timedelta(seconds=10)
    assert (
        await conversations_repo.get_conversation(
            session,
            conversation_id=conversation.id,
            profile_id=profile.id,
            now=later,
        )
        is None
    )
    assert (
        await conversations_repo.latest_conversation(session, profile.id, now=later)
        is None
    )


async def test_recommendations_repository_filters_and_dismisses(
    session: AsyncSession,
) -> None:
    profile = await _profile(session)
    household = await _household(session, profile.id)
    await session.commit()

    air = await recommendations_repo.create(
        session,
        household_id=household.id,
        module="air",
        severity="moderate",
        title="Ventilate",
        body="Open windows after 10am.",
        source="deterministic",
    )
    family = await recommendations_repo.create(
        session,
        household_id=household.id,
        module="family",
        severity="info",
        title="Carry water",
        body="Keep children hydrated.",
        source="deterministic",
    )
    dismissed = await recommendations_repo.create(
        session,
        household_id=household.id,
        module="air",
        severity="info",
        title="Old tip",
        body="This was dismissed.",
        source="deterministic",
    )
    await recommendations_repo.dismiss(
        session, dismissed, now=datetime.now(tz=UTC) + timedelta(seconds=1)
    )
    await session.commit()

    visible = await recommendations_repo.list_for_household(
        session, household_id=household.id, limit=10
    )
    assert {row.id for row in visible} == {air.id, family.id}

    all_rows = await recommendations_repo.list_for_household(
        session, household_id=household.id, limit=10, include_dismissed=True
    )
    assert len(all_rows) == 3

    air_only = await recommendations_repo.list_for_household(
        session, household_id=household.id, limit=10, module="air"
    )
    assert [row.id for row in air_only] == [air.id]

    assert (
        await recommendations_repo.get(
            session, household_id=uuid4(), recommendation_id=air.id
        )
        is None
    )


async def test_daily_budget_is_atomic_under_concurrency(db_app: FastAPI) -> None:
    factory = db_app.state.database.session_factory
    assert isinstance(factory, async_sessionmaker)
    key = "integrity-concurrency"
    day = datetime.now(tz=UTC).date()

    async def attempt() -> bool:
        async with factory() as concurrent_session:
            allowed = await air_repo.consume_budget(
                concurrent_session, key=key, budget=5, day=day
            )
            await concurrent_session.commit()
            return allowed

    results = await asyncio.gather(*(attempt() for _ in range(8)))

    assert sum(1 for allowed in results if allowed) == 5
    async with factory() as check_session:
        stored = await check_session.scalar(
            select(UsageDaily.requests).where(
                UsageDaily.day == day, UsageDaily.key == key
            )
        )
        assert stored == 5


async def test_duplicate_snapshot_insert_keeps_one_row(db_app: FastAPI) -> None:
    factory = db_app.state.database.session_factory
    assert isinstance(factory, async_sessionmaker)
    now = datetime.now(tz=UTC)

    def values() -> dict[str, Any]:
        return {
            "provider": "integrity-concurrency",
            "lat_key": Decimal("28.61"),
            "lon_key": Decimal("77.21"),
            "kind": "modelled",
            "observed_at": now,
            "fetched_at": now,
            "expires_at": now + timedelta(minutes=30),
            "pm2_5": 42.0,
        }

    async def insert() -> IntegrityError | None:
        async with factory() as concurrent_session:
            concurrent_session.add(AirQualitySnapshot(**values()))
            try:
                await concurrent_session.commit()
            except IntegrityError as exc:
                await concurrent_session.rollback()
                return exc
            return None

    outcomes = await asyncio.gather(insert(), insert())

    assert sum(1 for outcome in outcomes if outcome is None) == 1
    async with factory() as check_session:
        count = await check_session.scalar(
            select(func.count()).select_from(AirQualitySnapshot)
        )
        assert count == 1
