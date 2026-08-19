"""What separates wins from losses?

Everything here is correlation, not cause: winning also creates opportunities.
All rates are therefore per minute, so the comparison does not simply measure
the longer time winners spend in the match.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .. import theme as T
from ..context import Ctx
from ..data import STATS_BY_COLUMN
from . import helpers as H

# Stats that describe how someone plays. bonusHonor is deliberately absent -
# honor is mechanically tied to winning and would make the comparison circular.
COMPARE_STATS = [
    "flagReturns", "damageOnEFC", "healsOnFC", "attemptsOnFlag",
    "killingBlows", "successfulInterrupts", "dispelsDefensive", "dispelsOffensive",
    "hardCCCount", "softCCCount", "damageDone", "healingDone", "absorbsDone",
    "damageTaken", "deaths",
]

WINRATE_STATS = ["flagReturns", "damageOnEFC", "healsOnFC",
                 "damageDone", "healingDone", "killingBlows"]


def win_vs_loss(ctx: Ctx):
    """Relative difference in per-minute values between winning and losing."""
    r = ctx.rates
    r = r[~r["draw"] & (r["deserted"] == 0)]      # deserters are their own story
    win, lose = r[r["win"] == 1], r[r["win"] == 0]

    rows = []
    for col in COMPARE_STATS:
        pm = f"{col}_pm"
        if pm not in r.columns:
            continue
        a, b = win[pm].mean(), lose[pm].mean()
        if b > 0:
            rows.append((STATS_BY_COLUMN[col].label, (a - b) / b * 100))
    rows.sort(key=lambda t: t[1], reverse=True)

    fig = plt.figure(figsize=(12, 8.4))
    top = T.figure_title(
        fig, "WSG per-minute stats: winners vs losers",
        "Difference in mean per-minute values, winners relative to losers")
    bottom = T.footnote(fig, ctx.source_note(
        f"{T.num(len(win))} winner vs {T.num(len(lose))} loser rows (>=60 s played, no "
        "deserters or draws)."))
    ax = fig.add_axes([0.30, bottom + 0.03, 0.60, top - bottom - 0.06])

    H.diverging_hbar(ax, [t[0] for t in rows], [t[1] for t in rows],
                     pos_label="higher when winning", neg_label="higher when losing")
    ax.legend(loc="lower right", bbox_to_anchor=(1.0, -0.09), ncols=2)
    return fig


def desertion(ctx: Ctx):
    """What happens when players leave a match?"""
    w = ctx.wsg
    dec = w[~w["draw"]]

    # Deserters on the player's own team, excluding the player themselves.
    team_des = dec.groupby(["eventId", "team"])["deserted"].sum().rename("team_des")
    d = dec.join(team_des, on=["eventId", "team"])
    d["mates_deserted"] = d["team_des"] - d["deserted"]
    own = d[d["deserted"] == 0]
    by_mates = own.groupby(own["mates_deserted"].clip(upper=3)).agg(
        winrate=("win", "mean"), n=("win", "size"))

    fig = plt.figure(figsize=(12.5, 5.8))
    top = T.figure_title(
        fig, "WSG desertions",
        "Time played by deserters, and win rate by deserters on your own team")
    bottom = T.footnote(fig, ctx.source_note(
        f"{T.num(int(w['deserted'].sum()))} of {T.num(len(w))} rows deserted "
        f"({w['deserted'].mean()*100:.1f} %). Right panel counts only players who "
        "stayed."))
    xb = T.xband(fig)
    h = top - bottom - xb

    # Left: time played by deserters against those who stayed.
    ax1 = fig.add_axes([0.07, bottom + xb, 0.37, h])
    stay = w.loc[w["deserted"] == 0, "minutes"]
    left = w.loc[w["deserted"] == 1, "minutes"]
    bins = np.arange(0, max(stay.max(), left.max()) + 1, 1.5)
    ax1.hist(stay, bins=bins, color=T.CATEGORICAL[0], linewidth=0,
             label="stayed", density=True)
    ax1.hist(left, bins=bins, color=T.CATEGORICAL[1], linewidth=0,
             label="deserted", density=True, alpha=0.75)
    T.clean_axes(ax1)
    ax1.set_title("Time played in the match", fontsize=10.5, pad=8)
    ax1.set_xlabel("minutes in the match")
    ax1.set_ylabel("share (density)")
    ax1.set_yticks([])
    ax1.legend(loc="upper right")

    # Right: win rate by number of deserters on the player's own team.
    ax2 = fig.add_axes([0.57, bottom + xb, 0.37, h])
    x = by_mates.index.to_numpy()
    ax2.bar(x, by_mates["winrate"].to_numpy(), width=0.6, color=T.PRIMARY, linewidth=0)
    T.clean_axes(ax2)
    H.percent_axis(ax2)
    ax2.set_title("Win rate by deserters on your own team", fontsize=10.5, pad=8)
    ax2.set_xlabel("team mates who left the match")
    ax2.set_xticks(x)
    ax2.set_xticklabels([str(int(v)) if v < 3 else "3+" for v in x])
    ax2.set_ylim(0, max(0.65, by_mates["winrate"].max() * 1.25))
    for xi, v, n in zip(x, by_mates["winrate"], by_mates["n"]):
        ax2.text(xi, v, f"{v*100:.0f} %", ha="center", va="bottom", fontsize=9,
                 color=T.INK_SECONDARY)
        ax2.text(xi, 0, f"n = {T.num(n)}", ha="center", va="bottom", fontsize=8,
                 color=T.INK_MUTED)
    return fig


def winrate_by_stat(ctx: Ctx):
    """Win rate by quintile of the player's own per-minute performance."""
    r = ctx.rates
    r = r[~r["draw"] & (r["deserted"] == 0)]
    baseline = r["win"].mean()

    fig = plt.figure(figsize=(13, 7.4))
    top = T.figure_title(
        fig, "WSG win rate by per-minute stat quintile",
        "Player rows split into five equal groups per statistic – from the lowest 20 % "
        "to the highest 20 %")
    bottom = T.footnote(fig, ctx.source_note(
        f"Values per minute. Line = mean of the rows shown ({baseline*100:.0f} %), "
        "which is above 50 % because deserters are excluded and they mostly lose. "
        "Associations, not causal effects."))
    axes = H.grid_axes(fig, 2, 3, left=0.06, right=0.98, top=top,
                       bottom=bottom + T.xband(fig), wspace=0.30, hspace=0.62)

    for i, col in enumerate(WINRATE_STATS):
        ax = axes[i // 3][i % 3]
        # Many stats are zero-heavy; ranking first keeps the five groups equal.
        q = pd.qcut(r[f"{col}_pm"].rank(method="first"), 5, labels=False)
        grp = r.groupby(q)["win"].agg(["mean", "size"])
        ax.bar(grp.index, grp["mean"], width=0.68, color=T.PRIMARY, linewidth=0)
        ax.axhline(baseline, color=T.INK, linewidth=1.2)
        T.clean_axes(ax)
        H.percent_axis(ax)
        ax.set_title(STATS_BY_COLUMN[col].label, fontsize=10, pad=6)
        ax.set_xticks(range(5))
        ax.set_xticklabels(["1\nlowest", "2", "3", "4", "5\nhighest"], fontsize=8)
        ax.set_ylim(0, 1)
        ax.tick_params(axis="y", labelsize=8)
        if i % 3 == 0:
            ax.set_ylabel("win rate")
        for xi, v in zip(grp.index, grp["mean"]):
            ax.text(xi, v, f"{v*100:.0f}", ha="center", va="bottom", fontsize=8,
                    color=T.INK_SECONDARY)
    return fig


def deserter_ranking(ctx: Ctx):
    """Who leaves matches - by name, with class, and by class overall."""
    w = ctx.wsg
    tot = ctx.totals
    q = tot[tot["games"] >= ctx.min_games]

    by_rate = q.nlargest(12, "desert_rate")
    by_count = tot.nlargest(12, "desertions")
    by_class = (w.dropna(subset=["class_name"])
                  .groupby("class_name")["deserted"].agg(["sum", "size"]))
    by_class["rate"] = by_class["sum"] / by_class["size"]
    # This panel is a ranking, so it sorts by value rather than following the
    # fixed class order the comparison charts use.
    by_class = by_class.sort_values("rate", ascending=False)
    class_order = list(by_class.index)

    fig = plt.figure(figsize=(13.5, 6.6))
    top = T.figure_title(
        fig, "WSG desertions: who leaves",
        "Characters ranked by how often they abandon a match, and desertion rate "
        "per class")
    bottom = T.footnote(fig, ctx.source_note(
        f"{T.num(int(w['deserted'].sum()))} of {T.num(len(w))} player rows are flagged "
        f"as deserted. The rate board needs >={ctx.min_games} matches, otherwise a "
        "single leave on a single match tops it at 100 %; the count board has no "
        "threshold."))
    xb = T.xband(fig)
    h = top - bottom - xb
    wax = 0.235

    ax1 = fig.add_axes([0.105, bottom + xb, wax, h])
    H.top_hbar(ax1, by_rate["player"], (by_rate["desert_rate"] * 100).to_numpy(),
               colors=H.class_colors(by_rate["class_name"]),
               label_colors=H.class_text_colors(by_rate["class_name"]),
               value_fmt=lambda v: f"{v:.0f} %",
               title=f"Highest desertion rate (>={ctx.min_games} matches)")
    ax1.set_xlabel("share of own matches left")

    ax2 = fig.add_axes([0.435, bottom + xb, wax, h])
    H.top_hbar(ax2, by_count["player"], by_count["desertions"].to_numpy(),
               colors=H.class_colors(by_count["class_name"]),
               label_colors=H.class_text_colors(by_count["class_name"]), value_fmt=T.num,
               title="Most desertions in total")
    ax2.set_xlabel("matches left")

    ax3 = fig.add_axes([0.765, bottom + xb, wax, h])
    H.top_hbar(ax3, class_order, (by_class["rate"] * 100).to_numpy(),
               colors=H.class_colors(class_order),
               value_fmt=lambda v: f"{v:.1f} %", title="Desertion rate by class")
    ax3.set_xlabel("share of player rows")
    return fig


CHARTS = [
    ("18_win_vs_loss", win_vs_loss),
    ("19_winrate_by_stat", winrate_by_stat),
    ("20_desertion", desertion),
    ("21_deserter_ranking", deserter_ranking),
]
