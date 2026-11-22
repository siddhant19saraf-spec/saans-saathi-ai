"""IndoorShield deterministic engine and persisted workflow tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from pydantic import SecretStr

from app.domain.indoor_shield import (
    AssessmentSnapshot,
    OutdoorSnapshot,
    RoomSnapshot,
    SensorSnapshot,
    SourceSnapshot,
    recommend,
)
from app.integrations.ai.gemini import GeminiError
from app.integrations.air_quality.circuit import CircuitBreaker

NOW = datetime.now(tz=UTC)

ROOM = RoomSnapshot(
    name="Living room",
    room_type="living_room",
    area_m2=20.0,
    ceiling_m=2.7,
    ventilation="windows",
    windows_count=2,
    has_purifier=False,
    purifier_cadr=None,
    dampness="none",
)


def _assessment(
    *sources: SourceSnapshot,
    cooking_fuel: str = "lpg",
    cooking_exhaust: bool = True,
    cleaning_frequency: str = "weekly",
    rooms: tuple[RoomSnapshot, ...] = (ROOM,),
) -> AssessmentSnapshot:
    return AssessmentSnapshot(
        rooms=rooms,
        sources=sources,
        cooking_fuel=cooking_fuel,
        cooking_location="indoor_kitchen",
        cooking_exhaust=cooking_exhaust,
        cleaning_frequency=cleaning_frequency,
        sensor_available=False,
        sensitive_members=False,
    )


def _sensor(
    pollutant: str,
    value: float,
    *,
    unit: str = "µg/m³",
    hours_old: int = 1,
    calibration: str = "unverified",
) -> SensorSnapshot:
    return SensorSnapshot(
        pollutant=pollutant,
        value=value,
        unit=unit,
        measured_at=NOW - timedelta(hours=hours_old),
        calibration_status=calibration,
    )


# -- deterministic engine ---------------------------------------------------


def test_source_variants_produce_distinct_rules() -> None:
    plan = recommend(
        _assessment(
            SourceSnapshot(code="biomass_cooking", frequency="daily"),
            SourceSnapshot(code="tobacco_smoke", frequency="daily"),
            SourceSnapshot(code="dust", frequency="weekly"),
        ),
        (),
        OutdoorSnapshot(available=False),
    )
    rule_ids = {item.rule_id for item in plan.recommendations}
    assert "IND-SRC-SOLID-FUEL" in rule_ids
    assert "IND-SRC-TOBACCO" in rule_ids
    assert "IND-SRC-DUST" in rule_ids
    scores = [item.priority_score for item in plan.recommendations]
    assert scores == sorted(scores, reverse=True)
    assert plan.recommendations[0].priority == "high"


def test_repeated_source_raises_priority_above_occasional() -> None:
    daily = recommend(
        _assessment(SourceSnapshot(code="candles_incense", frequency="daily")),
        (),
        OutdoorSnapshot(available=False),
    )
    occasional = recommend(
        _assessment(SourceSnapshot(code="candles_incense", frequency="occasional")),
        (),
        OutdoorSnapshot(available=False),
    )
    assert daily.recommendations[0].priority_score > (
        occasional.recommendations[0].priority_score
    )


def test_missing_outdoor_and_sensor_data_are_explicit() -> None:
    plan = recommend(_assessment(), (), OutdoorSnapshot(available=False))
    assert any("Indoor sensor data is unavailable" in item for item in plan.limitations)
    assert any(
        "Outdoor air-quality context is unavailable" in item
        for item in plan.limitations
    )
    assert all(item.rule_id != "IND-OUTDOOR-PEAK" for item in plan.recommendations)


def test_stale_outdoor_value_is_not_used_for_ventilation_timing() -> None:
    plan = recommend(
        _assessment(),
        (),
        OutdoorSnapshot(
            available=True,
            provider="fake",
            observed_at=NOW - timedelta(days=2),
            stale=True,
            pm2_5=220.0,
            forecast_available=True,
            forecast_min_pm2_5=10.0,
            forecast_min_at=NOW + timedelta(hours=2),
        ),
    )
    rule_ids = [item.rule_id for item in plan.recommendations]
    assert rule_ids == ["IND-OUTDOOR-STALE"]
    assert "stale" in plan.limitations[-1].casefold() or any(
        "stale" in item.casefold() for item in plan.limitations
    )


def test_sensor_rules_trigger_only_above_guidelines() -> None:
    plan = recommend(
        _assessment(),
        (
            _sensor("pm2_5", 40.0),
            _sensor("pm10", 80.0),
            _sensor("co2", 1200.0, unit="ppm"),
            _sensor("co", 5.0, unit="mg/m³"),
            _sensor("humidity", 70.0, unit="%"),
            _sensor("pm2_5", 5.0, hours_old=2),
        ),
        OutdoorSnapshot(available=False),
    )
    rule_ids = {item.rule_id for item in plan.recommendations}
    assert "IND-SENSOR-PM25" in rule_ids
    assert "IND-SENSOR-PM10" in rule_ids
    assert "IND-SENSOR-CO2" in rule_ids
    assert "IND-SENSOR-CO" in rule_ids
    assert "IND-SENSOR-HUMIDITY" in rule_ids
    assert plan.recommendations[0].rule_id == "IND-SENSOR-CO"


def test_unsupported_sensor_pollutant_is_ignored_by_engine() -> None:
    plan = recommend(
        _assessment(),
        (_sensor("no2", 400.0),),
        OutdoorSnapshot(available=False),
    )
    assert plan.recommendations[0].rule_id == "IND-GENERAL-CHECK"


def test_damp_room_and_low_cleaning_generate_actions() -> None:
    damp = replace(ROOM, dampness="persistent")
    plan = recommend(
        _assessment(cleaning_frequency="less", rooms=(damp,)),
        (),
        OutdoorSnapshot(available=False),
    )
    rule_ids = {item.rule_id for item in plan.recommendations}
    assert "IND-ROOM-MOISTURE" in rule_ids
    assert "IND-CLEAN-FREQUENCY" in rule_ids


def test_cooking_fuel_without_exhaust_recommends_exhaust() -> None:
    plan = recommend(
        _assessment(cooking_fuel="biomass", cooking_exhaust=False),
        (),
        OutdoorSnapshot(available=False),
    )
    assert "IND-COOK-EXHAUST" in {item.rule_id for item in plan.recommendations}


# -- API helpers ------------------------------------------------------------

BASE_ASSESSMENT: dict[str, Any] = {
    "dwelling": "apartment_upper",
    "cooking_fuel": "lpg",
    "cooking_location": "indoor_kitchen",
    "cooking_exhaust": False,
    "cleaning_frequency": "weekly",
    "sensor_available": False,
    "rooms": [
        {
            "name": "Kitchen",
            "room_type": "kitchen",
            "area_m2": 12,
            "ceiling_m": 2.7,
            "ventilation": "windows",
            "windows_count": 1,
            "has_purifier": False,
            "dampness": "none",
        }
    ],
    "sources": [{"code": "gas_stove", "frequency": "daily"}],
}


async def _save_household(client: AsyncClient, headers: dict[str, str]) -> None:
    response = await client.put(
        "/api/v1/household",
        headers=headers,
        json={
            "lat": 28.6139,
            "lon": 77.209,
            "timezone": "Asia/Kolkata",
            "dwelling": "apartment_upper",
            "cooking_fuel": "lpg",
        },
    )
    assert response.status_code == 200, response.text


async def _new_session(client: AsyncClient) -> dict[str, str]:
    response = await client.post(
        "/api/v1/sessions",
        json={"consent_version": "2026-11-test", "health_consent": True},
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['data']['token']}"}


async def _create_assessment(
    client: AsyncClient, headers: dict[str, str]
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/indoor/assessments", headers=headers, json=BASE_ASSESSMENT
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


class FakeGemini:
    def __init__(self, *, text: str | None = None, error: GeminiError | None = None):
        self.text = text
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def generate(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(
            text=self.text
            or (
                '{"answer":"The plan starts with source control and '
                'ventilation.","actions":[],"avoid":[]}'
            ),
            model="fake-gemini",
        )


# -- assessment workflow ----------------------------------------------------


async def test_create_assessment_persists_deterministic_plan(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Any,
    reading_factory: Any,
    forecast_factory: Any,
) -> None:
    await _save_household(db_client, auth_headers)
    db_app.state.air_provider = fake_provider(
        reading=reading_factory(pm2_5=85.0),
        forecast=forecast_factory(hours=24, pm2_5=50.0),
    )

    data = await _create_assessment(db_client, auth_headers)

    assert data["status"] == "completed"
    assert len(data["rooms"]) == 1
    assert data["sources"][0]["code"] == "gas_stove"
    assert data["outdoor_context"]["available"] is True
    assert data["outdoor_context"]["pm2_5"] == 85.0
    assert data["action_counts"]["pending"] == len(data["recommendations"])
    assert data["recommendations"]
    scores = [item["priority_score"] for item in data["recommendations"]]
    assert scores == sorted(scores, reverse=True)
    assert data["explanation"]["status"] == "deterministic"
    assert "general household recommendations" in data["explanation"]["text"]
    assert any(
        "Indoor sensor data is unavailable" in item for item in data["limitations"]
    )
    assert all(item["rule_id"] != "IND-SENSOR-PM25" for item in data["recommendations"])

    listed = await db_client.get("/api/v1/indoor/assessments", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()["data"]["count"] == 1

    fetched = await db_client.get(
        f"/api/v1/indoor/assessments/{data['id']}", headers=auth_headers
    )
    assert fetched.status_code == 200
    assert fetched.json()["data"]["id"] == data["id"]

    overview = await db_client.get("/api/v1/indoor/overview", headers=auth_headers)
    assert overview.status_code == 200
    overview_data = overview.json()["data"]
    assert overview_data["latest_assessment"]["id"] == data["id"]
    assert overview_data["sensors"]["available"] is False
    assert overview_data["sensors"]["message"] == "Indoor sensor data unavailable."
    assert overview_data["data_status"]["indoor_sensors"] == "unavailable"
    assert overview_data["data_status"]["outdoor"] == "available"


async def test_assessment_update_replaces_rooms_and_actions(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Any,
    reading_factory: Any,
) -> None:
    await _save_household(db_client, auth_headers)
    db_app.state.air_provider = fake_provider(reading=reading_factory(pm2_5=30.0))
    created = await _create_assessment(db_client, auth_headers)

    updated = await db_client.patch(
        f"/api/v1/indoor/assessments/{created['id']}",
        headers=auth_headers,
        json={
            "cooking_fuel": "induction",
            "cooking_exhaust": True,
            "rooms": [
                {
                    "name": "Bedroom",
                    "room_type": "bedroom",
                    "area_m2": 15,
                    "ceiling_m": 2.6,
                    "ventilation": "windows",
                    "windows_count": 1,
                    "dampness": "occasional",
                }
            ],
            "sources": [],
        },
    )
    assert updated.status_code == 200, updated.text
    data = updated.json()["data"]
    assert data["cooking_fuel"] == "induction"
    assert [room["name"] for room in data["rooms"]] == ["Bedroom"]
    assert data["sources"] == []
    assert "IND-ROOM-MOISTURE" in {item["rule_id"] for item in data["recommendations"]}


async def test_assessment_delete_and_missing_household(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Any,
    reading_factory: Any,
) -> None:
    no_household = await db_client.post(
        "/api/v1/indoor/assessments", headers=auth_headers, json=BASE_ASSESSMENT
    )
    assert no_household.status_code == 422
    assert no_household.json()["code"] == "NO_HOUSEHOLD"

    await _save_household(db_client, auth_headers)
    db_app.state.air_provider = fake_provider(reading=reading_factory())
    created = await _create_assessment(db_client, auth_headers)

    deleted = await db_client.delete(
        f"/api/v1/indoor/assessments/{created['id']}", headers=auth_headers
    )
    assert deleted.status_code == 204
    missing = await db_client.get(
        f"/api/v1/indoor/assessments/{created['id']}", headers=auth_headers
    )
    assert missing.status_code == 404


async def test_missing_and_stale_outdoor_context_are_explicit(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Any,
    reading_factory: Any,
    forecast_factory: Any,
) -> None:
    from app.integrations.air_quality.base import AirQualityProviderError

    await _save_household(db_client, auth_headers)
    db_app.state.air_provider = fake_provider(
        current_error=AirQualityProviderError("down", kind="timeout"),
        forecast_error=AirQualityProviderError("down", kind="timeout"),
    )
    missing = await _create_assessment(db_client, auth_headers)
    assert missing["outdoor_context"]["available"] is False
    assert "unavailable" in missing["outdoor_context"]["note"].casefold()

    db_app.state.air_provider = fake_provider(
        reading=replace(
            reading_factory(pm2_5=180.0),
            quality_flags=("stale_measurement",),
        ),
        forecast=forecast_factory(hours=24, pm2_5=20.0),
    )
    db_app.state.air_breaker = CircuitBreaker()
    stale = await _create_assessment(db_client, auth_headers)
    assert stale["outdoor_context"]["available"] is True
    assert stale["outdoor_context"]["stale"] is True
    assert "IND-OUTDOOR-STALE" in {item["rule_id"] for item in stale["recommendations"]}


async def test_ownership_is_scoped_to_the_household(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Any,
    reading_factory: Any,
) -> None:
    await _save_household(db_client, auth_headers)
    db_app.state.air_provider = fake_provider(reading=reading_factory())
    created = await _create_assessment(db_client, auth_headers)

    other_headers = await _new_session(db_client)
    await _save_household(db_client, other_headers)

    foreign = await db_client.get(
        f"/api/v1/indoor/assessments/{created['id']}", headers=other_headers
    )
    assert foreign.status_code == 404

    unauthorized = await db_client.post(
        "/api/v1/indoor/assessments", json=BASE_ASSESSMENT
    )
    assert unauthorized.status_code == 401


# -- sensors ----------------------------------------------------------------


async def test_sensor_validation_availability_and_measured_actions(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Any,
    reading_factory: Any,
) -> None:
    await _save_household(db_client, auth_headers)
    db_app.state.air_provider = fake_provider(reading=reading_factory(pm2_5=20.0))

    created = await db_client.post(
        "/api/v1/indoor/sensors",
        headers=auth_headers,
        json={
            "provider": "test-provider",
            "external_id": "device-1",
            "name": "Living room monitor",
            "room_name": "Living room",
            "calibration_status": "unverified",
        },
    )
    assert created.status_code == 201, created.text
    sensor_id = created.json()["data"]["id"]
    assert created.json()["data"]["data_status"] == "unavailable"

    before = await db_client.get("/api/v1/indoor/sensors", headers=auth_headers)
    assert before.json()["data"]["available"] is False

    reading = await db_client.post(
        f"/api/v1/indoor/sensors/{sensor_id}/readings",
        headers=auth_headers,
        json={
            "pollutant": "pm2_5",
            "value": 42.0,
            "unit": "ug/m3",
            "measured_at": datetime.now(tz=UTC).isoformat(),
            "quality_status": "valid",
        },
    )
    assert reading.status_code == 201, reading.text
    assert reading.json()["data"]["unit"] == "µg/m³"
    assert reading.json()["data"]["stale"] is False

    measured = await db_client.get("/api/v1/indoor/sensors", headers=auth_headers)
    sensor = measured.json()["data"]["sensors"][0]
    assert measured.json()["data"]["available"] is True
    assert sensor["data_status"] == "measured"
    assert sensor["latest_readings"][0]["value"] == 42.0

    assessment = await _create_assessment(db_client, auth_headers)
    assert "IND-SENSOR-PM25" in {
        item["rule_id"] for item in assessment["recommendations"]
    }
    assert "Indoor sensor data is unavailable" not in " ".join(
        assessment["limitations"]
    )


async def test_sensor_rejects_unsupported_pollutant_unit_value_and_future_time(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    await _save_household(db_client, auth_headers)
    created = await db_client.post(
        "/api/v1/indoor/sensors",
        headers=auth_headers,
        json={"provider": "p", "external_id": "e", "name": "Sensor"},
    )
    sensor_id = created.json()["data"]["id"]
    base = {
        "pollutant": "pm2_5",
        "value": 20.0,
        "unit": "µg/m³",
        "measured_at": datetime.now(tz=UTC).isoformat(),
    }

    unsupported = await db_client.post(
        f"/api/v1/indoor/sensors/{sensor_id}/readings",
        headers=auth_headers,
        json={**base, "pollutant": "no2"},
    )
    assert unsupported.status_code == 422
    assert unsupported.json()["code"] == "UNSUPPORTED_POLLUTANT"

    unit = await db_client.post(
        f"/api/v1/indoor/sensors/{sensor_id}/readings",
        headers=auth_headers,
        json={**base, "pollutant": "co2", "unit": "µg/m³"},
    )
    assert unit.status_code == 422
    assert unit.json()["code"] == "UNIT_MISMATCH"

    out_of_range = await db_client.post(
        f"/api/v1/indoor/sensors/{sensor_id}/readings",
        headers=auth_headers,
        json={**base, "pollutant": "humidity", "unit": "%", "value": 150.0},
    )
    assert out_of_range.status_code == 422
    assert out_of_range.json()["code"] == "VALUE_OUT_OF_RANGE"

    future = await db_client.post(
        f"/api/v1/indoor/sensors/{sensor_id}/readings",
        headers=auth_headers,
        json={
            **base,
            "measured_at": (datetime.now(tz=UTC) + timedelta(hours=2)).isoformat(),
        },
    )
    assert future.status_code == 422
    assert future.json()["code"] == "FUTURE_MEASUREMENT"


async def test_duplicate_reading_and_stale_sensor_data(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Any,
    reading_factory: Any,
) -> None:
    await _save_household(db_client, auth_headers)
    db_app.state.air_provider = fake_provider(reading=reading_factory())
    created = await db_client.post(
        "/api/v1/indoor/sensors",
        headers=auth_headers,
        json={"provider": "p", "external_id": "stale", "name": "Sensor"},
    )
    sensor_id = created.json()["data"]["id"]
    measured_at = datetime.now(tz=UTC) - timedelta(days=2)
    payload = {
        "pollutant": "pm2_5",
        "value": 80.0,
        "unit": "µg/m³",
        "measured_at": measured_at.isoformat(),
    }
    first = await db_client.post(
        f"/api/v1/indoor/sensors/{sensor_id}/readings",
        headers=auth_headers,
        json=payload,
    )
    assert first.status_code == 201
    duplicate = await db_client.post(
        f"/api/v1/indoor/sensors/{sensor_id}/readings",
        headers=auth_headers,
        json=payload,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "DUPLICATE_READING"

    sensors = await db_client.get("/api/v1/indoor/sensors", headers=auth_headers)
    assert sensors.json()["data"]["sensors"][0]["data_status"] == "stale"
    assert sensors.json()["data"]["available"] is False

    assessment = await _create_assessment(db_client, auth_headers)
    assert all(
        item["rule_id"] != "IND-SENSOR-PM25" for item in assessment["recommendations"]
    )
    assert any(
        "Indoor sensor data is unavailable" in item
        for item in assessment["limitations"]
    )


# -- action lifecycle -------------------------------------------------------


async def test_action_completion_reopen_reschedule_and_events(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Any,
    reading_factory: Any,
) -> None:
    await _save_household(db_client, auth_headers)
    db_app.state.air_provider = fake_provider(reading=reading_factory())
    assessment = await _create_assessment(db_client, auth_headers)
    action = assessment["recommendations"][0]

    completed = await db_client.post(
        f"/api/v1/indoor/recommendations/{action['id']}/complete",
        headers=auth_headers,
        json={"note": "Done today"},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["data"]["status"] == "completed"

    again = await db_client.post(
        f"/api/v1/indoor/recommendations/{action['id']}/complete",
        headers=auth_headers,
        json={},
    )
    assert again.status_code == 409
    assert again.json()["code"] == "ACTION_ALREADY_COMPLETED"

    reopened = await db_client.post(
        f"/api/v1/indoor/recommendations/{action['id']}/reopen",
        headers=auth_headers,
    )
    assert reopened.status_code == 200, reopened.text
    assert reopened.json()["data"]["status"] == "pending"

    future = datetime.now(tz=UTC) + timedelta(days=3)
    rescheduled = await db_client.post(
        f"/api/v1/indoor/recommendations/{action['id']}/reschedule",
        headers=auth_headers,
        json={"due_at": future.isoformat(), "note": "Weekend"},
    )
    assert rescheduled.status_code == 200, rescheduled.text
    assert rescheduled.json()["data"]["due_at"].startswith(future.date().isoformat())

    past = await db_client.post(
        f"/api/v1/indoor/recommendations/{action['id']}/reschedule",
        headers=auth_headers,
        json={"due_at": (datetime.now(tz=UTC) - timedelta(days=1)).isoformat()},
    )
    assert past.status_code == 422
    assert past.json()["code"] == "DUE_AT_IN_PAST"

    events = await db_client.get(
        f"/api/v1/indoor/recommendations/{action['id']}/events",
        headers=auth_headers,
    )
    assert events.status_code == 200
    event_types = [item["event_type"] for item in events.json()["data"]]
    assert event_types.count("completed") == 1
    assert "reopened" in event_types
    assert "rescheduled" in event_types

    listed = await db_client.get("/api/v1/indoor/recommendations", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()["data"]["counts"]["pending"] >= 1


# -- AI explanation fallback ------------------------------------------------


async def test_ai_explanation_success_and_provider_failure_fallback(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Any,
    reading_factory: Any,
) -> None:
    await _save_household(db_client, auth_headers)
    db_app.state.air_provider = fake_provider(reading=reading_factory())
    assessment = await _create_assessment(db_client, auth_headers)
    db_app.state.settings.gemini_api_key = SecretStr("test-key")

    db_app.state.gemini = FakeGemini()
    success = await db_client.post(
        f"/api/v1/indoor/assessments/{assessment['id']}/explain",
        headers=auth_headers,
    )
    assert success.status_code == 200, success.text
    assert success.json()["data"]["explanation"]["status"] == "ai"
    assert success.json()["data"]["explanation"]["model"] == "fake-gemini"

    db_app.state.gemini = FakeGemini(
        error=GeminiError("provider down", code="provider_error")
    )
    fallback = await db_client.post(
        f"/api/v1/indoor/assessments/{assessment['id']}/explain",
        headers=auth_headers,
    )
    assert fallback.status_code == 200, fallback.text
    explanation = fallback.json()["data"]["explanation"]
    assert explanation["status"] == "fallback"
    assert explanation["note"] == "provider_error"
    assert "general household recommendations" in explanation["text"]


async def test_ai_explanation_rejects_unsafe_claim(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Any,
    reading_factory: Any,
) -> None:
    await _save_household(db_client, auth_headers)
    db_app.state.air_provider = fake_provider(reading=reading_factory())
    assessment = await _create_assessment(db_client, auth_headers)
    db_app.state.settings.gemini_api_key = SecretStr("test-key")
    db_app.state.gemini = FakeGemini(
        text=(
            '{"answer":"Your home is safe and pollution-free now.",'
            '"actions":[],"avoid":[]}'
        )
    )

    response = await db_client.post(
        f"/api/v1/indoor/assessments/{assessment['id']}/explain",
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    explanation = response.json()["data"]["explanation"]
    assert explanation["status"] == "fallback"
    assert explanation["note"] == "unsafe_claim"


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            {
                **BASE_ASSESSMENT,
                "rooms": [
                    {
                        "name": "A",
                        "area_m2": 10,
                        "ventilation": "windows",
                    },
                    {
                        "name": "a",
                        "area_m2": 12,
                        "ventilation": "windows",
                    },
                ],
            },
            "Room names must be unique",
        ),
    ],
)
def test_duplicate_room_names_are_rejected_by_schema(
    payload: dict[str, Any], expected: str
) -> None:
    from pydantic import ValidationError

    from app.schemas.indoor import AssessmentCreate

    with pytest.raises(ValidationError, match=expected):
        AssessmentCreate.model_validate(payload)
