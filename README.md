# Warsong Gulch visualisations (19pvp, WotLK 3.3.5)

Turns the 19pvp level-19 PvP raw export into a set of PNG charts: general
statistics, match dynamics, win factors, player leaderboards, play-style
profiles and a short arena companion.

## Run

```bash
python make_charts.py
```

Charts land in `output/` (41 PNGs, numbered `01_…` to `43_…`; three numbers were
freed when bar grids were merged into tables). The script
picks the newest `leaderboard-raw-*.csv` in `Data/` automatically.

Options:

```bash
python make_charts.py --only 12 15 19      # render selected charts by prefix
python make_charts.py --tz Europe/Berlin   # day/hour axes in a local zone
python make_charts.py --min-games 30       # stricter threshold for rate/win-rate boards
python make_charts.py --csv path/to.csv --outdir path/to/out
```

Requires Python 3.10+ with `pandas`, `numpy` and `matplotlib`:

```bash
pip install -r requirements.txt
```

## The charts

41 charts, numbered in reading order.

**The bracket** — how big the scene is and when it is alive
| # | File | Shows |
|---|------|-------|
| 01 | overview | headline numbers of the dataset |
| 02 | bracket_population | characters, regulars, and who carries the play |
| 03 | participation | matches-per-character distribution + Lorenz curve |
| 04 | player_base | active vs new characters per day |
| 05 | activity_per_hour | **real-player density by hour** (peak times) |
| 06 | activity_heatmap | real players per match, weekday × hour |
| 07 | activity_per_day | matches per day per mode |

**Classes** (official WoW class colours throughout)
| 08 | class_distribution | characters and player-matches per class |
| 09 | class_meta | popularity vs win rate on one panel |
| 10 | team_composition | what a typical team is made of |
| 11 | class_winrate | win rate per class with Wilson interval |
| 12 | class_matrix | all classes × nine statistics, shaded within each column |

**Matches and what wins them**
| 14 | match_length | match-length distribution |
| 15 | final_score | how the round ended and on what score |
| 16 | humans_vs_bots | humans per team, and win rate by human advantage |
| 17 | win_vs_loss | per-minute stats, winners vs losers |
| 18 | winrate_by_stat | win rate by performance quintile |
| 19 | desertion | what leaving costs |
| 20 | deserter_ranking | who leaves, by name and by class |

**Full lobbies** — the least bot-diluted matches
| 21 | realgames_overview | scope and final score |
| 22 | realgames_team_compare | winning vs losing team totals (near-complete) |
| 23 | realgames_length | full-lobby vs rest match length |
| 24 | contested_record | **win rate in contested vs thin lobbies** |

**Player leaderboards** (bars and names coloured by class)
| 25 | leaders_flag_combat | leaders table, 12 flag and combat statistics |
| 26 | leaders_utility | leaders table, 9 utility statistics |
| 27 | leaders_per_minute | leaders table, 9 rates per minute |
| 28 | leaderboard_winrate | best win rate with an uncertainty band |
| 29 | leaderboard_activity | most matches / hours / days active |
| 31 | role_map | damage vs healing scatter, coloured by class |
| 32 | player_profiles | player cards: headline numbers plus radar |

**Arena 2v2**
| 33–35 | 2v2_overview / _leaderboards / _winrate | 2v2 |

3v3 is not charted: 5 matches across 7 characters is too little to read.

**Feature charts**
| 36 | record_book | best single-match performance per statistic |
| 37 | rivalries | head-to-head matrix + longest win/losing streaks |
| 38 | flag_efficiency | pickup→capture conversion + objective focus |
| 39 | first_match | retention curve by whether the debut was won |

**Standings and form** — sports-page shapes the deck was missing
| 40 | power_ranking | standings table by opponent-adjusted rating (Elo) |
| 41 | form_board | last 25 results per character as a W/L strip |
| 42 | capture_race | cumulative captures over the period |
| 43 | class_boards | best characters of each class |

### Conventions

- **Class colours** are the official WoW ones and carry no legend — the audience
  reads them at a glance, and class charts name the class on the axis anyway.
  Priest white is shifted to a mid grey so it stays visible on a light surface.
  Player *names* are tinted too, but darkened first (`theme.readable_on_surface`)
  until they clear 4.5:1 contrast — rogue yellow as 9pt type would be unreadable.
- **Duplicate character names are disambiguated.** Several distinct characters
  share a name (two Sebs, three Garys). `data._disambiguate` appends the class,
  or a short id when that still collides, so they never merge into one bar.
- **A "contested" lobby is 8+ real players per team** (`data.CONTESTED_PER_TEAM`),
  "thin" is 5 or fewer. A team holds 10 slots and bots fill the rest; the cut is
  defined once so every chart uses the same one.
- **No "overall win rate" reference line.** Every match has one winner and one
  loser, so the average is 50 % by construction and carries no information. (The
  quintile chart is the exception: its line is the mean of the *filtered* rows,
  which sits above 50 % because deserters are excluded.)
- **Footnotes** carry only what the chart cannot show: sample sizes, exclusions,
  units, plus a one-line source stamp.

## What the data does and does not support

Read these before trusting any team- or match-level number.

- **Bots, not missing data.** WSG is filled with bots when too few real players
  queue, and bots are absent from the export. Every real player *is* recorded —
  arena proves it, where all 1,113 2v2 matches carry exactly four rows — so a
  team's recorded players are its complete human side (median 4 of 10 slots).
  The **full-lobby charts (21–24)** isolate matches with ≥8 real players per team.
- **The round timer is 25 minutes.** A match ends on 3 captures *or* when the
  timer expires, so 2–1 and 1–0 are ordinary results — the data shows lengths
  piling up in the last half minute before 25:00 and stopping there. `matches()`
  records `capped_out` and `timer_ended`; a score is withheld only when the
  recorded players all left before the end (79 of 775 matches).
- **Class data (new export).** The current export carries a `class` id (standard
  WoW ids; 6 = Death Knight and 10 = Monk never appear — neither exists at
  level 19). 253 older WSG rows predate class tracking and are excluded from the
  class charts. Class colours are the official WoW palette (Priest shown as grey
  for contrast on a light background).
- **`won` is 1/0/−1** (win/draw/loss) in the current export; older files used
  1/0. The code derives a clean win indicator and treats `winner == 2` as a draw,
  so both encodings work.
- **`games`/`wins`/`losses`/`arenaPoints` are 0 in WSG rows**, so win rate is
  recomputed from the outcome.
- **`timePlayed` is per player, not per match**; match length is approximated by
  the longest time played in the match. Distinct tracked players per team can
  exceed 10 because deserters are replaced (rotation), so "tracked per team" is a
  count over the match, not a simultaneous headcount.
- **Correlation, not cause.** Win-factor charts compare per-minute rates, but
  winning still creates opportunities; the charts say so.

## Publishing it for the server

```bash
python make_web.py
```

Builds `site/` — a static folder with no backend and no running costs:

- `index.html` — player search plus the full chart gallery. The data is **inlined**,
  so the file works opened by double-click, served from GitHub Pages, or copied to
  any static host. No `fetch`, no CORS, no database. Click a chart to open it full
  size and arrow (or swipe) through the set.
- `charts/` and `charts-contested/` — the PNGs, rendered twice
- `stats.json` — the same aggregates as a standalone file, for anyone who wants them

The page is a thin viewer on purpose: all statistics are precomputed in Python
(`wsgviz/webexport.py`), so nothing had to be reimplemented in JavaScript. The
payload is ~64 KB gzipped for 408 characters.

**Contested lobbies are the default.** A match the bots had to fill is not the game
players mean when they compare themselves, so the page opens on contested lobbies
only (`data.CONTESTED_PER_TEAM`+ real players per team) and a checkbox brings the
rest back. That switch drives everything: the player card, the game log and which
chart set the gallery shows. Seven charts are about the human/bot split itself and
exist only in the all-lobby set — see `ALL_LOBBIES_ONLY` in `make_charts.py`.

```bash
python make_charts.py --lobby contested --outdir output-contested
```

**Auto-updating.** `.github/workflows/publish.yml` rebuilds and deploys to GitHub
Pages daily. Both Pages and Actions are free for public repositories. To make it
self-refreshing, set a repository variable `LEADERBOARD_CSV_URL` to the raw export
endpoint; without it the workflow just rebuilds from the CSV in `Data/`.

To publish: push to a public repo, then Settings → Pages → Source: *GitHub Actions*.

## Layout of the code

```
wsgviz/
  theme.py          design system: palette, number formatting, title/footnote/axis-band layout
  data.py           load + clean + enrich; stat metadata; class names/colours; aggregation
  context.py        Ctx: one precomputed data bundle shared by every chart
  plots/
    helpers.py      reusable marks: top-N bars, diverging bars, histograms, radar, class colours/legend
    overview.py     charts 01–07
    match.py        charts 08–11
    winfactors.py   charts 12–14
    leaderboards.py charts 15–20
    classes.py      charts 21–24
    roles.py        charts 25–27
    realgames.py    charts 28–30  (full-lobby / near 10v10)
    arena.py        charts 31–36  (2v2 and 3v3, generated per bracket)
make_charts.py      CLI runner
```

Colours: the brand-neutral chart palette (categorical hues in fixed order, a
blue ramp for magnitude, blue↔red for polarity) for structural charts, and the
official WoW class palette for class identity (class charts and per-player
leaderboards), always paired with a class label or legend so identity never
rests on colour alone. To add a chart, append a `(filename, function)` pair to a
module's `CHARTS` list; each function takes a `Ctx` and returns a `Figure`.
