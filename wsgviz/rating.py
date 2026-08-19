"""Derived per-character measures that need the match sequence, not just totals.

Totals answer "how much"; these answer "against whom", "in what order" and
"with whom" - the things a sports page leads with.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Elo constants. K is deliberately modest: a WSG result is a ten-a-side outcome
# that one player only partly controls, so a single match should not swing a
# rating far.
ELO_START = 1500.0
ELO_K = 24.0


def elo_ratings(decided: pd.DataFrame) -> pd.Series:
    """Opponent-adjusted rating from match outcomes, in chronological order.

    Each side is rated by the mean of its recorded players, and everyone on a
    side moves by the same amount. Bots are unrated and simply absent, so a
    match with few real players carries the same weight as a full one - the
    rating says who beat whom, not how hard it was.
    """
    rating: dict[int, float] = {}
    for _, g in decided.sort_values("at").groupby("eventId", sort=False):
        sides = list(g.groupby("team"))
        if len(sides) != 2:
            continue
        (_, a), (_, b) = sides
        ra = float(np.mean([rating.get(p, ELO_START) for p in a["playerGuid"]]))
        rb = float(np.mean([rating.get(p, ELO_START) for p in b["playerGuid"]]))
        expected_a = 1.0 / (1.0 + 10.0 ** ((rb - ra) / 400.0))
        score_a = 1.0 if a["win"].iloc[0] == 1 else 0.0
        for p in a["playerGuid"]:
            rating[p] = rating.get(p, ELO_START) + ELO_K * (score_a - expected_a)
        for p in b["playerGuid"]:
            rating[p] = rating.get(p, ELO_START) + ELO_K * ((1 - score_a) - (1 - expected_a))
    return pd.Series(rating, name="elo", dtype=float)


def streaks(decided: pd.DataFrame) -> pd.DataFrame:
    """Current run and the longest winning and losing runs per character."""
    rows = []
    for guid, g in decided.sort_values("at").groupby("playerGuid"):
        wins = g["win"].to_numpy()
        best_w = best_l = run_w = run_l = 0
        for v in wins:
            run_w, run_l = (run_w + 1, 0) if v == 1 else (0, run_l + 1)
            best_w, best_l = max(best_w, run_w), max(best_l, run_l)
        # A positive current streak counts wins, a negative one losses.
        current = run_w if run_w else -run_l
        rows.append((guid, current, best_w, best_l))
    return pd.DataFrame(rows, columns=["playerGuid", "current", "best_win",
                                       "best_loss"]).set_index("playerGuid")


def _pairs(decided: pd.DataFrame, same_team: bool) -> pd.DataFrame:
    """Every ordered pair of characters that shared a match, as opponents or
    as team mates, with the first one's result."""
    cols = ["eventId", "playerGuid", "team", "win"]
    a = decided[cols]
    both = a.merge(a, on="eventId", suffixes=("", "_o"))
    if same_team:
        both = both[(both["team"] == both["team_o"])
                    & (both["playerGuid"] != both["playerGuid_o"])]
    else:
        both = both[both["team"] != both["team_o"]]
    return both


def head_to_head(decided: pd.DataFrame, min_meetings: int = 6) -> pd.DataFrame:
    """Record against each opponent faced at least `min_meetings` times."""
    both = _pairs(decided, same_team=False)
    g = both.groupby(["playerGuid", "playerGuid_o"])["win"].agg(["size", "sum"])
    g = g[g["size"] >= min_meetings]
    g.columns = ["played", "won"]
    g["lost"] = g["played"] - g["won"]
    return g.reset_index().rename(columns={"playerGuid_o": "opponent"})


def duos(decided: pd.DataFrame, min_together: int = 8) -> pd.DataFrame:
    """Record alongside each team mate met at least `min_together` times."""
    both = _pairs(decided, same_team=True)
    g = both.groupby(["playerGuid", "playerGuid_o"])["win"].agg(["size", "sum"])
    g = g[g["size"] >= min_together]
    g.columns = ["played", "won"]
    g["lost"] = g["played"] - g["won"]
    return g.reset_index().rename(columns={"playerGuid_o": "mate"})
