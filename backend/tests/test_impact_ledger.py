"""Impact ledger branches beyond the basic happy path.

Covers household scoping, duplicate detection, modelled baseline disclosure,
trend bucketing and goal lifecycle.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from httpx import AsyncClient

HOUSEHOLD = {
    "lat": 28.6139,
    "lon": 77.209,
    "timezone": "Asia/Kolkata",
    "dwelling": "apartment_upper",
    "cooking_fuel": "lpg",
}


def _today() -> str:
    return datetime.now(tz=UTC).date().isoformat()


async def _household(client: AsyncClient, headers: dict[str, str]) -> None:
    response = await client.put("/api/v1/household", headers=headers, json=HOUSEHOLD)
    assert response.status_code == 200, response.text


async def test_ledger_routes_require_a_household(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    goals = await db_client.get("/api/v1/impact/goals", headers=auth_headers)
    summary = await db_client.get("/api/v1/impact/summary", headers=auth_headers)
    baseline = await db_client.get(
        "/api/v1/impact/baseline-savings", headers=auth_headers
    )
    trends = await db_client.get("/api/v1/impact/trends", headers=auth_headers)
    activities = await db_client.get("/api/v1/impact/activities", headers=auth_headers)
    created = await db_client.post(
        "/api/v1/impact/goals",
        headers=auth_headers,
        json={
            "title": "Walk more",
            "activity_type": "walked",
            "unit": "km",
            "target_value": 100,
        },
    )

    for response in (goals, summary, baseline, trends, activities, created):
        assert response.status_code == 422, response.text
        assert response.json()["code"] == "NO_HOUSEHOLD"


async def test_duplicate_activity_is_rejected(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _household(db_client, auth_headers)
    payload = {
        "activity_type": "walked",
        "quantity": 5,
        "unit": "km",
        "occurred_on": _today(),
    }

    first = await db_client.post(
        "/api/v1/impact/activities", headers=auth_headers, json=payload
    )
    duplicate = await db_client.post(
        "/api/v1/impact/activities", headers=auth_headers, json=payload
    )

    assert first.status_code == 201, first.text
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "DUPLICATE_ACTIVITY"


async def test_baseline_savings_and_trends_disclose_the_modelled_baseline(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _household(db_client, auth_headers)
    today = datetime.now(tz=UTC).date()
    for index, activity_type in enumerate(("walked", "worked-from-home")):
        response = await db_client.post(
            "/api/v1/impact/activities",
            headers=auth_headers,
            json={
                "activity_type": activity_type,
                "quantity": 10 if activity_type == "walked" else 1,
                "occurred_on": (today - timedelta(days=index)).isoformat(),
            },
        )
        assert response.status_code == 201, response.text

    summary = await db_client.get(
        "/api/v1/impact/summary", headers=auth_headers, params={"days": 7}
    )
    assert summary.status_code == 200
    body = summary.json()["data"]
    assert body["range"] == "7d"
    assert body["activity_count"] == 2
    assert {item["activity_type"] for item in body["by_type"]} == {
        "walked",
        "worked-from-home",
    }

    savings = await db_client.get(
        "/api/v1/impact/baseline-savings", headers=auth_headers, params={"days": 7}
    )
    assert savings.status_code == 200
    savings_body = savings.json()["data"]
    assert savings_body["baseline_co2e_kg"] is not None
    assert savings_body["baseline_co2e_kg"] > 0
    assert savings_body["activity_co2e_kg"] > 0
    assert savings_body["savings_co2e_kg"] is not None
    assert "not a measured baseline" in savings_body["baseline_basis"].lower()
    assert "assumption" in savings_body["savings_basis"].lower()

    trends = await db_client.get(
        "/api/v1/impact/trends", headers=auth_headers, params={"days": 30}
    )
    assert trends.status_code == 200
    trends_body = trends.json()["data"]
    assert len(trends_body["weekly"]) >= 1
    assert len(trends_body["monthly"]) >= 1
    assert trends_body["weekly"][0]["activity_count"] >= 1
    assert "-W" in trends_body["weekly"][0]["period"]
    assert trends_body["monthly"][0]["period"].count("-") == 1

    empty = await db_client.get(
        "/api/v1/impact/baseline-savings", headers=auth_headers, params={"days": 1}
    )
    assert empty.status_code == 200


async def test_goal_lifecycle_and_unit_validation(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _household(db_client, auth_headers)

    wrong_unit = await db_client.post(
        "/api/v1/impact/goals",
        headers=auth_headers,
        json={
            "title": "Walk more",
            "activity_type": "walked",
            "unit": "days",
            "target_value": 100,
        },
    )
    assert wrong_unit.status_code == 422
    assert wrong_unit.json()["code"] == "UNIT_MISMATCH"

    created = await db_client.post(
        "/api/v1/impact/goals",
        headers=auth_headers,
        json={
            "title": "Walk more",
            "description": "A weekly distance goal",
            "activity_type": "walked",
            "unit": "km",
            "target_value": 100,
            "target_date": (datetime.now(tz=UTC).date() + timedelta(days=30)).isoformat(),
        },
    )
    assert created.status_code == 201, created.text
    goal = created.json()["data"]
    assert goal["current_value"] == 0
    assert goal["progress_percent"] == 0

    listed = await db_client.get("/api/v1/impact/goals", headers=auth_headers)
    assert [item["id"] for item in listed.json()["data"]] == [goal["id"]]

    updated = await db_client.put(
        f"/api/v1/impact/goals/{goal['id']}",
        headers=auth_headers,
        json={"title": "Walk much more", "target_value": 150, "is_active": False},
    )
    assert updated.status_code == 200, updated.text
    updated_goal = updated.json()["data"]
    assert updated_goal["title"] == "Walk much more"
    assert updated_goal["target_value"] == 150
    assert updated_goal["is_active"] is False

    missing = uuid4()
    missing_update = await db_client.put(
        f"/api/v1/impact/goals/{missing}",
        headers=auth_headers,
        json={"title": "Nope"},
    )
    missing_delete = await db_client.delete(
        f"/api/v1/impact/goals/{missing}", headers=auth_headers
    )
    assert missing_update.status_code == 422
    assert missing_update.json()["code"] == "GOAL_NOT_FOUND"
    assert missing_delete.status_code == 422
    assert missing_delete.json()["code"] == "GOAL_NOT_FOUND"

    deleted = await db_client.delete(
        f"/api/v1/impact/goals/{goal['id']}", headers=auth_headers
    )
    assert deleted.status_code == 204
    after = await db_client.get("/api/v1/impact/goals", headers=auth_headers)
    assert after.json()["data"] == []


async def test_methodology_is_public_and_cites_limitations(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/impact/methodology")

    assert response.status_code == 200
    data = response.json()["data"]
    assert "Activity quantity" in data["formula"]
    assert "walked" in " ".join(data["factors_used"]) or data["factors_used"]
    assert any("assumption" in line.lower() for line in data["assumptions"])
    assert any("not measured" in line.lower() for line in data["limitations"])
