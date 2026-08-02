from __future__ import annotations

from pathlib import Path

import pytest

from src.catalog import BrawlerCatalog
from src.compare import compare_guess
from src.models import ATTRIBUTE_COLUMNS, GameStatus, MatchStatus
from src.session import GameAlreadyOverError, GameSession, InvalidGuessError

CSV_PATH = Path(__file__).resolve().parent.parent / "brawlers.csv"


@pytest.fixture
def catalog() -> BrawlerCatalog:
    return BrawlerCatalog(CSV_PATH)


def test_catalog_loads_brawlers(catalog: BrawlerCatalog) -> None:
    assert len(catalog) >= 100
    shelly = catalog.get_by_name("Shelly")
    assert shelly is not None
    assert shelly.name == "Shelly"
    assert shelly.attributes["Role"] == "Damage Dealer"


def test_catalog_case_insensitive_lookup(catalog: BrawlerCatalog) -> None:
    assert catalog.get_by_name("shelly") is not None
    assert catalog.get_by_name("  SHELLY  ") is not None
    assert catalog.get_by_name("not-a-brawler") is None


def test_compare_binary_match_and_miss(catalog: BrawlerCatalog) -> None:
    shelly = catalog.get_by_name("Shelly")
    colt = catalog.get_by_name("Colt")
    assert shelly is not None and colt is not None

    results = compare_guess(colt, shelly)
    assert len(results) == len(ATTRIBUTE_COLUMNS)
    by_col = {r.column: r for r in results}

    # Same era / role / range / gender-ish patterns from CSV
    assert by_col["brawler number"].status == MatchStatus.MATCH
    assert by_col["Role"].status == MatchStatus.MATCH
    assert by_col["Attack Range"].status == MatchStatus.MATCH
    assert by_col["Rarity"].status == MatchStatus.MISS
    assert by_col["Attacks per Ammo"].value == 6
    assert by_col["Attacks per Ammo"].status == MatchStatus.MISS


def test_compare_identical_is_all_match(catalog: BrawlerCatalog) -> None:
    shelly = catalog.get_by_name("Shelly")
    assert shelly is not None
    results = compare_guess(shelly, shelly)
    assert all(r.status == MatchStatus.MATCH for r in results)


def test_session_invalid_guess_does_not_count(catalog: BrawlerCatalog) -> None:
    answer = catalog.get_by_name("Shelly")
    assert answer is not None
    session = GameSession.new(catalog, answer=answer)

    with pytest.raises(InvalidGuessError):
        session.make_guess("TotallyFake")
    assert session.guess_count == 0
    assert session.status == GameStatus.IN_PROGRESS


def test_session_win_path(catalog: BrawlerCatalog) -> None:
    answer = catalog.get_by_name("Shelly")
    assert answer is not None
    session = GameSession.new(catalog, answer=answer)

    miss = session.make_guess("Colt")
    assert not miss.correct
    assert session.status == GameStatus.IN_PROGRESS

    win = session.make_guess("shelly")
    assert win.correct
    assert session.status == GameStatus.WON
    assert session.guess_count == 2
    assert session.state().answer_name == "Shelly"
    assert session.to_dict()["status"] == "won"


def test_session_rejects_guess_after_win(catalog: BrawlerCatalog) -> None:
    answer = catalog.get_by_name("Shelly")
    assert answer is not None
    session = GameSession.new(catalog, answer=answer)
    session.make_guess("Shelly")

    with pytest.raises(GameAlreadyOverError):
        session.make_guess("Colt")
