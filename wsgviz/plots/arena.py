"""Arena, evaluated per bracket.

Only 2v2 is charted: 3v3 has 5 matches across 7 characters in this export, which
is too little for any distribution or ranking to mean anything. Arena carries no
flag statistics, so the boards are combat only.
"""

from __future__ import annotations

from functools import partial

import matplotlib.pyplot as plt
import numpy as np

from .. import theme as T
from ..context import Ctx
from ..data import (STATS_BY_COLUMN, arena as arena_rows,
                    fmt_duration, player_totals, wilson_interval)
from . import helpers as H

BRACKETS = {"2v2": {"label": "Arena 2v2", "min_games": 10, "nums": (42, 43, 44)}}

COMBAT = ["damageDone", "healingDone", "damageTaken", "killingBlows",
          "honorableKills", "successfulInterrupts"]


def _bracket(ctx: Ctx, kind: str):
    a = arena_rows(ctx.raw)
    return a[a["kind"] == kind].copy()


def _small_sample(df, kind: str) -> str:
    """Warn when a bracket is too thin to read. 2v2 clears this comfortably."""
    if df["eventId"].nunique() < 50:
        return (f"Small sample: {df['eventId'].nunique()} matches, "
                f"{df['playerGuid'].nunique()} characters - anecdotal.")
    return ""


def overview(ctx: Ctx, kind: str):
    cfg = BRACKETS[kind]
    a = _bracket(ctx, kind)
    dur = a.loc[a.timePlayed > 0, "timePlayed"] / 60

    fig = plt.figure(figsize=(12.5, 6.0))
    top = T.figure_title(fig, f"{cfg['label']} overview",
                         f"Scope of the {kind} bracket in this export")
    bottom = T.footnote(fig, ctx.source_note(_small_sample(a, kind)))

    tiles = [
        (T.num(a.eventId.nunique()), "matches", "recorded"),
        (T.num(a.playerGuid.nunique()), "characters", ""),
        (fmt_duration(a.timePlayed.median()), "median length", "time played"),
        (T.num(int(a.arenaPoints.sum())), "arena points", "total"),
    ]
    for i, (v, lab, sub) in enumerate(tiles):
        H.stat_tile(fig, [0.05 + i * 0.235, top - 0.17, 0.20, 0.13], v, lab, sub)

    xb = T.xband(fig)
    ax = fig.add_axes([0.30, bottom + xb, 0.45, top - 0.30 - bottom - xb])
    H.hist(ax, dur, bins=np.arange(0, dur.max() + 0.5, 0.5) if len(dur) else 10)
    ax.set_title(f"{kind} match length", fontsize=10.5, pad=8)
    ax.set_xlabel("minutes")
    ax.set_ylabel("player rows")
    return fig


def leaderboards(ctx: Ctx, kind: str):
    cfg = BRACKETS[kind]
    a = _bracket(ctx, kind)
    tot = player_totals(a)
    tot = tot[tot["games"] >= cfg["min_games"]]

    fig = plt.figure(figsize=(13.5, 9.6))
    top = T.figure_title(
        fig, f"{cfg['label']} leaderboards: combat",
        f"Top 10 by total, characters with at least {cfg['min_games']} matches")
    bottom = T.footnote(fig, ctx.source_note(
        f"{len(tot)} characters clear the {cfg['min_games']}-match threshold. "
        + _small_sample(a, kind)))
    axes = H.grid_axes(fig, 2, 3, left=0.10, right=0.975, top=top,
                       bottom=bottom, wspace=0.85, hspace=0.42)
    for i, col in enumerate(COMBAT):
        ax = axes[i // 3][i % 3]
        best = tot.nlargest(10, f"{col}_sum")
        H.top_hbar(ax, best["player"], best[f"{col}_sum"].to_numpy(),
                   colors=H.class_colors(best["class_name"]),
                   label_colors=H.class_text_colors(best["class_name"]),
                   title=STATS_BY_COLUMN[col].label)
    return fig


def winrate(ctx: Ctx, kind: str):
    cfg = BRACKETS[kind]
    a = _bracket(ctx, kind)
    tot = player_totals(a)
    tot = tot[tot["games_decided"] >= cfg["min_games"]]
    tot["lo"], tot["hi"] = wilson_interval(tot["wins"], tot["games_decided"])
    best = tot.nlargest(15, "winrate").sort_values("winrate")

    fig = plt.figure(figsize=(12.5, 8.2))
    top = T.figure_title(
        fig, f"{cfg['label']} best win rate",
        f"Top 15 characters with at least {cfg['min_games']} decided matches")
    bottom = T.footnote(fig, ctx.source_note(
        "The thin line shows how certain the figure is at this number of games. "
        + _small_sample(a, kind)))
    ax = fig.add_axes([0.17, bottom + 0.02, 0.73, top - bottom - 0.05])

    y = np.arange(len(best))
    ax.barh(y, best["winrate"], height=0.6, color=H.class_colors(best["class_name"]),
            linewidth=0)
    ax.hlines(y, best["lo"], best["hi"], color=T.INK, linewidth=1.2, alpha=0.55)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{p}  ({int(g)} games)"
                        for p, g in zip(best["player"], best["games_decided"])],
                       fontsize=9, color=T.INK_SECONDARY)
    for tick, c in zip(ax.get_yticklabels(), H.class_text_colors(best["class_name"])):
        tick.set_color(c)
    T.hbar_axes(ax)
    ax.grid(axis="x", visible=True)
    ax.tick_params(axis="x", length=3)
    H.percent_axis(ax, "x")
    ax.set_xlim(0, min(1.0, best["hi"].max() * 1.06))
    ax.set_xlabel("win rate")
    for yi, v in zip(y, best["winrate"]):
        ax.text(v, yi + 0.34, f"{v*100:.0f} %", va="bottom", ha="center",
                fontsize=8.5, color=T.INK_SECONDARY)
    return fig


def _charts():
    out = []
    for kind, cfg in BRACKETS.items():
        n0, n1, n2 = cfg["nums"]
        out.append((f"{n0}_{kind}_overview", partial(overview, kind=kind)))
        out.append((f"{n1}_{kind}_leaderboards", partial(leaderboards, kind=kind)))
        out.append((f"{n2}_{kind}_winrate", partial(winrate, kind=kind)))
    return out


CHARTS = _charts()
