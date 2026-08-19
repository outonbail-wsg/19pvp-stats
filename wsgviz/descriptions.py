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

    "15_flag_hold": (
        "Flag hold and conversion",
        "Who spends the most time carrying the flag, and who turns a pickup into a "
        "capture most often. Conversion needs 25+ pickups, or one lucky grab tops it."),

    # --- control ---------------------------------------------------------
    "17_interrupt_leaders": (
        "Interrupts and fake casts",
        "Successful interrupts and fake casts, each total, per match and per minute. "
        "A fake cast is one started to bait an interrupt and cancelled, so the two "
        "boards are opposite sides of the same duel."),
    "18_cc_leaders": (
        "Crowd control",
        "Hard and soft crowd control as seconds applied, total, per match and per "
        "minute. Duration rather than count: ten brief roots are not one long sap."),

    # --- matches and what wins them --------------------------------------
    "26_match_length": (
        "Match length",
        "Distribution of match length in minutes, measured as the longest time any "
        "tracked player spent in the match."),
    "27_final_score": (
        "How a match ends",
        "Whether the round ended on three captures or on the 25-minute timer, and "
        "the score it finished on."),
    "28_humans_vs_bots": (
        "Humans and bots",
        "How many of a team's ten slots were real players, and the win rate by human "
        "advantage. Bots are absent from the export, so the recorded count is the "
        "human count and the rest of the slots were bots."),
    "33_win_vs_loss": (
        "Winners vs losers",
        "Mean per-minute values of the winning side relative to the losing side. "
        "Per minute, so the gap is not just the longer time winners spend in a match."),
    "34_winrate_by_stat": (
        "Win rate by stat quintile",
        "Player rows split into five equal groups per statistic, from the lowest "
        "fifth to the highest, with each group's win rate. Association, not cause: "
        "winning also creates the chances to put up numbers."),
    "35_desertion": (
        "Desertions",
        "How long deserters stay before leaving, and what a leaver on your own team "
        "does to your win rate."),
    "36_deserter_ranking": (
        "Who leaves",
        "Characters ranked by how often they abandon a match, by how many they left "
        "in total, and desertion rate per class."),

    # --- full lobbies ----------------------------------------------------
    "29_realgames_overview": (
        "Full-lobby matches",
        "Scope and final scores of the matches where both teams fielded at least "
        "eight real players - the ones least diluted by bots."),
    "30_realgames_team_compare": (
        "Full-lobby team totals",
        "Per-team totals of the winning side relative to the losing side, in full "
        "lobbies only. Team sums are near-complete there, so they can be compared."),
    "31_realgames_length": (
        "Full lobbies vs rest: length",
        "Match length of full-lobby matches against every other match."),
    "32_contested_record": (
        "Contested vs thin lobbies",
        "Each character's win rate in contested lobbies against their win rate in "
        "bot-filled ones, biggest gap first. Always computed from the complete data, "
        "because it is a comparison between the two kinds of lobby."),

    # --- player leaderboards ---------------------------------------------
    "19_leaders_flag_combat": (
        "Leaders: flag and combat",
        "Top characters by total across the flag and combat statistics."),
    "20_leaders_utility": (
        "Leaders: utility",
        "Top characters by total across the utility statistics - interrupts, dispels "
        "and crowd control."),
    "21_leaders_per_minute": (
        "Leaders: per minute",
        "The same kind of board as rates per minute played, so it does not simply "
        "reward whoever queued the most."),
    "22_leaderboard_winrate": (
        "Best win rate",
        "The highest win rates among characters with enough decided matches, each "
        "with an uncertainty band."),
    "23_leaderboard_activity": (
        "Most active",
        "Top characters by matches played, hours played and days active."),
    "24_role_map": (
        "Damage vs healing",
        "Every qualified character placed by damage and healing per minute, coloured "
        "by class. Where a character sits on the map is their play style."),
    "25_player_profiles": (
        "Player cards",
        "The eight most active characters as cards. Each radar axis is that "
        "character's percentile among all qualified characters, so the outer ring is "
        "the highest value in the pool."),

    # --- arena -----------------------------------------------------------
    "42_2v2_overview": (
        "2v2 overview",
        "Scope of the arena 2v2 bracket in this export."),
    "43_2v2_leaderboards": (
        "2v2 leaderboards",
        "Top 2v2 characters by total across the combat statistics."),
    "44_2v2_winrate": (
        "2v2 best win rate",
        "The highest 2v2 win rates among characters with enough decided matches."),

    # --- feature charts --------------------------------------------------
    "37_record_book": (
        "Record book",
        "The best single match anyone played in the period, one line per statistic."),
    "38_rivalries": (
        "Rivalries and streaks",
        "Head-to-head record between the ten most active characters, and the longest "
        "winning and losing runs anyone put together."),
    "16_flag_efficiency": (
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
    "41_class_boards": (
        "Highest power rating by class",
        "The five highest-rated characters of each class, on the same Elo rating as "
        "the power ranking - so beating strong opponents counts for more than beating "
        "weak ones. The chart itself spells out the full calculation."),
}


# Reading order for the gallery. The file numbers follow this list, so a chart's
# number and the section it sits in can never disagree.
GROUPS: list[tuple[str, list[str]]] = [
    ("The bracket", [
        "01_overview", "02_bracket_population", "03_participation",
        "04_player_base", "05_activity_per_hour", "06_activity_heatmap",
        "07_activity_per_day"]),
    ("Classes", [
        "08_class_distribution", "09_class_meta", "10_team_composition",
        "11_class_winrate", "12_class_matrix"]),
    ("The flag", [
        "13_flag_leaders", "14_carrier_leaders", "15_flag_hold",
        "16_flag_efficiency"]),
    ("Control", [
        "17_interrupt_leaders", "18_cc_leaders"]),
    ("Leaderboards", [
        "19_leaders_flag_combat", "20_leaders_utility", "21_leaders_per_minute",
        "22_leaderboard_winrate", "23_leaderboard_activity", "24_role_map",
        "25_player_profiles"]),
    ("Matches and lobbies", [
        "26_match_length", "27_final_score", "28_humans_vs_bots",
        "29_realgames_overview", "30_realgames_team_compare",
        "31_realgames_length", "32_contested_record"]),
    ("What separates wins from losses", [
        "33_win_vs_loss", "34_winrate_by_stat", "35_desertion",
        "36_deserter_ranking"]),
    ("Records and rivalries", [
        "37_record_book", "38_rivalries", "39_first_match"]),
    ("Standings", [
        "40_power_ranking", "41_class_boards"]),
    ("Arena", [
        "42_2v2_overview", "43_2v2_leaderboards", "44_2v2_winrate"]),
]


def grouped(stems) -> list[dict]:
    """The gallery sections, filtered to the charts actually shipped.

    A chart missing from GROUPS still reaches the reader, in a trailing section,
    rather than disappearing from a gallery that looks complete.
    """
    have = list(stems)
    placed, out = set(), []
    for name, members in GROUPS:
        files = [s for s in members if s in have]
        if files:
            out.append({"name": name, "charts": files})
            placed.update(files)
    rest = [s for s in have if s not in placed]
    if rest:
        out.append({"name": "Other", "charts": rest})
    return out


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
