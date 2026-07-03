from pathlib import Path
import sys
import pandas as pd
import numpy as np

CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]
PROJECT_ROOT = CURRENT_FILE.parents[3]

sys.path.append(str(SRC_DIR))

from data.load_data import load_historic_data


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "team_elo_ratings.csv"


DEFAULT_ELO = 1500
K_FACTOR = 30
HOME_ADVANTAGE = 60


def expected_score(team_elo: float, opponent_elo: float) -> float:
    return 1 / (1 + 10 ** ((opponent_elo - team_elo) / 400))


def actual_result(home_score: int, away_score: int) -> tuple[float, float]:
    if home_score > away_score:
        return 1.0, 0.0

    if home_score < away_score:
        return 0.0, 1.0

    return 0.5, 0.5


def goal_difference_multiplier(home_score: int, away_score: int) -> float:
    goal_diff = abs(home_score - away_score)

    if goal_diff <= 1:
        return 1.0

    return np.log(goal_diff + 1)


def calculate_elo_ratings(results: pd.DataFrame) -> pd.DataFrame:
    results = results.copy()

    results = results.dropna(subset=["home_score", "away_score"]).copy()
    results["date"] = pd.to_datetime(results["date"], errors="coerce")
    results = results.dropna(subset=["date"]).copy()

    results["home_score"] = results["home_score"].astype(int)
    results["away_score"] = results["away_score"].astype(int)

    results = results.sort_values("date").reset_index(drop=True)
    if "match_key" not in results.columns:
        results["match_key"] = np.arange(len(results))

    ratings = {}
    history = []

    for _, row in results.iterrows():
        home_team = row["home_team"]
        away_team = row["away_team"]

        home_elo_before = ratings.get(home_team, DEFAULT_ELO)
        away_elo_before = ratings.get(away_team, DEFAULT_ELO)

        home_adjusted_elo = home_elo_before
        away_adjusted_elo = away_elo_before

        if not bool(row["neutral"]):
            home_adjusted_elo += HOME_ADVANTAGE

        expected_home = expected_score(home_adjusted_elo, away_adjusted_elo)
        expected_away = 1 - expected_home

        actual_home, actual_away = actual_result(row["home_score"], row["away_score"])
        multiplier = goal_difference_multiplier(row["home_score"], row["away_score"])

        home_change = K_FACTOR * multiplier * (actual_home - expected_home)
        away_change = K_FACTOR * multiplier * (actual_away - expected_away)

        home_elo_after = home_elo_before + home_change
        away_elo_after = away_elo_before + away_change

        ratings[home_team] = home_elo_after
        ratings[away_team] = away_elo_after

        history.append(
            {
                "match_key": row["match_key"],
                "date": row["date"],
                "home_team": home_team,
                "away_team": away_team,
                "home_score": row["home_score"],
                "away_score": row["away_score"],
                "tournament": row["tournament"],
                "neutral": bool(row["neutral"]),
                "home_elo_before": round(home_elo_before, 2),
                "away_elo_before": round(away_elo_before, 2),
                "home_elo_after": round(home_elo_after, 2),
                "away_elo_after": round(away_elo_after, 2),
                "elo_diff_before": round(home_elo_before - away_elo_before, 2),
                "home_expected_score": round(expected_home, 4),
                "away_expected_score": round(expected_away, 4),
            }
        )

    history_df = pd.DataFrame(history)
    return history_df


def build_current_elo_table(elo_history: pd.DataFrame) -> pd.DataFrame:
    home_latest = elo_history[
        ["date", "home_team", "home_elo_after"]
    ].rename(
        columns={
            "home_team": "team",
            "home_elo_after": "elo_rating",
        }
    )

    away_latest = elo_history[
        ["date", "away_team", "away_elo_after"]
    ].rename(
        columns={
            "away_team": "team",
            "away_elo_after": "elo_rating",
        }
    )

    all_latest = pd.concat([home_latest, away_latest], ignore_index=True)
    all_latest = all_latest.sort_values("date")

    current = all_latest.groupby("team", as_index=False).tail(1)
    current = current.sort_values("elo_rating", ascending=False).reset_index(drop=True)
    current["elo_rank"] = np.arange(1, len(current) + 1)

    return current[["elo_rank", "team", "elo_rating", "date"]]


def main() -> None:
    historic = load_historic_data()
    results = historic["results"]

    elo_history = calculate_elo_ratings(results)
    current_elo = build_current_elo_table(elo_history)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    history_output = PROCESSED_DIR / "elo_history.csv"
    current_elo.to_csv(OUTPUT_FILE, index=False)
    elo_history.to_csv(history_output, index=False)

    print(f"Saved current Elo ratings to: {OUTPUT_FILE}")
    print(f"Saved Elo history to: {history_output}")

    print("\nTop 25 teams by Elo:")
    print(current_elo.head(25).to_string(index=False))


if __name__ == "__main__":
    main()