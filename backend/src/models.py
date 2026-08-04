from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


ATTRIBUTE_COLUMNS: tuple[str, ...] = (
    "brawler number",
    "Role",
    "Rarity",
    "Attack Range",
    "Gender",
    "Attacks per Ammo",
    "Super Type",
)


class MatchStatus(str, Enum):
    """Per-attribute feedback."""

    MATCH = "match"
    PARTIAL = "partial"
    HIGHER = "higher"
    LOWER = "lower"
    MISS = "miss"


class GameStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    WON = "won"


@dataclass(frozen=True)
class Brawler:
    id: int
    name: str
    attributes: dict[str, Any]

    def attribute_value(self, column: str) -> Any:
        return self.attributes[column]

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, **self.attributes}


@dataclass(frozen=True)
class SuperTagResult:
    value: str
    status: MatchStatus

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value, "status": self.status.value}


@dataclass(frozen=True)
class AttributeResult:
    column: str
    value: Any
    status: MatchStatus
    tags: tuple[SuperTagResult, ...] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "column": self.column,
            "value": self.value,
            "status": self.status.value,
        }
        if self.tags is not None:
            payload["tags"] = [t.to_dict() for t in self.tags]
        return payload


@dataclass(frozen=True)
class GuessResult:
    guess_name: str
    attributes: tuple[AttributeResult, ...]
    correct: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "guess_name": self.guess_name,
            "attributes": [a.to_dict() for a in self.attributes],
            "correct": self.correct,
        }


@dataclass
class GameState:
    status: GameStatus
    guess_count: int
    history: list[GuessResult] = field(default_factory=list)
    answer_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "guess_count": self.guess_count,
            "history": [g.to_dict() for g in self.history],
            "answer_name": self.answer_name,
        }
