from __future__ import annotations

import pytest

from app.domain.carbon import (
    BUS_FACTOR_KEY,
    CAR_PETROL_L_PER_100KM,
    REMOTE_WORK_COMMUTE_KM_PER_DAY,
    TWO_WHEELER_L_PER_100KM,
    activity_co2e,
    car_kg_per_km,
    transport_co2e,
    two_wheeler_kg_per_km,
)
from app.domain.factors import get_factor

PETROL = get_factor("petrol_combustion")


def test_car_emissions_use_the_sourced_factor() -> None:
    result = transport_co2e(mode="car", distance_km=10)

    assert result is not None
    expected = 10 * CAR_PETROL_L_PER_100KM / 100.0 * PETROL.value
    assert result.kg_co2e == pytest.approx(expected, abs=1e-4)
    assert result.factor_key == "petrol_combustion"
    assert result.factor_version
    assert result.factor_source_url.startswith("https://")


def test_two_wheeler_emissions_use_the_sourced_factor() -> None:
    result = transport_co2e(mode="two-wheeler", distance_km=5)

    assert result is not None
    expected = 5 * TWO_WHEELER_L_PER_100KM / 100.0 * PETROL.value
    assert result.kg_co2e == pytest.approx(expected, abs=1e-4)
    assert result.factor_value == pytest.approx(two_wheeler_kg_per_km(), abs=1e-6)
    assert car_kg_per_km() > two_wheeler_kg_per_km()


@pytest.mark.parametrize("mode", ["walk", "cycle", "metro", "unknown"])
def test_modes_without_a_sourced_factor_return_none(mode: str) -> None:
    assert transport_co2e(mode=mode, distance_km=8) is None


def test_bus_emissions_use_the_sourced_defra_factor() -> None:
    result = transport_co2e(mode="bus", distance_km=8)

    assert result is not None
    factor = get_factor(BUS_FACTOR_KEY)
    assert result.kg_co2e == pytest.approx(8 * factor.value, abs=1e-4)
    assert result.factor_key == BUS_FACTOR_KEY
    assert result.factor_version
    assert result.factor_source_url.startswith("https://")


def test_negative_distance_is_rejected() -> None:
    with pytest.raises(ValueError):
        transport_co2e(mode="car", distance_km=-1)


def test_walked_activity_offsets_a_car_trip() -> None:
    result = activity_co2e(activity_type="walked", quantity=4)

    assert result is not None
    expected = 4 * CAR_PETROL_L_PER_100KM / 100.0 * PETROL.value
    assert result.kg_co2e == pytest.approx(expected, abs=1e-4)


def test_remote_work_uses_the_documented_commute_assumption() -> None:
    result = activity_co2e(activity_type="worked-from-home", quantity=2)

    assert result is not None
    expected = (
        2
        * REMOTE_WORK_COMMUTE_KM_PER_DAY
        * CAR_PETROL_L_PER_100KM
        / 100.0
        * PETROL.value
    )
    assert result.kg_co2e == pytest.approx(expected, abs=1e-4)


def test_unsupported_activity_returns_none() -> None:
    assert activity_co2e(activity_type="recycled", quantity=1) is None


def test_non_positive_quantity_is_rejected() -> None:
    with pytest.raises(ValueError):
        activity_co2e(activity_type="walked", quantity=0)
