"""Small hand-drawn vector pictograms for stat categories.

These are simple original shapes (sword, heal cross, flag, shield, bolt, star),
not game assets - drawn with matplotlib primitives so they scale cleanly and
carry no copyright. Each stat column maps to one icon; a leaderboard or class
panel puts the icon just left of its title.
"""

from __future__ import annotations

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

from .. import theme as T

# Which pictogram represents each stat column.
STAT_ICON = {
    "damageDone": "sword", "damageOnEFC": "sword", "damageTaken": "shield",
    "killingBlows": "skull", "honorableKills": "swords",
    "healingDone": "heal", "healsOnFC": "heal", "absorbsDone": "shield",
    "flagCaptures": "flag", "flagReturns": "flag", "flagCarryTime": "flag",
    "attemptsOnFlag": "flag",
    "successfulInterrupts": "bolt", "fakeCastInterrupts": "bolt",
    "dispelsOffensive": "spark", "dispelsDefensive": "spark",
    "hardCCCount": "bolt", "hardCCDuration": "bolt",
    "softCCCount": "bolt", "softCCDuration": "bolt",
    "bonusHonor": "star",
}


def _sword(ax, c):
    # upright blade with a pointed tip, cross guard, grip and pommel
    ax.add_patch(mpatches.Polygon([[0.5, 0.90], [0.57, 0.72], [0.57, 0.40],
                                   [0.43, 0.40], [0.43, 0.72]], closed=True, color=c))
    ax.plot([0.28, 0.72], [0.38, 0.38], color=c, lw=2.0, solid_capstyle="round")
    ax.plot([0.5, 0.5], [0.38, 0.16], color=c, lw=2.0, solid_capstyle="round")
    ax.add_patch(mpatches.Circle((0.5, 0.13), 0.04, color=c))


def _swords(ax, c):
    # two crossed blades
    for x0, x1 in [(0.24, 0.80), (0.80, 0.24)]:
        ax.plot([x0, x1], [0.20, 0.82], color=c, lw=1.7, solid_capstyle="round")
    ax.plot([0.18, 0.34], [0.32, 0.16], color=c, lw=1.7, solid_capstyle="round")
    ax.plot([0.66, 0.82], [0.16, 0.32], color=c, lw=1.7, solid_capstyle="round")


def _heal(ax, c):
    ax.add_patch(mpatches.Rectangle((0.42, 0.18), 0.16, 0.64, color=c))
    ax.add_patch(mpatches.Rectangle((0.18, 0.42), 0.64, 0.16, color=c))


def _flag(ax, c):
    ax.plot([0.30, 0.30], [0.14, 0.86], color=c, lw=1.8, solid_capstyle="round")
    ax.add_patch(mpatches.Polygon([[0.30, 0.86], [0.80, 0.72], [0.30, 0.58]],
                                  closed=True, color=c))


def _shield(ax, c):
    pts = [[0.5, 0.88], [0.82, 0.74], [0.82, 0.42],
           [0.5, 0.14], [0.18, 0.42], [0.18, 0.74]]
    ax.add_patch(mpatches.Polygon(pts, closed=True, fill=False, edgecolor=c, lw=1.8,
                                  joinstyle="round"))


def _bolt(ax, c):
    pts = [[0.56, 0.86], [0.30, 0.50], [0.48, 0.50],
           [0.42, 0.14], [0.70, 0.52], [0.50, 0.52]]
    ax.add_patch(mpatches.Polygon(pts, closed=True, color=c))


def _spark(ax, c):
    ax.plot([0.5, 0.5], [0.16, 0.84], color=c, lw=1.7, solid_capstyle="round")
    ax.plot([0.16, 0.84], [0.5, 0.5], color=c, lw=1.7, solid_capstyle="round")
    ax.plot([0.28, 0.72], [0.28, 0.72], color=c, lw=1.4, solid_capstyle="round")
    ax.plot([0.28, 0.72], [0.72, 0.28], color=c, lw=1.4, solid_capstyle="round")


def _star(ax, c):
    ang = np.deg2rad(np.arange(90, 90 + 360, 72))
    outer = np.c_[0.5 + 0.38 * np.cos(ang), 0.5 + 0.38 * np.sin(ang)]
    ang2 = ang + np.deg2rad(36)
    inner = np.c_[0.5 + 0.16 * np.cos(ang2), 0.5 + 0.16 * np.sin(ang2)]
    pts = np.empty((10, 2))
    pts[0::2], pts[1::2] = outer, inner
    ax.add_patch(mpatches.Polygon(pts, closed=True, color=c))


def _skull(ax, c):
    ax.add_patch(mpatches.Circle((0.5, 0.56), 0.28, fill=False, edgecolor=c, lw=1.7))
    ax.add_patch(mpatches.Circle((0.40, 0.58), 0.055, color=c))
    ax.add_patch(mpatches.Circle((0.60, 0.58), 0.055, color=c))
    ax.plot([0.42, 0.42], [0.28, 0.40], color=c, lw=1.5, solid_capstyle="round")
    ax.plot([0.5, 0.5], [0.27, 0.40], color=c, lw=1.5, solid_capstyle="round")
    ax.plot([0.58, 0.58], [0.28, 0.40], color=c, lw=1.5, solid_capstyle="round")


_DRAW = {"sword": _sword, "swords": _swords, "heal": _heal, "flag": _flag,
         "shield": _shield, "bolt": _bolt, "spark": _spark, "star": _star,
         "skull": _skull}


def draw(fig, x_frac, y_frac, kind, *, size_in=0.15, color=None):
    """Draw one pictogram, centred on (x_frac, y_frac) in figure coordinates."""
    if kind not in _DRAW:
        return
    W, H = fig.get_size_inches()
    w, h = size_in / W, size_in / H
    ax = fig.add_axes([x_frac - w / 2, y_frac - h / 2, w, h], zorder=6)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")
    _DRAW[kind](ax, color or T.INK_SECONDARY)


def panel_title(fig, ax, text, col, *, pad=8):
    """Set a panel title with the stat's pictogram just left of the text."""
    kind = STAT_ICON.get(col)
    indent = 0.11 if kind else 0.0
    ax.set_title(text, fontsize=10.5, pad=pad, loc="left", x=indent)
    if kind:
        pos = ax.get_position()
        # icon sits in the indent, vertically aligned with the title baseline
        y = pos.y1 + (pad + 5) / (fig.get_size_inches()[1] * 72)
        draw(fig, pos.x0 + 0.007, y, kind, size_in=0.155)
