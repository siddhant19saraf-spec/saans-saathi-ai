"""Copilot conversations and messages.

Only server-generated structured output is stored in ``structured``; the raw
model response is never persisted.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.profile import utc_now


class AiConversation(Base):
    __tablename__ = "ai_conversations"
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="expiry_after_created"),
        CheckConstraint(
            "context_lat_key IS NULL OR context_lat_key BETWEEN -90 AND 90",
            name="lat_key_range",
        ),
        CheckConstraint(
            "context_lon_key IS NULL OR context_lon_key BETWEEN -180 AND 180",
            name="lon_key_range",
        ),
        Index("ix_ai_conversations_profile", "profile_id"),
        Index("ix_ai_conversations_expiry", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    profile_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    context_lat_key: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    context_lon_key: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class AiMessage(Base):
    __tablename__ = "ai_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user','assistant')", name="role_allowed"),
        CheckConstraint(
            "validation IS NULL OR validation IN ('valid','rejected','fallback')",
            name="validation_allowed",
        ),
        CheckConstraint("btrim(content) <> ''", name="content_present"),
        CheckConstraint(
            "input_tokens IS NULL OR input_tokens >= 0",
            name="input_tokens_non_negative",
        ),
        CheckConstraint(
            "output_tokens IS NULL OR output_tokens >= 0",
            name="output_tokens_non_negative",
        ),
        CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0", name="latency_non_negative"
        ),
        CheckConstraint(
            "fact_pack_hash IS NULL OR char_length(fact_pack_hash) = 64",
            name="fact_pack_hash_length",
        ),
        Index("ix_ai_messages_conv", "conversation_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    fact_pack_hash: Mapped[str | None] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(80))
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    validation: Mapped[str | None] = mapped_column(String(16))
    error_code: Mapped[str | None] = mapped_column(String(48))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
