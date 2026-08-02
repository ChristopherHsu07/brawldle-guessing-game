from __future__ import annotations

import difflib
import sys

from src.catalog import BrawlerCatalog
from src.models import ATTRIBUTE_COLUMNS, GameStatus, GuessResult, MatchStatus
from src.session import GameAlreadyOverError, GameSession, InvalidGuessError

# ANSI colors
_RESET = "\033[0m"
_GREEN = "\033[42m\033[30m"  # black on green
_GRAY = "\033[100m\033[97m"  # white on gray
_BOLD = "\033[1m"
_DIM = "\033[2m"

_SHORT_HEADERS = {
    "brawler number": "Brawler Number",
    "Role": "Role",
    "Rarity": "Rarity",
    "Attack Range": "Range",
    "Gender": "Gender",
    "Attacks per Ammo": "Ammo",
    "Super Type": "Super",
}


def _colorize(text: str, status: MatchStatus, width: int) -> str:
    padded = f" {text} ".center(width)
    if status == MatchStatus.MATCH:
        return f"{_GREEN}{padded}{_RESET}"
    return f"{_GRAY}{padded}{_RESET}"


def _column_widths(history: list[GuessResult]) -> dict[str, int]:
    widths: dict[str, int] = {}
    for col_index, col in enumerate(ATTRIBUTE_COLUMNS):
        header = _SHORT_HEADERS[col]
        max_val = max(
            (len(str(g.attributes[col_index].value)) for g in history),
            default=0,
        )
        # +2 for padding spaces inside the cell
        widths[col] = max(len(header), max_val) + 2
    name_w = max((len(g.guess_name) for g in history), default=6)
    widths["_name"] = max(name_w, 6) + 2
    return widths


def format_history(history: list[GuessResult]) -> str:
    if not history:
        return ""
    widths = _column_widths(history)
    name_w = widths["_name"]

    header_parts = [f"{'Guess':<{name_w}}"]
    for col in ATTRIBUTE_COLUMNS:
        header_parts.append(_SHORT_HEADERS[col].center(widths[col]))
    lines = ["  ".join(header_parts), _DIM + "─" * (sum(widths.values()) + 2 * len(widths)) + _RESET]

    for guess in history:
        row = [f"{guess.guess_name:<{name_w}}"]
        for i, col in enumerate(ATTRIBUTE_COLUMNS):
            attr = guess.attributes[i]
            row.append(_colorize(str(attr.value), attr.status, widths[col]))
        lines.append("  ".join(row))
    return "\n".join(lines)


def _suggest(name: str, catalog: BrawlerCatalog) -> str | None:
    matches = difflib.get_close_matches(
        name.strip(), catalog.all_names(), n=1, cutoff=0.6
    )
    return matches[0] if matches else None


def _print_help() -> None:
    cols = ", ".join(_SHORT_HEADERS[c] for c in ATTRIBUTE_COLUMNS)
    print(
        f"""
{_BOLD}Brawldle{_RESET} — guess the brawler by their stats.

Commands:
  help          Show this message
  quit / exit   Leave the game

Each guess shows your brawler's attributes:
  {_GREEN} green {_RESET}  = matches the answer
  {_GRAY} gray  {_RESET}  = does not match

Attributes: {cols}

Unlimited guesses until you get it right.
""".strip()
    )


def play_round(catalog: BrawlerCatalog) -> None:
    session = GameSession.new(catalog)
    print(f"\n{_BOLD}New round{_RESET} — {len(catalog)} brawlers. Type a name to guess.\n")

    while session.status == GameStatus.IN_PROGRESS:
        try:
            raw = input("Guess a brawler: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            sys.exit(0)

        if not raw:
            continue
        lower = raw.casefold()
        if lower in {"quit", "exit"}:
            print("Bye!")
            sys.exit(0)
        if lower == "help":
            _print_help()
            continue

        try:
            result = session.make_guess(raw)
        except InvalidGuessError:
            suggestion = _suggest(raw, catalog)
            msg = f"Unknown brawler {raw!r}."
            if suggestion:
                msg += f" Did you mean {suggestion}?"
            print(msg)
            continue
        except GameAlreadyOverError as exc:
            print(exc)
            break

        print()
        print(format_history(session.history))
        print()

        if result.correct:
            n = session.guess_count
            guesses_word = "guess" if n == 1 else "guesses"
            print(
                f"{_BOLD}You got it!{_RESET} {result.guess_name} "
                f"in {n} {guesses_word}."
            )


def run() -> None:
    catalog = BrawlerCatalog()
    print(f"{_BOLD}=== Brawldle ==={_RESET}")
    _print_help()

    while True:
        play_round(catalog)
        try:
            again = input("\nPlay again? [Y/n] ").strip().casefold()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            return
        if again in {"n", "no", "quit", "exit"}:
            print("Bye!")
            return


if __name__ == "__main__":
    run()
