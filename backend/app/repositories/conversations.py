"""Copilot conversation and message persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AiConversation, AiMessage


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(tz=UTC)


async def get_conversation(
    session: AsyncSession,
    *,
    conversation_id: UUID,
    profile_id: UUID,
    now: datetime | None = None,
) -> AiConversation | None:
    """Return an unexpired conversation owned by the profile.

    Expired conversations are treated as absent so a client cannot continue a
    thread past its retention window.
    """
    return await session.scalar(
        select(AiConversation).where(
            AiConversation.id == conversation_id,
            AiConversation.profile_id == profile_id,
            AiConversation.expires_at > _now(now),
        )
    )


async def get_conversation_by_id(
    session: AsyncSession, conversation_id: UUID
) -> AiConversation | None:
    return await session.get(AiConversation, conversation_id)


async def latest_conversation(
    session: AsyncSession,
    profile_id: UUID,
    *,
    now: datetime | None = None,
) -> AiConversation | None:
    return await session.scalar(
        select(AiConversation)
        .where(
            AiConversation.profile_id == profile_id,
            AiConversation.expires_at > _now(now),
        )
        .order_by(AiConversation.last_message_at.desc())
        .limit(1)
    )


async def create_conversation(
    session: AsyncSession,
    *,
    profile_id: UUID,
    expires_at: datetime,
    lat_key: Decimal | None,
    lon_key: Decimal | None,
) -> AiConversation:
    conversation = AiConversation(
        profile_id=profile_id,
        expires_at=expires_at,
        context_lat_key=lat_key,
        context_lon_key=lon_key,
    )
    session.add(conversation)
    await session.flush()
    return conversation


async def touch_conversation(
    session: AsyncSession, conversation: AiConversation, now: datetime
) -> None:
    conversation.last_message_at = now
    await session.flush()


async def add_message(
    session: AsyncSession,
    *,
    conversation_id: UUID,
    role: str,
    content: str,
    structured: dict[str, object] | None = None,
    fact_pack_hash: str | None = None,
    model: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    latency_ms: int | None = None,
    validation: str | None = None,
    error_code: str | None = None,
) -> AiMessage:
    message = AiMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        structured=structured,
        fact_pack_hash=fact_pack_hash,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        validation=validation,
        error_code=error_code,
    )
    session.add(message)
    await session.flush()
    return message


async def list_messages(
    session: AsyncSession, conversation_id: UUID, *, limit: int = 50
) -> list[AiMessage]:
    statement = (
        select(AiMessage)
        .where(AiMessage.conversation_id == conversation_id)
        .order_by(AiMessage.created_at)
        .limit(limit)
    )
    return list((await session.scalars(statement)).all())


async def recent_user_messages(
    session: AsyncSession, conversation_id: UUID, *, limit: int = 4
) -> list[str]:
    statement = (
        select(AiMessage.content)
        .where(
            AiMessage.conversation_id == conversation_id,
            AiMessage.role == "user",
        )
        .order_by(AiMessage.created_at.desc())
        .limit(limit)
    )
    rows = list((await session.scalars(statement)).all())
    return list(reversed(rows))


async def delete_conversation(
    session: AsyncSession, *, conversation_id: UUID, profile_id: UUID
) -> bool:
    conversation = await get_conversation(
        session, conversation_id=conversation_id, profile_id=profile_id
    )
    if conversation is None:
        return False
    await session.delete(conversation)
    await session.flush()
    return True


async def delete_conversations_for_profile(
    session: AsyncSession, profile_id: UUID
) -> None:
    await session.execute(
        delete(AiConversation).where(AiConversation.profile_id == profile_id)
    )
    await session.flush()
