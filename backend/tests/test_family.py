from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.integrations.ai.gemini import GeminiError, GeminiOutput
from app.integrations.air_quality.base import AirQualityProviderError
from app.models.household import Household
from app.models.routine import Recommendation
from app.services import family_service

PROFILE = {
    "name": "Sharma household",
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
    "members": [
        {"age_band": "6-12", "health_flags": []},
        {"age_band": "18-59", "health_flags": []},
    ],
}

WINDOWS = [
    {
        "id": "school-run",
        "title": "School run",
        "activity": "school_commute",
        "start": "07:30",
        "duration_min": 45,
        "intensity": "moderate",
        "venue": "outdoor",
        "transport_mode": "walk",
        "indoor_alternative": "Use public transport or a vehicle with recirculated air",
    },
    {
        "id": "evening-walk",
        "title": "Evening walk",
        "activity": "walking",
        "start": "18:30",
        "duration_min": 45,
        "intensity": "light",
        "venue": "outdoor",
    },
    {
        "id": "park-time",
        "title": "Park time",
        "activity": "outdoor_play",
        "start": "16:00",
        "duration_min": 60,
        "intensity": "moderate",
        "venue": "outdoor",
        "indoor_alternative": "Indoor play away from open windows",
    },
]

PREFERENCES = {
    "locale": "en-IN",
    "activity_windows": WINDOWS,
    "alert_threshold_aqi": 150,
}

EMPTY_ANSWER = (
    '{"answer":"General guidance only, not medical advice.","actions":[],"avoid":[]}'
)


class FakeGemini:
    def __init__(self, *, text: str | None = None, error: GeminiError | None = None):
        self._text = text
        self._error = error
        self.calls = 0

    async def generate(
        self, *, system_instruction: str, user_text: str
    ) -> GeminiOutput:
        self.calls += 1
        if self._error is not None:
            raise self._error
        return GeminiOutput(
            text=self._text or EMPTY_ANSWER,
            model="fake-model",
            latency_ms=5,
            input_tokens=10,
            output_tokens=8,
        )


async def _create_profile(
    client: AsyncClient, headers: dict[str, str], **overrides: object
) -> dict[str, object]:
    response = await client.post(
        "/api/v1/family/profile", headers=headers, json={**PROFILE, **overrides}
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


async def _save_preferences(
    client: AsyncClient,
    headers: dict[str, str],
    windows: list[dict[str, object]] | None = None,
) -> None:
    response = await client.put(
        "/api/v1/family/preferences",
        headers=headers,
        json={**PREFERENCES, "activity_windows": windows or WINDOWS},
    )
    assert response.status_code == 200, response.text


async def _generate(client: AsyncClient, headers: dict[str, str]):
    return await client.post("/api/v1/family/recommendations/generate", headers=headers)


def _use_poor_air(
    db_app: FastAPI,
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., object],
    forecast_factory: Callable[..., object],
) -> None:
    db_app.state.air_provider = fake_provider(
        reading=reading_factory(pm2_5=110.0),
        forecast=forecast_factory(hours=48, pm2_5=70.0),
    )


def _use_missing_air(db_app: FastAPI, fake_provider: Callable[..., object]) -> None:
    error = AirQualityProviderError("unavailable", kind="not_configured")
    db_app.state.air_provider = fake_provider(current_error=error, forecast_error=error)


async def test_family_routes_require_authentication(db_client: AsyncClient) -> None:
    response = await db_client.get("/api/v1/family/profile")

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


async def test_profile_create_read_update_and_validation(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    invalid_members = await db_client.post(
        "/api/v1/family/profile",
        headers=auth_headers,
        json={**PROFILE, "members": []},
    )
    assert invalid_members.status_code == 422

    too_many = await db_client.post(
        "/api/v1/family/profile",
        headers=auth_headers,
        json={**PROFILE, "members": [{"age_band": "18-59"}] * 13},
    )
    assert too_many.status_code == 422

    extra_field = await db_client.post(
        "/api/v1/family/profile",
        headers=auth_headers,
        json={**PROFILE, "nickname": "not allowed"},
    )
    assert extra_field.status_code == 422

    missing_name = await db_client.post(
        "/api/v1/family/profile",
        headers=auth_headers,
        json={key: value for key, value in PROFILE.items() if key != "name"},
    )
    assert missing_name.status_code == 422

    created = await _create_profile(db_client, auth_headers)
    assert created["size"] == 2
    assert created["has_children"] is True
    assert created["has_older_adults"] is False

    duplicate = await db_client.post(
        "/api/v1/family/profile", headers=auth_headers, json=PROFILE
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "CONFLICT"

    updated = await db_client.put(
        "/api/v1/family/profile",
        headers=auth_headers,
        json={
            **PROFILE,
            "name": "Sharma grandparents",
            "members": [{"age_band": "60+", "health_flags": []}],
        },
    )
    assert updated.status_code == 200, updated.text
    data = updated.json()["data"]
    assert data["name"] == "Sharma grandparents"
    assert data["size"] == 1
    assert data["has_children"] is False
    assert data["has_older_adults"] is True

    read = await db_client.get("/api/v1/family/profile", headers=auth_headers)
    assert read.status_code == 200
    assert read.json()["data"]["id"] == created["id"]

    deleted = await db_client.delete("/api/v1/family/profile", headers=auth_headers)
    assert deleted.status_code == 204
    missing = await db_client.get("/api/v1/family/profile", headers=auth_headers)
    assert missing.status_code == 404


async def test_health_flags_require_consent(
    db_client: AsyncClient, plain_headers: dict[str, str]
) -> None:
    response = await db_client.post(
        "/api/v1/family/profile",
        headers=plain_headers,
        json={
            **PROFILE,
            "members": [{"age_band": "6-12", "health_flags": ["asthma"]}],
        },
    )
    assert response.status_code == 403
    assert response.json()["code"] == "CONSENT_REQUIRED"

    without_flags = await db_client.post(
        "/api/v1/family/profile", headers=plain_headers, json=PROFILE
    )
    assert without_flags.status_code == 201


async def test_preferences_validate_activity_and_schedule(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _create_profile(db_client, auth_headers)

    defaults = await db_client.get("/api/v1/family/preferences", headers=auth_headers)
    assert defaults.status_code == 200
    assert defaults.json()["data"]["activity_windows"] == []

    saved = await db_client.put(
        "/api/v1/family/preferences", headers=auth_headers, json=PREFERENCES
    )
    assert saved.status_code == 200, saved.text
    data = saved.json()["data"]
    assert data["transport_mode"] == "mixed"
    assert len(data["activity_windows"]) == 3
    assert data["activity_windows"][0]["activity"] == "school_commute"

    bad_activity = await db_client.put(
        "/api/v1/family/preferences",
        headers=auth_headers,
        json={
            **PREFERENCES,
            "activity_windows": [{**WINDOWS[0], "activity": "skydiving"}],
        },
    )
    assert bad_activity.status_code == 422

    missing_schedule = await db_client.put(
        "/api/v1/family/preferences",
        headers=auth_headers,
        json={
            **PREFERENCES,
            "activity_windows": [
                {key: value for key, value in WINDOWS[0].items() if key != "start"}
            ],
        },
    )
    assert missing_schedule.status_code == 422

    duplicate_ids = await db_client.put(
        "/api/v1/family/preferences",
        headers=auth_headers,
        json={**PREFERENCES, "activity_windows": [WINDOWS[0], WINDOWS[0]]},
    )
    assert duplicate_ids.status_code == 422


async def test_generate_with_poor_air_uses_deterministic_rules_and_history(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., object],
    forecast_factory: Callable[..., object],
) -> None:
    _use_poor_air(db_app, fake_provider, reading_factory, forecast_factory)
    await _create_profile(db_client, auth_headers)
    await _save_preferences(db_client, auth_headers)

    response = await _generate(db_client, auth_headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["rules_version"].startswith("family-rules-")
    assert data["pollution_context"]["guidance_basis"] == "cpcb_aqi"
    assert data["pollution_context"]["stale"] is False
    assert data["pollution_context"]["aqi"] is not None
    assert data["pollution_context"]["attribution"]
    assert data["ai_explanation"]["status"] == "unavailable"
    assert data["disclaimer"]

    recommendations = data["recommendations"]
    assert len(recommendations) == 3
    by_activity = {item["activity"]: item for item in recommendations}
    assert by_activity["school_commute"]["rule_id"] == "FAM-012"
    assert by_activity["school_commute"]["action_label"]
    assert by_activity["walking"]["recommended_action"] == "move_indoor"
    assert by_activity["outdoor_play"]["alternative_activity"]
    for item in recommendations:
        assert (
            item["relevant_pollution_context"]["aqi"]
            == data["pollution_context"]["aqi"]
        )
        assert item["evidence"]
        assert item["data_source"]
        assert item["reason"]

    listed = await db_client.get("/api/v1/family/recommendations", headers=auth_headers)
    assert listed.status_code == 200
    items = listed.json()["data"]["items"]
    assert len(items) == 3

    detail = await db_client.get(
        f"/api/v1/family/recommendations/{items[0]['recommendation_id']}",
        headers=auth_headers,
    )
    assert detail.status_code == 200
    assert detail.json()["data"]["recommendation_id"] == items[0]["recommendation_id"]

    async with db_app.state.database.session() as session:
        stored = await session.scalar(
            select(func.count())
            .select_from(Recommendation)
            .where(Recommendation.module == "family")
        )
    assert stored == 3


async def test_forecast_only_when_current_is_unavailable(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    forecast_factory: Callable[..., object],
) -> None:
    db_app.state.air_provider = fake_provider(
        current_error=AirQualityProviderError("down", kind="not_configured"),
        forecast=forecast_factory(hours=48, pm2_5=60.0),
    )
    await _create_profile(db_client, auth_headers)
    await _save_preferences(db_client, auth_headers)

    response = await _generate(db_client, auth_headers)

    assert response.status_code == 200, response.text
    context = response.json()["data"]["pollution_context"]
    assert context["forecast_only"] is True
    assert context["guidance_basis"] == "pm25_band"
    assert context["source_type"] == "model_forecast"
    assert context["aqi"] is None
    assert "forecast" in context["aqi_unavailable_reason"].lower()


async def test_missing_pollution_data_returns_check_back(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
) -> None:
    _use_missing_air(db_app, fake_provider)
    await _create_profile(db_client, auth_headers)
    await _save_preferences(db_client, auth_headers)

    response = await _generate(db_client, auth_headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["pollution_context"]["guidance_basis"] == "none"
    assert data["pollution_context"]["aqi"] is None
    assert data["pollution_context"]["pm2_5"] is None
    assert data["pollution_context"]["forecast_used"] is False
    for item in data["recommendations"]:
        assert item["rule_id"] == "FAM-001"
        assert item["recommended_action"] == "check_back"
        assert item["uncertainty_information"]
        assert item["confidence"] == "low"


async def test_valid_gemini_explanation_is_returned_without_changing_rules(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., object],
    forecast_factory: Callable[..., object],
) -> None:
    _use_poor_air(db_app, fake_provider, reading_factory, forecast_factory)
    db_app.state.settings.gemini_api_key = SecretStr("test-key-not-used")
    db_app.state.gemini = FakeGemini()
    await _create_profile(db_client, auth_headers)
    await _save_preferences(db_client, auth_headers)

    response = await _generate(db_client, auth_headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["ai_explanation"]["status"] == "available"
    assert data["ai_explanation"]["model"] == "fake-model"
    assert data["ai_explanation"]["text"]
    rules = {item["rule_id"] for item in data["recommendations"]}
    assert "FAM-009" in rules


@pytest.mark.parametrize(
    ("answer", "reason"),
    [
        ("PM2.5 is 999 µg/m³.", "ungrounded_number"),
        ("This plan is completely safe.", "unsafe_claim"),
        ("No data is available for this area.", "contradicts_available_data"),
    ],
)
async def test_untrusted_gemini_output_is_rejected(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., object],
    forecast_factory: Callable[..., object],
    answer: str,
    reason: str,
) -> None:
    _use_poor_air(db_app, fake_provider, reading_factory, forecast_factory)
    db_app.state.settings.gemini_api_key = SecretStr("test-key-not-used")
    db_app.state.gemini = FakeGemini(
        text=f'{{"answer":"{answer}","actions":[],"avoid":[]}}'
    )
    await _create_profile(db_client, auth_headers)
    await _save_preferences(db_client, auth_headers)

    response = await _generate(db_client, auth_headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["ai_explanation"]["status"] == "rejected"
    assert data["ai_explanation"]["reason"] == reason
    assert data["ai_explanation"]["text"] is None
    assert data["recommendations"]


async def test_gemini_unavailable_falls_back_to_deterministic_results(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., object],
    forecast_factory: Callable[..., object],
) -> None:
    _use_poor_air(db_app, fake_provider, reading_factory, forecast_factory)
    db_app.state.settings.gemini_api_key = SecretStr("test-key-not-used")
    db_app.state.gemini = FakeGemini(error=GeminiError("down", code="timeout"))
    await _create_profile(db_client, auth_headers)
    await _save_preferences(db_client, auth_headers)

    response = await _generate(db_client, auth_headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["ai_explanation"]["status"] == "unavailable"
    assert data["ai_explanation"]["reason"] == "timeout"
    assert data["recommendations"]


async def test_generate_requires_activity_preferences(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., object],
    forecast_factory: Callable[..., object],
) -> None:
    _use_poor_air(db_app, fake_provider, reading_factory, forecast_factory)
    await _create_profile(db_client, auth_headers)

    response = await _generate(db_client, auth_headers)

    assert response.status_code == 422
    assert response.json()["code"] == "NO_ACTIVITIES"


async def test_legacy_household_preferences_are_reported_as_incomplete(
    db_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    household = await db_client.put(
        "/api/v1/household",
        headers=auth_headers,
        json={
            "lat": 28.6139,
            "lon": 77.209,
            "timezone": "Asia/Kolkata",
            "dwelling": "apartment_upper",
            "cooking_fuel": "lpg",
        },
    )
    assert household.status_code == 200, household.text
    legacy = await db_client.put(
        "/api/v1/household/preferences",
        headers=auth_headers,
        json={
            "activity_windows": [
                {
                    "id": "legacy",
                    "title": "Legacy walk",
                    "start": "07:00",
                    "duration_min": 30,
                    "intensity": "light",
                    "venue": "outdoor",
                }
            ]
        },
    )
    assert legacy.status_code == 200, legacy.text

    response = await db_client.get("/api/v1/family/preferences", headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["code"] == "PREFERENCES_INCOMPLETE"


async def test_recommendations_are_scoped_to_the_session(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., object],
    forecast_factory: Callable[..., object],
) -> None:
    _use_poor_air(db_app, fake_provider, reading_factory, forecast_factory)
    await _create_profile(db_client, auth_headers)
    await _save_preferences(db_client, auth_headers)
    generated = await _generate(db_client, auth_headers)
    assert generated.status_code == 200, generated.text
    recommendation_id = generated.json()["data"]["recommendations"][0][
        "recommendation_id"
    ]

    other = await db_client.post(
        "/api/v1/sessions",
        json={"consent_version": "2026-11-test", "health_consent": False},
    )
    other_headers = {"Authorization": f"Bearer {other.json()['data']['token']}"}
    await _create_profile(db_client, other_headers)

    crossed = await db_client.get(
        f"/api/v1/family/recommendations/{recommendation_id}",
        headers=other_headers,
    )
    assert crossed.status_code == 404
    assert crossed.json()["code"] == "NOT_FOUND"

    listed = await db_client.get(
        "/api/v1/family/recommendations", headers=other_headers
    )
    assert listed.status_code == 200
    assert listed.json()["data"]["items"] == []


async def test_delete_profile_cascades_recommendations(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., object],
    forecast_factory: Callable[..., object],
) -> None:
    _use_poor_air(db_app, fake_provider, reading_factory, forecast_factory)
    await _create_profile(db_client, auth_headers)
    await _save_preferences(db_client, auth_headers)
    assert (await _generate(db_client, auth_headers)).status_code == 200

    deleted = await db_client.delete("/api/v1/family/profile", headers=auth_headers)
    assert deleted.status_code == 204

    async with db_app.state.database.session() as session:
        households = await session.scalar(select(func.count()).select_from(Household))
        stored = await session.scalar(select(func.count()).select_from(Recommendation))
    assert households == 0
    assert stored == 0

    missing = await db_client.get("/api/v1/family/profile", headers=auth_headers)
    assert missing.status_code == 404


async def test_persistence_failure_rolls_back_all_recommendations(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., object],
    forecast_factory: Callable[..., object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _use_poor_air(db_app, fake_provider, reading_factory, forecast_factory)
    await _create_profile(db_client, auth_headers)
    await _save_preferences(db_client, auth_headers)

    async def _fail(*args: object, **kwargs: object) -> None:
        raise SQLAlchemyError("forced failure")

    monkeypatch.setattr(family_service.recommendations_repo, "create", _fail)

    response = await _generate(db_client, auth_headers)

    assert response.status_code == 503
    assert response.json()["code"] == "DATABASE_UNAVAILABLE"

    async with db_app.state.database.session() as session:
        stored = await session.scalar(
            select(func.count())
            .select_from(Recommendation)
            .where(Recommendation.module == "family")
        )
    assert stored == 0


async def test_generation_is_rate_limited_per_session(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., object],
    forecast_factory: Callable[..., object],
) -> None:
    _use_poor_air(db_app, fake_provider, reading_factory, forecast_factory)
    db_app.state.settings.family_generations_per_hour = 1
    await _create_profile(db_client, auth_headers)
    await _save_preferences(db_client, auth_headers)

    first = await _generate(db_client, auth_headers)
    second = await _generate(db_client, auth_headers)

    assert first.status_code == 200, first.text
    assert second.status_code == 429
    assert second.json()["code"] == "RATE_LIMITED"
