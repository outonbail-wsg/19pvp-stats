"""Sports-page forms the deck was missing: a standings table, a form board,
a race over time, and a board per class.

The rest of the deck is almost entirely rows of horizontal bars. These four
exist as much for their shape as for their numbers - a table, a strip, a set of
lines and a grid of small boards read differently at a glance.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from .. import theme as T
from ..context import Ctx
from ..data import CLASS_ORDER
from .. import rating
from . import helpers as H

TABLE_ROWS = 20          # standings rows that fit without shrinking the type
FORM_PLAYERS = 14
FORM_MATCHES = 25

WIN_COLOR = "#1baf7a"
LOSS_COLOR = "#e34948"


def _qualified(ctx: Ctx) -> pd.DataFrame:
    q = ctx.qualified.copy()
    dec = ctx.wsg[~ctx.wsg["draw"]]
    q["elo"] = rating.elo_ratings(dec)
    runs = rating.streaks(dec)
    return q.join(runs, how="left")


def power_ranking(ctx: Ctx):
    """A standings table: rank, character, class, record, rating.

    Drawn as text rather than bars - a league table is read row by row, and a
    bar chart of Elo would waste the space that the record belongs in.
    """
    q = _qualified(ctx).sort_values("elo", ascending=False).head(TABLE_ROWS)

    fig = plt.figure(figsize=(11.5, 9.6))
    top = T.figure_title(
        fig, "WSG power ranking",
        f"Top {TABLE_ROWS} by opponent-adjusted rating, characters with at least "
        f"{ctx.games_phrase()}")
    bottom = T.footnote(fig, ctx.source_note(
        f"Every character starts at {rating.ELO_START:.0f}. After each match both sides "
        "move by the same amount, more when the result was unexpected. Unlike a raw win rate this "
        "accounts for who was on the other side, so a record built against weak "
        "opposition is worth less. Bots are unrated and absent, so a thin lobby counts "
        "the same as a full one."))

    cols = [(0.045, "left", "#"), (0.10, "left", "Character"), (0.34, "left", "Class"),
            (0.55, "right", "Rating"), (0.68, "right", "W–L"),
            (0.80, "right", "Win rate"), (0.95, "right", "Run")]
    y = top - 0.035
    for x, ha, label in cols:
        fig.text(x, y, label, fontsize=10, fontweight="semibold",
                 color=T.INK_SECONDARY, ha=ha, va="center")
    fig.add_artist(plt.Line2D([0.045, 0.95], [y - 0.018, y - 0.018],
                              color=T.AXIS, linewidth=1))

    step = (y - 0.02 - bottom) / len(q)
    for i, (_, r) in enumerate(q.iterrows()):
        ry = y - 0.038 - i * step
        colour = H.class_text_colors([r["class_name"]])[0]
        wins, losses = int(r["wins"]), int(r["games_decided"] - r["wins"])
        run = int(r["current"]) if pd.notna(r.get("current")) else 0
        run_txt = f"{run}W" if run > 0 else (f"{abs(run)}L" if run < 0 else "–")
        cells = [f"{i + 1}", r["player"], r["class_name"] or "unknown",
                 f"{r['elo']:.0f}", f"{wins}–{losses}",
                 f"{r['winrate'] * 100:.0f} %", run_txt]
        for (x, ha, _), text in zip(cols, cells):
            is_name = text == r["player"]
            fig.text(x, ry, text, fontsize=10.5 if is_name else 10,
                     fontweight="semibold" if is_name else "normal",
                     color=colour if is_name else T.INK_SECONDARY, ha=ha, va="center")
        if i % 2 == 0:
            fig.patches.append(plt.Rectangle(
                (0.035, ry - step * 0.42), 0.925, step * 0.84,
                transform=fig.transFigure, facecolor=T.PAGE, zorder=-1, linewidth=0))
    return fig


def class_boards(ctx: Ctx):
    """Top of each class by rating - a board every player can find themselves on."""
    q = _qualified(ctx).dropna(subset=["class_name"])
    present = [c for c in CLASS_ORDER if (q["class_name"] == c).sum() >= 3]

    fig = plt.figure(figsize=(13.5, 8.6))
    top = T.figure_title(
        fig, "Highest power rating by class",
        f"Top characters per class by power rating, at least {ctx.games_phrase()}")
    bottom = T.footnote(fig, ctx.source_note(
        f"Power rating is an Elo: everyone starts at {rating.ELO_START:.0f} and after each "
        "match the winning side takes points from the losing side, more when it was the "
        "lower-rated one. Each side is rated by the mean of its recorded players. Classes "
        "with fewer than three qualified characters are left out."))
    axes = H.grid_axes(fig, 3, 3, left=0.075, right=0.975, top=top,
                       bottom=bottom, wspace=0.75, hspace=0.55)

    for i, cls in enumerate(present[:9]):
        ax = axes[i // 3][i % 3]
        sub = q[q["class_name"] == cls].nlargest(5, "elo")
        H.top_hbar(ax, sub["player"], sub["elo"].to_numpy() - 1400,
                   colors=H.class_colors(sub["class_name"]),
                   label_colors=H.class_text_colors(sub["class_name"]),
                   value_fmt=lambda v: f"{v + 1400:.0f}", title=cls)
    for j in range(len(present), 9):
        axes[j // 3][j % 3].axis("off")
    return fig


CHARTS = [
    ("40_power_ranking", power_ranking),
    ("41_class_boards", class_boards),
]
