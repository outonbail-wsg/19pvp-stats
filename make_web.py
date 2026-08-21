"""Build the shareable web page into `site/`.

    python make_web.py                # charts + data + page
    python make_web.py --skip-charts  # reuse the PNGs already in output/

The result is a folder that works three ways: opened locally by double-click,
served from GitHub Pages, or dropped into any static host. The data is inlined
into index.html, so the page needs no server and no fetch to show a player card.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from html import escape
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from wsgviz import context, data, descriptions, theme, webexport  # noqa: E402

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "web" / "template.html"
PLACEHOLDER = "__DATA__"
ANALYTICS_SLOT = "<!--ANALYTICS-->"


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Build the WSG stats web page")
    p.add_argument("--csv", type=Path, default=None)
    p.add_argument("--outdir", type=Path, default=ROOT / "site")
    p.add_argument("--charts", type=Path, default=ROOT / "output",
                   help="where the PNGs live (or are written to)")
    p.add_argument("--skip-charts", action="store_true",
                   help="do not re-render the PNGs, just reuse them")
    p.add_argument("--tz", default="UTC")
    p.add_argument("--min-games", type=int, default=10)
    p.add_argument("--analytics", default=os.environ.get("GOATCOUNTER_URL", ""),
                   help="GoatCounter endpoint, e.g. https://NAME.goatcounter.com/count; "
                        "taken from GOATCOUNTER_URL when not given. Empty means no script at all.")
    return p.parse_args(argv)


def analytics_tag(endpoint: str) -> str:
    """The visitor-counting script, or nothing at all when none is configured.

    The endpoint lives in an environment variable rather than in the template so
    it is never committed, and so a build without it produces a page that phones
    home to nobody.
    """
    endpoint = (endpoint or "").strip()
    if not endpoint:
        return ""
    if not endpoint.startswith("https://"):
        raise SystemExit(f"--analytics must be an https URL, got: {endpoint}")
    return (f'<script data-goatcounter="{escape(endpoint, quote=True)}" '
            f'async src="//gc.zgo.at/count.js"></script>')


def WINDOW_MIN_GAMES(base: int, window: str) -> int:
    """Match threshold for a window's charts, matching the page's own tiers.

    A bar meant for a fortnight empties a one-day board: nobody plays ten
    matches in an evening, so a leaderboard filtered that way would be blank.
    Yesterday runs unfiltered - over a single day the sample is the day.
    """
    return {"all": base, "week": max(1, round(base / 2)), "yesterday": 1}[window]


def main(argv=None) -> int:
    args = parse_args(argv)
    csv_path = args.csv or data.default_csv(ROOT / "Data")

    import make_charts

    # One set per lobby filter per window. The page switches between them by
    # folder, so the presets narrow the pictures the same way they narrow the
    # boards. A hand-picked range has no set and cannot get one - there is no
    # end of possible ranges to render - so the picker is offered only where it
    # changes something.
    sets = [(f"{lobby}-{win}" if win != "all" else lobby, lobby, win)
            for win in ("all", "week", "yesterday")
            for lobby in ("all", "contested")]
    site = args.outdir
    chart_dir = {sid: ("charts" if sid == "all" else f"charts-{sid}")
                 for sid, _, _ in sets}
    rendered = {}

    if not args.skip_charts:
        common = ["--csv", str(csv_path), "--tz", args.tz]
        for sid, lobby, win in sets:
            outdir = args.charts.parent / f"{args.charts.name}-{sid}"
            cmd = common + ["--outdir", str(outdir), "--lobby", lobby,
                            "--window", win,
                            "--min-games", str(WINDOW_MIN_GAMES(args.min_games, win))]
            # A narrow window may leave a chart with nothing to draw. That is
            # the data speaking, so it must not fail the build - but over the
            # whole period it would be a real fault, and there it still does.
            if win != "all":
                cmd.append("--allow-failures")
            rc = make_charts.main(cmd)
            if rc:
                print(f"charts failed for {sid}; aborting", file=sys.stderr)
                return rc

    for sid, lobby, win in sets:
        src = args.charts.parent / f"{args.charts.name}-{sid}"
        target = site / chart_dir[sid]
        target.mkdir(parents=True, exist_ok=True)
        found = []
        for png in sorted(src.glob("*.png")):
            shutil.copy2(png, target / png.name)
            found.append(png.name)
        rendered[sid] = found

    # The charts that compare contested against bot-filled lobbies exist only in
    # the all-lobby render - and they are exactly the ones a reader in contested
    # view most wants. Carry them across from the same window, so the pair still
    # covers the same days; their own footnotes say they cover every lobby.
    for sid, lobby, win in sets:
        if lobby != "contested":
            continue
        twin = "all" if win == "all" else f"all-{win}"
        for name in sorted(make_charts.ALL_LOBBIES_ONLY):
            src = site / chart_dir[twin] / f"{name}.png"
            if src.exists() and src.name not in rendered[sid]:
                shutil.copy2(src, site / chart_dir[sid] / src.name)
                rendered[sid].append(src.name)
        rendered[sid].sort()

    theme.apply_theme()
    ctx = context.build(csv_path, args.outdir, tz=args.tz, min_games=args.min_games)
    ctx_contested = context.build(csv_path, args.outdir, tz=args.tz,
                                  min_games=args.min_games, lobby="contested")

    names, contested_names = rendered["all"], rendered["contested"]

    # A chart with no gallery text still renders, but silently as a bare file
    # name - so say it out loud rather than letting the wording drift.
    missing = descriptions.check(n.rsplit(".", 1)[0] for n in names)
    if missing:
        print(f"no gallery description for: {', '.join(missing)}", file=sys.stderr)

    payload = webexport.build_payload(ctx, names, ctx_contested,
                                      contested_names, chart_sets=rendered)
    webexport.write_payload(payload, site / "stats.json")

    # Inline the data so the page also works from file:// - a browser blocks
    # fetch() on local files, and players should be able to just open it.
    import json
    blob = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    html = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in html:
        print(f"template is missing {PLACEHOLDER}", file=sys.stderr)
        return 1
    # </script> inside JSON would close the host tag early.
    html = html.replace(PLACEHOLDER, blob.replace("</", "<\\/"))
    html = html.replace(ANALYTICS_SLOT, analytics_tag(args.analytics))
    (site / "index.html").write_text(html, encoding="utf-8")
    (site / ".nojekyll").write_text("", encoding="utf-8")

    size = (site / "index.html").stat().st_size / 1024
    print(f"\nSite      : {site}")
    print("Charts    : "
          + ", ".join(f"{sid} {len(v)}" for sid, v in rendered.items()))
    print(f"Players   : {len(payload['players'])}")
    print(f"Page      : index.html, {size:.0f} KB with data inlined")
    return 0


if __name__ == "__main__":
    sys.exit(main())
