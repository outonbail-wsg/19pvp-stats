"""Class-based statistics for WSG.

The export gained a class id (WoW standard ids; 6 = Death Knight and 10 = Monk
never appear because neither exists at level 19). One row = one player in one
match, so class figures here are per player-match, not per character.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .. import theme as T
from ..context import Ctx
from ..data import CLASS_COLORS, CLASS_ORDER, STATS_BY_COLUMN, wilson_interval
from . import helpers as H
from . import icons

# Per-minute stats shown in the class stat grid: a spread across roles.
CLASS_STAT_GRID = ["damageDone", "healingDone", "damageOnEFC", "healsOnFC",
                   "killingBlows", "successfulInterrupts"]


def _present_order(series: pd.Series) -> list[str]:
    """Classes that actually occur, in the fixed display order."""
    present = set(series.dropna().unique())
    return [c for c in CLASS_ORDER if c in present]


def _class_colors(order: list[str]) -> list[str]:
    return [CLASS_COLORS[c] for c in order]


def _class_note(w: pd.DataFrame) -> str:
    missing = int(w["class_name"].isna().sum())
    return f"{missing} of {T.num(len(w))} rows have no class and are excluded."


def class_distribution(ctx: Ctx):
    """How many characters and player-matches per class."""
    w = ctx.wsg
    # Ranked by play volume rather than the fixed class order, and the same
    # order in both panels so the eye can carry a class across.
    rows = w["class_name"].value_counts()
    order = [c for c in rows.index if pd.notna(c)]
    char_cls = ctx.totals.dropna(subset=["class_name"])
    chars = char_cls["class_name"].value_counts().reindex(order).fillna(0)
    rows = rows.reindex(order).fillna(0)

    fig = plt.figure(figsize=(12.5, 6.0))
    top = T.figure_title(
        fig, "WSG class distribution",
        "Distinct characters and recorded player-matches per class, "
        "most-played first")
    bottom = T.footnote(fig, ctx.source_note(_class_note(w)))
    xb = T.xband(fig)
    h = top - bottom - xb

    cols = _class_colors(order)
    ax1 = fig.add_axes([0.09, bottom + xb, 0.37, h])
    H.top_hbar(ax1, order, chars.to_numpy(), value_fmt=T.num, colors=cols,
               title="Distinct characters")
    ax1.set_xlabel("characters")

    ax2 = fig.add_axes([0.58, bottom + xb, 0.37, h])
    H.top_hbar(ax2, order, rows.to_numpy(), value_fmt=T.num, colors=cols,
               title="Player-matches recorded")
    ax2.set_xlabel("player-matches")
    return fig


def class_winrate(ctx: Ctx):
    """Win rate per class with a Wilson interval."""
    w = ctx.wsg
    dec = w[~w["draw"] & w["class_name"].notna()]
    grp = dec.groupby("class_name")["win"].agg(["mean", "sum", "size"])
    order = _present_order(w["class_name"])
    grp = grp.reindex(order)
    lo, hi = wilson_interval(grp["sum"], grp["size"])

    fig = plt.figure(figsize=(12, 6.4))
    top = T.figure_title(
        fig, "WSG win rate by class",
        "Share of decided player-matches in the winning team, per class")
    bottom = T.footnote(fig, ctx.source_note(
        "One row = one player-match, so this also reflects team composition. The thin "
        "line shows how certain each figure is at this number of matches. "
        + _class_note(w)))
    ax = fig.add_axes([0.13, bottom + 0.04, 0.80, top - bottom - 0.07])

    y = np.arange(len(order))[::-1]
    ax.barh(y, grp["mean"].to_numpy(), height=0.62, color=_class_colors(order), linewidth=0)
    ax.hlines(y, lo.to_numpy(), hi.to_numpy(), color=T.INK, linewidth=1.2, alpha=0.55)
    ax.set_yticks(y)
    ax.set_yticklabels(order, fontsize=9.5, color=T.INK_SECONDARY)
    T.hbar_axes(ax)
    ax.grid(axis="x", visible=True)
    ax.tick_params(axis="x", length=3)
    H.percent_axis(ax, "x")
    ax.set_xlim(0.30, min(0.70, hi.max() * 1.05))
    ax.set_xlabel("win rate")
    for yi, m, n in zip(y, grp["mean"], grp["size"]):
        ax.text(m, yi + 0.34, f"{m*100:.0f} %  (n = {T.num(int(n))})", va="bottom",
                ha="center", fontsize=8.3, color=T.INK_SECONDARY)
    return fig


def class_matrix(ctx: Ctx):
    """Every class against every core statistic in one shaded table.

    Nine separate bar panels forced a reader to compare across panels that each
    had their own scale. A table puts the numbers side by side; the shading is
    per column, so it says "high for this statistic", never across units.
    """
    r = ctx.rates[ctx.rates["class_name"].notna()]
    w = ctx.wsg[ctx.wsg["class_name"].notna()]
    order = _present_order(r["class_name"])

    per_match = w.groupby("class_name").agg(
        games=("eventId", "size"), carry=("flagCarryTime", "sum"),
        returns=("flagReturns", "sum"), caps=("flagCaptures", "sum"))
    rate = r.groupby("class_name")

    # (label, series, formatter) - all per minute except the flag work, which
    # reads better per match.
    columns = [
        ("Damage\n/min", rate["damageDone_pm"].mean(), T.compact),
        ("Healing\n/min", rate["healingDone_pm"].mean(), T.compact),
        ("Absorbs\n/min", rate["absorbsDone_pm"].mean(), T.compact),
        ("On enemy\ncarrier /min", rate["damageOnEFC_pm"].mean(), T.compact),
        ("Heals on\ncarrier /min", rate["healsOnFC_pm"].mean(), T.compact),
        ("Killing blows\n/min", rate["killingBlows_pm"].mean(), lambda v: f"{v:.2f}"),
        ("Interrupts\n/min", rate["successfulInterrupts_pm"].mean(), lambda v: f"{v:.2f}"),
        ("Carry time\nper match", per_match["carry"] / per_match["games"],
         lambda v: f"{v:.0f}s"),
        ("Returns\nper match", per_match["returns"] / per_match["games"],
         lambda v: f"{v:.2f}"),
    ]

    fig = plt.figure(figsize=(13.5, 6.4))
    top = T.figure_title(
        fig, "Class comparison",
        "Mean output per class across nine statistics")
    bottom = T.footnote(fig, ctx.source_note(
        "Shading runs within each column, from the lowest value in that column to the "
        "highest - it never compares across columns, whose units differ. Per-minute "
        "figures use rows with at least 60 s played. " + _class_note(ctx.wsg)))
    ax = fig.add_axes([0.105, bottom, 0.875, top - bottom - 0.09])

    values = np.array([[float(s.reindex(order).iloc[i]) for _, s, _ in columns]
                       for i in range(len(order))])
    # Rank within each column so a single dominant class cannot flatten the rest.
    shade = np.zeros_like(values)
    for j in range(values.shape[1]):
        col = values[:, j]
        lo, hi = np.nanmin(col), np.nanmax(col)
        shade[:, j] = (col - lo) / (hi - lo) if hi > lo else 0.5

    ax.imshow(shade, cmap=T.SEQUENTIAL, aspect="auto", vmin=-0.15, vmax=1.15)
    ax.set_xticks(range(len(columns)))
    ax.set_xticklabels([c[0] for c in columns], fontsize=9, color=T.INK_SECONDARY)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order, fontsize=10)
    for tick, cls in zip(ax.get_yticklabels(), order):
        tick.set_color(H.class_text_colors([cls])[0])
        tick.set_fontweight("semibold")
    ax.xaxis.set_ticks_position("top")
    ax.tick_params(length=0)
    ax.grid(False)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)

    for i in range(values.shape[0]):
        for j, (_, _, fmt) in enumerate(columns):
            # Dark cells need light type; the ramp crosses over around 0.55.
            colour = T.SURFACE if shade[i, j] > 0.55 else T.INK
            ax.text(j, i, fmt(values[i, j]), ha="center", va="center",
                    fontsize=9.5, color=colour)
    return fig


CHARTS = [
    ("08_class_distribution", class_distribution),
    ("11_class_winrate", class_winrate),
    ("12_class_matrix", class_matrix),
]
