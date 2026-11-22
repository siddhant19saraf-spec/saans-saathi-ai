"""Server-built FactPack: the only factual input the language model receives.

No coordinates, names, free-text notes or health labels are included.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Fact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=120)
    value: float | str | None = None
    unit: str | None = None
    category: str | None = None
    source: str
    observed_at: datetime | None = None
    at: datetime | None = None
    kind: str | None = None


class FactPack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facts: list[Fact] = Field(max_length=40)
    context: dict[str, Any] = Field(default_factory=dict)
    engine: dict[str, Any] = Field(default_factory=dict)

    def ids(self) -> set[str]:
        return {fact.id for fact in self.facts}

    def numeric_values(self) -> dict[str, float]:
        return {
            fact.id: float(fact.value)
            for fact in self.facts
            if isinstance(fact.value, (int, float)) and not isinstance(fact.value, bool)
        }

    def by_id(self, fact_id: str) -> Fact | None:
        for fact in self.facts:
            if fact.id == fact_id:
                return fact
        return None

    def find(self, fact_id: str) -> Fact | None:
        return self.by_id(fact_id)

    def sha256(self) -> str:
        canonical = json.dumps(
            self.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
