"""Per-process sliding-window rate limiting.

A single API instance owns one limiter. Limits protect unmetered public
endpoints and the metered AI dependency; they are intentionally in memory
because a shared store would add infrastructure the deployment does not have.
Proxy deployments must enable ``--proxy-headers`` so the client address is the
real caller, never a spoofable forwarded value read by this module.
"""

from __future__ import annotations

import math
import time
from collections import deque

_MAX_TRACKED_KEYS = 10_000


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}

    def consume(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
        now: float | None = None,
    ) -> int | None:
        """Record one event.

        Returns ``None`` when the request is allowed, otherwise the number of
        seconds to wait before retrying.
        """
        current = time.monotonic() if now is None else now
        window_start = current - window_seconds
        hits = self._hits.setdefault(key, deque())

        while hits and hits[0] <= window_start:
            hits.popleft()

        if len(hits) >= limit:
            retry_after = hits[0] + window_seconds - current
            return max(1, math.ceil(retry_after))

        hits.append(current)
        if len(self._hits) > _MAX_TRACKED_KEYS:
            self._prune(window_start)
        return None

    def reset(self) -> None:
        self._hits.clear()

    def _prune(self, window_start: float) -> None:
        stale = [
            key
            for key, hits in self._hits.items()
            if not hits or hits[-1] <= window_start
        ]
        for key in stale:
            del self._hits[key]
