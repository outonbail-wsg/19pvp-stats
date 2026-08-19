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

FLAG_STATS = ["flagCaptures", "flagReturns", "flagCarryTime", "attemptsOnFlag",
              "damageOnEFC", "healsOnFC"]
COMBAT_STATS = ["damageDone", "healingDone", "absorbsDone", "killingBlows",
                "honorableKills", "damageTaken"]
UTILITY_STATS = ["successfulInterrupts", "fakeCastInterrupts", "dispelsOffensive",
                 "dispelsDefensive", "hardCCDuration", "softCCDuration"]
RATE_STATS = ["damageDone", "healingDone", "damageOnEFC", "healsOnFC",
              "flagReturns", "flagCaptures"]


def _fmt_for(col: str):
    return fmt_duration if STATS_BY_COLUMN[col].seconds else T.compact


def _panel(fig, ax, tot, col, suffix, title_suffix="", fmt=None):
    """One top-10 panel for a single statistic, bars coloured by class."""
    key = f"{col}{suffix}"
    top = tot.nlargest(TOP_N, key)
    H.top_hbar(ax, top["player"], top[key].to_numpy(),
               colors=H.class_colors(top["class_name"]),
               label_colors=H.class_text_colors(top["class_name"]),
               value_fmt=fmt or _fmt_for(col))
    icons.panel_title(fig, ax, STATS_BY_COLUMN[col].label + title_suffix, col)


def _leaderboard_grid(ctx: Ctx, stats, title, subtitle, note, *, suffix="_sum",
                      totals=None, fmt=None, title_suffix=""):
    tot = ctx.totals if totals is None else totals
    fig = plt.figure(figsize=(13.5, 9.8))
    top = T.figure_title(fig, title, subtitle)
    bottom = T.footnote(fig, ctx.source_note(note))
    axes = H.grid_axes(fig, 2, 3, left=0.10, right=0.975, top=top,
                       bottom=bottom, wspace=0.85, hspace=0.42)
    for i, col in enumerate(stats):
        _panel(fig, axes[i // 3][i % 3], tot, col, suffix, title_suffix, fmt)
    return fig


def leaderboard_flag(ctx: Ctx):
    """Everything around the flag - totals over the window."""
    return _leaderboard_grid(
        ctx, FLAG_STATS,
        "WSG leaderboards: flag play",
        f"Top {TOP_N} by total over the whole period",
        "Totals favour players with more matches; see the per-minute board.")


def leaderboard_combat(ctx: Ctx):
    """Damage, healing, kills - totals."""
    return _leaderboard_grid(
        ctx, COMBAT_STATS,
        "WSG leaderboards: combat",
        f"Top {TOP_N} by total over the whole period",
        "Damage taken tracks flag carriers and front-line play.")


def leaderboard_utility(ctx: Ctx):
    """Interrupts, dispels, crowd control - totals."""
    return _leaderboard_grid(
        ctx, UTILITY_STATS,
        "WSG leaderboards: interrupts, dispels and crowd control",
        f"Top {TOP_N} by total over the whole period",
        "Not class-adjusted; see the class charts.")


def leaderboard_per_minute(ctx: Ctx):
    """Efficiency rather than volume - values per minute played."""
    q = ctx.qualified
    return _leaderboard_grid(
        ctx, RATE_STATS,
        "WSG leaderboards: output per minute",
        f"Top {TOP_N} by value per minute played, characters with at least "
        f"{ctx.min_games} matches only",
        f"{len(q)} of {len(ctx.totals)} characters clear the threshold. Per minute "
        "actually played, not match length.",
        suffix="_pm", totals=q, fmt=lambda v: T.compact(v) + "/min",
        title_suffix=" per minute")


def leaderboard_winrate(ctx: Ctx):
    """Win rate with an uncertainty band."""
    q = ctx.qualified.copy()
    q = q[q["games_decided"] >= ctx.min_games]
    q["lo"], q["hi"] = wilson_interval(q["wins"], q["games_decided"])
    best = q.nlargest(15, "winrate").sort_values("winrate")

    fig = plt.figure(figsize=(12.5, 8.2))
    top = T.figure_title(
        fig, "WSG best win rate",
        f"Top 15 characters with at least {ctx.min_games} decided matches")
    bottom = T.footnote(fig, ctx.source_note(
        "Thin line = 95 % Wilson interval - the range the true rate plausibly sits in "
        "at this sample size."))
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
    """Who plays the most - by matches, hours and days shown up.

    Desertions have their own board; repeating them here would double-count the
    same story.
    """
    tot = ctx.totals.copy()
    tot["days_active"] = ctx.wsg.groupby("playerGuid")["date"].nunique()

    fig = plt.figure(figsize=(13.5, 5.8))
    top = T.figure_title(fig, "WSG leaderboards: activity",
                         f"Top {TOP_N} by matches, hours played and days active")
    bottom = T.footnote(fig, ctx.source_note(
        "'Days active' counts distinct calendar days the character appeared in."))
    xb = T.xband(fig)
    h = top - bottom - xb
    w = 0.21

    ax1 = fig.add_axes([0.09, bottom + xb, w, h])
    t1 = tot.nlargest(TOP_N, "games")
    H.top_hbar(ax1, t1["player"], t1["games"].to_numpy(), value_fmt=T.num,
               colors=H.class_colors(t1["class_name"]),
               label_colors=H.class_text_colors(t1["class_name"]),
               title="Most matches")

    ax2 = fig.add_axes([0.42, bottom + xb, w, h])
    t2 = tot.nlargest(TOP_N, "minutes")
    H.top_hbar(ax2, t2["player"], (t2["minutes"] / 60).to_numpy(),
               colors=H.class_colors(t2["class_name"]),
               label_colors=H.class_text_colors(t2["class_name"]),
               value_fmt=lambda v: T.num(v, 1) + " h", title="Most hours played")

    ax3 = fig.add_axes([0.75, bottom + xb, w, h])
    t3 = tot.nlargest(TOP_N, "days_active")
    H.top_hbar(ax3, t3["player"], t3["days_active"].to_numpy(),
               colors=H.class_colors(t3["class_name"]),
               label_colors=H.class_text_colors(t3["class_name"]), value_fmt=T.num,
               title="Most days active")
    return fig


CHARTS = [
    ("25_leaderboard_flag", leaderboard_flag),
    ("26_leaderboard_combat", leaderboard_combat),
    ("27_leaderboard_utility", leaderboard_utility),
    ("28_leaderboard_per_minute", leaderboard_per_minute),
    ("29_leaderboard_winrate", leaderboard_winrate),
    ("30_leaderboard_activity", leaderboard_activity),
]
