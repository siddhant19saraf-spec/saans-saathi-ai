"""IndoorShield persistence helpers.

Every query is scoped by ``household_id`` where the caller is authenticated.
Transactions are owned by the service layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.indoor import (
    IndoorActionEvent,
    IndoorAssessment,
    IndoorRecommendation,
    IndoorRoom,
    IndoorSensor,
    IndoorSensorReading,
    IndoorSource,
)

# -- assessments ------------------------------------------------------------


async def create_assessment(
    session: AsyncSession,
    *,
    household_id: UUID,
    values: dict[str, Any],
) -> IndoorAssessment:
    assessment = IndoorAssessment(household_id=household_id, **values)
    session.add(assessment)
    await session.flush()
    return assessment


async def get_assessment(
    session: AsyncSession, *, household_id: UUID, assessment_id: UUID
) -> IndoorAssessment | None:
    return await session.scalar(
        select(IndoorAssessment).where(
            IndoorAssessment.id == assessment_id,
            IndoorAssessment.household_id == household_id,
        )
    )


async def latest_assessment(
    session: AsyncSession, *, household_id: UUID
) -> IndoorAssessment | None:
    return await session.scalar(
        select(IndoorAssessment)
        .where(IndoorAssessment.household_id == household_id)
        .order_by(IndoorAssessment.created_at.desc(), IndoorAssessment.id.desc())
        .limit(1)
    )


async def list_assessments(
    session: AsyncSession, *, household_id: UUID, limit: int, offset: int = 0
) -> list[IndoorAssessment]:
    statement = (
        select(IndoorAssessment)
        .where(IndoorAssessment.household_id == household_id)
        .order_by(IndoorAssessment.created_at.desc(), IndoorAssessment.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list((await session.scalars(statement)).all())


async def delete_assessment(
    session: AsyncSession, assessment: IndoorAssessment
) -> None:
    await session.delete(assessment)
    await session.flush()


async def replace_rooms(
    session: AsyncSession, *, assessment_id: UUID, rooms: list[dict[str, Any]]
) -> None:
    await session.execute(
        delete(IndoorRoom).where(IndoorRoom.assessment_id == assessment_id)
    )
    for position, room in enumerate(rooms):
        session.add(IndoorRoom(assessment_id=assessment_id, position=position, **room))
    await session.flush()


async def list_rooms(session: AsyncSession, *, assessment_id: UUID) -> list[IndoorRoom]:
    statement = (
        select(IndoorRoom)
        .where(IndoorRoom.assessment_id == assessment_id)
        .order_by(IndoorRoom.position, IndoorRoom.created_at)
    )
    return list((await session.scalars(statement)).all())


async def replace_sources(
    session: AsyncSession, *, assessment_id: UUID, sources: list[dict[str, Any]]
) -> None:
    await session.execute(
        delete(IndoorSource).where(IndoorSource.assessment_id == assessment_id)
    )
    for source in sources:
        session.add(IndoorSource(assessment_id=assessment_id, **source))
    await session.flush()


async def list_sources(
    session: AsyncSession, *, assessment_id: UUID
) -> list[IndoorSource]:
    statement = (
        select(IndoorSource)
        .where(IndoorSource.assessment_id == assessment_id)
        .order_by(IndoorSource.code)
    )
    return list((await session.scalars(statement)).all())


# -- sensors ----------------------------------------------------------------


async def get_sensor(
    session: AsyncSession, *, household_id: UUID, sensor_id: UUID
) -> IndoorSensor | None:
    return await session.scalar(
        select(IndoorSensor).where(
            IndoorSensor.id == sensor_id,
            IndoorSensor.household_id == household_id,
        )
    )


async def get_sensor_by_identity(
    session: AsyncSession, *, provider: str, external_id: str
) -> IndoorSensor | None:
    return await session.scalar(
        select(IndoorSensor).where(
            IndoorSensor.provider == provider,
            IndoorSensor.external_id == external_id,
        )
    )


async def list_sensors(
    session: AsyncSession, *, household_id: UUID, include_inactive: bool = False
) -> list[IndoorSensor]:
    statement = select(IndoorSensor).where(IndoorSensor.household_id == household_id)
    if not include_inactive:
        statement = statement.where(IndoorSensor.status == "active")
    statement = statement.order_by(IndoorSensor.created_at, IndoorSensor.id)
    return list((await session.scalars(statement)).all())


def add_sensor(
    session: AsyncSession, *, household_id: UUID, values: dict[str, Any]
) -> IndoorSensor:
    sensor = IndoorSensor(household_id=household_id, **values)
    session.add(sensor)
    return sensor


# -- readings ---------------------------------------------------------------


async def add_reading(
    session: AsyncSession, *, values: dict[str, Any]
) -> IndoorSensorReading:
    reading = IndoorSensorReading(**values)
    session.add(reading)
    await session.flush()
    return reading


async def latest_reading(
    session: AsyncSession, *, sensor_id: UUID, pollutant: str
) -> IndoorSensorReading | None:
    return await session.scalar(
        select(IndoorSensorReading)
        .where(
            IndoorSensorReading.sensor_id == sensor_id,
            IndoorSensorReading.pollutant == pollutant,
        )
        .order_by(IndoorSensorReading.measured_at.desc())
        .limit(1)
    )


async def list_readings(
    session: AsyncSession, *, sensor_id: UUID, limit: int
) -> list[IndoorSensorReading]:
    statement = (
        select(IndoorSensorReading)
        .where(IndoorSensorReading.sensor_id == sensor_id)
        .order_by(
            IndoorSensorReading.measured_at.desc(),
            IndoorSensorReading.id.desc(),
        )
        .limit(limit)
    )
    return list((await session.scalars(statement)).all())


async def recent_readings(
    session: AsyncSession, *, household_id: UUID, limit: int = 200
) -> list[IndoorSensorReading]:
    statement = (
        select(IndoorSensorReading)
        .where(IndoorSensorReading.household_id == household_id)
        .order_by(
            IndoorSensorReading.measured_at.desc(),
            IndoorSensorReading.id.desc(),
        )
        .limit(limit)
    )
    return list((await session.scalars(statement)).all())


# -- recommendations --------------------------------------------------------


async def replace_pending_recommendations(
    session: AsyncSession,
    *,
    assessment_id: UUID,
    household_id: UUID,
    values: list[dict[str, Any]],
) -> None:
    await session.execute(
        delete(IndoorRecommendation).where(
            IndoorRecommendation.assessment_id == assessment_id,
            IndoorRecommendation.status == "pending",
        )
    )
    for item in values:
        session.add(
            IndoorRecommendation(
                assessment_id=assessment_id,
                household_id=household_id,
                **item,
            )
        )
    await session.flush()


async def list_recommendations(
    session: AsyncSession,
    *,
    household_id: UUID,
    assessment_id: UUID | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[IndoorRecommendation]:
    statement = select(IndoorRecommendation).where(
        IndoorRecommendation.household_id == household_id
    )
    if assessment_id is not None:
        statement = statement.where(IndoorRecommendation.assessment_id == assessment_id)
    if status is not None:
        statement = statement.where(IndoorRecommendation.status == status)
    statement = (
        statement.order_by(
            IndoorRecommendation.priority_score.desc(),
            IndoorRecommendation.created_at,
            IndoorRecommendation.rule_id,
        )
        .offset(offset)
        .limit(limit)
    )
    return list((await session.scalars(statement)).all())


async def get_recommendation(
    session: AsyncSession, *, household_id: UUID, recommendation_id: UUID
) -> IndoorRecommendation | None:
    return await session.scalar(
        select(IndoorRecommendation).where(
            IndoorRecommendation.id == recommendation_id,
            IndoorRecommendation.household_id == household_id,
        )
    )


async def add_action_event(
    session: AsyncSession,
    *,
    recommendation_id: UUID,
    household_id: UUID,
    event_type: str,
    previous_due_at: datetime | None,
    new_due_at: datetime | None,
    note: str | None,
) -> IndoorActionEvent:
    event = IndoorActionEvent(
        recommendation_id=recommendation_id,
        household_id=household_id,
        event_type=event_type,
        previous_due_at=previous_due_at,
        new_due_at=new_due_at,
        note=note,
    )
    session.add(event)
    await session.flush()
    return event


async def list_action_events(
    session: AsyncSession, *, recommendation_id: UUID, limit: int = 50
) -> list[IndoorActionEvent]:
    statement = (
        select(IndoorActionEvent)
        .where(IndoorActionEvent.recommendation_id == recommendation_id)
        .order_by(IndoorActionEvent.created_at.desc(), IndoorActionEvent.id.desc())
        .limit(limit)
    )
    return list((await session.scalars(statement)).all())
