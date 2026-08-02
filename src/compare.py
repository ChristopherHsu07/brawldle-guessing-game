from __future__ import annotations

from src.models import ATTRIBUTE_COLUMNS, AttributeResult, Brawler, MatchStatus


def compare_guess(guess: Brawler, answer: Brawler) -> tuple[AttributeResult, ...]:
    """Binary match/miss comparison for each clue attribute."""
    results: list[AttributeResult] = []
    for column in ATTRIBUTE_COLUMNS:
        guess_value = guess.attribute_value(column)
        answer_value = answer.attribute_value(column)
        status = (
            MatchStatus.MATCH if guess_value == answer_value else MatchStatus.MISS
        )
        results.append(
            AttributeResult(column=column, value=guess_value, status=status)
        )
    return tuple(results)
