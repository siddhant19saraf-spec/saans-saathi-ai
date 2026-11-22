"""Carbon estimation with explicit factor provenance.

Only sourced factors appear in the registry. Transport modes without a
sourced factor return ``None`` instead of an invented number.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.factors import Factor, get_factor

# Product assumptions, labelled as such in API responses and never presented
# as measured fleet data.
CAR_PETROL_L_PER_100KM = 7.0
TWO_WHEELER_L_PER_100KM = 2.5
REMOTE_WORK_COMMUTE_KM_PER_DAY = 16.0

PETROL_FACTOR_KEY = "petrol_combustion"
DIESEL_FACTOR_KEY = "diesel_combustion"
GRID_INDIA_KEY = "grid_india_cea_v22"
BUS_FACTOR_KEY = "bus_average_uk_defra_2023"
TRAIN_FACTOR_KEY = "train_national_rail_uk_defra_2023"


@dataclass(frozen=True)
class CarbonResult:
    kg_co2e: float
    factor_key: str
    factor_value: float
    factor_unit: str
    factor_version: str
    factor_source_url: str


@dataclass(frozen=True)
class TransportCarbonResult:
    """Per-passenger carbon result for a transport mode.

    ``per_passenger_kg_co2e`` is the emissions allocated to one passenger.
    ``total_kg_co2e`` is the total vehicle emissions before allocation.
    ``passengers`` documents how many passengers the total is shared across.
    """

    mode: str
    distance_km: float
    passengers: int
    total_kg_co2e: float
    per_passenger_kg_co2e: float
    factor_key: str
    factor_value: float
    factor_unit: str
    factor_version: str
    factor_source_url: str
    allocation_method: str


def _result(kg: float, factor: Factor, applied_value: float) -> CarbonResult:
    return CarbonResult(
        kg_co2e=round(kg, 4),
        factor_key=factor.key,
        factor_value=applied_value,
        factor_unit=factor.unit,
        factor_version=factor.version,
        factor_source_url=str(factor.source_url),
    )


def car_kg_per_km() -> float:
    petrol = get_factor(PETROL_FACTOR_KEY)
    return CAR_PETROL_L_PER_100KM / 100.0 * petrol.value


def two_wheeler_kg_per_km() -> float:
    petrol = get_factor(PETROL_FACTOR_KEY)
    return TWO_WHEELER_L_PER_100KM / 100.0 * petrol.value


def transport_co2e(*, mode: str, distance_km: float) -> CarbonResult | None:
    """Return emissions for a mode, or ``None`` when no sourced factor exists."""
    if distance_km < 0:
        raise ValueError("Distance cannot be negative.")
    if mode in {"walk", "cycle"}:
        return None
    petrol = get_factor(PETROL_FACTOR_KEY)
    if mode == "car":
        kg = distance_km * CAR_PETROL_L_PER_100KM / 100.0 * petrol.value
        return _result(kg, petrol, round(car_kg_per_km(), 6))
    if mode == "two-wheeler":
        kg = distance_km * TWO_WHEELER_L_PER_100KM / 100.0 * petrol.value
        return _result(kg, petrol, round(two_wheeler_kg_per_km(), 6))
    if mode == "bus":
        factor = get_factor(BUS_FACTOR_KEY)
        # DEFRA factor is per-passenger-km; return emissions for one passenger.
        kg = distance_km * factor.value
        return _result(kg, factor, factor.value)
    if mode == "train":
        factor = get_factor(TRAIN_FACTOR_KEY)
        # DEFRA factor is per-passenger-km; return emissions for one passenger.
        kg = distance_km * factor.value
        return _result(kg, factor, factor.value)
    # Metro and shared-mobility lack verified factors; a null is honest.
    return None


def transport_co2e_per_passenger(
    *,
    mode: str,
    distance_km: float,
    passengers: int,
) -> TransportCarbonResult | None:
    """Return per-passenger emissions with documented allocation.

    For car and two-wheeler, total vehicle emissions are divided evenly
    across passengers. Walk and cycle report zero per-passenger emissions.
    Modes without a verified factor return ``None``.
    """
    if distance_km < 0:
        raise ValueError("Distance cannot be negative.")
    if passengers < 1:
        raise ValueError("Passenger count must be at least 1.")
    if mode in {"walk", "cycle"}:
        return TransportCarbonResult(
            mode=mode,
            distance_km=distance_km,
            passengers=passengers,
            total_kg_co2e=0.0,
            per_passenger_kg_co2e=0.0,
            factor_key=PETROL_FACTOR_KEY,
            factor_value=get_factor(PETROL_FACTOR_KEY).value,
            factor_unit=get_factor(PETROL_FACTOR_KEY).unit,
            factor_version=get_factor(PETROL_FACTOR_KEY).version,
            factor_source_url=str(get_factor(PETROL_FACTOR_KEY).source_url),
            allocation_method="zero-emission mode; no fuel consumed",
        )
    petrol = get_factor(PETROL_FACTOR_KEY)
    if mode == "car":
        total_kg = distance_km * CAR_PETROL_L_PER_100KM / 100.0 * petrol.value
        per_passenger = total_kg / passengers
        return TransportCarbonResult(
            mode=mode,
            distance_km=distance_km,
            passengers=passengers,
            total_kg_co2e=round(total_kg, 4),
            per_passenger_kg_co2e=round(per_passenger, 4),
            factor_key=PETROL_FACTOR_KEY,
            factor_value=round(car_kg_per_km(), 6),
            factor_unit=petrol.unit,
            factor_version=petrol.version,
            factor_source_url=str(petrol.source_url),
            allocation_method="total vehicle emissions divided equally across passengers",
        )
    if mode == "two-wheeler":
        total_kg = distance_km * TWO_WHEELER_L_PER_100KM / 100.0 * petrol.value
        per_passenger = total_kg / passengers
        return TransportCarbonResult(
            mode=mode,
            distance_km=distance_km,
            passengers=passengers,
            total_kg_co2e=round(total_kg, 4),
            per_passenger_kg_co2e=round(per_passenger, 4),
            factor_key=PETROL_FACTOR_KEY,
            factor_value=round(two_wheeler_kg_per_km(), 6),
            factor_unit=petrol.unit,
            factor_version=petrol.version,
            factor_source_url=str(petrol.source_url),
            allocation_method="total vehicle emissions divided equally across passengers",
        )
    if mode == "bus":
        factor = get_factor(BUS_FACTOR_KEY)
        # DEFRA factor is already per-passenger-km; passenger count does not
        # change the per-passenger rate (it reflects average occupancy).
        per_passenger = distance_km * factor.value
        return TransportCarbonResult(
            mode=mode,
            distance_km=distance_km,
            passengers=passengers,
            total_kg_co2e=round(per_passenger * passengers, 4),
            per_passenger_kg_co2e=round(per_passenger, 4),
            factor_key=BUS_FACTOR_KEY,
            factor_value=factor.value,
            factor_unit=factor.unit,
            factor_version=factor.version,
            factor_source_url=str(factor.source_url),
            allocation_method=(
                "DEFRA per-passenger-km factor multiplied by distance; "
                "already reflects average bus occupancy."
            ),
        )
    if mode == "train":
        factor = get_factor(TRAIN_FACTOR_KEY)
        # DEFRA factor is already per-passenger-km.
        per_passenger = distance_km * factor.value
        return TransportCarbonResult(
            mode=mode,
            distance_km=distance_km,
            passengers=passengers,
            total_kg_co2e=round(per_passenger * passengers, 4),
            per_passenger_kg_co2e=round(per_passenger, 4),
            factor_key=TRAIN_FACTOR_KEY,
            factor_value=factor.value,
            factor_unit=factor.unit,
            factor_version=factor.version,
            factor_source_url=str(factor.source_url),
            allocation_method=(
                "DEFRA per-passenger-km factor multiplied by distance; "
                "already reflects average rail occupancy."
            ),
        )
    # Metro, shared-mobility and custom modes lack verified factors;
    # return None rather than invent a value.
    return None


def activity_co2e(*, activity_type: str, quantity: float) -> CarbonResult | None:
    """Estimate logged activity emissions.

    Supported activities have a complete, documented derivation. Unsupported
    types return ``None`` and the API rejects them with a clear code.
    """
    if quantity <= 0:
        raise ValueError("Quantity must be positive.")
    if activity_type == "walked":
        petrol = get_factor(PETROL_FACTOR_KEY)
        kg = quantity * CAR_PETROL_L_PER_100KM / 100.0 * petrol.value
        return _result(kg, petrol, round(car_kg_per_km(), 6))
    if activity_type == "worked-from-home":
        petrol = get_factor(PETROL_FACTOR_KEY)
        kg = (
            quantity
            * REMOTE_WORK_COMMUTE_KM_PER_DAY
            * CAR_PETROL_L_PER_100KM
            / 100.0
            * petrol.value
        )
        return _result(kg, petrol, round(car_kg_per_km(), 6))
    return None


__all__ = [
    "CAR_PETROL_L_PER_100KM",
    "DIESEL_FACTOR_KEY",
    "GRID_INDIA_KEY",
    "PETROL_FACTOR_KEY",
    "REMOTE_WORK_COMMUTE_KM_PER_DAY",
    "TWO_WHEELER_L_PER_100KM",
    "CarbonResult",
    "TransportCarbonResult",
    "activity_co2e",
    "car_kg_per_km",
    "transport_co2e",
    "transport_co2e_per_passenger",
    "two_wheeler_kg_per_km",
]
