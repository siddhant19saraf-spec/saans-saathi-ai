from __future__ import annotations

import pytest

from app.domain.aqi import (
    AQI_CATEGORIES,
    AveragingInfo,
    category_for,
    evaluate_cpcb_aqi,
    required_hours,
    rolling_averages,
    sub_index,
)


def test_sub_index_reproduces_documented_examples() -> None:
    assert sub_index("pm2_5", 45.0) == pytest.approx(75.0)
    assert round(sub_index("pm2_5", 75.2)) == 151
    assert round(sub_index("pm2_5", 150.0)) == 323


def test_sub_index_converts_co_from_micrograms_to_milligrams() -> None:
    assert sub_index("co_ug_m3", 900.0) == pytest.approx(45.0)
    assert sub_index("co_ug_m3", 1000.0) == pytest.approx(50.0)


def test_sub_index_clamps_at_500() -> None:
    assert sub_index("pm2_5", 10_000.0) == 500.0
    assert sub_index("o3_ug_m3", 5_000.0) == 500.0


def test_category_boundaries() -> None:
    assert category_for(0) == AQI_CATEGORIES[0]
    assert category_for(50) == AQI_CATEGORIES[0]
    assert category_for(51) == AQI_CATEGORIES[1]
    assert category_for(100) == AQI_CATEGORIES[1]
    assert category_for(101) == AQI_CATEGORIES[2]
    assert category_for(200) == AQI_CATEGORIES[2]
    assert category_for(201) == AQI_CATEGORIES[3]
    assert category_for(300) == AQI_CATEGORIES[3]
    assert category_for(301) == AQI_CATEGORIES[4]
    assert category_for(400) == AQI_CATEGORIES[4]
    assert category_for(401) == AQI_CATEGORIES[5]


def test_required_hours_matches_cpcb_completeness() -> None:
    assert required_hours(24) == 16
    assert required_hours(8) == 6


def test_overall_aqi_requires_a_particle_anchor() -> None:
    series = {
        "no2_ug_m3": [80.0] * 24,
        "so2_ug_m3": [80.0] * 24,
        "o3_ug_m3": [100.0] * 8,
    }
    averages = rolling_averages(series)
    assessment = evaluate_cpcb_aqi(
        {key: value for key, (value, _info) in averages.items()},
        averaging=[info for _value, info in averages.values()],
    )
    assert assessment.aqi is None
    assert "PM2.5 or PM10" in (assessment.reason or "")


def test_overall_aqi_requires_three_complete_pollutants() -> None:
    series = {
        "pm2_5": [60.0] * 24,
        "pm10": [100.0] * 24,
        "no2_ug_m3": [80.0] * 12,
        "o3_ug_m3": [100.0] * 3,
    }
    averages = rolling_averages(series)
    assessment = evaluate_cpcb_aqi(
        {key: value for key, (value, _info) in averages.items()},
        averaging=[info for _value, info in averages.values()],
    )
    assert assessment.aqi is None
    assert "three pollutants" in (assessment.reason or "")


def test_incomplete_window_is_excluded_not_padded() -> None:
    series = {
        "pm2_5": [60.0] * 15,
        "pm10": [100.0] * 24,
        "no2_ug_m3": [80.0] * 24,
        "o3_ug_m3": [100.0] * 8,
    }
    averages = rolling_averages(series)
    assert averages["pm2_5"][1].valid_hours == 15
    assert averages["pm2_5"][1].complete is False
    assessment = evaluate_cpcb_aqi(
        {key: value for key, (value, _info) in averages.items()},
        averaging=[info for _value, info in averages.values()],
    )
    assert assessment.aqi is not None
    assert "pm2_5" not in assessment.aqi.coverage


def test_missing_hours_are_not_treated_as_zero() -> None:
    series = {"pm2_5": [None] * 10 + [60.0] * 14}
    averages = rolling_averages(series)
    value, info = averages["pm2_5"]
    assert info.valid_hours == 14
    assert info.complete is False
    assert value == pytest.approx(60.0)


def test_o3_above_208_uses_latest_one_hour_value() -> None:
    series = {"o3_ug_m3": [220.0] * 7 + [260.0]}
    averages = rolling_averages(series)
    value, info = averages["o3_ug_m3"]
    assert value == pytest.approx(260.0)
    assert info.method == "1h_override"
    assert info.window.startswith("1h")


def test_worst_sub_index_is_the_overall_aqi() -> None:
    series = {
        "pm2_5": [150.0] * 24,
        "pm10": [100.0] * 24,
        "no2_ug_m3": [80.0] * 24,
        "so2_ug_m3": [40.0] * 24,
        "co_ug_m3": [900.0] * 8,
        "o3_ug_m3": [100.0] * 8,
    }
    averages = rolling_averages(series)
    assessment = evaluate_cpcb_aqi(
        {key: value for key, (value, _info) in averages.items()},
        averaging=[info for _value, info in averages.values()],
    )
    assert assessment.aqi is not None
    assert assessment.aqi.value == 323
    assert assessment.aqi.dominant_pollutant == "pm2_5"
    assert assessment.aqi.category == "very_poor"
    assert assessment.aqi.partial is False
    assert "pm2_5" in assessment.aqi.coverage


def test_explicit_incomplete_averaging_blocks_computation() -> None:
    assessment = evaluate_cpcb_aqi(
        {"pm2_5": 150.0, "pm10": 100.0, "no2_ug_m3": 80.0},
        averaging=[
            AveragingInfo("pm2_5", "24h", 24, 16, 16),
            AveragingInfo("pm10", "24h", 24, 16, 16),
            AveragingInfo("no2_ug_m3", "24h", 24, 15, 16),
        ],
    )
    assert assessment.aqi is None
    assert "three pollutants" in (assessment.reason or "")


def test_rolling_averages_reject_non_hourly_cadence() -> None:
    with pytest.raises(ValueError, match="hourly"):
        rolling_averages({"pm2_5": [10.0]}, basis_hours=24)
