"""Success envelope shared by every endpoint."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class PaginationMeta(BaseModel):
    next_cursor: str | None = None
    has_more: bool = False


class ResponseMeta(BaseModel):
    request_id: str | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    pagination: PaginationMeta | None = None


class Envelope[T](BaseModel):
    data: T
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


def envelope[T](data: T, request_id: str | None = None) -> Envelope[T]:
    return Envelope[T](data=data, meta=ResponseMeta(request_id=request_id or None))
