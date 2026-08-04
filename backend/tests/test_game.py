from __future__ import annotations

from pathlib import Path

import pytest

from src.catalog import BrawlerCatalog
from src.compare import compare_guess
from src.models import ATTRIBUTE_COLUMNS, GameStatus, MatchStatus
from src.session import GameAlreadyOverError, GameSession, InvalidGuessError

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "brawlers.csv"


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
    # Damage overlaps Shelly's "CC, Damage" → partial, not miss
    assert by_col["Super Type"].status == MatchStatus.PARTIAL
    assert by_col["Super Type"].tags is not None
    assert [(t.value, t.status) for t in by_col["Super Type"].tags] == [
        ("Damage", MatchStatus.MATCH),
    ]


def test_compare_identical_is_all_match(catalog: BrawlerCatalog) -> None:
    shelly = catalog.get_by_name("Shelly")
    assert shelly is not None
    results = compare_guess(shelly, shelly)
    assert all(r.status == MatchStatus.MATCH for r in results)


def test_super_type_partial_and_miss(catalog: BrawlerCatalog) -> None:
    shelly = catalog.get_by_name("Shelly")  # CC, Damage
    colt = catalog.get_by_name("Colt")  # Damage
    bull = catalog.get_by_name("Bull")  # CC, Damage, Debuff, Mobility
    poco = catalog.get_by_name("Poco")  # Heal
    assert shelly and colt and bull and poco

    def super_result(guess_name: str, answer_name: str):
        guess = catalog.get_by_name(guess_name)
        answer = catalog.get_by_name(answer_name)
        assert guess and answer
        by_col = {r.column: r for r in compare_guess(guess, answer)}
        return by_col["Super Type"]

    shelly_self = super_result("Shelly", "Shelly")
    assert shelly_self.status == MatchStatus.MATCH
    assert [(t.value, t.status) for t in shelly_self.tags] == [
        ("CC", MatchStatus.MATCH),
        ("Damage", MatchStatus.MATCH),
    ]

    colt_vs_shelly = super_result("Colt", "Shelly")
    assert colt_vs_shelly.status == MatchStatus.PARTIAL
    assert [(t.value, t.status) for t in colt_vs_shelly.tags] == [
        ("Damage", MatchStatus.MATCH),
    ]

    bull_vs_shelly = super_result("Bull", "Shelly")
    assert bull_vs_shelly.status == MatchStatus.PARTIAL
    assert [(t.value, t.status) for t in bull_vs_shelly.tags] == [
        ("CC", MatchStatus.MATCH),
        ("Damage", MatchStatus.MATCH),
        ("Debuff", MatchStatus.MISS),
        ("Mobility", MatchStatus.MISS),
    ]

    poco_vs_colt = super_result("Poco", "Colt")
    assert poco_vs_colt.status == MatchStatus.MISS
    assert [(t.value, t.status) for t in poco_vs_colt.tags] == [
        ("Heal", MatchStatus.MISS),
    ]


def test_brawler_number_higher_lower(catalog: BrawlerCatalog) -> None:
    shelly = catalog.get_by_name("Shelly")  # Original 15
    colt = catalog.get_by_name("Colt")  # Original 15
    gene = catalog.get_by_name("Gene")  # 22
    griff = catalog.get_by_name("Griff")  # 50
    assert shelly and colt and gene and griff

    def number_result(guess_name: str, answer_name: str):
        guess = catalog.get_by_name(guess_name)
        answer = catalog.get_by_name(answer_name)
        assert guess and answer
        by_col = {r.column: r for r in compare_guess(guess, answer)}
        return by_col["brawler number"]

    gene_vs_shelly = number_result("Gene", "Shelly")
    assert gene_vs_shelly.status == MatchStatus.LOWER
    assert gene_vs_shelly.value == "22"

    shelly_vs_gene = number_result("Shelly", "Gene")
    assert shelly_vs_gene.status == MatchStatus.HIGHER
    assert shelly_vs_gene.value == "Original 15"

    shelly_vs_colt = number_result("Shelly", "Colt")
    assert shelly_vs_colt.status == MatchStatus.MATCH
    assert shelly_vs_colt.value == "Original 15"

    gene_vs_griff = number_result("Gene", "Griff")
    assert gene_vs_griff.status == MatchStatus.HIGHER
    assert gene_vs_griff.value == "22"


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
