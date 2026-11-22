"""Anonymous device profile.

There is deliberately no name, email, phone or password column. The bearer
token is only ever stored as a SHA-256 digest.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    LargeBinary,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="expiry_after_created"),
        CheckConstraint(
            "deleted_at IS NULL OR deleted_at >= created_at",
            name="deleted_after_created",
        ),
        CheckConstraint("btrim(consent_version) <> ''", name="consent_version_present"),
        Index("ix_profiles_expires", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    token_hash: Mapped[bytes] = mapped_column(
        LargeBinary(32), nullable=False, unique=True
    )
    consent_version: Mapped[str] = mapped_column(String(32), nullable=False)
    health_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
