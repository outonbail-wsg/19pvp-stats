"""Player leaderboards.

Total-based boards reward volume, rate-based boards reward efficiency. They are
kept apart here so it stays clear which question each one answers.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from .. import theme as T
from ..context import Ctx
from ..data import STATS_BY_COLUMN, fmt_duration, wilson_interval
from . import helpers as H
from . import icons

TOP_N = 10

# flagCaptures, flagReturns, damageOnEFC and healsOnFC have dedicated charts
# in objective.py, so the tables carry what is left.
FLAG_STATS = ["flagCarryTime", "attemptsOnFlag"]
COMBAT_STATS = ["damageDone", "healingDone", "absorbsDone", "killingBlows",
                "honorableKills", "damageTaken"]
UTILITY_STATS = ["successfulInterrupts", "fakeCastInterrupts", "dispelsOffensive",
                 "dispelsDefensive", "hardCCDuration", "softCCDuration"]
RATE_STATS = ["damageDone", "healingDone", "damageTaken", "honorableKills"]


TABLE_TOP = 5            # names shown per statistic in a leaders table


def _fmt_for(col: str):
    return fmt_duration if STATS_BY_COLUMN[col].seconds else T.compact


def _leaders_table(ctx: Ctx, stats, title, subtitle, note, *, suffix="_sum",
                   totals=None, fmt=None, unit=""):
    """One row per statistic, the leading characters listed across it.

    A table rather than a grid of bars: the deck already leans heavily on bars,
    and a reader asking "who leads this" wants to scan names, not compare bar
    lengths across panels that each carry their own scale.
    """
    tot = ctx.totals if totals is None else totals
    fig = plt.figure(figsize=(13.5, 1.15 + 0.66 * len(stats)))
    top = T.figure_title(fig, title, subtitle)
    bottom = T.footnote(fig, ctx.source_note(note))

    x_label, x_first, x_step = 0.055, 0.235, 0.152
    step = (top - bottom) / len(stats)
    for i, col in enumerate(stats):
        row_y = top - step * (i + 0.42)
        icons.draw(fig, 0.026, row_y + step * 0.06, icons.STAT_ICON.get(col),
                   size_in=0.17)
        fig.text(x_label, row_y + step * 0.06, STATS_BY_COLUMN[col].label,
                 fontsize=10.5, fontweight="semibold", color=T.INK,
                 ha="left", va="center")

        best = tot.nlargest(TABLE_TOP, f"{col}{suffix}")
        value_fmt = fmt or _fmt_for(col)
        colours = H.class_text_colors(best["class_name"])
        for rank, ((_, r), colour) in enumerate(zip(best.iterrows(), colours), start=1):
            x = x_first + (rank - 1) * x_step
            fig.text(x, row_y + step * 0.18, f"{rank}", fontsize=9,
                     color=T.INK_MUTED, ha="left", va="center")
            fig.text(x + 0.016, row_y + step * 0.18, r["player"], fontsize=10,
                     fontweight="semibold", color=colour, ha="left", va="center")
            fig.text(x + 0.016, row_y - step * 0.16,
                     value_fmt(r[f"{col}{suffix}"]) + unit, fontsize=9.5,
                     color=T.INK_SECONDARY, ha="left", va="center")
        # Hairline under the row, so the eye can follow it across.
        fig.add_artist(plt.Line2D([0.022, 0.978], [row_y - step * 0.42] * 2,
                                  color=T.GRID, linewidth=0.8))
    return fig


def leaderboard_flag(ctx: Ctx):
    """Flag play and combat totals, as one leaders table."""
    return _leaders_table(
        ctx, FLAG_STATS + COMBAT_STATS,
        "WSG stat leaders: flag play and combat",
        f"The {TABLE_TOP} leading characters per statistic, totals over the period",
        "Totals favour players with more matches; the per-minute table ranks by rate "
        "instead. 'Damage taken' tracks flag carriers and front-line play.")


def leaderboard_utility(ctx: Ctx):
    """Interrupts, dispels, crowd control and the flag-work rates."""
    return _leaders_table(
        ctx, UTILITY_STATS + ["attemptsOnFlag", "bonusHonor", "deaths"],
        "WSG stat leaders: utility",
        f"The {TABLE_TOP} leading characters per statistic, totals over the period",
        "These depend heavily on class - a priest will always outrank a warrior on "
        "dispels. See the class charts for a per-class view.")


def leaderboard_per_minute(ctx: Ctx):
    """Efficiency rather than volume - values per minute played."""
    q = ctx.qualified
    return _leaders_table(
        ctx, RATE_STATS + ["killingBlows", "absorbsDone", "successfulInterrupts"],
        "WSG stat leaders: output per minute",
        f"The {TABLE_TOP} leading characters per statistic, per minute played, "
        f"characters with at least {ctx.games_phrase()}",
        f"{len(q)} of {len(ctx.totals)} characters clear the threshold. Rates are per "
        "minute actually played, not per match length.",
        suffix="_pm", totals=q, fmt=T.compact, unit="/min")


def leaderboard_winrate(ctx: Ctx):
    """Win rate with an uncertainty band."""
    q = ctx.qualified.copy()
    q = q[q["games_decided"] >= ctx.min_games]
    q["lo"], q["hi"] = wilson_interval(q["wins"], q["games_decided"])
    best = q.nlargest(15, "winrate").sort_values("winrate")

    fig = plt.figure(figsize=(12.5, 8.2))
    top = T.figure_title(
        fig, "WSG best win rate",
        f"Top 15 characters with at least {ctx.games_phrase('decided matches')}")
    bottom = T.footnote(fig, ctx.source_note(
        "The thin line shows how certain the figure is at this number of games - "
        "where the bands overlap, the order between them is not settled."))
    ax = fig.add_axes([0.16, bottom + 0.02, 0.74, top - bottom - 0.05])

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


def leaderboard_activity(ctx: Ctx):
    """Who plays the most - by matches, hours, days shown up, and losses taken.

    Desertions have their own board; repeating them here would double-count the
    same story.
    """
    tot = ctx.totals.copy()
    tot["days_active"] = ctx.wsg.groupby("playerGuid")["date"].nunique()
    tot["losses"] = tot["games_decided"] - tot["wins"]

    fig = plt.figure(figsize=(16, 5.8))
    top = T.figure_title(
        fig, "WSG leaderboards: activity",
        f"Top {TOP_N} by matches, hours played, days active and matches lost")
    bottom = T.footnote(fig, ctx.source_note(
        "'Days active' counts distinct calendar days the character appeared in. The "
        "loss board tracks the match board closely - nobody collects losses without "
        "queueing for them - so read it as volume, not as a verdict; win rate has its "
        "own board."))
    xb = T.xband(fig)
    h = top - bottom - xb
    w = 0.155

    ax1 = fig.add_axes([0.075, bottom + xb, w, h])
    t1 = tot.nlargest(TOP_N, "games")
    H.top_hbar(ax1, t1["player"], t1["games"].to_numpy(), value_fmt=T.num,
               colors=H.class_colors(t1["class_name"]),
               label_colors=H.class_text_colors(t1["class_name"]),
               title="Most matches")

    ax2 = fig.add_axes([0.32, bottom + xb, w, h])
    t2 = tot.nlargest(TOP_N, "minutes")
    H.top_hbar(ax2, t2["player"], (t2["minutes"] / 60).to_numpy(),
               colors=H.class_colors(t2["class_name"]),
               label_colors=H.class_text_colors(t2["class_name"]),
               value_fmt=lambda v: T.num(v, 1) + " h", title="Most hours played")

    ax3 = fig.add_axes([0.565, bottom + xb, w, h])
    t3 = tot.nlargest(TOP_N, "days_active")
    H.top_hbar(ax3, t3["player"], t3["days_active"].to_numpy(),
               colors=H.class_colors(t3["class_name"]),
               label_colors=H.class_text_colors(t3["class_name"]), value_fmt=T.num,
               title="Most days active")

    ax4 = fig.add_axes([0.81, bottom + xb, w, h])
    t4 = tot.nlargest(TOP_N, "losses")
    H.top_hbar(ax4, t4["player"], t4["losses"].to_numpy(),
               colors=H.class_colors(t4["class_name"]),
               label_colors=H.class_text_colors(t4["class_name"]), value_fmt=T.num,
               title="Most matches lost")
    return fig


CHARTS = [
    ("19_leaders_flag_combat", leaderboard_flag),
    ("20_leaders_utility", leaderboard_utility),
    ("21_leaders_per_minute", leaderboard_per_minute),
    ("22_leaderboard_winrate", leaderboard_winrate),
    ("23_leaderboard_activity", leaderboard_activity),
]
