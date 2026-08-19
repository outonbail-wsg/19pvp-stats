"""Leaderboards for the statistics that decide a Warsong Gulch round.

Flag work and carrier support get their own charts rather than a row in a
leaders table, and each one is shown three ways at once. Totals reward whoever
played most; per match and per minute say who was most useful while there. The
three columns disagree often enough that showing only one is misleading.
"""

from __future__ import annotations

import matplotlib.pyplot as plt

from .. import theme as T
from ..context import Ctx
from ..data import STATS_BY_COLUMN, fmt_duration
from . import helpers as H
from . import icons

TOP_N = 8


def _board(ctx: Ctx, stats, title, subtitle, note, *, fmt_total=T.compact,
           rate_decimals=2):
    """One row per statistic, three columns: total, per match, per minute."""
    tot = ctx.totals
    qual = ctx.qualified
    fig = plt.figure(figsize=(13.5, 3.1 + 3.5 * len(stats)))
    top = T.figure_title(fig, title, subtitle)
    bottom = T.footnote(fig, ctx.source_note(note))

    rows, cols = len(stats), 3
    axes = H.grid_axes(fig, rows, cols, left=0.105, right=0.975, top=top - 0.035,
                       bottom=bottom, wspace=0.80, hspace=0.34)

    for i, col in enumerate(stats):
        label = STATS_BY_COLUMN[col].label
        seconds = STATS_BY_COLUMN[col].seconds
        # Totals use everyone; the two rate columns need the match threshold, or
        # a single lucky match tops the board.
        per_match = (qual[f"{col}_sum"] / qual["games"]).rename("v")
        per_min = qual[f"{col}_pm"].rename("v")
        variants = [
            ("total", tot[f"{col}_sum"], tot,
             fmt_duration if seconds else fmt_total),
            ("per match", per_match, qual,
             fmt_duration if seconds else (lambda v: T.compact(v) if v >= 10
                                           else f"{v:.{rate_decimals}f}")),
            ("per minute", per_min, qual,
             lambda v: T.compact(v) if v >= 10 else f"{v:.{rate_decimals}f}"),
        ]
        for j, (suffix, series, frame, value_fmt) in enumerate(variants):
            ax = axes[i][j]
            best = series.nlargest(TOP_N)
            sub = frame.loc[best.index]
            H.top_hbar(ax, sub["player"], best.to_numpy(),
                       colors=H.class_colors(sub["class_name"]),
                       label_colors=H.class_text_colors(sub["class_name"]),
                       value_fmt=value_fmt)
            heading = f"{label} — {suffix}" if j == 0 else suffix
            if j == 0:
                icons.panel_title(fig, ax, heading, col)
            else:
                ax.set_title(heading, fontsize=10.5, pad=8, loc="left")
    return fig


def flag_leaders(ctx: Ctx):
    """Who scores and who takes the flag back."""
    return _board(
        ctx, ["flagCaptures", "flagReturns"],
        "WSG flag leaders",
        f"Top {TOP_N} for captures and returns, three ways: in total, per match "
        "and per minute played",
        f"Totals cover every character; the per-match and per-minute boards need at "
        f"least {ctx.min_games} matches, otherwise one good round tops them. The three "
        "columns rarely hold the same names - a heavy schedule wins the totals, "
        "efficiency wins the rates.")


def carrier_leaders(ctx: Ctx):
    """Who breaks the enemy carrier and who keeps their own alive."""
    return _board(
        ctx, ["damageOnEFC", "healsOnFC"],
        "WSG flag carrier support leaders",
        f"Top {TOP_N} for damage on the enemy carrier and healing on their own, "
        "three ways: in total, per match and per minute played",
        f"Totals cover every character; the rate boards need at least {ctx.min_games} "
        "matches. These two statistics separate objective play from raw output: a "
        "character can lead damage overall and appear nowhere here.")


CHARTS = [
    ("13_flag_leaders", flag_leaders),
    ("14_carrier_leaders", carrier_leaders),
]
