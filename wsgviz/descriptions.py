"""Gallery text for every chart: a display title and a short explanation.

The PNG carries its own title and footnote, but the gallery shows the image
without them until it is opened, so each entry has to say on its own what the
chart is and how to read it. Where a number is computed in a way the picture
cannot show - a rating, an interval, a rate - the blurb says so.

Kept in one place rather than beside each plot function so the wording can be
compared and kept even; `check()` fails the build if it drifts from the charts
that actually exist.
"""

from __future__ import annotations

# stem -> (gallery title, one or two sentences)
CHART_INFO: dict[str, tuple[str, str]] = {
    # --- the bracket -----------------------------------------------------
    "01_overview": (
        "Dataset overview",
        "The headline counts for the whole period: matches, distinct characters, "
        "hours played and how the rounds ended."),
    "02_bracket_population": (
        "Bracket population",
        "Characters grouped by how many days they were active, and how much of all "
        "play each group accounts for."),
    "03_participation": (
        "Matches per character",
        "How many matches each character played, with a cumulative curve showing "
        "what share of all play the most active ones account for."),
    "04_player_base": (
        "Player base per day",
        "Active characters per day, split into returning and new."),
    "05_activity_per_hour": (
        "Activity by hour of day",
        "Real players per match, share of full lobbies and match count, per hour. "
        "This is the chart for finding peak times."),
    "06_activity_heatmap": (
        "Activity heatmap",
        "Average real players per match for each weekday and hour. Darker means "
        "more humans in the lobby."),
    "07_activity_per_day": (
        "Matches per day",
        "Recorded matches per calendar day, split by game mode."),

    # --- classes ---------------------------------------------------------
    "08_class_distribution": (
        "Class distribution",
        "Distinct characters and recorded player-matches per class. Both panels "
        "use the same order, most-played first, so they can be read against each "
        "other."),
    "09_class_meta": (
        "Class meta",
        "Each class placed by how often it is played against how often it wins. "
        "Dot size scales with the number of distinct characters."),
    "10_team_composition": (
        "Team composition",
        "The average number of each class per team, and how often a team fields "
        "the class at all."),
    "11_class_winrate": (
        "Win rate by class",
        "Share of decided player-matches spent on the winning side, per class. The "
        "band is a Wilson interval, so a class with few matches shows a wider one."),
    "12_class_matrix": (
        "Class comparison",
        "All classes against nine statistics. Shading runs within each column, so "
        "a colour compares a class only against the other classes in that same "
        "statistic."),

    # --- the objective ---------------------------------------------------
    "13_flag_leaders": (
        "Flag captures and returns",
        "The two objective statistics, each ranked three ways: total, per match and "
        "per minute played. The orders differ, because a high total can come from "
        "playing more rather than from a higher rate."),
    "14_carrier_leaders": (
        "Flag carrier support",
        "Damage on the enemy flag carrier and healing on your own, ranked total, per "
        "match and per minute. These two separate objective play from raw output."),

    # --- matches and what wins them --------------------------------------
    "15_match_length": (
        "Match length",
        "Distribution of match length in minutes, measured as the longest time any "
        "tracked player spent in the match."),
    "16_final_score": (
        "How a match ends",
        "Whether the round ended on three captures or on the 25-minute timer, and "
        "the score it finished on."),
    "17_humans_vs_bots": (
        "Humans and bots",
        "How many of a team's ten slots were real players, and the win rate by human "
        "advantage. Bots are absent from the export, so the recorded count is the "
        "human count and the rest of the slots were bots."),
    "18_win_vs_loss": (
        "Winners vs losers",
        "Mean per-minute values of the winning side relative to the losing side. "
        "Per minute, so the gap is not just the longer time winners spend in a match."),
    "19_winrate_by_stat": (
        "Win rate by stat quintile",
        "Player rows split into five equal groups per statistic, from the lowest "
        "fifth to the highest, with each group's win rate. Association, not cause: "
        "winning also creates the chances to put up numbers."),
    "20_desertion": (
        "Desertions",
        "How long deserters stay before leaving, and what a leaver on your own team "
        "does to your win rate."),
    "21_deserter_ranking": (
        "Who leaves",
        "Characters ranked by how often they abandon a match, by how many they left "
        "in total, and desertion rate per class."),

    # --- full lobbies ----------------------------------------------------
    "22_realgames_overview": (
        "Full-lobby matches",
        "Scope and final scores of the matches where both teams fielded at least "
        "eight real players - the ones least diluted by bots."),
    "23_realgames_team_compare": (
        "Full-lobby team totals",
        "Per-team totals of the winning side relative to the losing side, in full "
        "lobbies only. Team sums are near-complete there, so they can be compared."),
    "24_realgames_length": (
        "Full lobbies vs rest: length",
        "Match length of full-lobby matches against every other match."),
    "25_contested_record": (
        "Contested vs thin lobbies",
        "Each character's win rate in contested lobbies against their win rate in "
        "bot-filled ones, biggest gap first. Always computed from the complete data, "
        "because it is a comparison between the two kinds of lobby."),

    # --- player leaderboards ---------------------------------------------
    "26_leaders_flag_combat": (
        "Leaders: flag and combat",
        "Top characters by total across the flag and combat statistics."),
    "27_leaders_utility": (
        "Leaders: utility",
        "Top characters by total across the utility statistics - interrupts, dispels "
        "and crowd control."),
    "28_leaders_per_minute": (
        "Leaders: per minute",
        "The same kind of board as rates per minute played, so it does not simply "
        "reward whoever queued the most."),
    "29_leaderboard_winrate": (
        "Best win rate",
        "The highest win rates among characters with enough decided matches, each "
        "with an uncertainty band."),
    "30_leaderboard_activity": (
        "Most active",
        "Top characters by matches played, hours played and days active."),
    "31_role_map": (
        "Damage vs healing",
        "Every qualified character placed by damage and healing per minute, coloured "
        "by class. Where a character sits on the map is their play style."),
    "32_player_profiles": (
        "Player cards",
        "The eight most active characters as cards. Each radar axis is that "
        "character's percentile among all qualified characters, so the outer ring is "
        "the highest value in the pool."),

    # --- arena -----------------------------------------------------------
    "33_2v2_overview": (
        "2v2 overview",
        "Scope of the arena 2v2 bracket in this export."),
    "34_2v2_leaderboards": (
        "2v2 leaderboards",
        "Top 2v2 characters by total across the combat statistics."),
    "35_2v2_winrate": (
        "2v2 best win rate",
        "The highest 2v2 win rates among characters with enough decided matches."),

    # --- feature charts --------------------------------------------------
    "36_record_book": (
        "Record book",
        "The best single match anyone played in the period, one line per statistic."),
    "37_rivalries": (
        "Rivalries and streaks",
        "Head-to-head record between the ten most active characters, and the longest "
        "winning and losing runs anyone put together."),
    "38_flag_efficiency": (
        "Flag efficiency",
        "How often a flag pickup turns into a capture, and how much of a character's "
        "output goes to the flag carriers rather than to everyone else."),
    "39_first_match": (
        "The first match",
        "Share of new characters still playing after N matches, split by whether they "
        "won or lost their very first one."),

    # --- standings -------------------------------------------------------
    "40_power_ranking": (
        "Power ranking",
        "Standings by power rating, with each character's record alongside. The "
        "rating is an Elo: the winning side takes points from the losing side, more "
        "when it was the lower-rated one."),
    "41_capture_race": (
        "Flag capture race",
        "Running total of flag captures over the period for the leading characters."),
    "42_class_boards": (
        "Highest power rating by class",
        "The five highest-rated characters of each class, on the same Elo rating as "
        "the power ranking - so beating strong opponents counts for more than beating "
        "weak ones. The chart itself spells out the full calculation."),
}


def title(stem: str) -> str:
    """Gallery title, falling back to the file name if a chart is new."""
    if stem in CHART_INFO:
        return CHART_INFO[stem][0]
    return stem.split("_", 1)[-1].replace("_", " ").capitalize()


def blurb(stem: str) -> str:
    return CHART_INFO.get(stem, ("", ""))[1]


def check(stems) -> list[str]:
    """Chart stems with no entry here. Empty list means the two are in step."""
    return [s for s in stems if s not in CHART_INFO]
