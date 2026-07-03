from pathlib import Path
import random
import sys
from collections import defaultdict
from typing import Dict, List, Tuple

import pandas as pd


CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]
PROJECT_ROOT = CURRENT_FILE.parents[3]

sys.path.append(str(SRC_DIR))

from prediction.predict_scoreline import predict_scoreline
from simulation.simulate_match import simulate_single_match_from_prediction


TEAMS_PATH = PROJECT_ROOT / "data" / "raw" / "worldcup_2026" / "teams.csv"
ELO_PATH = PROJECT_ROOT / "data" / "processed" / "team_elo_ratings.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "predictions" / "tournament_simulation_results.csv"


prediction_cache: Dict[Tuple[str, str], Dict] = {}


def load_worldcup_teams_with_elo() -> pd.DataFrame:
    if not TEAMS_PATH.exists():
        raise FileNotFoundError(f"Teams file not found: {TEAMS_PATH}")

    if not ELO_PATH.exists():
        raise FileNotFoundError(
            f"Elo ratings file not found: {ELO_PATH}\n"
            "Run: python src\\models\\elo_model.py"
        )

    teams = pd.read_csv(TEAMS_PATH)
    elo = pd.read_csv(ELO_PATH)

    teams = teams.rename(columns={"team_name": "team"})

    elo = elo.rename(
        columns={
            "elo_rating": "historic_elo_rating",
            "elo_rank": "historic_elo_rank",
        }
    )

    merged = teams.merge(
        elo[["team", "historic_elo_rating", "historic_elo_rank"]],
        on="team",
        how="left",
    )

    if "elo_rating" in merged.columns:
        merged["final_elo_rating"] = merged["historic_elo_rating"].fillna(
            merged["elo_rating"]
        )
    else:
        merged["final_elo_rating"] = merged["historic_elo_rating"].fillna(1500)

    merged["final_elo_rating"] = merged["final_elo_rating"].fillna(1500)
    merged["historic_elo_rank"] = merged["historic_elo_rank"].fillna(999)

    merged = merged.sort_values("final_elo_rating", ascending=False).reset_index(drop=True)

    return merged


def select_knockout_teams(teams: pd.DataFrame, n_teams: int = 32) -> List[str]:
    return (
        teams.sort_values("final_elo_rating", ascending=False)
        .head(n_teams)["team"]
        .tolist()
    )


def seed_bracket(teams: List[str]) -> List[tuple[str, str]]:
    bracket = []

    for i in range(len(teams) // 2):
        home_team = teams[i]
        away_team = teams[-(i + 1)]
        bracket.append((home_team, away_team))

    return bracket


def get_cached_prediction(home_team: str, away_team: str) -> Dict:
    key = (home_team, away_team)

    if key not in prediction_cache:
        prediction_cache[key] = predict_scoreline(home_team, away_team)

    return prediction_cache[key]


def simulate_cached_match(home_team: str, away_team: str, allow_draw: bool = False) -> Dict:
    prediction = get_cached_prediction(home_team, away_team)

    return simulate_single_match_from_prediction(
        prediction=prediction,
        allow_draw=allow_draw,
    )


def simulate_knockout_round(matches: List[tuple[str, str]]) -> tuple[List[str], List[Dict]]:
    winners = []
    match_results = []

    for home_team, away_team in matches:
        result = simulate_cached_match(
            home_team=home_team,
            away_team=away_team,
            allow_draw=False,
        )

        winners.append(result["winner"])
        match_results.append(result)

    return winners, match_results


def build_next_round_matches(winners: List[str]) -> List[tuple[str, str]]:
    matches = []

    for i in range(0, len(winners), 2):
        matches.append((winners[i], winners[i + 1]))

    return matches


def simulate_one_tournament(knockout_teams: List[str]) -> Dict:
    round_of_32_matches = seed_bracket(knockout_teams)

    round_of_16_teams, r32_results = simulate_knockout_round(round_of_32_matches)

    round_of_16_matches = build_next_round_matches(round_of_16_teams)
    quarter_final_teams, r16_results = simulate_knockout_round(round_of_16_matches)

    quarter_final_matches = build_next_round_matches(quarter_final_teams)
    semi_final_teams, qf_results = simulate_knockout_round(quarter_final_matches)

    semi_final_matches = build_next_round_matches(semi_final_teams)
    finalist_teams, sf_results = simulate_knockout_round(semi_final_matches)

    final_match = [(finalist_teams[0], finalist_teams[1])]
    winner_teams, final_results = simulate_knockout_round(final_match)

    winner = winner_teams[0]

    return {
        "winner": winner,
        "finalists": finalist_teams,
        "semi_finalists": semi_final_teams,
        "quarter_finalists": quarter_final_teams,
        "round_of_16": round_of_16_teams,
        "match_results": {
            "round_of_32": r32_results,
            "round_of_16": r16_results,
            "quarter_finals": qf_results,
            "semi_finals": sf_results,
            "final": final_results,
        },
    }


def simulate_tournament_many_times(n_simulations: int = 100) -> pd.DataFrame:
    teams_df = load_worldcup_teams_with_elo()
    knockout_teams = select_knockout_teams(teams_df, n_teams=32)

    winner_counts = defaultdict(int)
    finalist_counts = defaultdict(int)
    semi_finalist_counts = defaultdict(int)
    quarter_finalist_counts = defaultdict(int)
    round_of_16_counts = defaultdict(int)

    print(f"Simulating {n_simulations:,} tournaments...")
    print(f"Knockout teams: {len(knockout_teams)}")
    print("Prediction caching: ON")

    for simulation_number in range(1, n_simulations + 1):
        result = simulate_one_tournament(knockout_teams)

        winner_counts[result["winner"]] += 1

        for team in result["finalists"]:
            finalist_counts[team] += 1

        for team in result["semi_finalists"]:
            semi_finalist_counts[team] += 1

        for team in result["quarter_finalists"]:
            quarter_finalist_counts[team] += 1

        for team in result["round_of_16"]:
            round_of_16_counts[team] += 1

        if simulation_number % 10 == 0:
            print(
                f"Completed {simulation_number:,}/{n_simulations:,} simulations "
                f"| cached matchups: {len(prediction_cache):,}"
            )

    rows = []

    all_teams = sorted(set(knockout_teams))

    for team in all_teams:
        rows.append(
            {
                "team": team,
                "winner_probability": winner_counts[team] / n_simulations,
                "final_probability": finalist_counts[team] / n_simulations,
                "semi_final_probability": semi_finalist_counts[team] / n_simulations,
                "quarter_final_probability": quarter_finalist_counts[team] / n_simulations,
                "round_of_16_probability": round_of_16_counts[team] / n_simulations,
            }
        )

    results_df = pd.DataFrame(rows)
    results_df = results_df.sort_values("winner_probability", ascending=False).reset_index(drop=True)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(OUTPUT_PATH, index=False)

    return results_df


def print_tournament_results(results_df: pd.DataFrame, top_n: int = 20) -> None:
    print("\nTournament Simulation Results")
    print("=" * 80)

    display_df = results_df.head(top_n).copy()

    for col in [
        "winner_probability",
        "final_probability",
        "semi_final_probability",
        "quarter_final_probability",
        "round_of_16_probability",
    ]:
        display_df[col] = (display_df[col] * 100).round(2)

    print(display_df.to_string(index=False))

    print(f"\nSaved results to: {OUTPUT_PATH}")


if __name__ == "__main__":
    results = simulate_tournament_many_times(n_simulations=1000)
    print_tournament_results(results, top_n=20)