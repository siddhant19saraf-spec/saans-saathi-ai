"""RFC 9457 problem details shared by all error responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProblemDetail(BaseModel):
    type: str = Field(description="URI identifying the problem type")
    title: str = Field(description="Short, human-readable summary")
    status: int = Field(description="HTTP status code")
    detail: str = Field(description="Human-readable explanation")
    instance: str = Field(description="Request path where the problem occurred")
    code: str = Field(description="Stable machine-readable error code")
    request_id: str | None = Field(
        default=None,
        description="Correlation ID to quote when reporting the problem",
    )


class FieldError(BaseModel):
    field: str
    message: str
    type: str
