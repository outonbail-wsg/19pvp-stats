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
    order = _present_order(w["class_name"])
    # Distinct characters per class (one class per character).
    char_cls = ctx.totals.dropna(subset=["class_name"])
    chars = char_cls["class_name"].value_counts().reindex(order).fillna(0)
    rows = w["class_name"].value_counts().reindex(order).fillna(0)

    fig = plt.figure(figsize=(12.5, 6.0))
    top = T.figure_title(
        fig, "WSG class distribution",
        "Distinct characters and recorded player-matches per class")
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


def class_stats(ctx: Ctx):
    """Mean per-minute output per class across six stats."""
    r = ctx.rates[ctx.rates["class_name"].notna()]
    order = _present_order(r["class_name"])

    fig = plt.figure(figsize=(13, 7.6))
    top = T.figure_title(
        fig, "WSG per-minute output by class",
        "Mean value per minute played, per class, for six core statistics")
    bottom = T.footnote(fig, ctx.source_note(
        "Rows with >=60 s played. Panels share the class order but not the scale. "
        + _class_note(ctx.wsg)))
    axes = H.grid_axes(fig, 2, 3, left=0.09, right=0.975, top=top,
                       bottom=bottom + 0.02, wspace=0.75, hspace=0.40)

    cols = _class_colors(order)
    for i, col in enumerate(CLASS_STAT_GRID):
        ax = axes[i // 3][i % 3]
        means = r.groupby("class_name")[f"{col}_pm"].mean().reindex(order)
        H.top_hbar(ax, order, means.to_numpy(), colors=cols,
                   value_fmt=lambda v: T.compact(v))
        icons.panel_title(fig, ax, STATS_BY_COLUMN[col].label + " / min", col)
    return fig


def class_flag_roles(ctx: Ctx):
    """Which classes carry, return, and pressure the enemy carrier."""
    r = ctx.rates[ctx.rates["class_name"].notna()]
    order = _present_order(r["class_name"])
    panels = [
        ("flagCarryTime", "flagCarryTime_sum", "Flag carry time per match", "s"),
        ("flagReturns", "flagReturns_sum", "Flag returns per match", ""),
        ("damageOnEFC", "damageOnEFC_pm", "Damage on enemy carrier / min", ""),
    ]
    w = ctx.wsg[ctx.wsg["class_name"].notna()]
    per_match = w.groupby("class_name").agg(
        games=("eventId", "size"),
        carry=("flagCarryTime", "sum"),
        returns=("flagReturns", "sum"))

    fig = plt.figure(figsize=(13, 5.8))
    top = T.figure_title(
        fig, "WSG flag work by class",
        "Flag carrying, returns and pressure on the enemy carrier, per class")
    bottom = T.footnote(fig, ctx.source_note(
        "Carry time and returns per player-match; damage on carrier per minute. "
        + _class_note(ctx.wsg)))
    xb = T.xband(fig)
    h = top - bottom - xb
    w_ax = 0.255

    cols = _class_colors(order)
    carry = (per_match["carry"] / per_match["games"]).reindex(order)
    ax1 = fig.add_axes([0.075, bottom + xb, w_ax, h])
    H.top_hbar(ax1, order, carry.to_numpy(), colors=cols,
               value_fmt=lambda v: f"{v:.0f}s", title="Flag carry time per match")

    rets = (per_match["returns"] / per_match["games"]).reindex(order)
    ax2 = fig.add_axes([0.40, bottom + xb, w_ax, h])
    H.top_hbar(ax2, order, rets.to_numpy(), colors=cols,
               value_fmt=lambda v: T.num(v, 2), title="Flag returns per match")

    efc = r.groupby("class_name")["damageOnEFC_pm"].mean().reindex(order)
    ax3 = fig.add_axes([0.725, bottom + xb, w_ax, h])
    H.top_hbar(ax3, order, efc.to_numpy(), colors=cols,
               value_fmt=lambda v: T.compact(v), title="Damage on enemy carrier / min")
    return fig


CHARTS = [
    ("08_class_distribution", class_distribution),
    ("11_class_winrate", class_winrate),
    ("12_class_stats", class_stats),
    ("13_class_flag_roles", class_flag_roles),
]
