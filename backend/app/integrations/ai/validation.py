"""Fail-closed validation of model output.

A rejected answer is never shown to the user; the caller substitutes the
deterministic fallback. Citations are built from the FactPack by the caller,
never copied from the model.
"""

from __future__ import annotations

import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.domain.facts import FactPack

Confidence = Literal["high", "medium", "low"]

_URL_PATTERN = re.compile(r"https?://|www\.", re.IGNORECASE)
_HTML_PATTERN = re.compile(r"<[^>]+>")
_CODE_FENCE_PATTERN = re.compile(r"```")
_MEDICAL_PATTERN = re.compile(
    r"\b(diagnos\w*|cure[sd]?|dosage|prescri\w*)\b", re.IGNORECASE
)
_POLLUTANT_PATTERN = re.compile(
    r"\bpm\s*[._]?\s*2[._]?5\b|\bpm\s*10\b|\bno2\b|\bso2\b|\bo3\b|\bco2\b",
    re.IGNORECASE,
)
_TIME_PATTERN = re.compile(r"\b\d{1,2}:\d{2}\b")
_NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?")


class DraftAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=60)
    detail: str = Field(min_length=1, max_length=160)
    time_window: str | None = Field(default=None, max_length=20)
    fact_refs: list[str] = Field(min_length=1, max_length=5)
    confidence: Confidence = "medium"


class DraftAvoid(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=80)
    reason_fact_ref: str | None = None


class AiDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1, max_length=600)
    actions: list[DraftAction] = Field(default_factory=list, max_length=5)
    avoid: list[DraftAvoid] = Field(default_factory=list, max_length=3)


class DraftValidationError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def parse_and_validate(text: str, pack: FactPack) -> AiDraft:
    try:
        payload = json.loads(text)
    except ValueError as exc:
        raise DraftValidationError("invalid_json") from exc
    if not isinstance(payload, dict):
        raise DraftValidationError("invalid_json")

    actions = payload.get("actions")
    avoid = payload.get("avoid")
    if isinstance(actions, list):
        payload["actions"] = actions[:5]
    if isinstance(avoid, list):
        payload["avoid"] = avoid[:3]

    try:
        draft = AiDraft.model_validate(payload)
    except ValidationError as exc:
        raise DraftValidationError("schema") from exc

    known_facts = pack.ids()
    for action in draft.actions:
        for fact_ref in action.fact_refs:
            if fact_ref not in known_facts:
                raise DraftValidationError("unknown_fact_ref")
    for item in draft.avoid:
        if item.reason_fact_ref is not None and item.reason_fact_ref not in known_facts:
            raise DraftValidationError("unknown_fact_ref")

    draft = _strip_unsafe(draft)
    if not _numbers_grounded(draft, pack):
        raise DraftValidationError("ungrounded_number")
    return draft


def _unsafe(text: str) -> bool:
    return bool(
        _URL_PATTERN.search(text)
        or _HTML_PATTERN.search(text)
        or _CODE_FENCE_PATTERN.search(text)
        or _MEDICAL_PATTERN.search(text)
    )


def _strip_unsafe(draft: AiDraft) -> AiDraft:
    answer_lines = [line for line in draft.answer.splitlines() if not _unsafe(line)]
    answer = "\n".join(answer_lines).strip()
    if not answer:
        raise DraftValidationError("unsafe_content")
    actions = [
        action
        for action in draft.actions
        if not _unsafe(action.title) and not _unsafe(action.detail)
    ]
    avoid = [item for item in draft.avoid if not _unsafe(item.title)]
    return AiDraft(answer=answer, actions=actions, avoid=avoid)


def _numbers_grounded(draft: AiDraft, pack: FactPack) -> bool:
    values = list(pack.numeric_values().values())
    texts = [draft.answer]
    for action in draft.actions:
        texts.extend([action.title, action.detail])
    for item in draft.avoid:
        texts.append(item.title)

    for text in texts:
        cleaned = _POLLUTANT_PATTERN.sub("", text)
        cleaned = _TIME_PATTERN.sub("", cleaned)
        for match in _NUMBER_PATTERN.findall(cleaned):
            number = float(match)
            if number.is_integer() and 0 <= number <= 24:
                continue
            if any(
                abs(number - value) <= max(abs(value) * 0.01, 0.0001)
                for value in values
            ):
                continue
            return False
    return True
