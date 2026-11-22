from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain.family_rules import (
    RULES,
    ActivityWindow,
    ForecastHour,
    GuidanceBasis,
    PollutionSignal,
    Sensitivity,
    assess_activities,
)

TZ = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 11, 19, 8, 0, tzinfo=TZ)


def _signal(
    *,
    aqi: int | None = 250,
    category: str | None = "poor",
    pm2_5: float | None = 120.0,
    stale: bool = False,
    basis: GuidanceBasis = "cpcb_aqi",
    forecast_only: bool = False,
) -> PollutionSignal:
    return PollutionSignal(
        aqi=aqi,
        category=category,
        pm2_5=pm2_5,
        pm10=180.0,
        provider="Test provider",
        source_type="model_forecast",
        observed_at=NOW,
        fetched_at=NOW,
        age_minutes=5,
        stale=stale,
        aqi_partial=False,
        unavailable_reason=None,
        forecast_only=forecast_only,
        attribution=("Test provider",),
        guidance_basis=basis,
    )


def _window(**overrides: object) -> ActivityWindow:
    values: dict[str, object] = {
        "id": "walk",
        "title": "Morning walk",
        "activity": "walking",
        "start": "09:00",
        "duration_min": 45,
        "intensity": "light",
        "venue": "outdoor",
        "days": ("mon", "tue", "wed", "thu", "fri", "sat", "sun"),
        "flexibility_min": 60,
        "indoor_alternative": None,
        "transport_mode": None,
    }
    values.update(overrides)
    return ActivityWindow(**values)  # type: ignore[arg-type]


def _assess(
    signal: PollutionSignal,
    *,
    windows: list[ActivityWindow] | None = None,
    sensitive: bool = False,
    forecast: list[ForecastHour] | None = None,
):
    return assess_activities(
        signal=signal,
        windows=windows or [_window()],
        sensitivity=Sensitivity(
            has_children=sensitive,
            has_older_adults=False,
            has_health_flags=False,
        ),
        forecast=forecast or [],
        timezone="Asia/Kolkata",
        now=NOW,
    )


def test_missing_measurements_are_not_treated_as_zero() -> None:
    signal = _signal(aqi=None, category=None, pm2_5=None, basis="none")
    [result] = _assess(signal)

    assert result.rule_id == "FAM-001"
    assert result.action == "check_back"
    assert "No validated pollution reading" in result.reason
    assert any("No current or forecast" in note for note in result.uncertainty)
    assert result.confidence == "low"


def test_stale_measurements_are_never_treated_as_current() -> None:
    [result] = _assess(_signal(stale=True))

    assert result.rule_id == "FAM-002"
    assert result.action == "check_back"
    assert "stale" in result.reason
    assert any("stale" in note for note in result.uncertainty)


def test_sensitive_household_gets_a_more_cautious_rule() -> None:
    signal = _signal(aqi=75, category="satisfactory", pm2_5=45.0)
    window = _window(duration_min=90, intensity="vigorous")

    [general] = _assess(signal, windows=[window], sensitive=False)
    [sensitive] = _assess(signal, windows=[window], sensitive=True)

    assert (general.rule_id, general.action) == ("FAM-004", "proceed")
    assert (sensitive.rule_id, sensitive.action) == ("FAM-005", "reduce_exposure")


def test_poor_air_moves_a_sensitive_outdoor_activity_indoors() -> None:
    window = _window(
        activity="outdoor_play",
        title="Park play",
        intensity="moderate",
        indoor_alternative="Indoor play away from windows",
    )

    [result] = _assess(_signal(), windows=[window], sensitive=True)

    assert result.rule_id == "FAM-009"
    assert result.action == "move_indoor"
    assert result.alternative_activity == "Indoor play away from windows"


def test_active_commute_uses_the_commute_rule() -> None:
    window = _window(
        activity="school_commute",
        title="School run",
        transport_mode="walk",
        duration_min=30,
    )

    [result] = _assess(_signal(), windows=[window], sensitive=False)

    assert result.rule_id == "FAM-012"
    assert result.action == "reduce_exposure"
    assert result.alternative_activity is not None


def test_forecast_only_data_is_labelled_and_still_evaluated() -> None:
    signal = _signal(
        aqi=None,
        category="moderate",
        pm2_5=80.0,
        basis="pm25_band",
        forecast_only=True,
        stale=False,
    )

    [result] = _assess(signal, sensitive=True)

    assert result.rule_id == "FAM-007"
    assert result.action == "reduce_exposure"
    assert any("forecast" in note.lower() for note in result.uncertainty)
    assert result.confidence in {"medium", "low"}


def test_lower_forecast_window_is_suggested() -> None:
    window = _window(flexibility_min=240)
    forecast = [
        ForecastHour(
            time=(NOW + timedelta(hours=offset)).astimezone(ZoneInfo("UTC")),
            pm2_5=value,
        )
        for offset, value in enumerate([120.0, 110.0, 100.0, 20.0, 20.0, 20.0, 20.0])
    ]

    [result] = _assess(_signal(pm2_5=120.0), windows=[window], forecast=forecast)

    assert result.suggested_at is not None
    assert result.suggested_time == "11:00"
    assert any("forecast data" in note for note in result.uncertainty)


def test_indoor_activity_does_not_claim_outdoor_data() -> None:
    window = _window(activity="indoor_activity", title="Indoor workout", venue="indoor")

    [result] = _assess(_signal(), windows=[window])

    assert result.rule_id == "FAM-000"
    assert result.action == "proceed"
    assert "Outdoor readings do not describe indoor air" in result.reason


def test_engine_is_deterministic() -> None:
    signal = _signal()
    first = _assess(signal, sensitive=True)
    second = _assess(signal, sensitive=True)

    assert first == second


def test_every_rule_documents_its_evidence() -> None:
    for identifier, rule in RULES.items():
        assert rule.identifier == identifier
        assert rule.trigger
        assert rule.explanation
        assert rule.data_requirements
        if rule.evidence_status in {"official", "public_guidance"}:
            assert rule.evidence
        for evidence in rule.evidence:
            assert evidence.source
            assert evidence.note
