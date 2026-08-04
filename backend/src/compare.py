from __future__ import annotations

from typing import Any

from src.models import (
    ATTRIBUTE_COLUMNS,
    AttributeResult,
    Brawler,
    MatchStatus,
    SuperTagResult,
)

_ORIGINAL_15 = "Original 15"


def _super_tags(value: Any) -> frozenset[str]:
    text = "" if value is None else str(value)
    return frozenset(tag.strip() for tag in text.split(",") if tag.strip())


def _ordered_super_tags(value: Any) -> tuple[str, ...]:
    """Comma-split tags in order, dropping empties and later duplicates."""
    text = "" if value is None else str(value)
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in text.split(","):
        tag = raw.strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        ordered.append(tag)
    return tuple(ordered)


def _compare_super(
    guess_value: Any, answer_value: Any
) -> tuple[MatchStatus, tuple[SuperTagResult, ...]]:
    guess_tags = _super_tags(guess_value)
    answer_tags = _super_tags(answer_value)
    if guess_tags == answer_tags:
        status = MatchStatus.MATCH
    elif guess_tags & answer_tags:
        status = MatchStatus.PARTIAL
    else:
        status = MatchStatus.MISS

    tags = tuple(
        SuperTagResult(
            value=tag,
            status=(
                MatchStatus.MATCH if tag in answer_tags else MatchStatus.MISS
            ),
        )
        for tag in _ordered_super_tags(guess_value)
    )
    return status, tags


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
        tags: tuple[SuperTagResult, ...] | None = None
        if column == "Super Type":
            status, tags = _compare_super(guess_value, answer_value)
        elif column == "brawler number":
            status = _compare_brawler_number(guess_value, answer_value)
        else:
            status = (
                MatchStatus.MATCH
                if guess_value == answer_value
                else MatchStatus.MISS
            )
        results.append(
            AttributeResult(
                column=column,
                value=guess_value,
                status=status,
                tags=tags,
            )
        )
    return tuple(results)
