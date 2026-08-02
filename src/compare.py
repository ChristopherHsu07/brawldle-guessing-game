from __future__ import annotations

from typing import Any

from src.models import ATTRIBUTE_COLUMNS, AttributeResult, Brawler, MatchStatus

_ORIGINAL_15 = "Original 15"


def _super_tags(value: Any) -> frozenset[str]:
    text = "" if value is None else str(value)
    return frozenset(tag.strip() for tag in text.split(",") if tag.strip())


def _compare_super(guess_value: Any, answer_value: Any) -> MatchStatus:
    guess_tags = _super_tags(guess_value)
    answer_tags = _super_tags(answer_value)
    if guess_tags == answer_tags:
        return MatchStatus.MATCH
    if guess_tags & answer_tags:
        return MatchStatus.PARTIAL
    return MatchStatus.MISS


def _brawler_number_rank(value: Any) -> int:
    """Original 15 shares rank 1; later brawlers use their roster number."""
    text = str(value).strip()
    if text == _ORIGINAL_15:
        return 1
    return int(text)


def _compare_brawler_number(guess_value: Any, answer_value: Any) -> MatchStatus:
    guess_rank = _brawler_number_rank(guess_value)
    answer_rank = _brawler_number_rank(answer_value)
    if guess_rank < answer_rank:
        return MatchStatus.HIGHER
    if guess_rank > answer_rank:
        return MatchStatus.LOWER
    return MatchStatus.MATCH


def compare_guess(guess: Brawler, answer: Brawler) -> tuple[AttributeResult, ...]:
    """Compare attributes with Super partial and brawler-number higher/lower."""
    results: list[AttributeResult] = []
    for column in ATTRIBUTE_COLUMNS:
        guess_value = guess.attribute_value(column)
        answer_value = answer.attribute_value(column)
        if column == "Super Type":
            status = _compare_super(guess_value, answer_value)
        elif column == "brawler number":
            status = _compare_brawler_number(guess_value, answer_value)
        else:
            status = (
                MatchStatus.MATCH
                if guess_value == answer_value
                else MatchStatus.MISS
            )
        results.append(
            AttributeResult(column=column, value=guess_value, status=status)
        )
    return tuple(results)
