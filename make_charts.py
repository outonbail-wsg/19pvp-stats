"""Render every WSG chart to PNG.

    python make_charts.py                 # everything into output/
    python make_charts.py --only 03 15    # only selected charts
    python make_charts.py --tz Europe/Berlin
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from wsgviz import context, data, theme  # noqa: E402
from wsgviz.plots import (  # noqa: E402
    arena, bracket, classes, control, leaderboards, match, objective, overview,
    realgames, roles, standings, stories, winfactors,
)

# Ordered to match the chart numbering, so the run log reads in sequence.
MODULES = [overview, bracket, classes, objective, stories, control, leaderboards,
           roles, match, realgames, winfactors, standings, arena]

ROOT = Path(__file__).resolve().parent

# Charts that only mean something across every lobby: they are about how much of
# a match was human, or they compare contested against thin directly. Filtering
# them to contested lobbies would answer a question nobody asked.
ALL_LOBBIES_ONLY = {
    "05_activity_per_hour",     # one panel is the share of contested lobbies
    "06_activity_heatmap",      # real players per match, by definition high here
    "28_humans_vs_bots",        # entirely about the human/bot split
    "29_realgames_overview",    # already the contested slice
    "30_realgames_team_compare",
    "31_realgames_length",      # compares full lobbies against the rest
    "32_contested_record",      # needs both sides of the comparison
}


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Render the WSG visualisations")
    p.add_argument("--csv", type=Path, default=None,
                   help="raw export; default: newest file in Data/")
    p.add_argument("--outdir", type=Path, default=ROOT / "output")
    p.add_argument("--tz", default="UTC",
                   help="time zone for day/hour axes (default UTC)")
    p.add_argument("--min-games", type=int, default=10,
                   help="minimum matches for average-based leaderboards")
    p.add_argument("--only", nargs="*", default=None,
                   help="only charts whose file name starts with one of these prefixes")
    p.add_argument("--lobby", choices=["all", "contested"], default="all",
                   help="restrict every chart to contested lobbies")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    csv_path = args.csv or data.default_csv(ROOT / "Data")
    args.outdir.mkdir(parents=True, exist_ok=True)

    theme.apply_theme()
    ctx = context.build(csv_path, args.outdir, tz=args.tz, min_games=args.min_games,
                        lobby=args.lobby)

    print(f"Source : {csv_path.name}")
    print(f"Period : {ctx.period_label} ({ctx.tz})")
    print(f"Scope  : {len(ctx.matches)} WSG matches, "
          f"{ctx.wsg['playerGuid'].nunique()} characters, "
          f"{len(ctx.arena)} arena records")
    print(f"Lobby  : {args.lobby}")
    print(f"Output : {args.outdir}\n")

    failures = 0
    for module in MODULES:
        for name, func in module.CHARTS:
            if args.only and not any(name.startswith(p) for p in args.only):
                continue
            if args.lobby == "contested" and name in ALL_LOBBIES_ONLY:
                continue
            path = args.outdir / f"{name}.png"
            try:
                fig = func(ctx)
                fig.savefig(path)
                plt.close(fig)
                print(f"  ok   {path.name}")
            except Exception:
                failures += 1
                print(f"  FAIL {path.name}")
                traceback.print_exc()
                plt.close("all")

    print(f"\nDone. {failures} error(s)." if failures else "\nDone.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
