from __future__ import annotations

from app.integrations.air_quality.circuit import CircuitBreaker


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def _breaker(clock: FakeClock) -> CircuitBreaker:
    return CircuitBreaker(
        failure_threshold=5,
        timeout_threshold=3,
        open_seconds=60,
        clock=clock,
    )


def test_closed_circuit_allows_calls() -> None:
    breaker = _breaker(FakeClock())

    assert breaker.state == "closed"
    assert breaker.allow() is True


def test_five_consecutive_failures_open_the_circuit() -> None:
    clock = FakeClock()
    breaker = _breaker(clock)

    for _ in range(4):
        breaker.record_failure(timeout=False)
        assert breaker.allow() is True
    breaker.record_failure(timeout=False)

    assert breaker.state == "open"
    assert breaker.allow() is False


def test_three_timeouts_within_the_window_open_the_circuit() -> None:
    clock = FakeClock()
    breaker = _breaker(clock)

    for step in range(3):
        clock.now += step * 10
        breaker.record_failure(timeout=True)

    assert breaker.state == "open"


def test_old_timeouts_age_out_of_the_window() -> None:
    clock = FakeClock()
    breaker = _breaker(clock)

    breaker.record_failure(timeout=True)
    breaker.record_failure(timeout=True)
    clock.now += 120
    breaker.record_failure(timeout=True)

    assert breaker.state == "closed"


def test_half_open_allows_exactly_one_probe_and_success_closes() -> None:
    clock = FakeClock()
    breaker = _breaker(clock)
    for _ in range(5):
        breaker.record_failure(timeout=False)

    clock.now += 61

    assert breaker.allow() is True
    assert breaker.state == "half_open"
    assert breaker.allow() is False

    breaker.record_success()

    assert breaker.state == "closed"
    assert breaker.allow() is True


def test_failed_probe_reopens_the_circuit() -> None:
    clock = FakeClock()
    breaker = _breaker(clock)
    for _ in range(5):
        breaker.record_failure(timeout=False)

    clock.now += 61
    assert breaker.allow() is True
    breaker.record_failure(timeout=False)

    assert breaker.state == "open"
    assert breaker.allow() is False
