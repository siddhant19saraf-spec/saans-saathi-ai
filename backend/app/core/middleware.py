"""Request correlation, access logging and defensive header handling."""

from __future__ import annotations

import json
import re
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

import structlog
from starlette.datastructures import Headers
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.exceptions import PROBLEM_MEDIA_TYPE
from app.core.logging import get_logger

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{8,64}$")
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a safe request ID and emit one structured access log per request."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        incoming = request.headers.get("X-Request-ID", "")
        request_id = (
            incoming if _REQUEST_ID_PATTERN.fullmatch(incoming) else self._new_id()
        )

        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=round((time.perf_counter() - started) * 1000, 2),
            )
            raise

        response.headers["X-Request-ID"] = request_id
        for name, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        # Personal endpoints must never be stored by shared caches. Public
        # reads opt into caching explicitly by setting the header first.
        response.headers.setdefault("Cache-Control", "no-store")
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=int(response.status_code),
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
        )
        return response

    @staticmethod
    def _new_id() -> str:
        return uuid4().hex


class BodySizeLimitMiddleware:
    """Reject oversized request bodies before any handler runs.

    Buffering up to the configured limit (32 KB by default) is safe for a JSON
    API and guarantees the client receives a problem document rather than a
    connection reset mid-response.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = Headers(scope=scope).get("content-length")
        if declared is not None:
            try:
                if int(declared) > self.max_bytes:
                    await self._reject(scope, send)
                    return
            except ValueError:
                pass

        body = b""
        while True:
            message = await receive()
            if message["type"] != "http.request":
                break
            body += message.get("body", b"")
            if len(body) > self.max_bytes:
                await self._reject(scope, send)
                return
            if not message.get("more_body", False):
                break

        replayed = False

        async def replay() -> Message:
            nonlocal replayed
            if replayed:
                return {"type": "http.disconnect"}
            replayed = True
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, replay, send)

    async def _reject(self, scope: Scope, send: Send) -> None:
        state = scope.get("state") or {}
        request_id = state.get("request_id")
        payload = {
            "type": "https://saans-saathi.example/errors/payload_too_large",
            "title": "Request body too large",
            "status": 413,
            "detail": f"Request bodies must not exceed {self.max_bytes} bytes.",
            "instance": scope.get("path", ""),
            "code": "PAYLOAD_TOO_LARGE",
            "request_id": request_id,
        }
        body = json.dumps(payload).encode("utf-8")
        headers = [
            (b"content-type", PROBLEM_MEDIA_TYPE.encode("ascii")),
            (b"content-length", str(len(body)).encode("ascii")),
            (b"cache-control", b"no-store"),
            (b"x-content-type-options", b"nosniff"),
        ]
        if isinstance(request_id, str):
            headers.append((b"x-request-id", request_id.encode("ascii", "ignore")))
        await send({"type": "http.response.start", "status": 413, "headers": headers})
        await send({"type": "http.response.body", "body": body})
