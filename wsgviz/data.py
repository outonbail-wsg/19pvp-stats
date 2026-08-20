"""Load, clean and enrich the 19pvp raw export.

One CSV row = one player in one match. The export mixes WSG and arena
(2v2/3v3); the `kind` column separates them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# Columns the docs list for the raw export but that are zero throughout.
DEAD_COLUMNS = ["games", "wins", "losses"]

# WSG ends when a side captures 3 flags OR when the round timer expires - in
# this build after 25 minutes, which the data confirms: match lengths pile up
# sharply in the last half minute before 25:00 and essentially stop there.
# A timer ending is a normal result, so 2-1, 1-0 and 0-0 are real final scores,
# not evidence of missing data.
CAPS_TO_WIN = 3
TIMER_SECONDS = 25 * 60
# `duration` is the longest time played by anyone, which can run slightly past
# the round timer, so the test for a timer ending needs a little slack.
TIMER_SLACK = 30

# A WSG team holds 10 slots. A match counts as contested when both sides fielded
# at least this many distinct real players - bots fill whatever is left, and they
# are absent from the export. Defined once so every chart uses the same cut.
# A conversion rate needs a floor of attempts, or one lucky grab sits at 100 %
# above everyone who ever carried the flag properly.
MIN_PICKUPS = 25

CONTESTED_PER_TEAM = 8
THIN_PER_TEAM = 5

# Standard WoW class ids. 6 (Death Knight) and 10 (Monk) never appear: neither
# exists at level 19. Ids present in the export: 1-5, 7-9, 11.
CLASS_NAMES = {
    1: "Warrior", 2: "Paladin", 3: "Hunter", 4: "Rogue", 5: "Priest",
    6: "Death Knight", 7: "Shaman", 8: "Mage", 9: "Warlock", 10: "Monk", 11: "Druid",
}
# Fixed display order for class charts (only the classes that occur at level 19).
CLASS_ORDER = ["Warrior", "Paladin", "Hunter", "Rogue", "Priest",
               "Shaman", "Mage", "Warlock", "Druid"]

# Official WoW class colours, used for class identity throughout. This is a
# deliberate, documented departure from the brand-neutral palette: WoW players
# read these instantly, and class charts always label the class as well, so
# identity never rests on colour alone. Priest is officially white; shown as a
# mid grey so it stays visible on the light chart surface.
CLASS_COLORS = {
    "Warrior": "#C69B6D",
    "Paladin": "#F48CBA",
    "Hunter": "#AAD372",
    "Rogue": "#FFF468",
    "Priest": "#8a97a3",       # official white -> grey for contrast
    "Death Knight": "#C41E3A",
    "Shaman": "#0070DD",
    "Mage": "#3FC7EB",
    "Warlock": "#8788EE",
    "Monk": "#00FF98",
    "Druid": "#FF7C0A",
}


@dataclass(frozen=True)
class StatMeta:
    """Describes one statistic column for leaderboards and axes."""
    column: str
    label: str              # short title
    unit: str = ""          # unit for axes and values
    seconds: bool = False   # value is a duration in seconds
    wsg_only: bool = False


STATS: list[StatMeta] = [
    StatMeta("flagCaptures", "Flag captures", "captures", wsg_only=True),
    StatMeta("flagReturns", "Flag returns", "returns", wsg_only=True),
    StatMeta("flagCarryTime", "Flag carry time", "time", seconds=True, wsg_only=True),
    StatMeta("attemptsOnFlag", "Flag pickups", "pickups", wsg_only=True),
    StatMeta("damageOnEFC", "Damage on enemy flag carrier", "damage", wsg_only=True),
    StatMeta("healsOnFC", "Healing on own flag carrier", "healing", wsg_only=True),
    StatMeta("damageDone", "Damage done", "damage"),
    StatMeta("healingDone", "Healing done", "healing"),
    StatMeta("absorbsDone", "Absorbs done", "absorb"),
    StatMeta("damageTaken", "Damage taken", "damage"),
    StatMeta("killingBlows", "Killing blows", "KB"),
    StatMeta("honorableKills", "Honorable kills", "HK"),
    StatMeta("deaths", "Deaths", "deaths"),
    StatMeta("successfulInterrupts", "Successful interrupts", "interrupts"),
    StatMeta("fakeCastInterrupts", "Fake casts", "fake casts"),
    StatMeta("dispelsOffensive", "Offensive dispels", "dispels"),
    StatMeta("dispelsDefensive", "Defensive dispels", "dispels"),
    StatMeta("hardCCCount", "Hard CC (count)", "CC"),
    StatMeta("hardCCDuration", "Hard CC (duration)", "time", seconds=True),
    StatMeta("softCCCount", "Soft CC (count)", "CC"),
    StatMeta("softCCDuration", "Soft CC (duration)", "time", seconds=True),
    StatMeta("bonusHonor", "Bonus honor", "honor"),
]

STATS_BY_COLUMN = {s.column: s for s in STATS}


def default_csv(data_dir: Path) -> Path:
    """Newest raw export in the data folder."""
    files = sorted(data_dir.glob("leaderboard-raw-*.csv"))
    if not files:
        raise FileNotFoundError(f"No leaderboard-raw-*.csv in {data_dir}")
    return files[-1]


def load_raw(csv_path: Path, tz: str = "UTC") -> pd.DataFrame:
    """Read the export and append time and derived columns."""
    df = pd.read_csv(csv_path, encoding="utf-8")
    df["ts"] = pd.to_datetime(df["at"], unit="ms", utc=True).dt.tz_convert(tz)
    df["date"] = df["ts"].dt.normalize()
    df["hour"] = df["ts"].dt.hour
    df["weekday"] = df["ts"].dt.weekday           # 0 = Monday
    df["minutes"] = df["timePlayed"] / 60.0
    df["draw"] = df["winner"] == 2                # 2 = draw / unresolved
    # `won` is 1 (win), -1 (loss) or 0 (draw) in the current export; older files
    # used 1/0. A clean 0/1 win indicator works for both. Draws are excluded via
    # `draw` wherever a win rate is computed.
    df["win"] = (df["won"] == 1).astype(int)
    # Class id -> name (missing where the character predates class tracking).
    if "class" in df.columns:
        df["class_name"] = df["class"].map(CLASS_NAMES)
    else:
        df["class_name"] = pd.NA
    # Canonical display name per character: the last one seen, since some
    # characters were renamed during the window.
    last_name = (df.sort_values("at")
                   .groupby("playerGuid")["name"].last().rename("player"))
    df = df.join(_disambiguate(last_name, df), on="playerGuid")
    return df.drop(columns=[c for c in DEAD_COLUMNS if c in df.columns])


def _disambiguate(names: pd.Series, df: pd.DataFrame) -> pd.Series:
    """Make display names unique across characters.

    Several distinct characters share a name (there are two Sebs, three Garys).
    Left alone they collapse into one bar on a leaderboard. Ambiguous names get
    their class appended, and if that still collides, a short id.
    """
    dupes = names[names.duplicated(keep=False)]
    if dupes.empty:
        return names
    cls = df.dropna(subset=["class_name"]).groupby("playerGuid")["class_name"].last()
    out = names.copy()
    for name in dupes.unique():
        guids = names.index[names == name]
        labels = {g: cls.get(g) for g in guids}
        for g in guids:
            c = labels[g]
            tag = c if c and list(labels.values()).count(c) == 1 else str(g)[-4:]
            out.loc[g] = f"{name} ({tag})"
    return out


def character_class(df: pd.DataFrame) -> pd.Series:
    """One class per character (the most frequent non-null value seen)."""
    known = df.dropna(subset=["class_name"])
    return (known.groupby("playerGuid")["class_name"]
                 .agg(lambda s: s.mode().iloc[0]))


def wsg(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["kind"] == "wsg"].copy()


def arena(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["kind"].isin(["2v2", "3v3"])].copy()


def matches(w: pd.DataFrame) -> pd.DataFrame:
    """One row per WSG match, aggregated from the recorded player rows.

    `duration` is the longest time played in the match - the best available
    proxy for match length, since `timePlayed` is counted per player.
    """
    caps = (w.groupby(["eventId", "team"])["flagCaptures"].sum()
              .unstack(fill_value=0).reindex(columns=[0, 1], fill_value=0))
    m = w.groupby("eventId").agg(
        ts=("ts", "first"),
        date=("date", "first"),
        hour=("hour", "first"),
        weekday=("weekday", "first"),
        duration=("timePlayed", "max"),
        tracked=("playerGuid", "size"),
        winner=("winner", "first"),
        draw=("draw", "first"),
        deserters=("deserted", "sum"),
    )
    m["tracked_team0"] = w[w.team == 0].groupby("eventId").size().reindex(m.index, fill_value=0)
    m["tracked_team1"] = w[w.team == 1].groupby("eventId").size().reindex(m.index, fill_value=0)
    m["caps_team0"] = caps[0].reindex(m.index, fill_value=0)
    m["caps_team1"] = caps[1].reindex(m.index, fill_value=0)

    m["caps_winner"] = np.where(m.winner == 0, m.caps_team0,
                                np.where(m.winner == 1, m.caps_team1, np.nan))
    m["caps_loser"] = np.where(m.winner == 0, m.caps_team1,
                               np.where(m.winner == 1, m.caps_team0, np.nan))
    # How the round ended. A win on 3 captures is self-evidently complete; a
    # timer ending is complete too, just with a lower score. Anything else means
    # the recorded players left before the end, so `duration` understates the
    # match and the score cannot be trusted.
    m["capped_out"] = m["caps_winner"] == CAPS_TO_WIN
    m["timer_ended"] = m["duration"] >= TIMER_SECONDS - TIMER_SLACK
    m["score_known"] = (m["capped_out"] | m["timer_ended"]) & ~m["draw"]
    m["margin"] = np.where(m["score_known"], m["caps_winner"] - m["caps_loser"], np.nan)
    m["score"] = np.where(
        m["score_known"],
        (m["caps_winner"].astype("Float64").astype("string")
         .str.replace(r"\.0$", "", regex=True) + "–"
         + m["caps_loser"].astype("Float64").astype("string")
         .str.replace(r"\.0$", "", regex=True)),
        pd.NA)
    m["minutes"] = m["duration"] / 60.0
    return m


def rates(df: pd.DataFrame, min_seconds: int = 60) -> pd.DataFrame:
    """Per-minute rates for each player row.

    Rows below `min_seconds` are dropped - dividing by 12 seconds of play time
    produces rates that no longer mean anything.
    """
    r = df[df["timePlayed"] >= min_seconds].copy()
    for s in STATS:
        if s.column in r.columns and not s.seconds:
            r[f"{s.column}_pm"] = r[s.column] / r["minutes"]
    return r


def player_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Totals, averages, rates and win rate per character."""
    stat_cols = [s.column for s in STATS if s.column in df.columns]
    g = df.groupby("playerGuid")
    out = g[stat_cols].sum()
    out.columns = [f"{c}_sum" for c in out.columns]
    out[[f"{c}_avg" for c in stat_cols]] = g[stat_cols].mean()
    out["player"] = g["player"].last()
    out["games"] = g.size()
    out["minutes"] = g["minutes"].sum()

    decided = df[~df["draw"]]
    dg = decided.groupby("playerGuid")
    out["games_decided"] = dg.size().reindex(out.index, fill_value=0)
    out["wins"] = dg["win"].sum().reindex(out.index, fill_value=0)
    out["winrate"] = (out["wins"] / out["games_decided"]).where(out["games_decided"] > 0)

    out["desertions"] = g["deserted"].sum()
    out["desert_rate"] = out["desertions"] / out["games"]
    for c in stat_cols:
        out[f"{c}_pm"] = out[f"{c}_sum"] / out["minutes"].replace(0, np.nan)
    if "class_name" in df.columns:
        out["class_name"] = character_class(df).reindex(out.index)
    return out


def wilson_interval(wins, n, z: float = 1.96):
    """Wilson confidence interval - fair to players with few games."""
    n = n.replace(0, np.nan)
    p = wins / n
    denom = 1 + z ** 2 / n
    centre = (p + z ** 2 / (2 * n)) / denom
    margin = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denom
    return centre - margin, centre + margin


def fmt_duration(seconds: float) -> str:
    """Seconds -> 'm:ss' or 'h:mm:ss'."""
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
