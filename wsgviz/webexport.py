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

from . import data, descriptions, rating
from .context import Ctx

# One match of one character, as a fixed array of integers. Field names travel
# once in `logFields` instead of on every one of the 7,000+ entries - that is
# what keeps the complete history under 150 KB gzipped.
# Per-character totals worth shipping. Keys stay as the raw column names so the
# page can look up a label from STAT_LABELS without a second mapping.
SUM_STATS = [
    "flagCaptures", "flagReturns", "flagCarryTime", "attemptsOnFlag",
    "damageOnEFC", "healsOnFC", "damageDone", "healingDone", "absorbsDone",
    "damageTaken", "killingBlows", "honorableKills", "deaths",
    "successfulInterrupts", "fakeCastInterrupts", "dispelsOffensive",
    "dispelsDefensive", "hardCCDuration", "softCCDuration", "bonusHonor",
]
# Every summed stat also ships as a per-minute rate. Keeping the two lists in
# step matters: the card filters out a row whose rate is missing, so a narrower
# list here silently drops statistics from the table instead of failing.
RATE_STATS = SUM_STATS

# The match log carries every summed statistic, not a chosen few, because the
# page rebuilds "today" and "last 7 days" from it rather than shipping a second
# and third set of pre-aggregated totals. A statistic missing here would simply
# have no scoped view.
LOG_META = ["at", "win", "ownCaps", "oppCaps", "seconds", "deserted", "contested"]
LOG_FIELDS = LOG_META + SUM_STATS
# Single-match personal bests.
BEST_STATS = [
    "damageDone", "healingDone", "damageOnEFC", "healsOnFC", "killingBlows",
    "honorableKills", "flagReturns", "flagCaptures", "flagCarryTime",
]


def _clean(value):
    """JSON has no NaN, and no need for 15 decimals of a win rate.

    Rounding matters for size as much as tidiness: an unrounded float costs
    ~18 characters per value, across thousands of values.
    """
    if value is None:
        return None
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, (np.floating, float)):
        f = float(value)
        return None if not np.isfinite(f) else round(f, 4)
    return value


def _game_log(ctx: Ctx) -> dict[int, list[list[int]]]:
    """Complete match history per character, oldest first."""
    m = ctx.matches
    g = ctx.wsg.sort_values("at").copy()
    # Which side's captures were the character's own?
    own = np.where(g["team"] == 0, g["eventId"].map(m["caps_team0"]),
                   g["eventId"].map(m["caps_team1"]))
    opp = np.where(g["team"] == 0, g["eventId"].map(m["caps_team1"]),
                   g["eventId"].map(m["caps_team0"]))
    g["ownCaps"], g["oppCaps"] = own, opp
    g["at"] = (g["at"] // 1000).astype("int64")     # seconds are precise enough
    # -1 loss, 0 draw, 1 win, so the log can show a drawn round as such.
    g["win"] = np.where(g["draw"], 0, np.where(g["win"] == 1, 1, -1))
    g["seconds"] = g["timePlayed"]
    # Lets the page filter the log without shipping a second copy of it.
    from .context import contested_events
    g["contested"] = g["eventId"].isin(contested_events(m)).astype(int)

    out: dict[int, list[list[int]]] = {}
    frame = g[["playerGuid"] + LOG_FIELDS].fillna(0)
    for guid, sub in frame.groupby("playerGuid", sort=False):
        out[int(guid)] = sub[LOG_FIELDS].astype("int64").to_numpy().tolist()
    return out


def _relations(ctx: Ctx, names: pd.Series) -> tuple[dict, dict]:
    """Top opponents and team mates per character, best record first."""
    dec = ctx.wsg[~ctx.wsg["draw"]]
    rivals: dict[int, list] = {}
    allies: dict[int, list] = {}
    for table, key, sink in ((rating.head_to_head(dec), "opponent", rivals),
                             (rating.duos(dec), "mate", allies)):
        table = table[table[key].isin(names.index)]
        for guid, sub in table.groupby("playerGuid"):
            sub = sub.assign(rate=sub["won"] / sub["played"])
            sub = sub.sort_values(["played", "rate"], ascending=False).head(6)
            sink[int(guid)] = [
                [names.get(r[key]), int(r["won"]), int(r["lost"])]
                for _, r in sub.iterrows()]
    return rivals, allies


def lobby_split(full: Ctx) -> pd.DataFrame:
    """Win rate per character in contested and in thin lobbies.

    Always computed from the complete data: it is a comparison between the two
    kinds of lobby, so it cannot be recomputed inside one of them.
    """
    dec = full.wsg[~full.wsg["draw"]]
    m = full.matches
    contested = set(m[(m["tracked_team0"] >= data.CONTESTED_PER_TEAM)
                      & (m["tracked_team1"] >= data.CONTESTED_PER_TEAM)].index)
    thin = set(m[(m["tracked_team0"] <= data.THIN_PER_TEAM)
                 & (m["tracked_team1"] <= data.THIN_PER_TEAM)].index)
    tagged = dec.assign(
        lobby=np.where(dec["eventId"].isin(contested), "contested",
                       np.where(dec["eventId"].isin(thin), "thin", "mid")))
    return (tagged[tagged["lobby"] != "mid"]
            .groupby(["playerGuid", "lobby"])["win"].agg(["size", "mean"]))


def player_records(ctx: Ctx, split: pd.DataFrame) -> list[dict]:
    """One record per character, from whichever slice of matches `ctx` holds."""
    w, tot = ctx.wsg, ctx.totals
    dec = w[~w["draw"]]

    days_active = w.groupby("playerGuid")["date"].nunique()
    best = w.groupby("playerGuid")[BEST_STATS].max()
    first_seen = w.groupby("playerGuid")["ts"].min()
    last_seen = w.groupby("playerGuid")["ts"].max()
    elo = rating.elo_ratings(dec)
    runs = rating.streaks(dec)
    rivals, allies = _relations(ctx, tot["player"])

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
        deaths = row.get("deaths_sum", 0)
        rec["kd"] = _clean(row.get("killingBlows_sum", 0) / deaths) if deaths else None
        rec["takenPerDeath"] = _clean(row.get("damageTaken_sum", 0) / deaths) if deaths else None

        rec["elo"] = _clean(elo.get(guid))
        if guid in runs.index:
            rec["streak"] = int(runs.loc[guid, "current"])
            rec["bestWin"] = int(runs.loc[guid, "best_win"])
            rec["bestLoss"] = int(runs.loc[guid, "best_loss"])
        rec["firstSeen"] = first_seen[guid].strftime("%Y-%m-%d")
        rec["lastSeen"] = last_seen[guid].strftime("%Y-%m-%d")
        rec["rivals"] = rivals.get(int(guid), [])
        rec["allies"] = allies.get(int(guid), [])

        for kind in ("contested", "thin"):
            if (guid, kind) in split.index:
                rec[f"{kind}N"] = _clean(split.loc[(guid, kind), "size"])
                rec[f"{kind}Wr"] = _clean(split.loc[(guid, kind), "mean"])
            else:
                rec[f"{kind}N"], rec[f"{kind}Wr"] = 0, None
        players.append(rec)

    players.sort(key=lambda p: -(p["games"] or 0))
    return players


def _chart_info(*file_lists) -> dict:
    """Gallery title and blurb for every chart that is actually shipped."""
    stems = {f.rsplit(".", 1)[0] for files in file_lists for f in (files or [])}
    return {s: {"title": descriptions.title(s), "blurb": descriptions.blurb(s)}
            for s in sorted(stems)}


def build_payload(ctx: Ctx, chart_files=None, ctx_contested: Ctx | None = None,
                  contested_charts=None) -> dict:
    """The full payload, with a second set of per-character numbers computed
    from contested lobbies only so the page can switch between them."""
    w = ctx.wsg
    dec = w[~w["draw"]]
    tot = ctx.totals
    split = lobby_split(ctx)
    players = player_records(ctx, split)
    log = _game_log(ctx)

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
        "playersContested": (player_records(ctx_contested, split)
                             if ctx_contested else []),
        "logFields": LOG_FIELDS,
        "log": log,
        "charts": chart_files or [],
        "chartsContested": contested_charts or [],
        # Title and explanation per chart, keyed by file stem. The gallery shows
        # the image without its own title until it is opened, so it needs both.
        "chartInfo": _chart_info(chart_files, contested_charts),
        # Reading order for the gallery, per chart set: a contested build ships a
        # different list, so the sections have to be built from each separately.
        "chartGroups": descriptions.grouped(
            f.rsplit(".", 1)[0] for f in (chart_files or [])),
        "chartGroupsContested": descriptions.grouped(
            f.rsplit(".", 1)[0] for f in (contested_charts or [])),
    }


def write_payload(payload: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
                    encoding="utf-8")
    return path
