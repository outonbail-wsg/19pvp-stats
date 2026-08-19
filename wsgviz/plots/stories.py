"""Feature charts: the angles that carry a story rather than a summary.

Each of these leans on a derived measure that the plain leaderboards cannot
show - a record adjusted for how contested the lobby was, a conversion rate, a
head-to-head record, a retention curve.
"""

from __future__ import annotations

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .. import theme as T
from ..context import Ctx
from ..data import CONTESTED_PER_TEAM, THIN_PER_TEAM, fmt_duration
from . import helpers as H

MIN_IN_EACH = 8          # matches a character needs in both contexts

# Two shades of the same hue for the dumbbell - it is one measure in two
# conditions, not two different series.
SHADE_THIN = "#9ec5f4"
SHADE_FULL = "#1c5cab"

RECORD_STATS = [
    ("damageDone", "Damage in one match", None),
    ("healingDone", "Healing in one match", None),
    ("absorbsDone", "Absorbs in one match", None),
    ("killingBlows", "Killing blows", None),
    ("honorableKills", "Honorable kills", None),
    ("damageOnEFC", "Damage on enemy carrier", None),
    ("healsOnFC", "Healing on own carrier", None),
    ("flagReturns", "Flag returns", None),
    ("flagCarryTime", "Flag carried", fmt_duration),
]


def _lobby_sets(ctx: Ctx):
    m = ctx.matches
    full = set(m[(m["tracked_team0"] >= CONTESTED_PER_TEAM)
                 & (m["tracked_team1"] >= CONTESTED_PER_TEAM)].index)
    thin = set(m[(m["tracked_team0"] <= THIN_PER_TEAM)
                 & (m["tracked_team1"] <= THIN_PER_TEAM)].index)
    return full, thin


def contested_record(ctx: Ctx):
    """Win rate in contested lobbies against win rate in thin ones."""
    full, thin = _lobby_sets(ctx)
    d = ctx.wsg[~ctx.wsg["draw"]].copy()
    d["lobby"] = np.where(d["eventId"].isin(full), "full",
                          np.where(d["eventId"].isin(thin), "thin", "mid"))
    d = d[d["lobby"] != "mid"]

    g = d.groupby(["playerGuid", "lobby"])["win"].agg(["size", "mean"]).unstack()
    g.columns = ["n_full", "n_thin", "wr_full", "wr_thin"]
    g = g.dropna()
    g = g[(g["n_full"] >= MIN_IN_EACH) & (g["n_thin"] >= MIN_IN_EACH)]
    g = g.join(ctx.totals[["player", "class_name"]])
    g["drop"] = g["wr_thin"] - g["wr_full"]
    best = g.nlargest(14, "drop").sort_values("drop")

    fig = plt.figure(figsize=(12.5, 8.0))
    top = T.figure_title(
        fig, "Win rate in contested lobbies vs thin lobbies",
        f"Characters with at least {MIN_IN_EACH} decided matches in both kinds of lobby, "
        "biggest gap first")
    bottom = T.footnote(fig, ctx.source_note(
        f"A team holds 10 slots. Contested = both teams fielded at least "
        f"{CONTESTED_PER_TEAM} real players; thin = both at {THIN_PER_TEAM} or fewer, "
        f"where bots filled the rest. {len(g)} characters qualify. Thin lobbies run "
        "mostly at night, so the gap mixes lobby fill with opponent strength - it is a "
        "record adjusted for how contested the game was, not proof of farming."))
    ax = fig.add_axes([0.17, bottom + 0.05, 0.72, top - bottom - 0.09])

    y = np.arange(len(best))
    ax.hlines(y, best["wr_full"], best["wr_thin"], color=T.AXIS, linewidth=1.6,
              zorder=1)
    ax.scatter(best["wr_thin"], y, s=90, color=SHADE_THIN, zorder=3,
               edgecolors=T.SURFACE, linewidths=1.8, label="thin lobby")
    ax.scatter(best["wr_full"], y, s=90, color=SHADE_FULL, zorder=3,
               edgecolors=T.SURFACE, linewidths=1.8, label="contested lobby")

    ax.set_yticks(y)
    ax.set_yticklabels(best["player"], fontsize=9, color=T.INK_SECONDARY)
    for tick, c in zip(ax.get_yticklabels(), H.class_text_colors(best["class_name"])):
        tick.set_color(c)
    T.hbar_axes(ax)
    ax.grid(axis="x", visible=True)
    ax.tick_params(axis="x", length=3)
    H.percent_axis(ax, "x")
    ax.set_xlim(0, 1.16)
    ax.set_xticks(np.arange(0, 1.01, 0.2))
    ax.set_xlabel("win rate")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.005), ncols=2)
    # Sample size travels with each row rather than crowding the name.
    for yi, a, b in zip(y, best["n_thin"], best["n_full"]):
        ax.text(1.03, yi, f"{int(a)} / {int(b)}", va="center", ha="left",
                fontsize=8.5, color=T.INK_MUTED)
    ax.text(1.03, len(best) - 0.35, "thin / contested", va="center", ha="left",
            fontsize=8, color=T.INK_MUTED, style="italic")
    return fig


def record_book(ctx: Ctx):
    """Single-match bests - the numbers nobody has beaten."""
    w = ctx.wsg
    fig = plt.figure(figsize=(13, 6.9))
    top = T.figure_title(
        fig, "WSG record book",
        "Best single-match performance in the period, per statistic")
    bottom = T.footnote(fig, ctx.source_note(
        "One player in one match. Long matches favour totals, so the match length is "
        "shown with each record."))

    cols, rows = 3, 3
    cell_w, cell_h = 0.30, (top - bottom) / rows
    for i, (col, label, fmt) in enumerate(RECORD_STATS):
        r, c = divmod(i, cols)
        row = w.nlargest(1, col).iloc[0]
        x = 0.035 + c * cell_w
        y = top - r * cell_h
        value = fmt(row[col]) if fmt else T.num(row[col])
        cls = row["class_name"] if pd.notna(row["class_name"]) else None

        fig.text(x, y, value, fontsize=29, fontweight="semibold", color=T.INK,
                 va="top", ha="left")
        fig.text(x, y - 0.088, label, fontsize=10.5, color=T.INK_SECONDARY,
                 va="top", ha="left")
        # The holder's name carries the class colour, darkened to stay readable.
        fig.text(x, y - 0.132, row["player"], fontsize=10.5, fontweight="semibold",
                 color=H.class_text_colors([cls])[0], va="top", ha="left")
        fig.text(x, y - 0.176,
                 f"{cls or 'unknown class'} · {row['ts']:%d %b} · "
                 f"{row['timePlayed']/60:.0f} min",
                 fontsize=8.5, color=T.INK_MUTED, va="top", ha="left")
    return fig


def rivalries(ctx: Ctx):
    """Head-to-head records between the most active characters, plus streaks."""
    dec = ctx.wsg[~ctx.wsg["draw"]].sort_values("at")
    top_players = (dec.groupby("playerGuid").size().nlargest(10).index)
    sub = dec[dec["playerGuid"].isin(top_players)][
        ["eventId", "playerGuid", "player", "team", "win"]]

    opp = sub.merge(sub, on="eventId", suffixes=("", "_o"))
    opp = opp[opp["team"] != opp["team_o"]]
    h2h = opp.groupby(["player", "player_o"])["win"].agg(["size", "sum"])
    names = list(dec[dec["playerGuid"].isin(top_players)]
                 .groupby("playerGuid")["player"].last())

    n = len(names)
    wr = np.full((n, n), np.nan)
    txt = np.empty((n, n), dtype=object)
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            if a == b or (a, b) not in h2h.index:
                continue
            size, wins = h2h.loc[(a, b), "size"], h2h.loc[(a, b), "sum"]
            if size >= 8:
                wr[i, j] = wins / size
                txt[i, j] = f"{int(wins)}–{int(size - wins)}"

    # Longest streaks over every character with enough matches.
    streaks = []
    for guid, g in dec.groupby("playerGuid"):
        if len(g) < 20:
            continue
        cur = mx = curl = mxl = 0
        for v in g["win"].to_numpy():
            cur, curl = (cur + 1, 0) if v == 1 else (0, curl + 1)
            mx, mxl = max(mx, cur), max(mxl, curl)
        streaks.append((g["player"].iloc[-1], g["class_name"].iloc[-1], mx, mxl))
    sk = pd.DataFrame(streaks, columns=["player", "class_name", "wins", "losses"])

    fig = plt.figure(figsize=(14, 7.2))
    top = T.figure_title(
        fig, "Rivalries and streaks",
        "Head-to-head record between the ten most active characters, and the longest "
        "runs anyone put together")
    bottom = T.footnote(fig, ctx.source_note(
        "A cell reads as the row player's wins–losses against the column player when "
        "they were on opposite teams; blue means the row player is ahead, red behind, "
        "blank fewer than 8 meetings. These are team results, not duels. Streaks cover "
        "every character with 20+ decided matches."))

    ax = fig.add_axes([0.10, bottom + 0.03, 0.44, top - bottom - 0.06])
    norm = mcolors.TwoSlopeNorm(vmin=0.15, vcenter=0.5, vmax=0.85)
    # Reversed: a high win rate for the row player must read as the positive
    # pole (blue), otherwise winning cells come out red.
    ax.imshow(np.ma.masked_invalid(wr), cmap=T.DIVERGING.reversed(), norm=norm,
              interpolation="nearest")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=8.5,
                       color=T.INK_SECONDARY)
    ax.set_yticklabels(names, fontsize=8.5, color=T.INK_SECONDARY)
    ax.grid(False)
    ax.tick_params(length=0)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    for i in range(n):
        for j in range(n):
            if txt[i, j]:
                strong = abs(wr[i, j] - 0.5) > 0.22
                ax.text(j, i, txt[i, j], ha="center", va="center", fontsize=7.5,
                        color=T.SURFACE if strong else T.INK)
    ax.set_title("Head-to-head (row vs column)", fontsize=10.5, pad=10)

    # Two stacked panels sharing the right column, with a gap wide enough for the
    # lower panel's title to clear the upper panel's bars.
    gap = 0.13
    ph = (top - bottom - gap) / 2

    ax2 = fig.add_axes([0.63, bottom + ph + gap, 0.31, ph])
    b1 = sk.nlargest(6, "wins")
    H.top_hbar(ax2, b1["player"], b1["wins"].to_numpy(), value_fmt=T.num,
               colors=H.class_colors(b1["class_name"]),
               label_colors=H.class_text_colors(b1["class_name"]),
               title="Longest win streak")

    ax3 = fig.add_axes([0.63, bottom, 0.31, ph])
    b2 = sk.nlargest(6, "losses")
    H.top_hbar(ax3, b2["player"], b2["losses"].to_numpy(), value_fmt=T.num,
               colors=H.class_colors(b2["class_name"]),
               label_colors=H.class_text_colors(b2["class_name"]),
               title="Longest losing streak")
    return fig


def flag_efficiency(ctx: Ctx):
    """Conversion rate on the flag, and how much output goes to the objective."""
    tot = ctx.totals
    q = tot[tot["attemptsOnFlag_sum"] >= 25].copy()
    q["cap_rate"] = q["flagCaptures_sum"] / q["attemptsOnFlag_sum"]
    q["hold"] = q["flagCarryTime_sum"] / q["attemptsOnFlag_sum"]

    obj = tot[tot["games"] >= ctx.min_games].copy()
    obj["dmg_obj"] = obj["damageOnEFC_sum"] / obj["damageDone_sum"].replace(0, np.nan)
    obj["heal_obj"] = obj["healsOnFC_sum"] / obj["healingDone_sum"].replace(0, np.nan)
    overall_dmg = ctx.wsg["damageOnEFC"].sum() / ctx.wsg["damageDone"].sum()
    overall_cap = ctx.wsg["flagCaptures"].sum() / ctx.wsg["attemptsOnFlag"].sum()

    fig = plt.figure(figsize=(14, 6.8))
    top = T.figure_title(
        fig, "Flag efficiency and objective focus",
        "How often a flag pickup becomes a capture, and how much of a character's "
        "output goes to the flag carriers")
    bottom = T.footnote(fig, ctx.source_note(
        f"Left: characters with 25+ pickups ({len(q)}); dot size scales with pickups. "
        f"Across everyone {overall_cap*100:.0f} % of pickups become a capture and "
        f"{overall_dmg*100:.0f} % of damage lands on the enemy carrier (grey line). "
        f"Right-hand boards need {ctx.min_games}+ matches."))
    xb = T.xband(fig)
    h = top - bottom - xb

    ax = fig.add_axes([0.055, bottom + xb, 0.34, h])
    ax.scatter(q["hold"], q["cap_rate"], s=22 + q["attemptsOnFlag_sum"] * 0.7,
               color=H.class_colors(q["class_name"]), alpha=0.85,
               edgecolors=T.SURFACE, linewidths=1.4, zorder=3)
    ax.axhline(overall_cap, color=T.AXIS, linewidth=1.0)
    T.clean_axes(ax, xgrid=True)
    H.percent_axis(ax)
    ax.set_xlabel("seconds carried per pickup")
    ax.set_ylabel("pickups that become a capture")
    ax.set_title("Conversion on the flag", fontsize=10.5, pad=8)
    for _, r in q.nlargest(3, "cap_rate").iterrows():
        ax.annotate(r["player"], xy=(r["hold"], r["cap_rate"]), xytext=(7, 5),
                    textcoords="offset points", fontsize=8.5,
                    color=T.INK_SECONDARY, zorder=4)

    ax2 = fig.add_axes([0.475, bottom + xb, 0.20, h])
    d1 = obj.nlargest(10, "dmg_obj")
    H.top_hbar(ax2, d1["player"], (d1["dmg_obj"] * 100).to_numpy(),
               colors=H.class_colors(d1["class_name"]),
               label_colors=H.class_text_colors(d1["class_name"]),
               value_fmt=lambda v: f"{v:.0f} %",
               title="Share of damage on enemy carrier")

    ax3 = fig.add_axes([0.775, bottom + xb, 0.20, h])
    d2 = obj.nlargest(10, "heal_obj")
    H.top_hbar(ax3, d2["player"], (d2["heal_obj"] * 100).to_numpy(),
               colors=H.class_colors(d2["class_name"]),
               label_colors=H.class_text_colors(d2["class_name"]),
               value_fmt=lambda v: f"{v:.0f} %",
               title="Share of healing on own carrier")
    return fig


def first_match(ctx: Ctx):
    """Does losing your debut predict walking away?"""
    dec = ctx.wsg[~ctx.wsg["draw"]].sort_values("at")
    debut = dec.groupby("playerGuid").head(1).set_index("playerGuid")["win"]
    career = dec.groupby("playerGuid").size().rename("career")
    f = pd.DataFrame({"won_debut": debut}).join(career)

    ks = np.arange(1, 21)
    curves = {}
    for won, lab in [(1, "won their debut"), (0, "lost their debut")]:
        c = f.loc[f["won_debut"] == won, "career"]
        curves[lab] = [(c >= k).mean() for k in ks], len(c)

    one_done = f.groupby("won_debut")["career"].apply(lambda s: (s == 1).mean())

    fig = plt.figure(figsize=(12.5, 6.2))
    top = T.figure_title(
        fig, "The first match and what follows",
        "Share of new characters still playing after N matches, split by whether they "
        "won or lost their very first one")
    bottom = T.footnote(fig, ctx.source_note(
        f"{len(f)} characters whose first decided match falls inside the window. "
        "Characters that debut near the end of the period have had less time to play "
        "again, which flattens both curves equally. Association, not proof that the "
        "loss caused the exit."))
    xb = T.xband(fig)
    h = top - bottom - xb
    ax = fig.add_axes([0.065, bottom + xb, 0.50, h])

    for (lab, (vals, n)), color in zip(curves.items(), T.CATEGORICAL):
        ax.plot(ks, vals, color=color, marker="o", markersize=4,
                markerfacecolor=color, markeredgecolor=T.SURFACE,
                markeredgewidth=1.2, label=f"{lab} (n = {n})")
    T.clean_axes(ax)
    H.percent_axis(ax)
    ax.set_xlabel("matches played")
    ax.set_ylabel("share still playing")
    ax.set_xlim(1, ks[-1])
    ax.set_ylim(0, 1)
    ax.legend(loc="upper right")
    ax.set_title("Retention curve", fontsize=10.5, pad=8)

    ax2 = fig.add_axes([0.70, bottom + xb, 0.25, h])
    labels = ["lost debut", "won debut"]
    vals = [one_done.get(0, np.nan) * 100, one_done.get(1, np.nan) * 100]
    H.top_hbar(ax2, labels, vals, value_fmt=lambda v: f"{v:.0f} %", bar_frac=0.42,
               highlight={0}, title="Never played again")
    ax2.set_xlabel("share of debut cohort")
    return fig


CHARTS = [
    ("24_contested_record", contested_record),
    ("36_record_book", record_book),
    ("37_rivalries", rivalries),
    ("38_flag_efficiency", flag_efficiency),
    ("39_first_match", first_match),
]
