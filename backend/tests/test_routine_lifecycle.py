"""SmartRoutine activity preferences and plan lifecycle.

These tests exercise the write paths that the happy-path suite does not:
validation errors, preference updates, replanning, manual changes and the
version chain. Every assertion is against the public API contract.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from httpx import AsyncClient

HOUSEHOLD = {
    "lat": 28.6139,
    "lon": 77.209,
    "timezone": "Asia/Kolkata",
    "dwelling": "apartment_upper",
    "cooking_fuel": "lpg",
}

ACTIVITY = {
    "title": "Morning walk",
    "category": "morning_walk",
    "preferred_start": "06:30",
    "duration_min": 60,
    "intensity": "light",
    "venue": "outdoor",
}


def _local_midnight() -> datetime:
    now = datetime.now(tz=ZoneInfo("Asia/Kolkata"))
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


async def _household(client: AsyncClient, headers: dict[str, str]) -> None:
    response = await client.put("/api/v1/household", headers=headers, json=HOUSEHOLD)
    assert response.status_code == 200, response.text


async def _member(client: AsyncClient, headers: dict[str, str]) -> str:
    response = await client.post(
        "/api/v1/household/members",
        headers=headers,
        json={"age_band": "18-59", "health_flags": []},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


async def _activity(
    client: AsyncClient, headers: dict[str, str], **overrides: object
) -> dict[str, object]:
    response = await client.post(
        "/api/v1/routines/activities",
        headers=headers,
        json={**ACTIVITY, **overrides},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


async def _prepare_plan(
    app: FastAPI,
    client: AsyncClient,
    headers: dict[str, str],
    provider: Callable[..., object],
    forecast: Callable[..., object],
) -> tuple[dict[str, object], str]:
    await _household(client, headers)
    await _member(client, headers)
    activity = await _activity(client, headers)
    app.state.air_provider = provider(
        forecast=forecast(start=_local_midnight(), hours=48)
    )
    today = _local_midnight().date().isoformat()
    generated = await client.post(
        "/api/v1/routines/generate", headers=headers, json={"date": today}
    )
    assert generated.status_code == 200, generated.text
    return generated.json()["data"], today


async def test_activities_before_a_household_exists(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    listed = await db_client.get("/api/v1/routines/activities", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()["data"]["items"] == []

    created = await db_client.post(
        "/api/v1/routines/activities", headers=auth_headers, json=ACTIVITY
    )
    assert created.status_code == 422
    assert created.json()["code"] == "NO_HOUSEHOLD"

    missing = uuid4()
    updated = await db_client.put(
        f"/api/v1/routines/activities/{missing}",
        headers=auth_headers,
        json={"duration_min": 30},
    )
    deleted = await db_client.delete(
        f"/api/v1/routines/activities/{missing}", headers=auth_headers
    )
    assert updated.status_code == 404
    assert deleted.status_code == 404


async def test_activities_require_household_coordinates(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await db_client.put(
        "/api/v1/household",
        headers=auth_headers,
        json={**HOUSEHOLD, "lat": None, "lon": None},
    )
    assert response.status_code == 200, response.text

    created = await db_client.post(
        "/api/v1/routines/activities", headers=auth_headers, json=ACTIVITY
    )

    assert created.status_code == 422
    assert created.json()["code"] == "NO_LOCATION"


async def test_activity_validation_rejects_invalid_windows_and_venues(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _household(db_client, auth_headers)

    cases = [
        (
            {"category": "indoor_exercise", "venue": "outdoor"},
            "VALIDATION_ERROR",
        ),
        (
            {"category": "morning_walk", "venue": "indoor"},
            "VALIDATION_ERROR",
        ),
        (
            {"preferred_start": "07:00", "earliest_start": "08:00"},
            "VALIDATION_ERROR",
        ),
        (
            {"preferred_start": "04:30", "earliest_start": "04:30"},
            "VALIDATION_ERROR",
        ),
        (
            {"preferred_start": "21:30", "latest_start": "22:30"},
            "VALIDATION_ERROR",
        ),
        (
            {"preferred_start": "21:30", "duration_min": 60},
            "VALIDATION_ERROR",
        ),
    ]
    for overrides, code in cases:
        response = await db_client.post(
            "/api/v1/routines/activities",
            headers=auth_headers,
            json={**ACTIVITY, **overrides},
        )
        assert response.status_code == 422, (overrides, response.text)
        assert response.json()["code"] == code, overrides

    unknown_member = await db_client.post(
        "/api/v1/routines/activities",
        headers=auth_headers,
        json={**ACTIVITY, "member_ids": [str(uuid4())]},
    )
    assert unknown_member.status_code == 422
    assert unknown_member.json()["code"] == "UNKNOWN_MEMBER"


async def test_activity_preferences_can_be_updated_cleared_and_deactivated(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _household(db_client, auth_headers)
    member_id = await _member(db_client, auth_headers)
    created = await _activity(
        db_client,
        auth_headers,
        preferred_start="07:00",
        earliest_start="06:30",
        latest_start="08:00",
        notes="Prefer the park",
        location={"label": "Park", "lat": 28.61, "lon": 77.2},
        member_ids=[member_id],
    )

    # A partial update is validated after merging with the stored preference,
    # so a window or venue conflict introduced by one field is rejected.
    broken_window = await db_client.put(
        f"/api/v1/routines/activities/{created['id']}",
        headers=auth_headers,
        json={"preferred_start": "08:30"},
    )
    assert broken_window.status_code == 422
    assert broken_window.json()["code"] == "INVALID_WINDOW"

    broken_venue = await db_client.put(
        f"/api/v1/routines/activities/{created['id']}",
        headers=auth_headers,
        json={"category": "indoor_exercise"},
    )
    assert broken_venue.status_code == 422
    assert broken_venue.json()["code"] == "INVALID_VENUE"

    updated = await db_client.put(
        f"/api/v1/routines/activities/{created['id']}",
        headers=auth_headers,
        json={
            "duration_min": 30,
            "earliest_start": None,
            "latest_start": None,
            "notes": None,
            "location": None,
        },
    )
    assert updated.status_code == 200, updated.text
    data = updated.json()["data"]
    assert data["duration_min"] == 30
    assert data["earliest_start"] is None
    assert data["latest_start"] is None
    assert data["notes"] is None
    assert data["location"] is None
    assert data["member_ids"] == [member_id]

    deactivated = await db_client.put(
        f"/api/v1/routines/activities/{created['id']}",
        headers=auth_headers,
        json={"active": False},
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["data"]["active"] is False

    listed = await db_client.get("/api/v1/routines/activities", headers=auth_headers)
    assert listed.json()["data"]["items"] == []

    deleted = await db_client.delete(
        f"/api/v1/routines/activities/{created['id']}", headers=auth_headers
    )
    assert deleted.status_code == 204
    again = await db_client.delete(
        f"/api/v1/routines/activities/{created['id']}", headers=auth_headers
    )
    # Deleting is idempotent: an already inactive preference stays inactive.
    assert again.status_code == 204


async def test_fixed_activities_must_not_overlap(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _household(db_client, auth_headers)
    await _activity(
        db_client,
        auth_headers,
        title="School drop",
        category="school_travel",
        fixed=True,
        preferred_start="06:00",
        duration_min=60,
    )

    overlapping = await db_client.post(
        "/api/v1/routines/activities",
        headers=auth_headers,
        json={
            **ACTIVITY,
            "title": "Second fixed",
            "fixed": True,
            "preferred_start": "06:30",
        },
    )
    assert overlapping.status_code == 422
    assert overlapping.json()["code"] == "FIXED_ACTIVITY_OVERLAP"

    flexible = await _activity(
        db_client,
        auth_headers,
        title="Flexible",
        preferred_start="07:30",
        duration_min=30,
    )
    promoted = await db_client.put(
        f"/api/v1/routines/activities/{flexible['id']}",
        headers=auth_headers,
        json={"fixed": True, "preferred_start": "06:30"},
    )
    assert promoted.status_code == 422
    assert promoted.json()["code"] == "FIXED_ACTIVITY_OVERLAP"


async def test_at_most_twenty_active_activities(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _household(db_client, auth_headers)
    for index in range(20):
        minute = (index * 15) % 60
        hour = 5 + (index * 15) // 60
        payload = {
            **ACTIVITY,
            "title": f"Activity {index}",
            "category": "school_travel",
            "preferred_start": f"{hour:02d}:{minute:02d}",
            "duration_min": 15,
        }
        response = await db_client.post(
            "/api/v1/routines/activities", headers=auth_headers, json=payload
        )
        assert response.status_code == 201, response.text

    overflow = await db_client.post(
        "/api/v1/routines/activities", headers=auth_headers, json=ACTIVITY
    )
    assert overflow.status_code == 422
    assert overflow.json()["code"] == "TOO_MANY_ACTIVITIES"


async def test_plan_read_history_replan_and_manual_change(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    forecast_factory: Callable[..., object],
) -> None:
    plan, today = await _prepare_plan(
        db_app, db_client, auth_headers, fake_provider, forecast_factory
    )
    routine_id = str(plan["id"])
    activity_id = str(plan["blocks"][0]["activity_id"])

    by_id = await db_client.get(
        f"/api/v1/routines/{routine_id}", headers=auth_headers
    )
    assert by_id.status_code == 200
    assert by_id.json()["data"]["id"] == plan["id"]

    by_date = await db_client.get(
        "/api/v1/routines", headers=auth_headers, params={"date": today}
    )
    assert by_date.status_code == 200

    history = await db_client.get(
        "/api/v1/routines/history", headers=auth_headers, params={"date": today}
    )
    assert history.status_code == 200
    assert history.json()["data"]["total"] == 1
    assert history.json()["data"]["items"][0]["version"] == 1

    mismatch = await db_client.post(
        f"/api/v1/routines/{routine_id}/replan",
        headers=auth_headers,
        json={"date": (_local_midnight() + timedelta(days=1)).date().isoformat()},
    )
    assert mismatch.status_code == 422
    assert mismatch.json()["code"] == "DATE_MISMATCH"

    replanned = await db_client.post(
        f"/api/v1/routines/{routine_id}/replan", headers=auth_headers, json={}
    )
    assert replanned.status_code == 200, replanned.text
    new_plan = replanned.json()["data"]
    assert new_plan["version"] == 2
    assert new_plan["parent_routine_id"] == plan["id"]

    stale = await db_client.post(
        f"/api/v1/routines/{routine_id}/replan", headers=auth_headers, json={}
    )
    assert stale.status_code == 409
    assert stale.json()["code"] == "ROUTINE_SUPERSEDED"

    changed = await db_client.put(
        f"/api/v1/routines/{new_plan['id']}/activities/{activity_id}",
        headers=auth_headers,
        json={"preferred_start": "07:00", "duration_min": 45},
    )
    assert changed.status_code == 200, changed.text
    changed_plan = changed.json()["data"]
    assert changed_plan["version"] == 3
    block = next(
        item
        for item in changed_plan["blocks"]
        if str(item["activity_id"]) == activity_id
    )
    assert block["override"] is True
    assert block["status"] == "overridden"

    missing_item = await db_client.patch(
        f"/api/v1/routines/{changed_plan['id']}/items/not-a-block",
        headers=auth_headers,
        json={"status": "done"},
    )
    assert missing_item.status_code == 404

    done = await db_client.patch(
        f"/api/v1/routines/{changed_plan['id']}/items/{block['id']}",
        headers=auth_headers,
        json={"status": "done"},
    )
    assert done.status_code == 200
    assert done.json()["data"]["blocks"][0]["status"] == "done"

    # Keep one active activity so cancelling this one can regenerate a plan.
    await _activity(
        db_client,
        auth_headers,
        title="Evening walk",
        preferred_start="18:00",
        duration_min=30,
    )
    cancelled = await db_client.put(
        f"/api/v1/routines/{changed_plan['id']}/activities/{activity_id}",
        headers=auth_headers,
        json={"cancel": True},
    )
    assert cancelled.status_code == 200, cancelled.text
    assert [item["title"] for item in cancelled.json()["data"]["blocks"]] == [
        "Evening walk"
    ]

    remaining = await db_client.get(
        "/api/v1/routines/activities", headers=auth_headers
    )
    assert [item["title"] for item in remaining.json()["data"]["items"]] == [
        "Evening walk"
    ]

    unknown_activity = await db_client.put(
        f"/api/v1/routines/{cancelled.json()['data']['id']}/activities/{uuid4()}",
        headers=auth_headers,
        json={"duration_min": 30},
    )
    assert unknown_activity.status_code == 404

    missing_routine = await db_client.post(
        f"/api/v1/routines/{uuid4()}/replan", headers=auth_headers, json={}
    )
    assert missing_routine.status_code == 404


async def test_plan_reads_without_a_household_are_404(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    today = _local_midnight().date().isoformat()

    read = await db_client.get(
        "/api/v1/routines", headers=auth_headers, params={"date": today}
    )
    history = await db_client.get("/api/v1/routines/history", headers=auth_headers)
    replan = await db_client.post(
        f"/api/v1/routines/{uuid4()}/replan", headers=auth_headers, json={}
    )

    assert read.status_code == 404
    assert history.status_code == 404
    assert replan.status_code == 404
