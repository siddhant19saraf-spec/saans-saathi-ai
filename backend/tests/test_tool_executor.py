"""Tool executor authorisation and failure-path tests.

Tool results are model-visible, so every handler must fail closed when the
session, profile or service it needs is missing.
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.integrations.ai.tool_executor import execute_tool


async def _run(
    name: str,
    arguments: dict[str, object],
    *,
    profile: object | None = None,
    session: object | None = None,
    air_service: object | None = None,
) -> dict[str, object]:
    return await execute_tool(
        tool_name=name,
        arguments=arguments,
        profile=profile,  # type: ignore[arg-type]
        session=session,  # type: ignore[arg-type]
        air_service=air_service,  # type: ignore[arg-type]
    )


async def test_unknown_tool_is_rejected() -> None:
    with pytest.raises(KeyError):
        await _run("delete_everything", {})


async def test_air_quality_requires_a_configured_service() -> None:
    result = await _run("get_air_quality", {"lat": 28.6, "lon": 77.2})

    assert result["status"] == "unavailable"
    assert "not available" in str(result["message"])


async def test_air_quality_without_coordinates_fails_closed() -> None:
    result = await _run(
        "get_air_quality",
        {},
        air_service=SimpleNamespace(),
    )

    assert result["status"] == "error"
    assert "No location" in str(result["message"])


async def test_tools_reject_another_profiles_id() -> None:
    profile = SimpleNamespace(id=uuid4())

    household = await _run(
        "get_household_profile",
        {"profile_id": str(uuid4())},
        profile=profile,
        session=SimpleNamespace(),
    )
    goals = await _run(
        "get_sustainability_goals",
        {"profile_id": str(uuid4())},
        profile=profile,
        session=SimpleNamespace(),
    )

    assert household["status"] == "unauthorized"
    assert goals["status"] == "unauthorized"


async def test_transport_tool_requires_a_valid_journey_id() -> None:
    result = await _run(
        "compare_transport_options",
        {"journey_id": "not-a-uuid"},
        profile=SimpleNamespace(id=uuid4()),
        session=SimpleNamespace(),
    )

    assert result["status"] == "error"
    assert "journey_id" in str(result["message"])


async def test_profile_scoped_tools_require_a_profile() -> None:
    for name in (
        "get_household_profile",
        "get_family_recommendations",
        "get_daily_routine",
        "get_indoor_recommendations",
        "get_impact_summary",
        "get_sustainability_goals",
    ):
        result = await _run(name, {})
        assert result["status"] == "error", name
        assert "profile" in str(result["message"]).lower(), name
