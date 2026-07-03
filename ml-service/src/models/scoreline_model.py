from math import exp, factorial
from typing import Dict, List, Tuple


def poisson_probability(expected_goals: float, actual_goals: int) -> float:
    """
    Probability of scoring exactly actual_goals using a Poisson distribution.
    """
    if expected_goals < 0:
        expected_goals = 0

    return (expected_goals ** actual_goals * exp(-expected_goals)) / factorial(actual_goals)


def build_score_probability_matrix(
    home_expected_goals: float,
    away_expected_goals: float,
    max_goals: int = 6,
) -> List[Dict]:
    """
    Builds probabilities for exact scores from 0-0 up to max_goals-max_goals.
    """

    scorelines = []

    for home_goals in range(max_goals + 1):
        for away_goals in range(max_goals + 1):
            home_prob = poisson_probability(home_expected_goals, home_goals)
            away_prob = poisson_probability(away_expected_goals, away_goals)
            probability = home_prob * away_prob

            scorelines.append(
                {
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "scoreline": f"{home_goals}-{away_goals}",
                    "probability": probability,
                }
            )

    scorelines = sorted(scorelines, key=lambda x: x["probability"], reverse=True)
    return scorelines


def calculate_scoreline_markets(scorelines: List[Dict]) -> Dict:
    """
    Calculates common football prediction markets from exact-score probabilities.
    """

    home_win_probability = 0.0
    draw_probability = 0.0
    away_win_probability = 0.0
    over_1_5_probability = 0.0
    over_2_5_probability = 0.0
    over_3_5_probability = 0.0
    both_teams_score_probability = 0.0
    home_clean_sheet_probability = 0.0
    away_clean_sheet_probability = 0.0

    for row in scorelines:
        home_goals = row["home_goals"]
        away_goals = row["away_goals"]
        probability = row["probability"]

        total_goals = home_goals + away_goals

        if home_goals > away_goals:
            home_win_probability += probability
        elif home_goals < away_goals:
            away_win_probability += probability
        else:
            draw_probability += probability

        if total_goals > 1.5:
            over_1_5_probability += probability

        if total_goals > 2.5:
            over_2_5_probability += probability

        if total_goals > 3.5:
            over_3_5_probability += probability

        if home_goals > 0 and away_goals > 0:
            both_teams_score_probability += probability

        if away_goals == 0:
            home_clean_sheet_probability += probability

        if home_goals == 0:
            away_clean_sheet_probability += probability

    return {
        "home_win_probability": home_win_probability,
        "draw_probability": draw_probability,
        "away_win_probability": away_win_probability,
        "over_1_5_probability": over_1_5_probability,
        "over_2_5_probability": over_2_5_probability,
        "over_3_5_probability": over_3_5_probability,
        "both_teams_score_probability": both_teams_score_probability,
        "home_clean_sheet_probability": home_clean_sheet_probability,
        "away_clean_sheet_probability": away_clean_sheet_probability,
    }


def predict_scorelines_from_expected_goals(
    home_expected_goals: float,
    away_expected_goals: float,
    max_goals: int = 6,
    top_n: int = 10,
) -> Dict:
    """
    Full scoreline prediction from expected goals.
    """

    scorelines = build_score_probability_matrix(
        home_expected_goals=home_expected_goals,
        away_expected_goals=away_expected_goals,
        max_goals=max_goals,
    )

    markets = calculate_scoreline_markets(scorelines)

    return {
        "home_expected_goals": home_expected_goals,
        "away_expected_goals": away_expected_goals,
        "all_scorelines": scorelines,
        "top_scorelines": scorelines[:top_n],
        "markets": markets,
    }