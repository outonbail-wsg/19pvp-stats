"""WSG matches played by full lobbies of real (addon-tracked) players.

This server fills WSG with bots when too few real players queue, and bots are
not in the export, so a low count means bot slots rather than missing data.
Matches where both teams fielded at least CONTESTED_PER_TEAM real players are
therefore the closest thing to a full 10v10.

Caveat: a single match holds 10 per team, but up to 14 distinct players rotate
through a team when deserters are replaced, so "tracked per team" is distinct
players over the match, not a simultaneous count.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from .. import theme as T
from ..context import Ctx
from ..data import (CAPS_TO_WIN, CONTESTED_PER_TEAM, STATS_BY_COLUMN,
                    TIMER_SECONDS, fmt_duration)
from . import helpers as H

# Team-total stats compared between winning and losing side. bonusHonor/honor
# excluded (mechanically tied to the result).
TEAM_STATS = ["flagReturns", "damageOnEFC", "killingBlows", "successfulInterrupts",
              "dispelsDefensive", "hardCCCount", "damageDone", "healingDone",
              "absorbsDone", "damageTaken", "deaths"]


def _full_lobby_events(ctx: Ctx):
    m = ctx.matches
    mask = ((m["tracked_team0"] >= CONTESTED_PER_TEAM)
            & (m["tracked_team1"] >= CONTESTED_PER_TEAM))
    return m[mask]


def realgames_overview(ctx: Ctx):
    """Scope of full-lobby matches and their final-score distribution."""
    full = _full_lobby_events(ctx)
    ok = full[full["score_known"]]
    counts = ok["score"].value_counts().head(6)
    total = counts.sum()

    fig = plt.figure(figsize=(12.5, 6.2))
    top = T.figure_title(
        fig, "Full-lobby WSG matches",
        f"Matches where both teams fielded at least {CONTESTED_PER_TEAM} real players")
    bottom = T.footnote(fig, ctx.source_note(
        f"{len(full)} of {len(ctx.matches)} matches ({len(full)/len(ctx.matches)*100:.0f} %) "
        f"reach {CONTESTED_PER_TEAM} real players on both teams - the matches least "
        f"diluted by bots. Score panel uses the {len(ok)} of them that ran to a natural "
        f"end, on {CAPS_TO_WIN} captures or on the {TIMER_SECONDS // 60}-minute timer."))

    tiles = [
        (T.num(len(full)), "full-lobby matches", f">= {CONTESTED_PER_TEAM} real per team"),
        (fmt_duration(full.loc[full.duration > 0, "duration"].median()),
         "median length", "longest time played"),
        (f"{ok['capped_out'].mean()*100:.0f} %" if len(ok) else "–",
         f"end on {CAPS_TO_WIN} captures", "rest run out the timer"),
        (T.num(int(full["deserters"].sum())), "desertions", "across these matches"),
    ]
    for i, (v, lab, sub) in enumerate(tiles):
        H.stat_tile(fig, [0.05 + i * 0.235, top - 0.17, 0.20, 0.13], v, lab, sub)

    ax = fig.add_axes([0.30, bottom + 0.02, 0.45, top - 0.30 - bottom])
    labels = [f"{s}   {v/total*100:.0f} %" for s, v in counts.items()]
    H.top_hbar(ax, labels, counts.to_numpy(), value_fmt=T.num,
               title="Final score (winner – loser)")
    return fig


def realgames_team_compare(ctx: Ctx):
    """Winning vs losing team totals - only meaningful in full lobbies."""
    full = set(_full_lobby_events(ctx).index)
    w = ctx.wsg[ctx.wsg["eventId"].isin(full) & ~ctx.wsg["draw"]].copy()
    w["side"] = np.where(w["team"] == w["winner"], "win", "lose")

    # Team total per event and side, then mean across matches.
    team_tot = w.groupby(["eventId", "side"])[TEAM_STATS].sum().groupby("side").mean()
    rows = []
    for col in TEAM_STATS:
        a, b = team_tot.loc["win", col], team_tot.loc["lose", col]
        if b > 0:
            rows.append((STATS_BY_COLUMN[col].label, (a - b) / b * 100))
    rows.sort(key=lambda t: t[1], reverse=True)

    fig = plt.figure(figsize=(12, 8.2))
    top = T.figure_title(
        fig, "Full-lobby WSG: winning vs losing team totals",
        "Difference in per-team totals, winning side relative to losing side")
    bottom = T.footnote(fig, ctx.source_note(
        f"Totals summed per match across {len(full)} full-lobby matches, then "
        "averaged, so they cover the human side of each team in full."))
    ax = fig.add_axes([0.30, bottom + 0.03, 0.60, top - bottom - 0.06])

    H.diverging_hbar(ax, [t[0] for t in rows], [t[1] for t in rows],
                     pos_label="higher for winning team", neg_label="higher for losing team")
    ax.legend(loc="lower right", bbox_to_anchor=(1.0, -0.08), ncols=2)
    return fig


def realgames_length(ctx: Ctx):
    """Match length: full lobbies vs the rest."""
    m = ctx.matches
    full = _full_lobby_events(ctx)
    rest = m.drop(full.index)
    a = full.loc[full.duration > 0, "duration"] / 60
    b = rest.loc[rest.duration > 0, "duration"] / 60

    fig = plt.figure(figsize=(12, 5.8))
    top = T.figure_title(
        fig, "WSG match length: full lobbies vs rest",
        "Match length in minutes, full-lobby matches against all others")
    bottom = T.footnote(fig, ctx.source_note(
        f"Full lobby: {len(a)} matches, median {fmt_duration(a.median()*60)}. "
        f"Others: {len(b)} matches, median {fmt_duration(b.median()*60)}."))
    xb = T.xband(fig)
    ax = fig.add_axes([0.065, bottom + xb, 0.90, top - bottom - xb])

    hi = max(a.max(), b.max())
    bins = np.arange(0, hi + 1, 1)
    ax.hist(b, bins=bins, color=T.DEEMPHASIS, linewidth=0, density=True, label="other matches")
    ax.hist(a, bins=bins, color=T.PRIMARY, linewidth=0, density=True, alpha=0.8,
            label="full lobby")
    T.clean_axes(ax)
    ax.set_xlabel("match length (minutes)")
    ax.set_ylabel("share (density)")
    ax.set_yticks([])
    ax.legend(loc="upper right")
    ax.set_xlim(0, hi * 1.02)
    return fig


CHARTS = [
    ("21_realgames_overview", realgames_overview),
    ("22_realgames_team_compare", realgames_team_compare),
    ("23_realgames_length", realgames_length),
]
