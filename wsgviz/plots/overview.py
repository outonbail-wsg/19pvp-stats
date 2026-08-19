"""General statistics: scope, activity, player base."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .. import theme as T
from ..context import TRACKING_CAVEAT, Ctx
from ..data import CONTESTED_PER_TEAM, fmt_duration
from . import helpers as H

MODE_LABEL = {"wsg": "Warsong Gulch", "2v2": "Arena 2v2", "3v3": "Arena 3v3"}


def overview(ctx: Ctx):
    """Headline numbers: the shape of the dataset at a glance."""
    raw, w, m = ctx.raw, ctx.wsg, ctx.matches
    days = (raw["ts"].max() - raw["ts"].min()).total_seconds() / 86400

    fig = plt.figure(figsize=(13, 7.6))
    top = T.figure_title(
        fig, "Warsong Gulch – dataset overview",
        f"19pvp level 19 PvP | {ctx.period_label} | {days:.1f} days")
    bottom = T.footnote(fig, ctx.source_note(TRACKING_CAVEAT))

    tiles = [
        (T.num(m.shape[0]), "WSG matches", "recorded battles"),
        (T.num(raw["playerGuid"].nunique()), "characters total", "across all modes"),
        (T.num(w["playerGuid"].nunique()), "characters in WSG", "of those"),
        (T.num(len(raw)), "player-match records", "one row = one player per match"),
        (fmt_duration(m["duration"].median()), "median match length", "longest time played in match"),
        (T.num(m.shape[0] / max(days, 1e-9), 1), "matches per day", "on average"),
        (T.num(w["flagCaptures"].sum()), "flags captured", "by tracked players"),
        (T.num(w["damageDone"].sum() / 1e6, 1) + "M", "damage dealt", "in WSG"),
    ]
    tile_h = 0.115
    row_y = [top - tile_h, top - tile_h * 2 - 0.045]
    for i, (value, label, sub) in enumerate(tiles):
        r, c = divmod(i, 4)
        H.stat_tile(fig, [0.035 + c * 0.242, row_y[r], 0.21, tile_h], value, label, sub)

    plot_h = (row_y[1] - 0.09) - bottom
    xb = T.xband(fig)

    # Mode split: three nominal categories, so one colour for all of them.
    ax = fig.add_axes([0.115, bottom + xb * 0.4, 0.33, plot_h - xb * 0.4])
    by_mode = (raw.groupby("kind")
                  .agg(matches=("eventId", "nunique"), players=("playerGuid", "nunique"))
                  .reindex(["wsg", "2v2", "3v3"]).dropna(how="all"))
    labels = [f"{MODE_LABEL[k]}\n{T.num(by_mode.loc[k, 'players'])} characters"
              for k in by_mode.index]
    H.top_hbar(ax, labels, by_mode["matches"].to_numpy(),
               title="Matches per game mode", value_fmt=T.num, bar_frac=0.34)

    # How many of a match's up-to-20 slots are recorded at all?
    ax2 = fig.add_axes([0.60, bottom + xb, 0.37, plot_h - xb])
    H.hist(ax2, m["tracked"], bins=np.arange(0, m["tracked"].max() + 2) - 0.5)
    ax2.set_title("Tracked players per match", fontsize=10.5, pad=8)
    ax2.set_xlabel("players running the addon")
    ax2.set_ylabel("matches")
    return fig


def activity_per_day(ctx: Ctx):
    """Matches per day, split by mode."""
    per_day = (ctx.raw.groupby(["date", "kind"])["eventId"].nunique()
                  .unstack(fill_value=0).sort_index())
    for k in ("wsg", "2v2", "3v3"):
        if k not in per_day.columns:
            per_day[k] = 0

    fig = plt.figure(figsize=(12, 6))
    top = T.figure_title(fig, "Matches per day",
                         "Recorded matches per calendar day and game mode")
    bottom = T.footnote(fig, ctx.source_note(
        "First and last day are partial."))
    xb = T.xband(fig, label=False)
    ax = fig.add_axes([0.065, bottom + xb, 0.79, top - bottom - xb - 0.05])

    for key, color in zip(("wsg", "2v2", "3v3"), T.CATEGORICAL):
        ax.plot(per_day.index, per_day[key], color=color, marker="o",
                markersize=4, markerfacecolor=color, markeredgecolor=T.SURFACE,
                markeredgewidth=1.4, label=MODE_LABEL[key])
        H.label_last_point(ax, per_day.index[-1], per_day[key].iloc[-1],
                           MODE_LABEL[key], color)

    T.clean_axes(ax)
    ax.set_ylabel("matches")
    ax.set_ylim(0, per_day.to_numpy().max() * 1.10)
    ax.legend(loc="lower left", ncols=3, bbox_to_anchor=(0, 1.01))
    ax.set_xlim(per_day.index[0], per_day.index[-1] + pd.Timedelta(days=1.6))
    fig.autofmt_xdate(rotation=0, ha="center")
    return fig


def activity_per_hour(ctx: Ctx):
    """Peak hours, measured by real-player density rather than match count.

    Match count is the wrong metric here: bots fill empty slots whenever anyone
    queues, so matches run around the clock at a near-constant rate. What varies
    is how much of a match is made of real players.
    """
    m = ctx.matches
    hours = range(24)
    per_hour = m.groupby("hour").size().reindex(hours, fill_value=0)
    real_per_match = m.groupby("hour")["tracked"].mean().reindex(hours)
    full = m[(m["tracked_team0"] >= CONTESTED_PER_TEAM)
             & (m["tracked_team1"] >= CONTESTED_PER_TEAM)]
    full_share = (full.groupby("hour").size().reindex(hours, fill_value=0)
                  / per_hour.replace(0, np.nan)).fillna(0)

    days = (m["ts"].max() - m["ts"].min()).total_seconds() / 86400

    fig = plt.figure(figsize=(13.5, 5.6))
    top = T.figure_title(
        fig, "WSG activity by hour of day",
        "Real players per match, share of full lobbies, and match count, per "
        "hour-of-day bucket")
    bottom = T.footnote(fig, ctx.source_note(
        f"WSG only: all {T.num(len(m))} matches placed in their hour-of-day bucket and "
        f"summed over {days:.1f} days, so the right panel totals are sums, not rates - "
        f"they correspond to {per_hour.mean()/days:.1f} matches per hour. Real players "
        f"per match ranges {real_per_match.min():.1f} to {real_per_match.max():.1f}; "
        "counts are distinct players over the match, so replacements inflate them "
        "slightly."))
    xb = T.xband(fig)
    h = top - bottom - xb
    w = 0.263

    def hour_axis(ax):
        T.clean_axes(ax)
        # Every 2 h: with 24 bars, 4-hourly ticks make it guesswork which bar is
        # which hour. Minor ticks mark the hours in between.
        ax.set_xticks(range(0, 24, 2))
        ax.set_xticklabels([f"{x:02d}" for x in range(0, 24, 2)], fontsize=8)
        ax.set_xticks(range(24), minor=True)
        ax.tick_params(axis="x", which="minor", length=2, color=T.AXIS)
        ax.set_xlabel(f"hour of day ({ctx.tz})")
        ax.set_xlim(-0.8, 23.8)

    ax1 = fig.add_axes([0.065, bottom + xb, w, h])
    peak = int(real_per_match.idxmax())
    # Emphasis: the maximum bar keeps the accent, the rest steps back one shade,
    # so the label can only refer to one bar.
    bar_colors = [T.PRIMARY if x == peak else "#8ab6ea" for x in hours]
    ax1.bar(hours, real_per_match.to_numpy(), width=0.72, color=bar_colors, linewidth=0)
    hour_axis(ax1)
    ax1.set_ylabel("real players per match")
    ax1.set_title("Real players per match", fontsize=10.5, pad=8)
    ax1.set_ylim(0, real_per_match.max() * 1.28)
    # Leader line straight up from the highest bar, text left of it so it cannot
    # be read as belonging to a neighbour.
    ax1.annotate(f"max {peak:02d}:00 · {real_per_match.max():.1f}",
                 xy=(peak, real_per_match.max()),
                 xytext=(peak - 1.2, real_per_match.max() * 1.20),
                 fontsize=9, color=T.INK, ha="right", va="center",
                 arrowprops=dict(arrowstyle="-", color=T.INK_MUTED, linewidth=1,
                                 shrinkB=3))

    ax2 = fig.add_axes([0.395, bottom + xb, w, h])
    ax2.bar(hours, full_share.to_numpy(), width=0.72, color=T.PRIMARY, linewidth=0)
    hour_axis(ax2)
    H.percent_axis(ax2)
    ax2.set_ylabel("share of matches")
    ax2.set_title(f"Matches with {CONTESTED_PER_TEAM}+ real players per team",
                  fontsize=10.5, pad=8)
    ax2.set_ylim(0, max(0.1, full_share.max() * 1.25))

    # Match count is the denominator of the other two panels, not a finding of
    # its own, so it sits in the de-emphasis grey.
    ax3 = fig.add_axes([0.725, bottom + xb, w, h])
    ax3.bar(hours, per_hour.to_numpy(), width=0.72, color=T.DEEMPHASIS, linewidth=0)
    ax3.axhline(per_hour.mean(), color=T.INK, linewidth=1.2)
    hour_axis(ax3)
    ax3.set_ylabel(f"matches (sum over {days:.0f} days)")
    ax3.set_title("WSG matches played", fontsize=10.5, pad=8)
    ax3.set_ylim(0, per_hour.max() * 1.20)
    return fig


def activity_heatmap(ctx: Ctx):
    """Weekday x hour of real-player density. Magnitude -> one blue ramp.

    A mean rather than a count: with 11 days each cell holds only a few matches,
    and a raw count would be mostly noise.
    """
    grid = (ctx.matches.groupby(["weekday", "hour"])["tracked"].mean()
              .unstack()
              .reindex(index=range(7), columns=range(24)))
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    fig = plt.figure(figsize=(12.5, 5.2))
    top = T.figure_title(fig, "Real players per match by weekday and hour",
                         "Darker = more real players in the average match")
    bottom = T.footnote(fig, ctx.source_note(
        "Mean real players per match per cell; blank cells had no matches. Each weekday "
        "occurs once or twice in the window, so single cells are noisy - read the "
        "columns, not the cells."))
    xb = T.xband(fig)
    ax = fig.add_axes([0.085, bottom + xb, 0.80, top - bottom - xb])

    im = ax.imshow(grid.to_numpy(), aspect="auto", cmap=T.SEQUENTIAL,
                   vmin=0, interpolation="nearest")
    ax.set_yticks(range(7))
    ax.set_yticklabels(days, fontsize=9, color=T.INK_SECONDARY)
    ax.set_xticks(range(0, 24, 2))
    ax.set_xticklabels([f"{h:02d}" for h in range(0, 24, 2)])
    ax.set_xlabel(f"hour ({ctx.tz})")
    ax.grid(False)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)

    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("real players per match", fontsize=9, color=T.INK_SECONDARY)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=8, length=0, colors=T.INK_MUTED)
    return fig


def player_base(ctx: Ctx):
    """Active and new characters per day."""
    w = ctx.wsg.sort_values("at")
    first_seen = w.groupby("playerGuid")["date"].min()
    active = w.groupby("date")["playerGuid"].nunique()
    new = first_seen.value_counts().reindex(active.index, fill_value=0).sort_index()
    returning = active - new

    fig = plt.figure(figsize=(12, 6))
    top = T.figure_title(fig, "Player base per day",
                         "Active characters in WSG, split into returning and new")
    bottom = T.footnote(fig, ctx.source_note(
        f"{T.num(w['playerGuid'].nunique())} distinct characters, median "
        f"{T.num(active.median())} active per day. Everyone counts as new on day one."))
    xb = T.xband(fig, label=False)
    ax = fig.add_axes([0.065, bottom + xb, 0.90, top - bottom - xb - 0.05])

    # Part-to-whole -> stacked, with a thin gap between the segments.
    gap = active.max() * 0.006
    ax.bar(active.index, returning, width=0.62, color=T.CATEGORICAL[0],
           label="seen before", linewidth=0)
    ax.bar(active.index, new, width=0.62, bottom=returning + gap,
           color=T.CATEGORICAL[1], label="first seen today", linewidth=0)

    T.clean_axes(ax)
    ax.set_ylabel("characters")
    ax.legend(loc="lower left", ncols=2, bbox_to_anchor=(0, 1.01))
    fig.autofmt_xdate(rotation=0, ha="center")
    return fig


def participation(ctx: Ctx):
    """How unevenly is play spread across characters?"""
    games = ctx.totals["games"].sort_values(ascending=False).to_numpy()

    fig = plt.figure(figsize=(12.5, 5.8))
    top = T.figure_title(
        fig, "Matches per character",
        "Distribution of matches played per character, and cumulative share of play")
    bottom = T.footnote(fig, ctx.source_note(
        f"Median {T.num(np.median(games))} matches per character, max {T.num(games.max())}."))
    xb = T.xband(fig)
    h = top - bottom - xb - 0.05

    ax1 = fig.add_axes([0.055, bottom + xb, 0.38, h])
    bins = np.array([1, 2, 3, 5, 10, 20, 40, 80, 160, games.max() + 1])
    counts, _ = np.histogram(games, bins=bins)
    labels = [f"{int(bins[i])}–{int(bins[i+1]-1)}" if bins[i + 1] - bins[i] > 1
              else f"{int(bins[i])}" for i in range(len(bins) - 1)]
    ax1.bar(np.arange(len(counts)), counts, width=0.68, color=T.PRIMARY, linewidth=0)
    T.clean_axes(ax1)
    ax1.set_xticks(np.arange(len(counts)))
    ax1.set_xticklabels(labels, fontsize=8.5)
    ax1.set_xlabel("matches played")
    ax1.set_ylabel("characters")
    ax1.set_title("Characters by matches played", fontsize=10.5, pad=8)
    ax1.set_ylim(0, counts.max() * 1.12)
    for x, c in enumerate(counts):
        ax1.text(x, c, T.num(c), ha="center", va="bottom", fontsize=8,
                 color=T.INK_SECONDARY)

    # Lorenz curve: share of characters against share of all participations.
    ax2 = fig.add_axes([0.575, bottom + xb, 0.38, h])
    cum = np.cumsum(games) / games.sum()
    share = np.arange(1, len(games) + 1) / len(games)
    ax2.plot(np.concatenate([[0], share]), np.concatenate([[0], cum]), color=T.PRIMARY)
    ax2.plot([0, 1], [0, 1], color=T.DEEMPHASIS, linewidth=1.4)
    T.clean_axes(ax2)
    H.percent_axis(ax2, "x")
    H.percent_axis(ax2, "y")
    ax2.set_xlabel("share of characters (most active first)")
    ax2.set_ylabel("share of all participations")
    ax2.set_title("Concentration of play", fontsize=10.5, pad=8)
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)

    top10 = cum[int(len(games) * 0.10) - 1]
    ax2.plot([0.10], [top10], marker="o", markersize=7, color=T.PRIMARY,
             markeredgecolor=T.SURFACE, markeredgewidth=2)
    ax2.annotate(f"top 10 % of characters: {top10*100:.0f} % of matches played",
                 xy=(0.10, top10), xytext=(0.18, top10 - 0.26), fontsize=9,
                 color=T.INK, ha="left",
                 arrowprops=dict(arrowstyle="-", color=T.INK_MUTED, linewidth=1))
    ax2.text(0.55, 0.47, "perfect equality", fontsize=8.5, color=T.INK_MUTED,
             rotation=30, ha="center", va="center")
    return fig


CHARTS = [
    ("01_overview", overview),
    ("03_participation", participation),
    ("04_player_base", player_base),
    ("05_activity_per_hour", activity_per_hour),
    ("06_activity_heatmap", activity_heatmap),
    ("07_activity_per_day", activity_per_day),
]
