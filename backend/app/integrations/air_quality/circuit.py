"""In-process circuit breaker for a single upstream provider."""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable

from app.core.logging import get_logger

logger = get_logger(__name__)


class CircuitBreaker:
    """Five consecutive failures or three timeouts in 60 s open the circuit.

    After the open window, exactly one probe is allowed. A success closes the
    circuit; a failure reopens it for another window. This is per process,
    which matches the single-instance deployment; it is not a distributed
    breaker.
    """

    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        timeout_threshold: int = 3,
        open_seconds: int = 60,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._timeout_threshold = timeout_threshold
        self._open_seconds = open_seconds
        self._clock = clock
        self._consecutive_failures = 0
        self._timeouts: deque[float] = deque()
        self._opened_at: float | None = None
        self._half_open = False

    @property
    def state(self) -> str:
        if self._opened_at is None:
            return "closed"
        return "half_open" if self._half_open else "open"

    def allow(self) -> bool:
        now = self._now()
        if self._opened_at is None:
            return True
        if now - self._opened_at < self._open_seconds:
            return False
        if not self._half_open:
            self._half_open = True
            return True
        return False

    def record_success(self) -> None:
        if self._opened_at is not None:
            logger.info("air_provider_circuit_closed")
        self._consecutive_failures = 0
        self._timeouts.clear()
        self._opened_at = None
        self._half_open = False

    def record_failure(self, *, timeout: bool) -> None:
        now = self._now()
        self._consecutive_failures += 1
        if timeout:
            self._timeouts.append(now)
        while self._timeouts and now - self._timeouts[0] > 60:
            self._timeouts.popleft()

        should_open = (
            self._consecutive_failures >= self._failure_threshold
            or len(self._timeouts) >= self._timeout_threshold
        )
        if should_open or self._half_open:
            self._opened_at = now
            self._half_open = False
            logger.warning("air_provider_circuit_open")

    def _now(self) -> float:
        return self._clock()
