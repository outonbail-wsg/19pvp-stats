"""Individual play style: how a character actually performs, not what it is.

Class is charted in classes.py. These two charts sit one level below that: where
each character lands on the damage/healing plane, and the full per-minute profile
of the most active ones. The rule-based role labels are only a fallback name for
the few characters the export carries no class for.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .. import theme as T
from ..context import Ctx
from ..data import fmt_duration
from . import helpers as H

# Fallback role labels for the few characters with no class in the export.
# Absolute thresholds, chosen from the observed distributions.
HEAL_SHARE_HEALER = 0.55      # healing as a share of healing + damage
CARRY_SECONDS_PER_MATCH = 150.0
RETURNS_PER_MATCH = 0.50

# Radar dimensions: column in `totals` and a SHORT axis label. Long labels on
# eight spokes collide with the neighbouring radar; the key below spells them out.
PROFILE_DIMS = [
    ("damageDone_pm", "DMG"),
    ("damageOnEFC_pm", "on EFC"),
    ("killingBlows_pm", "KB"),
    ("flagCarryTime_pm", "Carry"),
    ("flagReturns_pm", "Returns"),
    ("healsOnFC_pm", "Heal FC"),
    ("healingDone_pm", "HPS"),
    ("absorbsDone_pm", "Absorb"),
]

PROFILE_KEY = ("Axes (all per minute): DMG = damage done · on EFC = damage on the enemy "
               "flag carrier · KB = killing blows · Carry = flag carry time · Returns = "
               "flag returns · Heal FC = healing on own flag carrier · HPS = healing done "
               "· Absorb = absorbs done.")


def _profile(ctx: Ctx) -> pd.DataFrame:
    """Qualified characters plus the derived play-style measures."""
    q = ctx.qualified.copy()
    denom = (q["healingDone_pm"] + q["damageDone_pm"]).replace(0, np.nan)
    q["heal_share"] = q["healingDone_pm"] / denom
    q["carry_per_match"] = q["flagCarryTime_sum"] / q["games"]
    q["returns_per_match"] = q["flagReturns_sum"] / q["games"]

    def classify(row) -> str:
        if row["heal_share"] >= HEAL_SHARE_HEALER:
            return "Healer"
        if row["carry_per_match"] >= CARRY_SECONDS_PER_MATCH:
            return "Flag carrier"
        if row["returns_per_match"] >= RETURNS_PER_MATCH:
            return "Defender"
        return "Damage"

    q["archetype"] = q.apply(classify, axis=1)
    return q


def role_map(ctx: Ctx):
    """Damage against healing per minute, coloured by class."""
    q = _profile(ctx)

    fig = plt.figure(figsize=(12, 7.6))
    top = T.figure_title(
        fig, "WSG damage vs healing per minute",
        f"Each dot is one character with at least {ctx.min_games} matches, coloured by "
        "class; dot size scales with matches played")
    bottom = T.footnote(fig, ctx.source_note(
        "Both axes per minute played."))
    xb = T.xband(fig)
    ax = fig.add_axes([0.085, bottom + xb, 0.87, top - bottom - xb])

    ax.scatter(q["damageDone_pm"], q["healingDone_pm"],
               s=18 + q["games"] * 0.9, color=H.class_colors(q["class_name"]),
               alpha=0.85, linewidths=1.4, edgecolors=T.SURFACE, zorder=3)

    T.clean_axes(ax, xgrid=True)
    ax.set_xlabel("damage done per minute")
    ax.set_ylabel("healing done per minute")
    ax.xaxis.set_major_formatter(T.compact_formatter())
    ax.yaxis.set_major_formatter(T.compact_formatter())

    # Direct-label only the extremes, never every point.
    notable = pd.concat([q.nlargest(2, "damageDone_pm"), q.nlargest(2, "healingDone_pm")])
    for _, row in notable.drop_duplicates().iterrows():
        ax.annotate(row["player"], xy=(row["damageDone_pm"], row["healingDone_pm"]),
                    xytext=(8, 6), textcoords="offset points", fontsize=8.5,
                    color=T.INK_SECONDARY, zorder=4)
    return fig


def player_profiles(ctx: Ctx):
    """Radar profiles of the most active characters."""
    q = _profile(ctx)
    dims = [c for c, _ in PROFILE_DIMS if c in q.columns]
    labels = [lab for c, lab in PROFILE_DIMS if c in q.columns]
    # Percentile rank inside the qualified pool: the shape is a comparison, not
    # an absolute size.
    ranks = q[dims].rank(pct=True)

    top_players = q.nlargest(8, "games")
    fig = plt.figure(figsize=(13.5, 8.8))
    top = T.figure_title(
        fig, "WSG player profiles: eight most active characters",
        "Each axis is the character's percentile among all qualified characters – "
        "the outer ring is the highest value in the pool")
    bottom = T.footnote(fig, ctx.source_note(
        f"Percentile among {len(q)} characters with >={ctx.min_games} matches, all axes "
        "per minute. Area is meaningless - read each spoke on its own. " + PROFILE_KEY))

    # Each cell = a title strip on top and a square radar below it, with a wide
    # gutter so neighbouring axis labels never touch.
    cols, rows = 4, 2
    cell_w = (1 - 0.04) / cols
    cell_h = (top - bottom) / rows
    title_strip = 0.055          # figure-fraction reserved above each radar
    inset_x, inset_y = 0.030, 0.018
    for i, (_, row) in enumerate(top_players.iterrows()):
        r, c = divmod(i, cols)
        cell_left = 0.02 + c * cell_w
        cell_top = top - r * cell_h
        fig.text(cell_left + cell_w / 2, cell_top - 0.006,
                 f"{row['player']}", fontsize=10.5, fontweight="semibold",
                 ha="center", va="top", color=T.INK)
        cls = row["class_name"] if pd.notna(row.get("class_name")) else row["archetype"]
        fig.text(cell_left + cell_w / 2, cell_top - 0.030,
                 f"{int(row['games'])} matches · {row['winrate']*100:.0f} % WR · {cls}",
                 fontsize=8.3, ha="center", va="top", color=T.INK_SECONDARY)
        ax = fig.add_axes([cell_left + inset_x,
                           cell_top - cell_h + inset_y,
                           cell_w - 2 * inset_x,
                           cell_h - title_strip - 2 * inset_y],
                          projection="polar")
        color = H.class_colors([row.get("class_name")])[0]
        H.radar(ax, ranks.loc[row.name, dims].to_numpy(), labels, color=color)
    return fig


CHARTS = [
    ("31_role_map", role_map),
    ("32_player_profiles", player_profiles),
]
