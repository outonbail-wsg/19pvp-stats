"""Central design system for every chart.

Colours are taken unchanged from the validated reference palette (light surface).
Rules hard-wired here:

* categorical slots are assigned in fixed order, never cycled
* all-pairs forms (scatter) use at most the first three slots
* magnitude -> a single blue ramp, light to dark, never a rainbow
* polarity -> diverging blue <-> red with a neutral grey midpoint
* thin marks, hairline solid grid, never dashed axes
"""

from __future__ import annotations

import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

# --- Surfaces and ink -------------------------------------------------------
SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

# --- Categorical (fixed slot order) -----------------------------------------
CATEGORICAL = [
    "#2a78d6",  # 1 blue
    "#eb6834",  # 2 orange
    "#1baf7a",  # 3 aqua
    "#eda100",  # 4 yellow
    "#e87ba4",  # 5 magenta
    "#008300",  # 6 green
    "#4a3aa7",  # 7 violet
    "#e34948",  # 8 red
]
# Only these three are cleared for all-pairs forms (scatter, bubble).
CATEGORICAL_SCATTER = CATEGORICAL[:3]

PRIMARY = CATEGORICAL[0]
DEEMPHASIS = "#c9c8c2"  # grey for context marks in emphasis charts

# --- Sequential: one blue ramp ----------------------------------------------
BLUE_RAMP = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
    "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b",
]
SEQUENTIAL = LinearSegmentedColormap.from_list("wsg_blue", BLUE_RAMP)
# Ordinal ramps must not start lighter than step 250 on a light surface.
ORDINAL_RAMP = BLUE_RAMP[3:]

# --- Diverging: blue <-> red with a neutral midpoint ------------------------
DIVERGING = LinearSegmentedColormap.from_list(
    "wsg_div", ["#0d366b", "#2a78d6", "#9ec5f4", "#f0efec", "#f0a3a2", "#e34948", "#8f2020"]
)
POS = CATEGORICAL[0]   # blue -> "more when winning"
NEG = CATEGORICAL[7]   # red  -> "more when losing"
NEUTRAL = "#f0efec"

# --- Status (reserved, never a series colour) -------------------------------
STATUS = {"good": "#0ca30c", "warning": "#fab219", "serious": "#ec835a", "critical": "#d03b3b"}


def _relative_luminance(rgb) -> float:
    """WCAG relative luminance from 0..1 sRGB components."""
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(hex_a: str, hex_b: str = SURFACE) -> float:
    import matplotlib.colors as mcolors
    la = _relative_luminance(mcolors.to_rgb(hex_a))
    lb = _relative_luminance(mcolors.to_rgb(hex_b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def readable_on_surface(hex_color: str, target: float = 4.5,
                        surface: str = SURFACE) -> str:
    """Darken a fill colour along its own hue until it is readable as text.

    Returns the colour unchanged when it already clears `target`.
    """
    import matplotlib.colors as mcolors
    rgb = mcolors.to_rgb(hex_color)
    factor = 1.0
    while factor > 0.05:
        candidate = tuple(c * factor for c in rgb)
        if contrast_ratio(mcolors.to_hex(candidate), surface) >= target:
            return mcolors.to_hex(candidate)
        factor -= 0.04
    return INK


def apply_theme() -> None:
    """Set the rcParams. Call once at start-up."""
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "figure.dpi": 110,
        "savefig.dpi": 200,
        "savefig.facecolor": SURFACE,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.35,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": AXIS,
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "axes.labelcolor": INK_SECONDARY,
        "axes.labelsize": 10,
        "axes.titlesize": 12,
        "axes.titlecolor": INK,
        "axes.titleweight": "semibold",
        "axes.titlelocation": "left",
        "axes.titlepad": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.prop_cycle": mpl.cycler(color=CATEGORICAL),
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "grid.linestyle": "-",      # never dashed
        "grid.alpha": 1.0,
        "xtick.color": INK_MUTED,
        "ytick.color": INK_MUTED,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 3,
        "ytick.major.size": 0,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "legend.labelcolor": INK_SECONDARY,
        "lines.linewidth": 2.0,
        "lines.markersize": 5,
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial", "sans-serif"],
        "font.size": 10,
        "text.color": INK,
        "figure.autolayout": False,
    })


# --- Number formatting ------------------------------------------------------
def num(value: float, decimals: int = 0) -> str:
    """1234567.8 -> '1,234,567.8'"""
    return f"{value:,.{decimals}f}"


def compact(value: float) -> str:
    """Compact axis and bar labels: 12300 -> '12k'."""
    a = abs(value)
    if a >= 1_000_000:
        return num(value / 1_000_000, 1) + "M"
    if a >= 10_000:
        return num(value / 1000, 0) + "k"
    if a >= 1000:
        return num(value / 1000, 1) + "k"
    if a >= 10 or value == int(value):
        return num(value, 0)
    return num(value, 1)


def compact_formatter():
    return mpl.ticker.FuncFormatter(lambda v, _pos: compact(v))


# --- Layout blocks ----------------------------------------------------------
# All spacing in inches so the title block and footnote sit identically at any
# figure size; fractions would drift apart on tall figures.
_MARGIN_IN = 0.16
_TITLE_TOP_IN = 0.30
_SUBTITLE_GAP_IN = 0.30
_CONTENT_GAP_IN = 0.42
_FOOT_BOTTOM_IN = 0.10
_FOOT_GAP_IN = 0.30
_LINE_IN = 0.17           # footnote line height at 8.5pt


def _wrap(text: str, fig_width_in: float, chars_per_inch: float) -> list[str]:
    """Wrap each paragraph to the figure width. Without this a long footnote
    widens the saved figure and squashes the axes."""
    import textwrap
    width = max(40, int((fig_width_in - 2 * _MARGIN_IN) * chars_per_inch))
    lines: list[str] = []
    for para in text.split("\n"):
        lines.extend(textwrap.wrap(para, width=width) or [""])
    return lines


def figure_title(fig, title: str, subtitle: str | None = None) -> float:
    """Title block, top left. Returns the top of the content area as a figure
    fraction."""
    h = fig.get_figheight()
    x = _MARGIN_IN / fig.get_figwidth()
    y = 1 - _TITLE_TOP_IN / h
    fig.text(x, y, title, ha="left", va="top", fontsize=17,
             fontweight="semibold", color=INK)
    y -= _SUBTITLE_GAP_IN / h
    if subtitle:
        lines = _wrap(subtitle, fig.get_figwidth(), 10.5)
        fig.text(x, y, "\n".join(lines), ha="left", va="top", fontsize=10.5,
                 color=INK_SECONDARY, linespacing=1.4)
        y -= (len(lines) - 1) * 0.20 / h
    return y - _CONTENT_GAP_IN / h


def xband(fig, label: bool = True) -> float:
    """Height needed by tick labels and the axis title below a plot, as a figure
    fraction. Without this the x axis runs into the footnote."""
    return (0.50 if label else 0.28) / fig.get_figheight()


def footnote(fig, text: str) -> float:
    """Source and method note, bottom left. Returns the bottom of the content
    area as a figure fraction."""
    h = fig.get_figheight()
    lines = _wrap(text, fig.get_figwidth(), 14.0)
    y = _FOOT_BOTTOM_IN / h
    fig.text(_MARGIN_IN / fig.get_figwidth(), y, "\n".join(lines), ha="left",
             va="bottom", fontsize=8.5, color=INK_MUTED, linespacing=1.45)
    return y + (len(lines) * _LINE_IN + _FOOT_GAP_IN) / h


def clean_axes(ax, xgrid: bool = False, ygrid: bool = True) -> None:
    ax.set_axisbelow(True)
    ax.grid(axis="y", visible=ygrid)
    ax.grid(axis="x", visible=xgrid)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)


def hbar_axes(ax) -> None:
    """Horizontal bars: the grid runs along x, the category axis stays bare."""
    ax.set_axisbelow(True)
    ax.grid(axis="x", visible=True)
    ax.grid(axis="y", visible=False)
    for side in ("top", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color(AXIS)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=0)
