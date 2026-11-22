"""Declarative base for ORM models.

No business tables are defined in this milestone. Models are added only with
the approved schema from docs/BLUEPRINT.md §6, together with a migration and
tests.
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class with deterministic constraint names for Alembic."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
