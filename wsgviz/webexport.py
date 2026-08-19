"""Build the compact JSON payload the web page runs on.

The analysis stays in Python; the browser only reads pre-aggregated numbers and
sorts them. That keeps the page free of any statistics code and the download
small - the whole thing is well under 100 KB gzipped.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import data
from .context import Ctx

# Per-character totals worth shipping. Keys stay as the raw column names so the
# page can look up a label from STAT_LABELS without a second mapping.
SUM_STATS = [
    "flagCaptures", "flagReturns", "flagCarryTime", "attemptsOnFlag",
    "damageOnEFC", "healsOnFC", "damageDone", "healingDone", "absorbsDone",
    "damageTaken", "killingBlows", "honorableKills", "deaths",
    "successfulInterrupts", "fakeCastInterrupts", "dispelsOffensive",
    "dispelsDefensive", "hardCCDuration", "softCCDuration", "bonusHonor",
]
# Rates the card ranks a character on. flagCarryTime is a duration, so its
# per-minute value is a share of time rather than a rate - the page uses it only
# for the profile shape, not in the per-minute table.
RATE_STATS = [
    "damageDone", "healingDone", "damageOnEFC", "healsOnFC", "flagReturns",
    "flagCaptures", "killingBlows", "absorbsDone", "successfulInterrupts",
    "flagCarryTime",
]
# Single-match personal bests.
BEST_STATS = [
    "damageDone", "healingDone", "damageOnEFC", "healsOnFC", "killingBlows",
    "honorableKills", "flagReturns", "flagCaptures", "flagCarryTime",
]


def _clean(value):
    """JSON has no NaN. Missing stays missing."""
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return round(float(value), 4)
    return value


def build_payload(ctx: Ctx, chart_files: list[str] | None = None) -> dict:
    w, tot = ctx.wsg, ctx.totals
    dec = w[~w["draw"]]

    days_active = w.groupby("playerGuid")["date"].nunique()
    best = w.groupby("playerGuid")[BEST_STATS].max()

    # Contested vs thin lobby split - the headline comparison of the deck.
    m = ctx.matches
    contested = set(m[(m["tracked_team0"] >= data.CONTESTED_PER_TEAM)
                      & (m["tracked_team1"] >= data.CONTESTED_PER_TEAM)].index)
    thin = set(m[(m["tracked_team0"] <= data.THIN_PER_TEAM)
                 & (m["tracked_team1"] <= data.THIN_PER_TEAM)].index)
    lobby = dec.assign(
        lobby=np.where(dec["eventId"].isin(contested), "contested",
                       np.where(dec["eventId"].isin(thin), "thin", "mid")))
    split = (lobby[lobby["lobby"] != "mid"]
             .groupby(["playerGuid", "lobby"])["win"].agg(["size", "mean"]))

    players = []
    for guid, row in tot.iterrows():
        rec = {
            "id": int(guid),
            "name": row["player"],
            "class": row["class_name"] if pd.notna(row.get("class_name")) else None,
            "games": _clean(row["games"]),
            "wins": _clean(row["wins"]),
            "decided": _clean(row["games_decided"]),
            "winrate": _clean(row["winrate"]),
            "minutes": _clean(row["minutes"]),
            "days": _clean(days_active.get(guid)),
            "desertRate": _clean(row["desert_rate"]),
            "sum": {s: _clean(row.get(f"{s}_sum")) for s in SUM_STATS},
            "pm": {s: _clean(row.get(f"{s}_pm")) for s in RATE_STATS},
            "best": {s: _clean(best.loc[guid, s]) if guid in best.index else None
                     for s in BEST_STATS},
        }
        # Derived efficiency measures the page would otherwise have to compute.
        picks, caps = row.get("attemptsOnFlag_sum", 0), row.get("flagCaptures_sum", 0)
        rec["capRate"] = _clean(caps / picks) if picks else None
        dmg, dmg_efc = row.get("damageDone_sum", 0), row.get("damageOnEFC_sum", 0)
        rec["objDamage"] = _clean(dmg_efc / dmg) if dmg else None
        heal, heal_fc = row.get("healingDone_sum", 0), row.get("healsOnFC_sum", 0)
        rec["objHealing"] = _clean(heal_fc / heal) if heal else None

        for kind in ("contested", "thin"):
            if (guid, kind) in split.index:
                rec[f"{kind}N"] = _clean(split.loc[(guid, kind), "size"])
                rec[f"{kind}Wr"] = _clean(split.loc[(guid, kind), "mean"])
            else:
                rec[f"{kind}N"], rec[f"{kind}Wr"] = 0, None
        players.append(rec)

    players.sort(key=lambda p: -(p["games"] or 0))

    cls = (dec.dropna(subset=["class_name"])
              .groupby("class_name")
              .agg(rows=("win", "size"), wins=("win", "sum")))
    classes = [{"class": c, "rows": int(r["rows"]),
                "winrate": round(float(r["wins"] / r["rows"]), 4)}
               for c, r in cls.iterrows()]

    a, b = ctx.matches["ts"].min(), ctx.matches["ts"].max()
    return {
        "meta": {
            "source": ctx.source.name,
            "generated": pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "periodStart": a.strftime("%Y-%m-%d"),
            "periodEnd": b.strftime("%Y-%m-%d"),
            "periodLabel": ctx.period_label,
            "matches": int(len(ctx.matches)),
            "characters": int(w["playerGuid"].nunique()),
            "rows": int(len(w)),
            "minGames": int(ctx.min_games),
            "contestedPerTeam": int(data.CONTESTED_PER_TEAM),
            "thinPerTeam": int(data.THIN_PER_TEAM),
        },
        "statLabels": {s.column: s.label for s in data.STATS},
        "secondsStats": [s.column for s in data.STATS if s.seconds],
        "classColors": data.CLASS_COLORS,
        "classOrder": data.CLASS_ORDER,
        "classes": classes,
        "players": players,
        "charts": chart_files or [],
    }


def write_payload(payload: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
                    encoding="utf-8")
    return path
