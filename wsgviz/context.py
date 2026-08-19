"""A precomputed data context shared by every chart module.

Built once and passed around so no chart recomputes the aggregates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from . import data


@dataclass
class Ctx:
    source: Path
    tz: str
    raw: pd.DataFrame          # all modes
    wsg: pd.DataFrame          # WSG only, one row per player per match
    arena: pd.DataFrame        # 2v2 + 3v3
    matches: pd.DataFrame      # one row per WSG match
    totals: pd.DataFrame       # per-character aggregates (WSG)
    rates: pd.DataFrame        # player rows with per-minute columns
    min_games: int             # threshold for average-based leaderboards
    outdir: Path

    meta: dict = field(default_factory=dict)

    @property
    def qualified(self) -> pd.DataFrame:
        """Characters with enough games for average-based rankings."""
        return self.totals[self.totals["games"] >= self.min_games]

    @property
    def period_label(self) -> str:
        # No %-d / %#d: those are platform specific, so strip the zero by hand.
        a, b = self.matches["ts"].min(), self.matches["ts"].max()
        if (a.year, a.month) == (b.year, b.month):
            return f"{a.day}–{b.day} {b:%b %Y}"
        return f"{a.day} {a:%b} – {b.day} {b:%b %Y}"

    def source_note(self, extra: str = "") -> str:
        """One short provenance line, plus only the notes a chart really needs.

        Keep `extra` to what the reader cannot infer from the chart itself:
        sample sizes, exclusions, and units. No restating of the title.
        """
        base = f"19pvp export · {self.period_label} · {self.tz}"
        return f"{base}\n{extra}" if extra else base


# Used only where tracking actually limits the reading of a chart.
TRACKING_CAVEAT = (
    "Only addon-tracked real players are recorded; bots fill empty slots and are absent "
    "from the export, so team totals are samples."
)


def build(csv_path: Path, outdir: Path, tz: str = "UTC", min_games: int = 20) -> Ctx:
    raw = data.load_raw(csv_path, tz=tz)
    w = data.wsg(raw)
    return Ctx(
        source=csv_path,
        tz=tz,
        raw=raw,
        wsg=w,
        arena=data.arena(raw),
        matches=data.matches(w),
        totals=data.player_totals(w),
        rates=data.rates(w),
        min_games=min_games,
        outdir=outdir,
    )
