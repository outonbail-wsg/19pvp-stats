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
from ..data import MIN_PICKUPS, STATS_BY_COLUMN, fmt_duration
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
            # A duration per minute is still a rate, so it stays a number rather
            # than a clock reading - but it needs its unit, or "31" beside "1:10"
            # reads as a count.
            ("per minute", per_min, qual,
             (lambda v: f"{v:.0f} s" if v >= 10 else f"{v:.1f} s") if seconds
             else (lambda v: T.compact(v) if v >= 10 else f"{v:.{rate_decimals}f}")),
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


def flag_hold(ctx: Ctx):
    """Time spent on the flag, and how much of it turns into points."""
    tot, qual = ctx.totals, ctx.qualified

    hold = qual.copy()
    hold["per_match"] = hold["flagCarryTime_sum"] / hold["games"]
    hold["share"] = hold["flagCarryTime_sum"] / (hold["minutes"] * 60)

    conv = tot[tot["attemptsOnFlag_sum"] >= MIN_PICKUPS].copy()
    conv["rate"] = conv["flagCaptures_sum"] / conv["attemptsOnFlag_sum"]
    conv["per_pickup"] = conv["flagCarryTime_sum"] / conv["attemptsOnFlag_sum"]
    conv["pickups_pm"] = conv["attemptsOnFlag_sum"] / conv["games"]

    overall = ctx.wsg["flagCaptures"].sum() / ctx.wsg["attemptsOnFlag"].sum()

    fig = plt.figure(figsize=(13.5, 10.1))
    top = T.figure_title(
        fig, "WSG flag hold and conversion",
        f"Top {TOP_N} for time spent carrying the flag, and for turning a pickup "
        "into a capture")
    bottom = T.footnote(fig, ctx.source_note(
        f"The carry-time total covers every character; the two boards beside it need "
        f"at least {ctx.min_games} matches. Conversion needs {MIN_PICKUPS}+ pickups, "
        f"otherwise a single lucky grab tops it. Across everyone {overall*100:.0f} % of "
        "pickups become a capture."))
    axes = H.grid_axes(fig, 2, 3, left=0.105, right=0.975, top=top - 0.035,
                       bottom=bottom, wspace=0.80, hspace=0.34)

    panels = [
        (tot, tot["flagCarryTime_sum"], "Flag carry time — total", fmt_duration,
         "flagCarryTime"),
        (hold, hold["per_match"], "per match", fmt_duration, None),
        (hold, hold["share"], "share of own time played",
         lambda v: f"{v*100:.1f} %", None),
        (conv, conv["rate"], "Pickups that become a capture",
         lambda v: f"{v*100:.0f} %", "attemptsOnFlag"),
        (conv, conv["per_pickup"], "seconds carried per pickup", fmt_duration, None),
        (conv, conv["pickups_pm"], "pickups per match", lambda v: f"{v:.2f}", None),
    ]
    for i, (frame, series, heading, value_fmt, icon_col) in enumerate(panels):
        ax = axes[i // 3][i % 3]
        best = series.nlargest(TOP_N)
        sub = frame.loc[best.index]
        H.top_hbar(ax, sub["player"], best.to_numpy(),
                   colors=H.class_colors(sub["class_name"]),
                   label_colors=H.class_text_colors(sub["class_name"]),
                   value_fmt=value_fmt)
        if icon_col:
            icons.panel_title(fig, ax, heading, icon_col)
        else:
            ax.set_title(heading, fontsize=10.5, pad=8, loc="left")
    return fig


CHARTS = [
    ("13_flag_leaders", flag_leaders),
    ("14_carrier_leaders", carrier_leaders),
    ("15_flag_hold", flag_hold),
]
