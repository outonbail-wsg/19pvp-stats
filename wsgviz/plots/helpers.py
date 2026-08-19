"""Reusable chart building blocks.

These keep the rules from theme.py in one place: nominal categories get one
colour, never a value ramp; values sit outside the mark when they would
otherwise be clipped; axes stay recessive.
"""

from __future__ import annotations

import numpy as np

from .. import theme as T
from ..data import CLASS_COLORS


def class_colors(class_series, fallback=None):
    """Per-row WoW class colour; unknown class falls back to a neutral grey.

    No legend accompanies these: the class colours are a WoW-wide convention the
    audience reads instantly, and on class charts the class is named on the axis
    anyway.
    """
    fb = fallback or T.DEEMPHASIS
    return [CLASS_COLORS.get(c, fb) for c in class_series]


def class_text_colors(class_series, fallback=None):
    """Class colours darkened until they are readable as text.

    Fill colours are chosen to work as large blocks; several (rogue yellow, mage
    cyan, hunter green) are far too light for 9pt type on a near-white surface.
    Each is darkened along its own hue until it clears the 4.5:1 contrast bar, so
    the name still reads as its class without becoming unreadable.
    """
    fb = fallback or T.INK_SECONDARY
    return [T.readable_on_surface(CLASS_COLORS[c]) if c in CLASS_COLORS else fb
            for c in class_series]


def top_hbar(ax, labels, values, *, color=None, value_fmt=None, title=None,
             xlabel=None, highlight=None, pad_frac=0.28, bar_frac=0.62, colors=None,
             label_colors=None):
    """Top-N bars, largest on top, values at the bar end.

    Nominal categories (player names) get exactly one colour for every bar.
    `highlight` greys out everything except the given indices (emphasis form).
    `colors` gives an explicit per-bar colour list (e.g. class colours) and
    overrides both `color` and `highlight`. `label_colors` tints the category
    labels to match - pass `class_text_colors(...)`, never the raw fills.
    """
    labels = list(labels)
    values = np.asarray(values, dtype=float)
    n = len(labels)
    y = np.arange(n)[::-1]                      # largest on top
    base = color or T.PRIMARY
    if colors is not None:
        colors = list(colors)
    elif highlight is not None:
        colors = [base if i in highlight else T.DEEMPHASIS for i in range(n)]
    else:
        colors = [base] * n

    ax.barh(y, values, height=bar_frac, color=colors, linewidth=0)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9, color=T.INK_SECONDARY)
    if label_colors is not None:
        for tick, c in zip(ax.get_yticklabels(), label_colors):
            tick.set_color(c)
    T.hbar_axes(ax)

    vmax = values.max() if n and values.max() > 0 else 1.0
    ax.set_xlim(0, vmax * (1 + pad_frac))
    fmt = value_fmt or T.compact
    for yi, v, c in zip(y, values, colors):
        ax.text(v + vmax * 0.02, yi, fmt(v), va="center", ha="left",
                fontsize=8.5, color=T.INK_SECONDARY)
    ax.set_xticks([])
    ax.grid(False)
    if title:
        ax.set_title(title, fontsize=10.5, pad=8)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=8.5)
    return ax


def stat_tile(fig, rect, value, label, sub=None, color=None):
    """Headline number tile. Replaces the one-bar bar chart."""
    ax = fig.add_axes(rect)
    ax.axis("off")
    ax.text(0, 0.72, value, fontsize=27, fontweight="semibold", va="center",
            ha="left", color=color or T.INK)
    ax.text(0, 0.30, label, fontsize=10, va="center", ha="left", color=T.INK_SECONDARY)
    if sub:
        ax.text(0, 0.06, sub, fontsize=8.5, va="center", ha="left", color=T.INK_MUTED)
    return ax


def diverging_hbar(ax, labels, values, *, pos_label, neg_label, value_fmt=None,
                   pos_color=None, neg_color=None):
    """Deviation around a zero line. Two poles that read as opposites."""
    labels = list(labels)
    values = np.asarray(values, dtype=float)
    y = np.arange(len(labels))[::-1]
    pos_color = pos_color or T.POS
    neg_color = neg_color or T.NEG
    colors = [pos_color if v >= 0 else neg_color for v in values]

    ax.barh(y, values, height=0.62, color=colors, linewidth=0)
    ax.axvline(0, color=T.AXIS, linewidth=1.0)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9, color=T.INK_SECONDARY)
    T.hbar_axes(ax)
    ax.spines["left"].set_visible(False)

    span = np.abs(values).max() if len(values) else 1.0
    ax.set_xlim(-span * 1.35, span * 1.35)
    fmt = value_fmt or (lambda v: f"{v:+.0f}%")
    for yi, v in zip(y, values):
        off = span * 0.03
        ax.text(v + (off if v >= 0 else -off), yi, fmt(v), va="center",
                ha="left" if v >= 0 else "right", fontsize=8.5, color=T.INK_SECONDARY)
    ax.set_xticks([])
    ax.grid(False)

    # A legend rather than colour alone: both poles are named.
    ax.scatter([], [], marker="s", s=40, color=pos_color, label=pos_label)
    ax.scatter([], [], marker="s", s=40, color=neg_color, label=neg_label)
    return ax


def hist(ax, values, *, bins=30, color=None, median=True, mean=False,
         median_label="median"):
    """Distribution as a histogram with an optional median marker."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    ax.hist(values, bins=bins, color=color or T.PRIMARY, linewidth=0)
    T.clean_axes(ax)
    if median and len(values):
        med = float(np.median(values))
        ax.axvline(med, color=T.INK, linewidth=1.4)
        ax.annotate(f"{median_label} {T.compact(med)}", xy=(med, 1),
                    xycoords=("data", "axes fraction"), xytext=(6, -10),
                    textcoords="offset points", fontsize=9, color=T.INK,
                    ha="left", va="top")
    if mean and len(values):
        ax.axvline(float(np.mean(values)), color=T.INK_MUTED, linewidth=1.2)
    return ax


def label_last_point(ax, x, y, text, color, dx=6, dy=0):
    """Direct label at the end of a series instead of a number on every point."""
    ax.annotate(text, xy=(x, y), xytext=(dx, dy), textcoords="offset points",
                fontsize=9.5, color=color, va="center", ha="left",
                fontweight="semibold")


def grid_axes(fig, nrows, ncols, *, left=0.06, right=0.985, top=0.86,
              bottom=0.07, wspace=0.55, hspace=0.55):
    """Small-multiples grid that leaves room for the title block above."""
    gs = fig.add_gridspec(nrows, ncols, left=left, right=right, top=top,
                          bottom=bottom, wspace=wspace, hspace=hspace)
    return [[fig.add_subplot(gs[r, c]) for c in range(ncols)] for r in range(nrows)]


def percent_axis(ax, axis="y", decimals=0):
    import matplotlib.ticker as mticker
    f = mticker.FuncFormatter(lambda v, _p: T.num(v * 100, decimals) + " %")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(f)


def radar(ax, values, labels, *, color=None, ring_levels=(0.25, 0.5, 0.75, 1.0)):
    """Radar on axes normalised to 0..1. Only for profile comparison, never for
    absolute size - the enclosed area depends on the axis order."""
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    closed = np.concatenate([values, values[:1]])
    ang = np.concatenate([angles, angles[:1]])
    c = color or T.PRIMARY

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.plot(ang, closed, color=c, linewidth=1.8)
    ax.fill(ang, closed, color=c, alpha=0.18, linewidth=0)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=7.5, color=T.INK_SECONDARY)
    ax.set_yticks(list(ring_levels))
    ax.set_yticklabels([])
    ax.set_ylim(0, 1)
    ax.grid(color=T.GRID, linewidth=0.8, linestyle="-")
    ax.spines["polar"].set_color(T.GRID)
    ax.spines["polar"].set_linewidth(0.8)
    ax.set_facecolor(T.SURFACE)
    return ax
