from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
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


async def _prepare_household(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    with_member: bool = True,
    with_activity: bool = True,
) -> None:
    response = await client.put("/api/v1/household", headers=headers, json=HOUSEHOLD)
    assert response.status_code == 200, response.text
    if with_member:
        member = await client.post(
            "/api/v1/household/members",
            headers=headers,
            json={"age_band": "6-12", "health_flags": []},
        )
        assert member.status_code == 201, member.text
    if with_activity:
        activity = await client.post(
            "/api/v1/routines/activities",
            headers=headers,
            json=ACTIVITY,
        )
        assert activity.status_code == 201, activity.text


async def test_generate_requires_a_household(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await db_client.post(
        "/api/v1/routines/generate", headers=auth_headers, json={}
    )

    assert response.status_code == 422
    assert response.json()["code"] == "NO_HOUSEHOLD"


async def test_generate_requires_members_and_activities(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _prepare_household(
        db_client, auth_headers, with_member=False, with_activity=False
    )

    no_members = await db_client.post(
        "/api/v1/routines/generate", headers=auth_headers, json={}
    )
    assert no_members.status_code == 422
    assert no_members.json()["code"] == "NO_MEMBERS"

    member = await db_client.post(
        "/api/v1/household/members",
        headers=auth_headers,
        json={"age_band": "18-59", "health_flags": []},
    )
    assert member.status_code == 201

    no_activities = await db_client.post(
        "/api/v1/routines/generate", headers=auth_headers, json={}
    )
    assert no_activities.status_code == 422
    assert no_activities.json()["code"] == "NO_ACTIVITIES"


async def test_generate_persists_a_deterministic_plan(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    forecast_factory: Callable[..., object],
) -> None:
    await _prepare_household(db_client, auth_headers)
    db_app.state.air_provider = fake_provider(
        forecast=forecast_factory(start=_local_midnight(), hours=48, pm2_5=60.0)
    )
    today = _local_midnight().date().isoformat()

    generated = await db_client.post(
        "/api/v1/routines/generate", headers=auth_headers, json={"date": today}
    )

    assert generated.status_code == 200, generated.text
    plan = generated.json()["data"]
    assert plan["engine_version"] == "routine-2.0.0"
    assert plan["date"] == today
    assert plan["data_status"]["forecast"]["provider"] == "fake"
    assert plan["data_status"]["forecast"]["available"] is True
    assert len(plan["blocks"]) == 1
    block = plan["blocks"][0]
    assert block["title"] == "Morning walk"
    assert block["status"] == "recommended"
    assert block["fact_refs"]

    stored = await db_client.get(
        "/api/v1/routines", headers=auth_headers, params={"date": today}
    )
    assert stored.status_code == 200
    assert stored.json()["data"]["id"] == plan["id"]

    repeat = await db_client.post(
        "/api/v1/routines/generate", headers=auth_headers, json={"date": today}
    )
    assert repeat.status_code == 200
    assert repeat.json()["data"]["id"] == plan["id"]

    updated = await db_client.patch(
        f"/api/v1/routines/{plan['id']}/items/{block['id']}",
        headers=auth_headers,
        json={"status": "done"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["blocks"][0]["status"] == "done"


async def test_generate_rejects_a_date_the_forecast_does_not_cover(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    forecast_factory: Callable[..., object],
) -> None:
    await _prepare_household(db_client, auth_headers)
    db_app.state.air_provider = fake_provider(
        forecast=forecast_factory(start=_local_midnight(), hours=48)
    )
    far_date = (_local_midnight() + timedelta(days=5)).date().isoformat()

    response = await db_client.post(
        "/api/v1/routines/generate", headers=auth_headers, json={"date": far_date}
    )

    assert response.status_code == 422
    assert response.json()["code"] == "FORECAST_COVERAGE"


async def test_other_profiles_cannot_read_or_patch_a_routine(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    forecast_factory: Callable[..., object],
) -> None:
    await _prepare_household(db_client, auth_headers)
    db_app.state.air_provider = fake_provider(
        forecast=forecast_factory(start=_local_midnight(), hours=48)
    )
    today = _local_midnight().date().isoformat()
    generated = await db_client.post(
        "/api/v1/routines/generate", headers=auth_headers, json={"date": today}
    )
    assert generated.status_code == 200
    plan = generated.json()["data"]

    other = await db_client.post(
        "/api/v1/sessions",
        json={"consent_version": "2026-11", "health_consent": False},
    )
    other_headers = {"Authorization": f"Bearer {other.json()['data']['token']}"}

    read = await db_client.get(
        "/api/v1/routines", headers=other_headers, params={"date": today}
    )
    patch = await db_client.patch(
        f"/api/v1/routines/{plan['id']}/items/{plan['blocks'][0]['id']}",
        headers=other_headers,
        json={"status": "done"},
    )

    assert read.status_code == 404
    assert patch.status_code == 404


async def test_session_is_required(db_client: AsyncClient) -> None:
    response = await db_client.get("/api/v1/routines")

    assert response.status_code == 401
