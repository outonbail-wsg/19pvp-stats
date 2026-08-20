# Warsong Gulch visualisations (19pvp, WotLK 3.3.5)

Turns the 19pvp level-19 PvP raw export into a set of PNG charts: general
statistics, the flag game, interrupts and crowd control, match dynamics, win
factors, player leaderboards, play-style profiles and a short arena companion.

## Run

```bash
python make_charts.py
```

Charts land in `output/` as 44 PNGs, numbered `01_…` to `44_…`. The script
picks the newest `leaderboard-raw-*.csv` in `Data/` automatically.

Options:

```bash
python make_charts.py --only 12 15 19      # render selected charts by prefix
python make_charts.py --tz Europe/Berlin   # day/hour axes in a local zone
python make_charts.py --min-games 20       # stricter threshold for rate/win-rate boards
python make_charts.py --csv path/to.csv --outdir path/to/out
```

Requires Python 3.10+ with `pandas`, `numpy` and `matplotlib`:

```bash
pip install -r requirements.txt
```

## The charts

44 charts. The published page splits them across **Leaderboards** and **The bracket**; the file numbers follow the sections below.

### Leaderboards

**The flag**
| # | Chart | What it shows |
|---|-------|---------------|
| 13 | flag_leaders | The two objective statistics, each ranked three ways: total, per match and per minute played |
| 14 | carrier_leaders | Damage on the enemy flag carrier and healing on your own, ranked total, per match and per minute |
| 15 | flag_hold | Who spends the most time carrying the flag, and who turns a pickup into a capture most often |
| 16 | flag_efficiency | How often a flag pickup turns into a capture, and how much of a character's output goes to the flag carriers rather than to everyone else |

**Control**
| # | Chart | What it shows |
|---|-------|---------------|
| 17 | interrupt_leaders | Successful interrupts and fake casts, each total, per match and per minute |
| 18 | cc_leaders | Hard and soft crowd control as seconds applied, total, per match and per minute |

**Leaderboards**
| # | Chart | What it shows |
|---|-------|---------------|
| 19 | leaders_flag_combat | Top characters by total across the flag and combat statistics |
| 20 | leaders_utility | Top characters by total across the utility statistics - interrupts, dispels and crowd control |
| 21 | leaders_per_minute | The same kind of board as rates per minute played, so it does not simply reward whoever queued the most |
| 22 | leaderboard_winrate | The highest win rates among characters with enough decided matches, each with an uncertainty band |
| 23 | leaderboard_activity | Top characters by matches played, hours played, days active and matches lost |
| 24 | role_map | Every qualified character placed by damage and healing per minute, coloured by class |
| 25 | player_profiles | The eight most active characters as cards |

**Standings**
| # | Chart | What it shows |
|---|-------|---------------|
| 40 | power_ranking | Standings by power rating, with each character's record alongside |
| 41 | class_boards | The five highest-rated characters of each class, on the same Elo rating as the power ranking - so beating strong opponents counts for more than beating weak ones |

### The bracket

**The bracket**
| # | Chart | What it shows |
|---|-------|---------------|
| 01 | overview | The headline counts for the whole period: matches, distinct characters, hours played and how the rounds ended |
| 02 | bracket_population | Characters grouped by how many days they were active, and how much of all play each group accounts for |
| 03 | participation | How many matches each character played, with a cumulative curve showing what share of all play the most active ones account for |
| 04 | player_base | Active characters per day, split into returning and new |
| 05 | activity_per_hour | Real players per match, share of full lobbies and match count, per hour |
| 06 | activity_heatmap | Average real players per match for each weekday and hour |
| 07 | activity_per_day | Recorded matches per calendar day, split by game mode |

**Classes**
| # | Chart | What it shows |
|---|-------|---------------|
| 08 | class_distribution | Distinct characters and recorded player-matches per class |
| 09 | class_meta | Each class placed by how often it is played against how often it wins |
| 10 | team_composition | The average number of each class per team, and how often a team fields the class at all |
| 11 | class_winrate | Share of decided player-matches spent on the winning side, per class |
| 12 | class_matrix | All classes against nine statistics |

**Matches and lobbies**
| # | Chart | What it shows |
|---|-------|---------------|
| 26 | match_length | Distribution of match length in minutes, measured as the longest time any tracked player spent in the match |
| 27 | final_score | Whether the round ended on three captures or on the 25-minute timer, and the score it finished on |
| 28 | humans_vs_bots | How many of a team's ten slots were real players, and the win rate by human advantage |
| 29 | realgames_overview | Scope and final scores of the matches where both teams fielded at least eight real players - the ones least diluted by bots |
| 30 | realgames_team_compare | Per-team totals of the winning side relative to the losing side, in full lobbies only |
| 31 | realgames_length | Match length of full-lobby matches against every other match |
| 32 | contested_record | Each character's win rate in contested lobbies against their win rate in bot-filled ones, biggest gap first |

**What separates wins from losses**
| # | Chart | What it shows |
|---|-------|---------------|
| 33 | win_vs_loss | Mean per-minute values of the winning side relative to the losing side |
| 34 | winrate_by_stat | Player rows split into five equal groups per statistic, from the lowest fifth to the highest, with each group's win rate |
| 35 | desertion | How long deserters stay before leaving, and what a leaver on your own team does to your win rate |
| 36 | deserter_ranking | Characters ranked by how often they abandon a match, by how many they left in total, and desertion rate per class |

**Records and rivalries**
| # | Chart | What it shows |
|---|-------|---------------|
| 37 | record_book | The best single match anyone played in the period, one line per statistic |
| 38 | rivalries | Head-to-head record between the ten most active characters, and the longest winning and losing runs anyone put together |
| 39 | first_match | Share of new characters still playing after N matches, split by whether they won or lost their very first one |

**Arena**
| # | Chart | What it shows |
|---|-------|---------------|
| 42 | 2v2_overview | Scope of the arena 2v2 bracket in this export |
| 43 | 2v2_leaderboards | Top 2v2 characters by total across the combat statistics |
| 44 | 2v2_winrate | The highest 2v2 win rates among characters with enough decided matches |
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
  The **full-lobby charts (29–31)** isolate matches with ≥8 real players per team.
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
  size and arrow (or swipe) through the set — the arrows stay within the gallery
  page being read. Each chart carries a short explanation from
  `wsgviz/descriptions.py`, which the build checks for gaps.
- `charts/` and `charts-contested/` — the PNGs, rendered twice
- `stats.json` — the same aggregates as a standalone file, for anyone who wants them

The page is a thin viewer on purpose: all statistics are precomputed in Python
(`wsgviz/webexport.py`), so nothing had to be reimplemented in JavaScript. The
payload is ~64 KB gzipped for 408 characters.

**Contested lobbies are the default.** A match the bots had to fill is not the game
players mean when they compare themselves, so the page opens on contested lobbies
only (`data.CONTESTED_PER_TEAM`+ real players per team) and a checkbox brings the
rest back. That switch drives everything: the player card, the game log and which
chart set the gallery shows. Seven charts compare the two kinds of lobby against
each other, so they are rendered once from the complete data and appear in both
galleries unchanged — see `ALL_LOBBIES_ONLY` in `make_charts.py`.

```bash
python make_charts.py --lobby contested --outdir output-contested
```

**Auto-updating.** `.github/workflows/publish.yml` rebuilds and deploys to GitHub
Pages daily. Both Pages and Actions are free for public repositories. To make it
self-refreshing, set a repository variable `LEADERBOARD_CSV_URL` to the raw export
endpoint; without it the workflow just rebuilds from the CSV in `Data/`.

To publish: push to a public repo, then Settings → Pages → Source: *GitHub Actions*.

**Ranking pool.** Rate and win-rate boards need `--min-games` matches (default 10),
because a rate over three rounds swings too far to place. On the charts that
threshold is a hard filter. On a character's own page it is not: someone below it
is added to the pool and does get a placing — seeing where you stand is the point
of the page — but the card says plainly that the ranking is provisional and why.
The pool is the same one the charts use, so a card and a chart can never name a
different leader.

**Four pages, one file.** *The bracket* (how the game and the scene work) and
*Leaderboards* (who is best at what) are galleries of rendered charts, declared in
`descriptions.VIEWS` and built from the same `GROUPS` list the numbering follows,
so a chart cannot land in a section no page shows. *By class* and *Characters* are
built in the browser from the shipped records instead — which is why they can be
filtered and an image cannot. Each is addressable: `…/#/bracket`, `…/#/boards`,
`…/#/classes`, `…/#/characters`.

Separate HTML files would each need their own copy of the inlined payload and the
character search would only work on one of them; hidden pages cost nothing here
because their images are lazy and never requested until the page is opened.

**A rotating strip** at the top carries one fact at a time: who leads a statistic,
who has lost the most, and the best single match anyone played — the first two read
over today, the last seven days and the whole period. Clicking it opens the
character it names. Built from the same windowed records as everything else, so
nothing is pre-computed for the strip alone.

**Time windows.** The page reads *All time*, *Last 7 days*, *Yesterday* or a range
picked by hand, rebuilt
in the browser from the match log that already ships in the payload rather than
from a second and third set of pre-aggregated totals. The window anchors on the
newest match that passes the lobby filter, not the newest in the file — contested
play can stop a day before bot-filled play does. A single day is the last
*complete* one: the export is taken part-way through a day, so the newest is
always partial, and what it is missing is the evening — the busiest hours in the
bracket. Power rating, head-to-head and
team-mate records have no windowed form (they need every match in order, or the
other side of each match) and say so instead of showing an all-time figure under a
seven-day heading. The match threshold drops with the window: 10, 5, 3.

A picked range interpolates its threshold between those anchors rather than
looking one up — three matches over a single day, the full bar over the whole
period — so picking every date by hand gives the same pool *All time* does. The
charts do not follow any of this: they are rendered once per build over the whole
period, and the gallery says so whenever a window is on.

**Linkable characters.** A character view has its own address, `…/#/c/Name`, so a
player can bookmark their page or post it. Close it with the button on the card or
with Escape, which clears the address as well and returns to the report. A link that points at someone with no
matches in the current slice flips the lobby switch rather than showing an empty
card.

**Visitor counting (optional).** Set a repository variable `GOATCOUNTER_URL` to a
[GoatCounter](https://www.goatcounter.com) endpoint (`https://NAME.goatcounter.com/count`)
and the build emits the counting script; the page then also reports each character
view as `/c/Name`, so the dashboard shows which characters get read. Without the
variable no analytics script is emitted and the page contacts nobody. The endpoint
is only ever read from the environment, never committed. GoatCounter sets no
cookies, so no consent banner is needed.

## Layout of the code

```
wsgviz/
  theme.py          design system: palette, number formatting, title/footnote/axis-band layout
  data.py           load + clean + enrich; stat metadata; class names/colours; aggregation
  context.py        Ctx: one precomputed data bundle shared by every chart
  descriptions.py   gallery title and explanation per chart, in one place
  plots/
    helpers.py      reusable marks: top-N bars, diverging bars, histograms, radar, class colours/legend
    overview.py     01, 03–07      scope of the dataset and when it is played
    bracket.py      02, 09–10      who plays, and in what team shapes
    classes.py      08, 11–12      class distribution, win rate, stat matrix
    objective.py    13–15          flag work: captures, returns, carrier support, hold and conversion
    stories.py      16, 32, 37–39  feature charts
    control.py      17–18          interrupts, fake casts and crowd control
    leaderboards.py 19–23          per-player boards
    roles.py        24–25          role map and player profile cards
    match.py        26–28          length, score, human/bot split
    realgames.py    29–31          full-lobby / near 10v10
    winfactors.py   33–36          what separates wins from losses; desertion
    standings.py    40–41          Elo table and per-class boards
    arena.py        42–44          2v2 (generated per bracket)
make_charts.py      CLI runner
```

Colours: the brand-neutral chart palette (categorical hues in fixed order, a
blue ramp for magnitude, blue↔red for polarity) for structural charts, and the
official WoW class palette for class identity (class charts and per-player
leaderboards), always paired with a class label or legend so identity never
rests on colour alone. To add a chart, append a `(filename, function)` pair to a
module's `CHARTS` list; each function takes a `Ctx` and returns a `Figure`.
