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
    lobby: str = "all"         # "all" or "contested"
    window: str = "all"        # "all", "week" or "yesterday"

    meta: dict = field(default_factory=dict)

    @property
    def contested_only(self) -> bool:
        return self.lobby == "contested"

    @property
    def qualified(self) -> pd.DataFrame:
        """Characters with enough games for average-based rankings."""
        return self.totals[self.totals["games"] >= self.min_games]

    @property
    def period_label(self) -> str:
        # No %-d / %#d: those are platform specific, so strip the zero by hand.
        if self.matches.empty:
            return "no matches"
        a, b = self.matches["ts"].min(), self.matches["ts"].max()
        if (a.year, a.month) == (b.year, b.month):
            return f"{a.day}–{b.day} {b:%b %Y}"
        return f"{a.day} {a:%b} – {b.day} {b:%b %Y}"

    def games_phrase(self, noun: str = "matches") -> str:
        """The match threshold as a sentence fragment: "10 matches", "1 match".

        A window narrow enough to drop the threshold to one used to read "at
        least 1 decided matches", so the wording lives here rather than being
        typed out at each of the dozen places that quote it.
        """
        if self.min_games == 1:
            noun = noun.replace("matches", "match")
        return f"{self.min_games} {noun}"

    @property
    def min_pickups(self) -> int:
        """Attempts a conversion rate needs, scaled to the window.

        25 pickups is a fortnight's worth and unreachable in an evening, so the
        floor rides on the match threshold: full over the whole period, three at
        the least, which still keeps a single lucky grab off the board.
        """
        return max(3, round(data.MIN_PICKUPS * self.min_games / 10))

    def source_note(self, extra: str = "") -> str:
        """One short provenance line, plus only the notes a chart really needs.

        Keep `extra` to what the reader cannot infer from the chart itself:
        sample sizes, exclusions, and units. No restating of the title.
        """
        base = f"19pvp export · {self.period_label} · {self.tz}"
        if self.contested_only:
            base += (f" · contested lobbies only "
                     f"({data.CONTESTED_PER_TEAM}+ real players per team)")
        return f"{base}\n{extra}" if extra else base


# Used where the bot fill actually limits the reading of a chart. Every real
# player is in the export - arena confirms it, where all 1,113 2v2 matches carry
# exactly four rows - so a recorded team is its complete human side, and the
# missing slots were bots rather than missing data.
TRACKING_CAVEAT = (
    "Bots are not in the export, so a team's recorded players are its humans and the "
    "remaining slots were bots."
)


def contested_events(matches: pd.DataFrame) -> pd.Index:
    """Matches both teams turned up to with a near-full roster of real players."""
    return matches[(matches["tracked_team0"] >= data.CONTESTED_PER_TEAM)
                   & (matches["tracked_team1"] >= data.CONTESTED_PER_TEAM)].index


DAY_MS = 86_400_000

# Windows the charts can be rendered over, matching the ones the page offers:
# name -> (days, offset in days off the newest one). The newest day is always a
# partial one, so a single day means the last complete one.
WINDOWS = {"all": None, "week": (7, 0), "yesterday": (1, 1)}


def window_range(w, window: str, anchor: int | None = None):
    """[from, to) in epoch ms for `window`, cut on UTC day boundaries.

    Anchored on the moment of the build rather than on the newest match. The
    newest match drifts: play carries past midnight some nights and stops before
    it on others, so "the last complete day" landed on different days depending
    on whether anyone was still queuing at one in the morning. The build happens
    once and both the charts and the page are handed the same instant.
    """
    spec = WINDOWS.get(window)
    if spec is None or (anchor is None and w.empty):
        return None
    days, offset = spec
    base = int(anchor) if anchor is not None else int(w["at"].max())
    # Never anchor past the data. The export is fetched at build time so the two
    # normally agree, but if it ever lags a day the build anchor would open a
    # window with nothing in it - and an empty window has no period to label.
    if not w.empty:
        base = min(base, int(w["at"].max()) + DAY_MS)
    day_start = base // DAY_MS * DAY_MS
    lo = day_start - (days - 1 + offset) * DAY_MS
    hi = day_start - (offset - 1) * DAY_MS if offset else None
    return lo, hi


def build(csv_path: Path, outdir: Path, tz: str = "UTC", min_games: int = 10,
          lobby: str = "all", window: str = "all",
          anchor: int | None = None) -> Ctx:
    """Build the shared context.

    `lobby="contested"` drops every match that bots had to fill, and `window`
    narrows to a slice of days - both rebuild the aggregates from what is left,
    the same code path over a smaller frame.
    """
    raw = data.load_raw(csv_path, tz=tz)
    w = data.wsg(raw)
    if lobby == "contested":
        keep = contested_events(data.matches(w))
        w = w[w["eventId"].isin(keep)].copy()
        raw = raw[(raw["kind"] != "wsg") | raw["eventId"].isin(keep)].copy()
    elif lobby != "all":
        raise ValueError(f"unknown lobby filter: {lobby!r}")

    if window not in WINDOWS:
        raise ValueError(f"unknown window: {window!r}")
    rng = window_range(w, window, anchor)
    if rng is not None:
        lo, hi = rng

        def inside(at):
            keep = at >= lo
            return keep if hi is None else (keep & (at < hi))

        # The whole export, arena included. Cutting only the WSG rows would leave
        # the arena charts covering the full period under a one-day heading, and
        # the day count - which the overview divides by - reading nine days for a
        # window one day long.
        w = w[inside(w["at"])].copy()
        raw = raw[inside(raw["at"])].copy()
    return Ctx(
        source=csv_path,
        lobby=lobby,
        window=window,
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
