"""End-to-end persistence proof across every approved entity (§13).

One anonymous profile creates a household, family members, preferences, saved
location, air observation, routine, recommendation and copilot conversation.
Every row is read back, relationship keys are checked, and deleting the session
proves the cascade while the public air cache and privacy audit survive.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import func, select

from app.models.ai import AiConversation, AiMessage
from app.models.air import AirQualitySnapshot
from app.models.household import (
    Household,
    HouseholdMember,
    HouseholdPreference,
    SavedLocation,
)
from app.models.impact import PrivacyEvent, SustainabilityActivity
from app.models.profile import Profile
from app.models.routine import Recommendation, Routine
from app.repositories import (
    air as air_repo,
    conversations as conversations_repo,
    households as households_repo,
    recommendations as recommendations_repo,
    routines as routines_repo,
)

HOUSEHOLD = {
    "lat": 28.6139,
    "lon": 77.209,
    "city": "New Delhi",
    "timezone": "Asia/Kolkata",
    "dwelling": "apartment_upper",
    "cooking_fuel": "lpg",
    "has_purifier": True,
    "purifier_cadr": 300,
    "room_area_m2": 24,
    "ceiling_m": 2.7,
}


async def test_every_entity_persists_and_is_removed_with_the_session(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    me = await db_client.get("/api/v1/sessions/me", headers=auth_headers)
    assert me.status_code == 200, me.text
    profile_id = UUID(me.json()["data"]["profile_id"])

    household_response = await db_client.put(
        "/api/v1/household", headers=auth_headers, json=HOUSEHOLD
    )
    assert household_response.status_code == 200, household_response.text
    household_id = UUID(household_response.json()["data"]["id"])

    member_response = await db_client.post(
        "/api/v1/household/members",
        headers=auth_headers,
        json={"age_band": "6-12", "health_flags": ["asthma"]},
    )
    assert member_response.status_code == 201, member_response.text

    preferences_response = await db_client.put(
        "/api/v1/household/preferences",
        headers=auth_headers,
        json={
            "locale": "en-IN",
            "alert_threshold_aqi": 120,
            "activity_windows": [
                {
                    "id": "morning-walk",
                    "title": "Morning walk",
                    "start": "06:30",
                    "duration_min": 45,
                    "intensity": "moderate",
                    "venue": "outdoor",
                }
            ],
        },
    )
    assert preferences_response.status_code == 200, preferences_response.text

    location_response = await db_client.post(
        "/api/v1/household/locations",
        headers=auth_headers,
        json={"label": "School", "kind": "school", "lat": 28.62, "lon": 77.22},
    )
    assert location_response.status_code == 201, location_response.text

    today = datetime.now(tz=UTC).date().isoformat()
    activity_response = await db_client.post(
        "/api/v1/impact/activities",
        headers=auth_headers,
        json={"activity_type": "walked", "quantity": 4, "occurred_on": today},
    )
    assert activity_response.status_code == 201, activity_response.text

    now = datetime.now(tz=UTC)
    async with db_app.state.database.session() as database_session:
        household = await households_repo.get_for_profile(database_session, profile_id)
        assert household is not None
        assert household.id == household_id

        members = await households_repo.list_members(database_session, household.id)
        assert len(members) == 1
        assert members[0].health_flags == ["asthma"]

        preferences = await households_repo.get_preferences(
            database_session, household.id
        )
        assert preferences is not None
        assert preferences.alert_threshold_aqi == 120
        assert preferences.activity_windows[0]["id"] == "morning-walk"

        locations = await households_repo.list_locations(database_session, household.id)
        assert [row.label for row in locations] == ["School"]

        await air_repo.upsert_snapshot(
            database_session,
            provider="persistence-test",
            lat_key=Decimal("28.61"),
            lon_key=Decimal("77.21"),
            kind="modelled",
            observed_at=now,
            fetched_at=now,
            expires_at=now + timedelta(minutes=30),
            values={"pm2_5": 82.0, "pm10": 140.0},
            us_aqi=165,
            eu_aqi=110,
            raw={"source": "integration-test"},
        )
        await database_session.commit()

        snapshot = await air_repo.latest_snapshot(
            database_session,
            provider="persistence-test",
            lat_key=Decimal("28.61"),
            lon_key=Decimal("77.21"),
            max_age=timedelta(hours=1),
        )
        assert snapshot is not None
        assert snapshot.pm2_5 == 82.0
        assert snapshot.pm10 == 140.0
        assert snapshot.us_aqi == 165

        routine = routines_repo.add(
            database_session,
            household_id=household.id,
            plan_date=now.date(),
            timezone="Asia/Kolkata",
            engine_version="routine-2.0.0",
            inputs_hash="d" * 64,
            plan={"items": []},
            version=1,
            parent_routine_id=None,
            expires_at=now + timedelta(hours=6),
        )
        await database_session.flush()
        recommendation = await recommendations_repo.create(
            database_session,
            household_id=household.id,
            routine_id=routine.id,
            module="routine",
            severity="good",
            title="Walk before 9am",
            body="PM2.5 is forecast to rise after 9am.",
            source="deterministic",
        )
        conversation = await conversations_repo.create_conversation(
            database_session,
            profile_id=profile_id,
            expires_at=now + timedelta(days=7),
            lat_key=Decimal("28.61"),
            lon_key=Decimal("77.21"),
        )
        message = await conversations_repo.add_message(
            database_session,
            conversation_id=conversation.id,
            role="user",
            content="When should I walk today?",
        )
        await database_session.commit()

        routine_id = routine.id
        recommendation_id = recommendation.id
        conversation_id = conversation.id
        message_id = message.id

    async with db_app.state.database.session() as verify_session:
        stored_routine = await routines_repo.get(
            verify_session, household_id=household_id, routine_id=routine_id
        )
        assert stored_routine is not None
        assert stored_routine.plan == {"items": []}

        stored_recommendation = await recommendations_repo.get(
            verify_session,
            household_id=household_id,
            recommendation_id=recommendation_id,
        )
        assert stored_recommendation is not None
        assert stored_recommendation.routine_id == routine_id

        stored_conversation = await conversations_repo.get_conversation(
            verify_session,
            conversation_id=conversation_id,
            profile_id=profile_id,
        )
        assert stored_conversation is not None
        messages = await conversations_repo.list_messages(
            verify_session, conversation_id
        )
        assert [row.id for row in messages] == [message_id]
        assert messages[0].content == "When should I walk today?"

    read_household = await db_client.get("/api/v1/household", headers=auth_headers)
    assert read_household.status_code == 200
    body = read_household.json()["data"]
    assert body["id"] == str(household_id)
    assert len(body["members"]) == 1

    read_preferences = await db_client.get(
        "/api/v1/household/preferences", headers=auth_headers
    )
    assert read_preferences.status_code == 200
    assert read_preferences.json()["data"]["alert_threshold_aqi"] == 120

    read_locations = await db_client.get(
        "/api/v1/household/locations", headers=auth_headers
    )
    assert [row["label"] for row in read_locations.json()["data"]] == ["School"]

    read_activities = await db_client.get(
        "/api/v1/impact/activities", headers=auth_headers
    )
    assert len(read_activities.json()["data"]) == 1

    read_summary = await db_client.get("/api/v1/impact/summary", headers=auth_headers)
    assert read_summary.json()["data"]["activity_count"] == 1

    removed = await db_client.delete("/api/v1/sessions/me", headers=auth_headers)
    assert removed.status_code == 204

    denied = await db_client.get("/api/v1/household", headers=auth_headers)
    assert denied.status_code == 401

    async with db_app.state.database.session() as final_session:
        for model in (
            Profile,
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
            count = await final_session.scalar(select(func.count()).select_from(model))
            assert count == 0, f"{model.__name__} rows survived session deletion"

        assert (
            await final_session.scalar(
                select(func.count())
                .select_from(AirQualitySnapshot)
                .where(AirQualitySnapshot.provider == "persistence-test")
            )
            == 1
        ), "public air-quality cache must not be deleted with a session"

        events = list(
            (
                await final_session.scalars(
                    select(PrivacyEvent).order_by(PrivacyEvent.id)
                )
            ).all()
        )
        assert [event.event for event in events] == ["consent", "delete_all"]
        assert all(event.profile_id is None for event in events)
