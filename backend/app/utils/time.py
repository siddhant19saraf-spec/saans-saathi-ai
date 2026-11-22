"""UTC helper used across services and tests."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(tz=UTC)
