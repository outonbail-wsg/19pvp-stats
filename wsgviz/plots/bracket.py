"""Charts that describe the level 19 WSG bracket as a scene.

Not "who is best" but "what does this bracket look like": how big and how
committed the population is, which classes make it up, and what a typical team
is composed of.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .. import theme as T
from ..context import Ctx
from ..data import CLASS_ORDER
from . import helpers as H

# Commitment tiers by the number of distinct days a character was seen.
DAY_TIERS = [(1, 1, "1 day"), (2, 4, "2–4 days"),
             (5, 8, "5–8 days"), (9, 99, "9+ days")]


def _present_order(series: pd.Series) -> list[str]:
    present = set(series.dropna().unique())
    return [c for c in CLASS_ORDER if c in present]


def population(ctx: Ctx):
    """How big is the bracket, and how much of it is regulars?"""
    w = ctx.wsg
    days_active = w.groupby("playerGuid")["date"].nunique()
    rows_per_char = w.groupby("playerGuid").size()

    def tier(d):
        for lo, hi, lab in DAY_TIERS:
            if lo <= d <= hi:
                return lab
        return DAY_TIERS[-1][2]

    tiers = days_active.map(tier)
    labels = [t[2] for t in DAY_TIERS]
    chars = tiers.value_counts().reindex(labels).fillna(0)
    # How much of the actual play comes from each tier?
    play = rows_per_char.groupby(tiers).sum().reindex(labels).fillna(0)
    play_share = play / play.sum()

    fig = plt.figure(figsize=(13, 6.4))
    top = T.figure_title(
        fig, "Level 19 WSG bracket: population",
        "Characters by number of days active, and each group's share of all matches "
        "played")
    bottom = T.footnote(fig, ctx.source_note(
        f"'Days active' counts distinct calendar days a character appeared in, over an "
        f"{days_active.max()}-day window. A character is one level 19 twink, not one "
        "person - the same player may run several."))

    tiles = [
        (T.num(w["playerGuid"].nunique()), "characters", "seen in WSG"),
        (T.num(int((rows_per_char >= ctx.min_games).sum())), "regulars",
         f">= {ctx.min_games} matches"),
        (T.num(int((days_active == 1).sum())), "one-day characters",
         "seen on a single day"),
        (T.num(days_active.median()), "median days active", "per character"),
    ]
    for i, (v, lab, sub) in enumerate(tiles):
        H.stat_tile(fig, [0.05 + i * 0.235, top - 0.17, 0.20, 0.13], v, lab, sub)

    xb = T.xband(fig)
    h = (top - 0.30) - bottom - xb

    ax1 = fig.add_axes([0.11, bottom + xb, 0.31, h])
    H.top_hbar(ax1, labels, chars.to_numpy(), value_fmt=T.num, bar_frac=0.5,
               title="Characters by days active")
    ax1.set_xlabel("characters")

    ax2 = fig.add_axes([0.60, bottom + xb, 0.31, h])
    H.top_hbar(ax2, labels, (play_share * 100).to_numpy(),
               value_fmt=lambda v: f"{v:.0f} %", bar_frac=0.5,
               title="Share of all matches played")
    ax2.set_xlabel("share of player-matches")
    return fig


def class_meta(ctx: Ctx):
    """Popularity against success - the bracket meta on one panel."""
    w = ctx.wsg
    dec = w[~w["draw"] & w["class_name"].notna()]
    g = dec.groupby("class_name").agg(rows=("win", "size"), wr=("win", "mean"))
    g["share"] = g["rows"] / g["rows"].sum()
    chars = (ctx.totals.dropna(subset=["class_name"])["class_name"]
             .value_counts().reindex(g.index).fillna(0))
    g["chars"] = chars
    order = _present_order(w["class_name"])
    g = g.reindex(order)

    fig = plt.figure(figsize=(11.5, 7.2))
    top = T.figure_title(
        fig, "Class meta: how often played against how often winning",
        "Each dot is a class; dot size scales with the number of distinct characters")
    bottom = T.footnote(fig, ctx.source_note(
        f"Share of decided player-matches (x) against win rate (y). The vertical line "
        f"marks an even share ({1/len(g)*100:.0f} %). Win rate is per player-match, so it "
        "reflects team composition as much as class strength."))
    xb = T.xband(fig)
    ax = fig.add_axes([0.10, bottom + xb, 0.86, top - bottom - xb])

    ax.axvline(1 / len(g), color=T.AXIS, linewidth=1.0)
    ax.scatter(g["share"], g["wr"], s=40 + g["chars"] * 6,
               color=H.class_colors(g.index), alpha=0.9, linewidths=1.6,
               edgecolors=T.SURFACE, zorder=3)
    # Label above the dot, but flip below when a neighbour already sits there.
    placed: list[tuple[float, float]] = []
    x_tol = g["share"].max() * 0.09
    y_tol = (g["wr"].max() - g["wr"].min()) * 0.10
    for cls, row in g.iterrows():
        x, y = row["share"], row["wr"]
        above = not any(abs(x - px) < x_tol and abs(y - py) < y_tol for px, py in placed)
        ax.annotate(cls, xy=(x, y), xytext=(0, 14 if above else -22),
                    textcoords="offset points", fontsize=9.5, ha="center",
                    color=T.INK_SECONDARY, zorder=4)
        placed.append((x, y))

    T.clean_axes(ax, xgrid=True)
    H.percent_axis(ax, "x")
    H.percent_axis(ax, "y")
    ax.xaxis.set_major_locator(plt.MultipleLocator(0.02))
    ax.yaxis.set_major_locator(plt.MultipleLocator(0.02))
    ax.set_xlabel("share of all player-matches")
    ax.set_ylabel("win rate")
    ax.set_xlim(0, g["share"].max() * 1.25)
    pad = (g["wr"].max() - g["wr"].min()) * 0.35
    ax.set_ylim(g["wr"].min() - pad, g["wr"].max() + pad)
    return fig


def team_composition(ctx: Ctx):
    """What a typical WSG team is made of."""
    w = ctx.wsg.dropna(subset=["class_name"])
    counts = (w.groupby(["eventId", "team", "class_name"]).size()
                .unstack(fill_value=0))
    order = [c for c in CLASS_ORDER if c in counts.columns]
    counts = counts[order]
    mean_per_team = counts.mean()
    present = (counts > 0).mean()

    fig = plt.figure(figsize=(13, 6.0))
    top = T.figure_title(
        fig, "What a WSG team is made of",
        "Average class count per team, and how often a team fields the class at all")
    bottom = T.footnote(fig, ctx.source_note(
        f"Across {T.num(len(counts))} team-sides. Only real players are recorded, so "
        "these are the human slots of a team, not all 10."))
    xb = T.xband(fig)
    h = top - bottom - xb
    cols = H.class_colors(order)

    ax1 = fig.add_axes([0.10, bottom + xb, 0.33, h])
    H.top_hbar(ax1, order, mean_per_team.to_numpy(), colors=cols,
               value_fmt=lambda v: T.num(v, 2),
               title="Average real players per team")
    ax1.set_xlabel("players per team")

    ax2 = fig.add_axes([0.60, bottom + xb, 0.33, h])
    H.top_hbar(ax2, order, (present * 100).to_numpy(), colors=cols,
               value_fmt=lambda v: f"{v:.0f} %",
               title="Teams fielding at least one")
    ax2.set_xlabel("share of team-sides")
    return fig


CHARTS = [
    ("02_bracket_population", population),
    ("09_class_meta", class_meta),
    ("10_team_composition", team_composition),
]
