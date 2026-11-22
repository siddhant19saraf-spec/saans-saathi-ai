"""Structured logging with secret redaction."""

from __future__ import annotations

import logging
import sys
from typing import Any, cast

import structlog
from structlog.types import EventDict, Processor

REDACTED = "[redacted]"

_SENSITIVE_KEYS = frozenset(
    {
        "authorization",
        "api_key",
        "apikey",
        "cookie",
        "database_url",
        "gemini_api_key",
        "password",
        "secret",
        "token",
    }
)


def _redact_processor(
    _logger: Any,
    _method_name: str,
    event_dict: EventDict,
) -> EventDict:
    for key in list(event_dict):
        if key.lower() in _SENSITIVE_KEYS:
            event_dict[key] = REDACTED
    return event_dict


def configure_logging(*, level: str, json_logs: bool) -> None:
    """Configure structlog and the standard library on a single JSON pipeline.

    Existing root handlers are replaced so repeated calls (tests, reloads) do
    not duplicate log lines.
    """
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _redact_processor,
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    renderer: Processor = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer(colors=False)
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

    # Let uvicorn's loggers flow through the same formatter instead of
    # emitting a second, differently shaped stream.
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.propagate = True


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
