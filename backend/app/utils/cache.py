"""Bounded in-process TTL cache.

Only used for short-lived provider results; personal data is never cached
here. A separate API instance therefore cannot serve another instance's cache,
which is acceptable for modelled public data.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Callable


class TTLCache[V]:
    def __init__(
        self,
        *,
        maxsize: int = 256,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._maxsize = maxsize
        self._clock = clock
        self._entries: OrderedDict[str, tuple[float, V]] = OrderedDict()

    def get(self, key: str) -> V | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at <= self._clock():
            del self._entries[key]
            return None
        self._entries.move_to_end(key)
        return value

    def set(self, key: str, value: V, ttl_seconds: int) -> None:
        self._entries[key] = (self._clock() + ttl_seconds, value)
        self._entries.move_to_end(key)
        while len(self._entries) > self._maxsize:
            self._entries.popitem(last=False)

    def clear(self) -> None:
        self._entries.clear()
