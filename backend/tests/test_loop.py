from __future__ import annotations

import asyncio
import sys

from app.core.loop import selector_loop_factory


def test_selector_loop_factory_builds_a_psycopg_compatible_loop() -> None:
    loop = selector_loop_factory()
    try:
        assert isinstance(loop, asyncio.AbstractEventLoop)
        if sys.platform == "win32":
            assert isinstance(loop, asyncio.SelectorEventLoop)
            assert not isinstance(loop, asyncio.ProactorEventLoop)
    finally:
        loop.close()
