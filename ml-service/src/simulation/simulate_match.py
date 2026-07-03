from pathlib import Path
import random
import sys
from typing import Dict, List


CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]

sys.path.append(str(SRC_DIR))

from prediction.predict_scoreline import predict_scoreline


def weighted_choice(items: List[Dict], probability_key: str = "probability") -> Dict:
    total_probability = sum(item[probability_key] for item in items)

    if total_probability <= 0:
        return random.choice(items)

    random_value = random.uniform(0, total_probability)
    cumulative_probability = 0.0

    for item in items:
        cumulative_probability += item[probability_key]

        if random_value <= cumulative_probability:
            return item

    return items[-1]


def choose_penalty_winner(home_team: str, away_team: str) -> str:
    return random.choice([home_team, away_team])


def simulate_single_match_from_prediction(
    prediction: Dict,
    allow_draw: bool = True,
) -> Dict:
    home_team = prediction["home_team"]
    away_team = prediction["away_team"]

    # Use full scoreline matrix if available, otherwise top_scorelines.
    scorelines = prediction.get("all_scorelines", prediction["top_scorelines"])

    sampled_scoreline = weighted_choice(scorelines)

    home_goals = sampled_scoreline["home_goals"]
    away_goals = sampled_scoreline["away_goals"]

    if home_goals > away_goals:
        result = "HOME_WIN"
        winner = home_team
        method = "normal_time"
    elif away_goals > home_goals:
        result = "AWAY_WIN"
        winner = away_team
        method = "normal_time"
    else:
        result = "DRAW"

        if allow_draw:
            winner = None
            method = "draw"
        else:
            winner = choose_penalty_winner(home_team, away_team)
            method = "penalties"

    return {
        "home_team": home_team,
        "away_team": away_team,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "scoreline": sampled_scoreline["scoreline"],
        "scoreline_probability": sampled_scoreline["probability"],
        "result": result,
        "winner": winner,
        "method": method,
        "home_expected_goals": prediction["home_expected_goals"],
        "away_expected_goals": prediction["away_expected_goals"],
    }


def simulate_single_match(
    home_team: str,
    away_team: str,
    allow_draw: bool = True,
) -> Dict:
    prediction = predict_scoreline(home_team, away_team)

    return simulate_single_match_from_prediction(
        prediction=prediction,
        allow_draw=allow_draw,
    )


def simulate_match_many_times(
    home_team: str,
    away_team: str,
    n_simulations: int = 1000,
    allow_draw: bool = True,
) -> Dict:
    # IMPORTANT:
    # Predict once, then simulate many times from the same probabilities.
    prediction = predict_scoreline(home_team, away_team)

    home_wins = 0
    away_wins = 0
    draws = 0
    penalty_wins_home = 0
    penalty_wins_away = 0
    scoreline_counts = {}

    for _ in range(n_simulations):
        result = simulate_single_match_from_prediction(
            prediction=prediction,
            allow_draw=allow_draw,
        )

        scoreline = result["scoreline"]
        scoreline_counts[scoreline] = scoreline_counts.get(scoreline, 0) + 1

        if result["winner"] == home_team:
            home_wins += 1

            if result["method"] == "penalties":
                penalty_wins_home += 1

        elif result["winner"] == away_team:
            away_wins += 1

            if result["method"] == "penalties":
                penalty_wins_away += 1

        else:
            draws += 1

    top_scorelines = sorted(
        [
            {
                "scoreline": scoreline,
                "count": count,
                "probability": count / n_simulations,
            }
            for scoreline, count in scoreline_counts.items()
        ],
        key=lambda row: row["count"],
        reverse=True,
    )

    return {
        "home_team": home_team,
        "away_team": away_team,
        "n_simulations": n_simulations,
        "home_expected_goals": prediction["home_expected_goals"],
        "away_expected_goals": prediction["away_expected_goals"],
        "home_win_probability": home_wins / n_simulations,
        "draw_probability": draws / n_simulations,
        "away_win_probability": away_wins / n_simulations,
        "home_penalty_win_probability": penalty_wins_home / n_simulations,
        "away_penalty_win_probability": penalty_wins_away / n_simulations,
        "top_scorelines": top_scorelines[:10],
    }


if __name__ == "__main__":
    result = simulate_match_many_times(
        home_team="Brazil",
        away_team="Germany",
        n_simulations=1000,
        allow_draw=False,
    )

    print("\nMatch Simulation")
    print("=" * 80)
    print(f"{result['home_team']} vs {result['away_team']}")
    print(f"Simulations: {result['n_simulations']}")

    print("\nExpected goals:")
    print(f"{result['home_team']}: {result['home_expected_goals']:.2f}")
    print(f"{result['away_team']}: {result['away_expected_goals']:.2f}")

    print("\nOutcome probabilities:")
    print(f"{result['home_team']} win/advance: {result['home_win_probability']:.2%}")
    print(f"Draw: {result['draw_probability']:.2%}")
    print(f"{result['away_team']} win/advance: {result['away_win_probability']:.2%}")
    print(f"{result['home_team']} penalty win: {result['home_penalty_win_probability']:.2%}")
    print(f"{result['away_team']} penalty win: {result['away_penalty_win_probability']:.2%}")

    print("\nMost simulated scorelines:")
    for row in result["top_scorelines"]:
        print(f"{row['scoreline']}: {row['probability']:.2%}")