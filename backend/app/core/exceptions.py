"""Application error taxonomy and RFC 9457 problem responses.

Client-facing payloads never contain stack traces, SQL, or infrastructure
details. Log records carry the technical context instead.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

PROBLEM_MEDIA_TYPE = "application/problem+json"
_ERROR_TYPE_BASE = "https://saans-saathi.example/errors"

logger = get_logger(__name__)


class AppError(Exception):
    """Base class for expected, safe-to-expose application errors."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"
    title: str = "Internal server error"

    def __init__(
        self,
        detail: str | None = None,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.detail = detail or self.title
        self.headers = headers
        super().__init__(self.detail)


class BadRequestError(AppError):
    status_code = HTTPStatus.BAD_REQUEST
    code = "BAD_REQUEST"
    title = "Bad request"


class UnauthorizedError(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    code = "UNAUTHORIZED"
    title = "Authentication required"


class ForbiddenError(AppError):
    status_code = HTTPStatus.FORBIDDEN
    code = "FORBIDDEN"
    title = "Not permitted"


class ConsentRequiredError(ForbiddenError):
    code = "CONSENT_REQUIRED"
    title = "Health-data consent required"

    def __init__(self) -> None:
        super().__init__(
            "Health details can only be stored after explicit health-data consent."
        )


class NotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND
    code = "NOT_FOUND"
    title = "Resource not found"


class ConflictError(AppError):
    status_code = HTTPStatus.CONFLICT
    code = "CONFLICT"
    title = "Conflicting resource state"

    def __init__(self, detail: str | None = None, *, code: str | None = None) -> None:
        if code is not None:
            self.code = code
        super().__init__(detail)


class UnprocessableEntityError(AppError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    code = "UNPROCESSABLE_ENTITY"
    title = "Request cannot be processed"

    def __init__(self, detail: str | None = None, *, code: str | None = None) -> None:
        if code is not None:
            self.code = code
        super().__init__(detail)


class PayloadTooLargeError(AppError):
    status_code = HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    code = "PAYLOAD_TOO_LARGE"
    title = "Request body too large"


class RateLimitError(AppError):
    status_code = HTTPStatus.TOO_MANY_REQUESTS
    code = "RATE_LIMITED"
    title = "Too many requests"

    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            "Too many requests. Retry later.",
            headers={"Retry-After": str(retry_after_seconds)},
        )


class ServiceUnavailableError(AppError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "SERVICE_UNAVAILABLE"
    title = "Service temporarily unavailable"


class DatabaseUnavailableError(ServiceUnavailableError):
    code = "DATABASE_UNAVAILABLE"
    title = "Database unavailable"


class ProviderUnavailableError(ServiceUnavailableError):
    code = "PROVIDER_UNAVAILABLE"
    title = "Data provider unavailable"


def problem_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    title: str,
    detail: str,
    errors: list[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": f"{_ERROR_TYPE_BASE}/{code.lower()}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": request.url.path,
        "code": code,
        "request_id": getattr(request.state, "request_id", None),
    }
    if errors is not None:
        body["errors"] = errors
    return JSONResponse(
        status_code=status_code,
        content=body,
        media_type=PROBLEM_MEDIA_TYPE,
        headers=headers,
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    if exc.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
        logger.error("application_error", code=exc.code, detail=exc.detail)
    return problem_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        title=exc.title,
        detail=exc.detail,
        headers=exc.headers,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    status = HTTPStatus(exc.status_code)
    code = status.name.replace(" ", "_")
    return problem_response(
        request,
        status_code=exc.status_code,
        code=code,
        title=status.phrase,
        detail=str(exc.detail),
        headers=dict(exc.headers) if exc.headers else None,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    # Only location, message and error type are echoed. Pydantic's "input" and
    # "ctx" can contain secrets submitted by the client.
    errors = [
        {
            "field": ".".join(str(part) for part in error["loc"][1:]) or "body",
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return problem_response(
        request,
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        title="Request validation failed",
        detail="One or more request fields are invalid.",
        errors=errors,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_exception",
        method=request.method,
        path=request.url.path,
        error_type=type(exc).__name__,
    )
    return problem_response(
        request,
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        code="INTERNAL_ERROR",
        title="Internal server error",
        detail="An unexpected error occurred. Quote the request ID when reporting it.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
