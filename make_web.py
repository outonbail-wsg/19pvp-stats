"""Build the shareable web page into `site/`.

    python make_web.py                # charts + data + page
    python make_web.py --skip-charts  # reuse the PNGs already in output/

The result is a folder that works three ways: opened locally by double-click,
served from GitHub Pages, or dropped into any static host. The data is inlined
into index.html, so the page needs no server and no fetch to show a player card.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from wsgviz import context, data, theme, webexport  # noqa: E402

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "web" / "template.html"
PLACEHOLDER = "__DATA__"


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Build the WSG stats web page")
    p.add_argument("--csv", type=Path, default=None)
    p.add_argument("--outdir", type=Path, default=ROOT / "site")
    p.add_argument("--charts", type=Path, default=ROOT / "output",
                   help="where the PNGs live (or are written to)")
    p.add_argument("--skip-charts", action="store_true",
                   help="do not re-render the PNGs, just reuse them")
    p.add_argument("--tz", default="UTC")
    p.add_argument("--min-games", type=int, default=20)
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    csv_path = args.csv or data.default_csv(ROOT / "Data")

    charts_contested = args.charts.parent / (args.charts.name + "-contested")
    if not args.skip_charts:
        import make_charts
        common = ["--csv", str(csv_path), "--tz", args.tz,
                  "--min-games", str(args.min_games)]
        for outdir, lobby in ((args.charts, "all"), (charts_contested, "contested")):
            rc = make_charts.main(common + ["--outdir", str(outdir), "--lobby", lobby])
            if rc:
                print(f"charts failed for lobby={lobby}; aborting", file=sys.stderr)
                return rc

    theme.apply_theme()
    ctx = context.build(csv_path, args.outdir, tz=args.tz, min_games=args.min_games)
    ctx_contested = context.build(csv_path, args.outdir, tz=args.tz,
                                  min_games=args.min_games, lobby="contested")

    site = args.outdir
    names, contested_names = [], []
    for src, sub, sink in ((args.charts, "charts", names),
                           (charts_contested, "charts-contested", contested_names)):
        target = site / sub
        target.mkdir(parents=True, exist_ok=True)
        for png in sorted(src.glob("*.png")):
            shutil.copy2(png, target / png.name)
            sink.append(png.name)

    # The charts that compare contested against bot-filled lobbies exist only in
    # the all-lobby render - and they are exactly the ones a reader in contested
    # view most wants. Carry them across so the gallery never loses them; their
    # own footnotes already say they cover every lobby.
    import make_charts
    for name in sorted(make_charts.ALL_LOBBIES_ONLY):
        src = args.charts / f"{name}.png"
        if src.exists() and f"{name}.png" not in contested_names:
            shutil.copy2(src, site / "charts-contested" / src.name)
            contested_names.append(src.name)
    contested_names.sort()

    payload = webexport.build_payload(ctx, names, ctx_contested, contested_names)
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
    (site / "index.html").write_text(
        html.replace(PLACEHOLDER, blob.replace("</", "<\\/")), encoding="utf-8")
    (site / ".nojekyll").write_text("", encoding="utf-8")

    size = (site / "index.html").stat().st_size / 1024
    print(f"\nSite      : {site}")
    print(f"Charts    : {len(names)} all-lobby, {len(contested_names)} contested")
    print(f"Players   : {len(payload['players'])}")
    print(f"Page      : index.html, {size:.0f} KB with data inlined")
    return 0


if __name__ == "__main__":
    sys.exit(main())
