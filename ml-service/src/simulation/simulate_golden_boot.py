from pathlib import Path
import random
import sys
from collections import defaultdict
from typing import Dict, List

import numpy as np
import pandas as pd


CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]
PROJECT_ROOT = CURRENT_FILE.parents[3]

sys.path.append(str(SRC_DIR))

from prediction.predict_scoreline import predict_scoreline
from simulation.simulate_match import simulate_single_match_from_prediction
from simulation.simulate_live_tournament import (
    load_data,
    build_team_maps,
    get_completed_match_winner,
    get_completed_match_loser,
    resolve_source_team,
)


RAW_2026_DIR = PROJECT_ROOT / "data" / "raw" / "worldcup_2026"
PREDICTIONS_DIR = PROJECT_ROOT / "data" / "predictions"

PLAYER_STATS_PATH = RAW_2026_DIR / "player_stats.csv"
SQUADS_PATH = RAW_2026_DIR / "squads_and_players.csv"

OUTPUT_PATH = PREDICTIONS_DIR / "golden_boot_simulation_results.csv"

prediction_cache: Dict[tuple[str, str], Dict] = {}


def get_cached_prediction(home_team: str, away_team: str) -> Dict:
    key = (home_team, away_team)

    if key not in prediction_cache:
        prediction_cache[key] = predict_scoreline(home_team, away_team)

    return prediction_cache[key]


def normalize_position(position: str) -> str:
    position = str(position).strip().upper()

    if position in ["FWD", "FW", "FORWARD", "STRIKER", "WINGER"]:
        return "FWD"

    if position in ["MID", "MF", "MIDFIELDER"]:
        return "MID"

    if position in ["DEF", "DF", "DEFENDER"]:
        return "DEF"

    if position in ["GK", "GOALKEEPER"]:
        return "GK"

    return position


def load_player_data() -> pd.DataFrame:
    player_stats = pd.read_csv(PLAYER_STATS_PATH)
    squads = pd.read_csv(SQUADS_PATH)

    players = squads.merge(
        player_stats,
        on=["player_id", "team_id"],
        how="left",
        suffixes=("_squad", ""),
    )

    # Use tournament goals from player_stats, not career goals from squads.
    players["current_goals"] = players["goals"].fillna(0)
    players["current_assists"] = players["assists"].fillna(0)
    players["penalty_goals"] = players["penalty_goals"].fillna(0)

    for col in [
        "matches_played",
        "matches_started",
        "minutes_played",
        "shots",
        "shots_on_target",
        "average_rating",
        "market_value_eur",
        "caps",
    ]:
        if col not in players.columns:
            players[col] = 0

        players[col] = players[col].fillna(0)

    if "position" not in players.columns:
        players["position"] = "UNK"

    players["position"] = players["position"].fillna("UNK")
    players["normalized_position"] = players["position"].apply(normalize_position)

    players["starts_rate"] = np.where(
        players["matches_played"] > 0,
        players["matches_started"] / players["matches_played"],
        0,
    )

    players["goals_per_90"] = np.where(
        players["minutes_played"] > 0,
        players["current_goals"] / players["minutes_played"] * 90,
        0,
    )

    players["shots_per_90"] = np.where(
        players["minutes_played"] > 0,
        players["shots"] / players["minutes_played"] * 90,
        0,
    )

    players["shots_on_target_per_90"] = np.where(
        players["minutes_played"] > 0,
        players["shots_on_target"] / players["minutes_played"] * 90,
        0,
    )

    players["minutes_reliability"] = np.minimum(players["minutes_played"] / 180, 1)

    players["goals_per_90"] = (
        players["goals_per_90"] * players["minutes_reliability"]
    ).clip(upper=3.0)

    players["shots_per_90"] = (
        players["shots_per_90"] * players["minutes_reliability"]
    ).clip(upper=6.0)

    players["shots_on_target_per_90"] = (
        players["shots_on_target_per_90"] * players["minutes_reliability"]
    ).clip(upper=4.0)

    position_weight = {
        "FWD": 1.00,
        "MID": 0.45,
        "DEF": 0.12,
        "GK": 0.01,
    }

    players["position_weight"] = players["normalized_position"].map(position_weight).fillna(0.25)

    players["scoring_weight"] = (
        players["current_goals"] * 4.0
        + players["goals_per_90"] * 1.5
        + players["shots_on_target_per_90"] * 0.8
        + players["shots_per_90"] * 0.3
        + players["starts_rate"] * 1.0
        + players["position_weight"] * 2.0
        + np.log1p(players["market_value_eur"]) * 0.04
        + np.log1p(players["caps"]) * 0.08
    )

    players["scoring_weight"] = players["scoring_weight"].clip(lower=0.01)

    return players


def get_team_player_pool(players: pd.DataFrame, team_id: int) -> pd.DataFrame:
    team_players = players[players["team_id"].astype(int) == int(team_id)].copy()

    # Remove goalkeepers from scorer allocation unless no other players exist.
    non_gk = team_players[team_players["normalized_position"] != "GK"].copy()

    if not non_gk.empty:
        team_players = non_gk

    return team_players


def choose_goal_scorer(team_players: pd.DataFrame) -> int:
    weights = team_players["scoring_weight"].to_numpy(dtype=float)

    if weights.sum() <= 0:
        probabilities = np.ones(len(team_players)) / len(team_players)
    else:
        probabilities = weights / weights.sum()

    chosen_index = np.random.choice(team_players.index.to_numpy(), p=probabilities)

    return int(team_players.loc[chosen_index, "player_id"])


def allocate_goals_to_players(
    team_id: int,
    goals: int,
    players: pd.DataFrame,
    simulated_goals_by_player: Dict[int, int],
) -> None:
    if goals <= 0:
        return

    team_players = get_team_player_pool(players, team_id)

    if team_players.empty:
        return

    for _ in range(goals):
        scorer_id = choose_goal_scorer(team_players)
        simulated_goals_by_player[scorer_id] += 1


def simulate_scheduled_match_with_goals(
    home_team_id: int,
    away_team_id: int,
    id_to_name: Dict[int, str],
) -> tuple[int, int, int, int]:
    home_team = id_to_name[home_team_id]
    away_team = id_to_name[away_team_id]

    prediction = get_cached_prediction(home_team, away_team)

    result = simulate_single_match_from_prediction(
        prediction=prediction,
        allow_draw=False,
    )

    home_goals = int(
        result.get("home_score", result.get("home_goals", result.get("simulated_home_goals", 0)))
    )

    away_goals = int(
        result.get("away_score", result.get("away_goals", result.get("simulated_away_goals", 0)))
    )

    winner_name = result["winner"]

    winner_team_id = None

    for team_id, team_name in id_to_name.items():
        if team_name == winner_name:
            winner_team_id = team_id
            break

    if winner_team_id is None:
        raise ValueError(f"Could not resolve winner team name: {winner_name}")

    loser_team_id = away_team_id if winner_team_id == home_team_id else home_team_id

    return winner_team_id, loser_team_id, home_goals, away_goals


def simulate_one_tournament_golden_boot(
    matches: pd.DataFrame,
    bracket: pd.DataFrame,
    winners_file: pd.DataFrame,
    id_to_name: Dict[int, str],
    players: pd.DataFrame,
) -> Dict:
    matches_by_id = {
        int(row["match_id"]): row
        for _, row in matches.iterrows()
    }

    bracket_by_id = {
        int(row["match_id"]): row
        for _, row in bracket.iterrows()
    }

    winners_by_match: Dict[int, int] = {}
    losers_by_match: Dict[int, int] = {}

    simulated_goals_by_player = defaultdict(int)

    for match_id in range(73, 105):
        if match_id in matches_by_id:
            match_row = matches_by_id[match_id]
        elif match_id in bracket_by_id:
            match_row = bracket_by_id[match_id]
        else:
            continue

        home_team_id = match_row.get("home_team_id", pd.NA)
        away_team_id = match_row.get("away_team_id", pd.NA)

        if pd.isna(home_team_id) or pd.isna(away_team_id):
            bracket_row = bracket_by_id.get(match_id)

            if bracket_row is None:
                continue

            if pd.isna(home_team_id):
                home_team_id = resolve_source_team(
                    bracket_row["home_source_match_id"],
                    bracket_row["home_source_type"],
                    winners_by_match,
                    losers_by_match,
                )

            if pd.isna(away_team_id):
                away_team_id = resolve_source_team(
                    bracket_row["away_source_match_id"],
                    bracket_row["away_source_type"],
                    winners_by_match,
                    losers_by_match,
                )

        if home_team_id is None or away_team_id is None:
            continue

        home_team_id = int(home_team_id)
        away_team_id = int(away_team_id)

        status = str(match_row.get("status", "")).lower()

        if status == "completed":
            winner_team_id = get_completed_match_winner(match_row, winners_file)
            loser_team_id = get_completed_match_loser(match_row, winner_team_id)

            # Completed goals are already included in player_stats.csv.
            # Do not allocate them again.
        else:
            winner_team_id, loser_team_id, home_goals, away_goals = simulate_scheduled_match_with_goals(
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                id_to_name=id_to_name,
            )

            allocate_goals_to_players(
                team_id=home_team_id,
                goals=home_goals,
                players=players,
                simulated_goals_by_player=simulated_goals_by_player,
            )

            allocate_goals_to_players(
                team_id=away_team_id,
                goals=away_goals,
                players=players,
                simulated_goals_by_player=simulated_goals_by_player,
            )

        winners_by_match[match_id] = winner_team_id
        losers_by_match[match_id] = loser_team_id

    return {
        "simulated_goals_by_player": simulated_goals_by_player,
        "winners_by_match": winners_by_match,
    }


def simulate_golden_boot_many_times(n_simulations: int = 5000) -> pd.DataFrame:
    matches, teams, bracket, winners_file = load_data()
    id_to_name, _ = build_team_maps(teams)
    players = load_player_data()

    current_goals = dict(
        zip(players["player_id"].astype(int), players["current_goals"].astype(int))
    )

    golden_boot_wins = defaultdict(int)
    top_3_finishes = defaultdict(int)
    expected_final_goals = defaultdict(float)

    print(f"Simulating Golden Boot {n_simulations:,} times...")
    print("Current tournament goals are locked.")
    print("Remaining match goals are simulated and allocated to likely scorers.")
    print("Prediction caching: ON")

    for i in range(1, n_simulations + 1):
        sim_result = simulate_one_tournament_golden_boot(
            matches=matches,
            bracket=bracket,
            winners_file=winners_file,
            id_to_name=id_to_name,
            players=players,
        )

        final_goals = current_goals.copy()

        for player_id, extra_goals in sim_result["simulated_goals_by_player"].items():
            final_goals[player_id] = final_goals.get(player_id, 0) + int(extra_goals)

        max_goals = max(final_goals.values())
        golden_boot_candidates = [
            player_id
            for player_id, goals in final_goals.items()
            if goals == max_goals
        ]

        winner_player_id = random.choice(golden_boot_candidates)
        golden_boot_wins[winner_player_id] += 1

        sorted_players = sorted(
            final_goals.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        top_3_player_ids = [player_id for player_id, _ in sorted_players[:3]]

        for player_id in top_3_player_ids:
            top_3_finishes[player_id] += 1

        for player_id, goals in final_goals.items():
            expected_final_goals[player_id] += goals

        if i % 500 == 0:
            print(
                f"Completed {i:,}/{n_simulations:,} simulations "
                f"| cached matchups: {len(prediction_cache):,}"
            )

    player_lookup = players.set_index("player_id")

    rows = []

    for player_id, row in player_lookup.iterrows():
        player_id = int(player_id)

        rows.append(
            {
                "player_id": player_id,
                "player_name": row["player_name"],
                "team_id": int(row["team_id"]),
                "team_name": id_to_name.get(int(row["team_id"]), "Unknown"),
                "position": row["position"],
                "current_goals": int(row["current_goals"]),
                "expected_final_goals": expected_final_goals[player_id] / n_simulations,
                "golden_boot_probability": golden_boot_wins[player_id] / n_simulations,
                "top_3_probability": top_3_finishes[player_id] / n_simulations,
                "scoring_weight": row["scoring_weight"],
                "minutes_played": row["minutes_played"],
                "matches_started": row["matches_started"],
                "shots": row["shots"],
                "shots_on_target": row["shots_on_target"],
            }
        )

    results_df = pd.DataFrame(rows)

    results_df = results_df.sort_values(
        ["golden_boot_probability", "expected_final_goals", "current_goals"],
        ascending=False,
    ).reset_index(drop=True)

    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(OUTPUT_PATH, index=False)

    return results_df


def print_golden_boot_simulation_results(results_df: pd.DataFrame, top_n: int = 30) -> None:
    display = results_df.head(top_n).copy()

    display["expected_final_goals"] = display["expected_final_goals"].round(2)
    display["golden_boot_probability"] = (display["golden_boot_probability"] * 100).round(2)
    display["top_3_probability"] = (display["top_3_probability"] * 100).round(2)
    display["scoring_weight"] = display["scoring_weight"].round(2)

    print("\nGolden Boot Simulation Results")
    print("=" * 120)
    print(display.to_string(index=False))
    print(f"\nSaved results to: {OUTPUT_PATH}")


if __name__ == "__main__":
    results = simulate_golden_boot_many_times(n_simulations=5000)
    print_golden_boot_simulation_results(results, top_n=30)