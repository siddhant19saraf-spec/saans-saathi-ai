from __future__ import annotations

import json
from collections.abc import Callable
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from pydantic import SecretStr
from sqlalchemy import func, select

from app.domain.facts import FactPack
from app.integrations.ai.gemini import GeminiOutput
from app.integrations.air_quality.base import (
    AirQualityProviderError,
    ProviderReading,
)
from app.models.ai import AiMessage
from app.services import (
    ecoroute_service,
    family_service,
    impact_service,
    indoor_shield_service,
    routine_service,
)
from app.services.copilot_service import _answer, _build_fact_pack

CONTEXT = {"context": {"lat": 28.61, "lon": 77.21}}


class _FakeGemini:
    def __init__(self, text: str) -> None:
        self._text = text
        self.calls = 0

    async def generate(
        self, *, system_instruction: str, user_text: str
    ) -> GeminiOutput:
        self.calls += 1
        return GeminiOutput(
            text=self._text,
            model="fake-model",
            latency_ms=12,
            input_tokens=10,
            output_tokens=8,
        )


class _AirServiceMustNotBeCalled:
    async def current(self, *args: object, **kwargs: object) -> object:
        raise AssertionError("air service must not be called without coordinates")

    async def forecast(self, *args: object, **kwargs: object) -> object:
        raise AssertionError("air service must not be called without coordinates")


async def test_fact_pack_without_coordinates_skips_the_provider() -> None:
    pack = await _build_fact_pack(
        _AirServiceMustNotBeCalled(),  # type: ignore[arg-type]
        session=None,
        profile=None,
        lat=None,
        lon=None,
        timezone="Asia/Kolkata",
        members=[
            SimpleNamespace(age_band="0-5", health_flags=["asthma"]),
        ],
    )

    assert pack.facts == []
    assert pack.context["has_children"] is True
    assert pack.context["sensitive_group"] is True
    # Individual health conditions are a sensitive attribute and must never be
    # copied into the model input.
    assert "asthma" not in pack.model_dump_json()


async def test_fact_pack_excludes_names_coordinates_and_free_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = SimpleNamespace(id="00000000-0000-0000-0000-000000000001")

    async def fake_get_profile(*args: object, **kwargs: object) -> object:
        return SimpleNamespace(
            name="SECRET_HOUSEHOLD_NAME",
            lat=28.6139,
            lon=77.209,
            has_children=True,
            has_older_adults=False,
            has_health_flags=True,
            size=3,
            dwelling="apartment",
            cooking_fuel="lpg",
            has_purifier=False,
            timezone="Asia/Kolkata",
            members=[],
        )

    async def fake_recommendations(*args: object, **kwargs: object) -> object:
        return SimpleNamespace(
            items=[
                SimpleNamespace(
                    activity_title="Morning walk",
                    action_label="Move indoors",
                )
            ]
        )

    async def fake_routine(*args: object, **kwargs: object) -> object:
        return SimpleNamespace(
            date=SimpleNamespace(isoformat=lambda: "2026-11-21"),
            blocks=[],
        )

    async def fake_summary(*args: object, **kwargs: object) -> object:
        return SimpleNamespace(total_co2e_kg=1.25, activity_count=3)

    async def fake_savings(*args: object, **kwargs: object) -> object:
        return SimpleNamespace(savings_co2e_kg=None)

    async def fake_goals(*args: object, **kwargs: object) -> list[object]:
        return []

    async def fake_assessments(*args: object, **kwargs: object) -> object:
        return SimpleNamespace(assessments=[])

    async def fake_journeys(*args: object, **kwargs: object) -> list[object]:
        return []

    monkeypatch.setattr(family_service, "get_profile", fake_get_profile)
    monkeypatch.setattr(family_service, "list_recommendations", fake_recommendations)
    monkeypatch.setattr(routine_service, "get", fake_routine)
    monkeypatch.setattr(impact_service, "summary", fake_summary)
    monkeypatch.setattr(impact_service, "baseline_and_savings", fake_savings)
    monkeypatch.setattr(impact_service, "list_goals", fake_goals)
    monkeypatch.setattr(indoor_shield_service, "list_assessments", fake_assessments)
    monkeypatch.setattr(ecoroute_service, "list_journeys", fake_journeys)

    pack = await _build_fact_pack(
        _AirServiceMustNotBeCalled(),  # type: ignore[arg-type]
        session=object(),  # type: ignore[arg-type]
        profile=profile,  # type: ignore[arg-type]
        lat=None,
        lon=None,
        timezone="Asia/Kolkata",
        members=None,
    )
    dumped = pack.model_dump_json()

    assert "SECRET_HOUSEHOLD_NAME" not in dumped
    assert "28.6139" not in dumped
    assert "77.209" not in dumped
    assert "asthma" not in dumped
    assert "impact.total_co2e_30d" in {fact.id for fact in pack.facts}
    assert "Morning walk: Move indoors" in dumped


async def test_anonymous_without_data_gets_an_honest_fallback(
    app: FastAPI,
    client: AsyncClient,
    fake_provider: Callable[..., object],
) -> None:
    app.state.air_provider = fake_provider(
        current_error=AirQualityProviderError("down", kind="http_error")
    )

    response = await client.post(
        "/api/v1/copilot/chat", json={"message": "Is it safe to walk now?"}
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["source"] == "deterministic"
    assert data["citations"] == []
    assert "reading near you" in data["answer"]
    assert data["severity"] is None
    assert data["model"] is None


async def test_anonymous_with_location_gets_grounded_citations(
    app: FastAPI,
    client: AsyncClient,
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., ProviderReading],
    forecast_factory: Callable[..., object],
) -> None:
    app.state.air_provider = fake_provider(
        reading=reading_factory(pm2_5=140.0),
        forecast=forecast_factory(hours=24, pm2_5=75.0),
    )

    response = await client.post(
        "/api/v1/copilot/chat",
        json={"message": "When should we go outside today?", **CONTEXT},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["source"] == "deterministic"
    assert data["citations"]
    assert all(citation["fact_id"] for citation in data["citations"])
    assert all(citation["source"] for citation in data["citations"])
    assert data["disclaimer"]
    assert data["conversation_id"]
    assert data["message_id"]


async def test_conversations_are_scoped_to_the_profile(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., ProviderReading],
    forecast_factory: Callable[..., object],
) -> None:
    db_app.state.air_provider = fake_provider(
        reading=reading_factory(),
        forecast=forecast_factory(hours=24),
    )

    first = await db_client.post(
        "/api/v1/copilot/chat",
        headers=auth_headers,
        json={"message": "What should we do indoors?", **CONTEXT},
    )
    assert first.status_code == 200, first.text
    conversation_id = first.json()["data"]["conversation_id"]

    follow_up = await db_client.post(
        "/api/v1/copilot/chat",
        headers=auth_headers,
        json={
            "message": "And for a child?",
            "conversation_id": conversation_id,
            **CONTEXT,
        },
    )
    assert follow_up.status_code == 200
    assert follow_up.json()["data"]["conversation_id"] == conversation_id

    other = await db_client.post(
        "/api/v1/sessions",
        json={"consent_version": "2026-11", "health_consent": False},
    )
    other_headers = {"Authorization": f"Bearer {other.json()['data']['token']}"}
    crossed = await db_client.post(
        "/api/v1/copilot/chat",
        headers=other_headers,
        json={
            "message": "Show me the other conversation.",
            "conversation_id": conversation_id,
            **CONTEXT,
        },
    )
    assert crossed.status_code == 404
    assert crossed.json()["code"] == "NOT_FOUND"

    async with db_app.state.database.session() as session:
        count = await session.scalar(select(func.count()).select_from(AiMessage))
    assert count == 4


async def test_invalid_model_output_falls_back_and_is_recorded(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., ProviderReading],
    forecast_factory: Callable[..., object],
) -> None:
    db_app.state.air_provider = fake_provider(
        reading=reading_factory(),
        forecast=forecast_factory(hours=24),
    )
    db_app.state.settings.gemini_api_key = SecretStr("test-key-not-used")
    db_app.state.gemini = _FakeGemini("{not valid json")

    response = await db_client.post(
        "/api/v1/copilot/chat",
        headers=auth_headers,
        json={"message": "What is the outlook?", **CONTEXT},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["source"] == "deterministic"
    assert data["model"] is None

    async with db_app.state.database.session() as session:
        stored = await session.scalar(
            select(AiMessage).where(AiMessage.role == "assistant")
        )
    assert stored is not None
    assert stored.validation == "rejected"


async def test_valid_model_output_is_accepted_with_server_built_citations(
    db_app: FastAPI,
    db_client: AsyncClient,
    auth_headers: dict[str, str],
    fake_provider: Callable[..., object],
    reading_factory: Callable[..., ProviderReading],
    forecast_factory: Callable[..., object],
) -> None:
    db_app.state.air_provider = fake_provider(
        reading=reading_factory(),
        forecast=forecast_factory(hours=24),
    )
    db_app.state.settings.gemini_api_key = SecretStr("test-key-not-used")
    payload = json.dumps(
        {
            "answer": "Conditions are reported for your saved area.",
            "actions": [
                {
                    "title": "Check the reading",
                    "detail": "Review the current reading before going out.",
                    "fact_refs": ["aq.current.pm2_5"],
                    "confidence": "high",
                }
            ],
            "avoid": [],
        }
    )
    db_app.state.gemini = _FakeGemini(payload)

    response = await db_client.post(
        "/api/v1/copilot/chat",
        headers=auth_headers,
        json={"message": "What is the outlook?", **CONTEXT},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["source"] == "ai"
    assert data["model"] == "fake-model"
    assert data["latency_ms"] == 12
    assert data["citations"]


async def test_validation_flag_uses_a_database_allowed_value(app: FastAPI) -> None:
    """Rejected model output must be stored as 'rejected', not an integer.

    The ``ai_messages.validation`` column has a check constraint allowing only
    ``valid``, ``rejected`` or ``fallback``.
    """
    app.state.settings.gemini_api_key = SecretStr("test-key-not-used")
    pack = FactPack(facts=[], context={}, engine={})

    _, source, model, _, _, _, validation, _ = await _answer(
        pack,
        [],
        "What is the outlook?",
        app.state.settings,
        _FakeGemini("{not valid json"),
        None,
    )

    assert source == "deterministic"
    assert model is None
    assert validation == "rejected"


async def test_empty_message_is_rejected(client: AsyncClient) -> None:
    response = await client.post("/api/v1/copilot/chat", json={"message": "   "})

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_message_rate_limit_is_enforced(
    app: FastAPI,
    client: AsyncClient,
    fake_provider: Callable[..., object],
) -> None:
    app.state.air_provider = fake_provider()
    app.state.settings.copilot_messages_per_hour = 1

    first = await client.post("/api/v1/copilot/chat", json={"message": "Hello"})
    second = await client.post("/api/v1/copilot/chat", json={"message": "Again"})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["retry-after"]


@pytest.mark.parametrize("message", ["a" * 801])
async def test_overlong_message_is_rejected(client: AsyncClient, message: str) -> None:
    response = await client.post("/api/v1/copilot/chat", json={"message": message})

    assert response.status_code == 422
