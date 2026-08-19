"""Match level: length, final score, tracking coverage."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from .. import theme as T
from ..context import TRACKING_CAVEAT, Ctx
from ..data import CAPS_TO_WIN, fmt_duration
from . import helpers as H


def _score_label(margin: float) -> str:
    """margin = 3 minus the loser's captures."""
    return f"{CAPS_TO_WIN}–{int(CAPS_TO_WIN - margin)}"


def match_length(ctx: Ctx):
    """How long does a match run?"""
    m = ctx.matches
    dur = m.loc[m["duration"] > 0, "duration"] / 60.0

    fig = plt.figure(figsize=(12, 5.8))
    top = T.figure_title(
        fig, "WSG match length",
        "Distribution of match length in minutes (longest time played in the match)")
    bottom = T.footnote(fig, ctx.source_note(
        f"{len(dur)} of {len(m)} matches, median {fmt_duration(dur.median()*60)}. Length "
        "= longest time played by any tracked player."))
    xb = T.xband(fig)
    ax = fig.add_axes([0.065, bottom + xb, 0.90, top - bottom - xb])

    H.hist(ax, dur, bins=np.arange(0, dur.max() + 1, 1))
    ax.set_xlabel("match length (minutes)")
    ax.set_ylabel("matches")
    ax.set_xlim(0, dur.max() * 1.02)

    q90 = dur.quantile(0.9)
    ax.axvline(q90, color=T.INK_MUTED, linewidth=1.2)
    ax.annotate("90 % of matches", xy=(q90, 1), xycoords=("data", "axes fraction"),
                xytext=(-6, -10), textcoords="offset points", fontsize=9,
                color=T.INK_MUTED, ha="right", va="top")
    return fig


def final_score(ctx: Ctx):
    """How close do matches end?"""
    m = ctx.matches
    ok = m[m["fully_tracked"]]
    counts = ok["margin"].value_counts().reindex([3.0, 2.0, 1.0]).fillna(0).astype(int)
    total = counts.sum()

    fig = plt.figure(figsize=(11.5, 5.2))
    top = T.figure_title(
        fig, "WSG final score distribution",
        f"Final score of the {T.num(total)} matches whose score is fully tracked")
    bottom = T.footnote(fig, ctx.source_note(
        f"Only matches whose winning team shows all 3 captures ({ok.shape[0]} of "
        f"{m.shape[0]}); otherwise the score is biased low."))
    ax = fig.add_axes([0.13, bottom + 0.02, 0.72, top - bottom - 0.04])

    labels = [f"{_score_label(x)}\n{v/total*100:.0f} % of matches"
              for x, v in zip(counts.index, counts)]
    H.top_hbar(ax, labels, counts.to_numpy(), value_fmt=T.num,
               bar_frac=0.34, title="Final score (winner – loser)")
    return fig


def tracking_coverage(ctx: Ctx):
    """Data quality: how much of a match does the export actually see?"""
    m = ctx.matches
    caps = m.loc[~m["draw"], "caps_winner"].value_counts().reindex([3, 2, 1, 0]).fillna(0)

    fig = plt.figure(figsize=(12.5, 5.6))
    top = T.figure_title(
        fig, "WSG match tracking coverage",
        "How much of each match the export records")
    bottom = T.footnote(fig, ctx.source_note(
        TRACKING_CAVEAT + " Player-level rows are complete in themselves."))
    xb = T.xband(fig)
    h = top - bottom - xb

    ax1 = fig.add_axes([0.09, bottom + xb, 0.35, h])
    H.top_hbar(ax1, [f"{int(k)} of 3" for k in caps.index], caps.to_numpy(),
               value_fmt=T.num, highlight={0},
               title="Winning team's captures that are tracked")
    ax1.set_xlabel("matches")

    # Are both teams tracked equally well? Otherwise team comparisons tilt.
    ax2 = fig.add_axes([0.57, bottom + xb, 0.38, h])
    diff = m["tracked_team0"] - m["tracked_team1"]
    ax2.hist(diff, bins=np.arange(diff.min() - 0.5, diff.max() + 1.5, 1),
             color=T.PRIMARY, linewidth=0)
    ax2.axvline(0, color=T.INK, linewidth=1.4)
    T.clean_axes(ax2)
    ax2.set_title("Tracking difference between the teams", fontsize=10.5, pad=8)
    ax2.set_xlabel("tracked players on team 0 minus team 1")
    ax2.set_ylabel("matches")
    ax2.annotate(f"median {T.num(diff.median())}", xy=(0, 1),
                 xycoords=("data", "axes fraction"), xytext=(8, -8),
                 textcoords="offset points", fontsize=9, color=T.INK, va="top")
    return fig


CHARTS = [
    ("14_match_length", match_length),
    ("15_final_score", final_score),
    ("16_tracking_coverage", tracking_coverage),
]
