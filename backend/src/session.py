from __future__ import annotations

import random
from dataclasses import dataclass

from src.catalog import BrawlerCatalog
from src.compare import compare_guess
from src.models import Brawler, GameState, GameStatus, GuessResult


class InvalidGuessError(ValueError):
    """Raised when the guess is not a known brawler name."""


class GameAlreadyOverError(RuntimeError):
    """Raised when guessing after the round is already won."""


@dataclass
class GameSession:
    catalog: BrawlerCatalog
    answer: Brawler
    history: list[GuessResult]
    status: GameStatus

    @classmethod
    def new(
        cls,
        catalog: BrawlerCatalog,
        *,
        answer: Brawler | None = None,
        rng: random.Random | None = None,
    ) -> GameSession:
        if answer is None:
            picker = rng or random
            answer = picker.choice(catalog.all())
        return cls(
            catalog=catalog,
            answer=answer,
            history=[],
            status=GameStatus.IN_PROGRESS,
        )

    @property
    def guess_count(self) -> int:
        return len(self.history)

    def make_guess(self, name: str) -> GuessResult:
        if self.status != GameStatus.IN_PROGRESS:
            raise GameAlreadyOverError("This round is already over.")

        guess = self.catalog.get_by_name(name)
        if guess is None:
            raise InvalidGuessError(f"Unknown brawler: {name!r}")

        attributes = compare_guess(guess, self.answer)
        correct = guess.name.casefold() == self.answer.name.casefold()
        result = GuessResult(
            guess_name=guess.name,
            attributes=attributes,
            correct=correct,
        )
        self.history.append(result)
        if correct:
            self.status = GameStatus.WON
        return result

    def state(self, *, reveal_answer: bool = False) -> GameState:
        show_answer = reveal_answer or self.status == GameStatus.WON
        return GameState(
            status=self.status,
            guess_count=self.guess_count,
            history=list(self.history),
            answer_name=self.answer.name if show_answer else None,
        )

    def to_dict(self, *, reveal_answer: bool = False) -> dict:
        return self.state(reveal_answer=reveal_answer).to_dict()
