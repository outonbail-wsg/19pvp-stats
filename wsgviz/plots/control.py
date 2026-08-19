"""Leaderboards for the statistics that take a fight away from the other side.

Interrupts, fake-cast baits and crowd control never show up in a damage meter,
so a character who does nothing but lock casters down looks idle on every other
board. These give that work its own place, on the same three-way shape as the
flag boards: total, per match, per minute.

Crowd control is measured by duration rather than by count. Ten one-second roots
and one ten-second sap are the same number of casts and nothing like the same
effect on a round.
"""

from __future__ import annotations

from ..context import Ctx
from .objective import TOP_N, _board


def interrupt_leaders(ctx: Ctx):
    """Who stops casts, and who makes the other side stop their own."""
    return _board(
        ctx, ["successfulInterrupts", "fakeCastInterrupts"],
        "WSG interrupt leaders",
        f"Top {TOP_N} for successful interrupts and for fake casts, three ways: in "
        "total, per match and per minute played",
        f"Totals cover every character; the rate boards need at least {ctx.min_games} "
        "matches. A fake cast is a cast started to draw an interrupt and cancelled "
        "before it lands, so the two boards are opposite sides of the same duel and "
        "rarely hold the same names.")


def cc_leaders(ctx: Ctx):
    """Who keeps the other side out of the fight, and for how long."""
    return _board(
        ctx, ["hardCCDuration", "softCCDuration"],
        "WSG crowd control leaders",
        f"Top {TOP_N} for hard and soft crowd control, measured as seconds applied, "
        "three ways: in total, per match and per minute played",
        f"Totals cover every character; the rate boards need at least {ctx.min_games} "
        "matches. Hard CC takes a target out of the round entirely - stun, fear, "
        "polymorph; soft CC only slows or roots. Duration rather than count, because "
        "ten brief roots are not one long sap.")


CHARTS = [
    ("17_interrupt_leaders", interrupt_leaders),
    ("18_cc_leaders", cc_leaders),
]
