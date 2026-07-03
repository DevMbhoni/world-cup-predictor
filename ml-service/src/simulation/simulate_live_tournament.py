from pathlib import Path
import random
import sys
from collections import defaultdict
from typing import Dict, Optional

import pandas as pd


CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]
PROJECT_ROOT = CURRENT_FILE.parents[3]

sys.path.append(str(SRC_DIR))

from prediction.predict_scoreline import predict_scoreline
from simulation.simulate_match import simulate_single_match_from_prediction


RAW_2026_DIR = PROJECT_ROOT / "data" / "raw" / "worldcup_2026"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PREDICTIONS_DIR = PROJECT_ROOT / "data" / "predictions"

LIVE_MATCHES_PATH = PROCESSED_DIR / "worldcup_2026_matches_live.csv"
TEAMS_PATH = RAW_2026_DIR / "teams.csv"
BRACKET_PATH = RAW_2026_DIR / "knockout_bracket.csv"
KNOCKOUT_WINNERS_PATH = RAW_2026_DIR / "knockout_winners.csv"

OUTPUT_PATH = PREDICTIONS_DIR / "live_tournament_simulation_results.csv"

prediction_cache: Dict[tuple[str, str], Dict] = {}


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not LIVE_MATCHES_PATH.exists():
        raise FileNotFoundError(
            f"Live matches file not found: {LIVE_MATCHES_PATH}\n"
            "Run: python src\\data\\build_live_matches.py"
        )

    matches = pd.read_csv(LIVE_MATCHES_PATH)
    teams = pd.read_csv(TEAMS_PATH)
    bracket = pd.read_csv(BRACKET_PATH)

    if KNOCKOUT_WINNERS_PATH.exists():
        winners = pd.read_csv(KNOCKOUT_WINNERS_PATH)
    else:
        winners = pd.DataFrame(columns=["match_id", "winner_team_id"])

    return matches, teams, bracket, winners


def build_team_maps(teams: pd.DataFrame) -> tuple[Dict[int, str], Dict[str, int]]:
    id_to_name = dict(zip(teams["team_id"].astype(int), teams["team_name"]))
    name_to_id = {name: team_id for team_id, name in id_to_name.items()}
    return id_to_name, name_to_id


def get_team_name(team_id: Optional[float], id_to_name: Dict[int, str]) -> Optional[str]:
    if pd.isna(team_id):
        return None

    return id_to_name.get(int(team_id))


def get_manual_winner(match_id: int, winners: pd.DataFrame) -> Optional[int]:
    if winners.empty:
        return None

    row = winners[winners["match_id"].astype(int) == int(match_id)]

    if row.empty:
        return None

    value = row.iloc[0]["winner_team_id"]

    if pd.isna(value):
        return None

    return int(value)


def get_completed_match_winner(
    match_row: pd.Series,
    winners: pd.DataFrame,
) -> Optional[int]:
    match_id = int(match_row["match_id"])
    home_team_id = int(match_row["home_team_id"])
    away_team_id = int(match_row["away_team_id"])

    manual_winner = get_manual_winner(match_id, winners)

    if manual_winner is not None:
        return manual_winner

    home_score = match_row["home_score"]
    away_score = match_row["away_score"]

    if pd.isna(home_score) or pd.isna(away_score):
        return None

    if home_score > away_score:
        return home_team_id

    if away_score > home_score:
        return away_team_id

    # Completed knockout draw but no penalty winner recorded.
    # Temporary fallback: random penalty winner.
    return random.choice([home_team_id, away_team_id])


def get_completed_match_loser(
    match_row: pd.Series,
    winner_team_id: int,
) -> Optional[int]:
    home_team_id = int(match_row["home_team_id"])
    away_team_id = int(match_row["away_team_id"])

    if winner_team_id == home_team_id:
        return away_team_id

    if winner_team_id == away_team_id:
        return home_team_id

    return None


def get_cached_prediction(home_team: str, away_team: str) -> Dict:
    key = (home_team, away_team)

    if key not in prediction_cache:
        prediction_cache[key] = predict_scoreline(home_team, away_team)

    return prediction_cache[key]


def simulate_scheduled_match(
    match_id: int,
    home_team_id: int,
    away_team_id: int,
    id_to_name: Dict[int, str],
) -> tuple[int, int]:
    home_team = id_to_name[home_team_id]
    away_team = id_to_name[away_team_id]

    prediction = get_cached_prediction(home_team, away_team)

    result = simulate_single_match_from_prediction(
        prediction=prediction,
        allow_draw=False,
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

    return winner_team_id, loser_team_id


def resolve_source_team(
    source_match_id: int,
    source_type: str,
    winners_by_match: Dict[int, int],
    losers_by_match: Dict[int, int],
) -> Optional[int]:
    if pd.isna(source_match_id):
        return None

    source_match_id = int(source_match_id)

    if source_type == "winner":
        return winners_by_match.get(source_match_id)

    if source_type == "loser":
        return losers_by_match.get(source_match_id)

    return None


def simulate_one_live_tournament(
    matches: pd.DataFrame,
    bracket: pd.DataFrame,
    winners_file: pd.DataFrame,
    id_to_name: Dict[int, str],
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

    reached = defaultdict(set)

    # Process knockout matches in order.
    for match_id in range(73, 105):
        if match_id in matches_by_id:
            match_row = matches_by_id[match_id]
        elif match_id in bracket_by_id:
            match_row = bracket_by_id[match_id]
        else:
            continue

        stage_id = int(match_row["stage_id"])

        home_team_id = match_row.get("home_team_id", pd.NA)
        away_team_id = match_row.get("away_team_id", pd.NA)

        # Resolve placeholder teams from bracket source matches.
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

        reached[stage_id].add(home_team_id)
        reached[stage_id].add(away_team_id)

        status = str(match_row.get("status", "")).lower()

        if status == "completed":
            winner_team_id = get_completed_match_winner(match_row, winners_file)
            loser_team_id = get_completed_match_loser(match_row, winner_team_id)
        else:
            winner_team_id, loser_team_id = simulate_scheduled_match(
                match_id=match_id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                id_to_name=id_to_name,
            )

        winners_by_match[match_id] = winner_team_id
        losers_by_match[match_id] = loser_team_id

    final_winner_id = winners_by_match.get(104)

    if final_winner_id is None:
        raise ValueError("Could not resolve tournament winner. Check bracket mapping.")

    return {
        "winner_team_id": final_winner_id,
        "winner_team": id_to_name[final_winner_id],
        "reached": reached,
        "winners_by_match": winners_by_match,
        "losers_by_match": losers_by_match,
    }

def get_team_statuses(
    matches: pd.DataFrame,
    winners_file: pd.DataFrame,
    id_to_name: Dict[int, str],
) -> Dict[int, str]:
    """
    Determines whether each team is active, eliminated, or not in knockouts.
    Based only on completed knockout matches.
    """

    all_team_ids = set(id_to_name.keys())

    knockout_matches = matches[matches["stage_id"] >= 2].copy()

    knockout_team_ids = set()

    for _, row in knockout_matches.iterrows():
        if pd.notna(row["home_team_id"]):
            knockout_team_ids.add(int(row["home_team_id"]))

        if pd.notna(row["away_team_id"]):
            knockout_team_ids.add(int(row["away_team_id"]))

    eliminated_team_ids = set()
    active_team_ids = set(knockout_team_ids)

    completed_matches = knockout_matches[
        knockout_matches["status"].astype(str).str.lower() == "completed"
    ]

    for _, row in completed_matches.iterrows():
        winner_team_id = get_completed_match_winner(row, winners_file)

        if winner_team_id is None:
            continue

        loser_team_id = get_completed_match_loser(row, winner_team_id)

        if loser_team_id is not None:
            eliminated_team_ids.add(loser_team_id)

    active_team_ids = active_team_ids - eliminated_team_ids

    statuses = {}

    for team_id in all_team_ids:
        if team_id in eliminated_team_ids:
            statuses[team_id] = "Eliminated"
        elif team_id in active_team_ids:
            statuses[team_id] = "Active"
        else:
            statuses[team_id] = "Not qualified for knockouts"

    return statuses

def simulate_live_tournament_many_times(n_simulations: int = 1000) -> pd.DataFrame:
    matches, teams, bracket, winners_file = load_data()
    id_to_name, _ = build_team_maps(teams)
    team_statuses = get_team_statuses(matches, winners_file, id_to_name)

    winner_counts = defaultdict(int)
    final_counts = defaultdict(int)
    semi_counts = defaultdict(int)
    quarter_counts = defaultdict(int)
    r16_counts = defaultdict(int)
    r32_counts = defaultdict(int)

    print(f"Simulating live tournament {n_simulations:,} times...")
    print("Completed matches are locked. Scheduled matches are simulated.")
    print("Prediction caching: ON")

    for i in range(1, n_simulations + 1):
        result = simulate_one_live_tournament(
            matches=matches,
            bracket=bracket,
            winners_file=winners_file,
            id_to_name=id_to_name,
        )

        winner_counts[result["winner_team_id"]] += 1

        for team_id in result["reached"].get(2, set()):
            r32_counts[team_id] += 1

        for team_id in result["reached"].get(3, set()):
            r16_counts[team_id] += 1

        for team_id in result["reached"].get(4, set()):
            quarter_counts[team_id] += 1

        for team_id in result["reached"].get(5, set()):
            semi_counts[team_id] += 1

        for team_id in result["reached"].get(7, set()):
            final_counts[team_id] += 1

        if i % 100 == 0:
            print(
                f"Completed {i:,}/{n_simulations:,} simulations "
                f"| cached matchups: {len(prediction_cache):,}"
            )

    rows = []

    for team_id, team_name in id_to_name.items():
       rows.append(
            {
                "team_id": team_id,
                "team": team_name,
                "status": team_statuses.get(team_id, "Unknown"),
                "winner_probability": winner_counts[team_id] / n_simulations,
                "final_probability": final_counts[team_id] / n_simulations,
                "semi_final_probability": semi_counts[team_id] / n_simulations,
                "quarter_final_probability": quarter_counts[team_id] / n_simulations,
                "round_of_16_probability": r16_counts[team_id] / n_simulations,
                "round_of_32_probability": r32_counts[team_id] / n_simulations,
            }  
        )

    results_df = pd.DataFrame(rows)
    results_df = results_df.sort_values(
        ["winner_probability", "final_probability", "semi_final_probability"],
        ascending=False,
    ).reset_index(drop=True)

    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(OUTPUT_PATH, index=False)

    return results_df


def print_results(results_df: pd.DataFrame, top_n: int = 25) -> None:
    display = results_df.head(top_n).copy()

    probability_cols = [
        "winner_probability",
        "final_probability",
        "semi_final_probability",
        "quarter_final_probability",
        "round_of_16_probability",
        "round_of_32_probability",
    ]

    for col in probability_cols:
        display[col] = (display[col] * 100).round(2)

    print("\nLive Tournament Simulation Results")
    print("=" * 100)
    print(display.to_string(index=False))
    print(f"\nSaved results to: {OUTPUT_PATH}")


if __name__ == "__main__":
    results = simulate_live_tournament_many_times(n_simulations=1000)
    print_results(results, top_n=25)