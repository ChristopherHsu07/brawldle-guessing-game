from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.models import ATTRIBUTE_COLUMNS, Brawler

DEFAULT_CSV = Path(__file__).resolve().parent.parent / "data" / "brawlers.csv"


class BrawlerCatalog:
    """Load and look up brawlers from the answer-sheet CSV."""

    def __init__(self, csv_path: str | Path | None = None) -> None:
        path = Path(csv_path) if csv_path else DEFAULT_CSV
        df = pd.read_csv(path, header=0)
        missing = [c for c in ("id", "Name", *ATTRIBUTE_COLUMNS) if c not in df.columns]
        if missing:
            raise ValueError(f"CSV missing columns: {missing}")

        self._by_name: dict[str, Brawler] = {}
        self._brawlers: list[Brawler] = []

        for _, row in df.iterrows():
            name = str(row["Name"]).strip()
            attrs = {}
            for col in ATTRIBUTE_COLUMNS:
                value = row[col]
                if col == "Attacks per Ammo":
                    attrs[col] = int(value)
                else:
                    attrs[col] = value if pd.isna(value) else str(value).strip()
            brawler = Brawler(id=int(row["id"]), name=name, attributes=attrs)
            self._brawlers.append(brawler)
            self._by_name[name.casefold()] = brawler

    def __len__(self) -> int:
        return len(self._brawlers)

    def all(self) -> list[Brawler]:
        return list(self._brawlers)

    def all_names(self) -> list[str]:
        return [b.name for b in self._brawlers]

    def get_by_name(self, name: str) -> Brawler | None:
        return self._by_name.get(name.strip().casefold())
