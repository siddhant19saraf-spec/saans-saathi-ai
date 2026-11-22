"""Event-loop factory for running uvicorn without its Windows Proactor default.

psycopg's async connections refuse ``ProactorEventLoop``, and plain
``uvicorn app.main:app`` selects it on Windows (uvicorn only switches to a
selector loop when it spawns a reload/worker subprocess). Point uvicorn at this
factory when running without ``--reload``:

    uvicorn app.main:app --loop app.core.loop:selector_loop_factory
"""

from __future__ import annotations

import asyncio
import selectors
import sys


def selector_loop_factory() -> asyncio.AbstractEventLoop:
    if sys.platform == "win32":
        return asyncio.SelectorEventLoop(selectors.SelectSelector())
    return asyncio.new_event_loop()
