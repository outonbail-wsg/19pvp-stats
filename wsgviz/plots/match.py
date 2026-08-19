"""Match level: length, final score, tracking coverage."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .. import theme as T
from ..context import TRACKING_CAVEAT, Ctx
from ..data import CAPS_TO_WIN, TIMER_SECONDS, fmt_duration
from . import helpers as H


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
    """How matches end, and on what score."""
    m = ctx.matches
    known = m[m["score_known"]]
    total = len(known)

    ending = pd.Series({
        f"Captured {CAPS_TO_WIN} flags": int(known["capped_out"].sum()),
        "Timer expired": int((~known["capped_out"]).sum()),
    })
    scores = known["score"].value_counts().head(8)

    fig = plt.figure(figsize=(12.5, 5.6))
    top = T.figure_title(
        fig, "How a WSG match ends",
        f"Way the round finished and the resulting score, across {T.num(total)} matches")
    bottom = T.footnote(fig, ctx.source_note(
        f"A round ends on {CAPS_TO_WIN} captures or when the "
        f"{TIMER_SECONDS // 60}-minute timer expires, so 2–1 or 1–0 are normal results. "
        f"Excluded are {len(m) - total} matches whose recorded players all left before "
        "the end, where the score cannot be read."))
    xb = T.xband(fig)
    h = top - bottom - xb

    ax1 = fig.add_axes([0.14, bottom + xb, 0.28, h])
    H.top_hbar(ax1, [f"{k}\n{v/total*100:.0f} %" for k, v in ending.items()],
               ending.to_numpy(), value_fmt=T.num, bar_frac=0.26,
               title="How the round finished")
    ax1.set_xlabel("matches")

    ax2 = fig.add_axes([0.62, bottom + xb, 0.30, h])
    H.top_hbar(ax2, [f"{s}   {v/total*100:.0f} %" for s, v in scores.items()],
               scores.to_numpy(), value_fmt=T.num,
               title="Final score (winner – loser)")
    ax2.set_xlabel("matches")
    return fig


def humans_vs_bots(ctx: Ctx):
    """How much of a team was human, and what an imbalance does to the result."""
    m = ctx.matches
    dec = m[~m["draw"]]
    humans = pd.concat([dec["tracked_team0"], dec["tracked_team1"]])

    # Every real player is in the export, so the recorded count IS the human
    # count and the rest of the ten slots were bots.
    adv = (dec["tracked_team0"] - dec["tracked_team1"]).clip(-3, 3)
    by_adv = pd.DataFrame({"adv": adv, "win": (dec["winner"] == 0).astype(int)})
    grp = by_adv.groupby("adv")["win"].agg(["mean", "size"])
    grp = grp[grp["size"] >= 15]

    fig = plt.figure(figsize=(12.5, 5.8))
    top = T.figure_title(
        fig, "Humans and bots in a WSG match",
        "How many of a team's ten slots were real players, and what an imbalance "
        "does to the result")
    bottom = T.footnote(fig, ctx.source_note(
        TRACKING_CAVEAT + " Counts are distinct players over the match, so a team that "
        "replaced leavers can show more than ten. Association, not proof that the bots "
        "are what decide it."))
    xb = T.xband(fig)
    h = top - bottom - xb

    ax1 = fig.add_axes([0.075, bottom + xb, 0.37, h])
    ax1.hist(humans, bins=np.arange(0, humans.max() + 2) - 0.5,
             color=T.PRIMARY, linewidth=0)
    T.clean_axes(ax1)
    ax1.set_title("Real players per team", fontsize=10.5, pad=8)
    ax1.set_xlabel("humans in the team (of 10 slots)")
    ax1.set_ylabel("team-sides")
    ax1.annotate(f"median {int(humans.median())}", xy=(humans.median(), 1),
                 xycoords=("data", "axes fraction"), xytext=(6, -10),
                 textcoords="offset points", fontsize=9, color=T.INK, va="top")

    ax2 = fig.add_axes([0.585, bottom + xb, 0.37, h])
    x = grp.index.to_numpy()
    ax2.bar(x, grp["mean"].to_numpy(), width=0.62, color=T.PRIMARY, linewidth=0)
    T.clean_axes(ax2)
    H.percent_axis(ax2)
    ax2.set_title("Win rate by human advantage", fontsize=10.5, pad=8)
    ax2.set_xlabel("own humans minus enemy humans")
    ax2.set_ylabel("win rate")
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"{int(v):+d}" if v else "0" for v in x])
    ax2.set_ylim(0, 1)
    for xi, v, n in zip(x, grp["mean"], grp["size"]):
        ax2.text(xi, v, f"{v*100:.0f} %", ha="center", va="bottom", fontsize=9,
                 color=T.INK_SECONDARY)
        ax2.text(xi, 0.02, f"n={int(n)}", ha="center", va="bottom", fontsize=7.5,
                 color=T.INK_MUTED)
    return fig


CHARTS = [
    ("14_match_length", match_length),
    ("15_final_score", final_score),
    ("16_humans_vs_bots", humans_vs_bots),
]
