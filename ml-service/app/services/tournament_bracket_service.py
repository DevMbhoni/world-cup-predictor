from pathlib import Path
from collections import defaultdict

import pandas as pd


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]

RAW_2026_DIR = PROJECT_ROOT / "data" / "raw" / "worldcup_2026"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PREDICTIONS_DIR = PROJECT_ROOT / "data" / "predictions"

LIVE_MATCHES_PATH = PROCESSED_DIR / "worldcup_2026_matches_live.csv"
BRACKET_PATH = RAW_2026_DIR / "knockout_bracket.csv"
TEAMS_PATH = RAW_2026_DIR / "teams.csv"
KNOCKOUT_WINNERS_PATH = RAW_2026_DIR / "knockout_winners.csv"
LIVE_SIMULATION_PATH = PREDICTIONS_DIR / "live_tournament_simulation_results.csv"


STAGE_NAMES = {
    1: "Group Stage",
    2: "Round of 32",
    3: "Round of 16",
    4: "Quarter-finals",
    5: "Semi-finals",
    6: "Third-place match",
    7: "Final",
}


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    return pd.read_csv(path)


def load_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def get_team_maps(teams: pd.DataFrame) -> tuple[dict[int, str], dict[str, int]]:
    id_to_name = dict(zip(teams["team_id"].astype(int), teams["team_name"]))
    name_to_id = {name: team_id for team_id, name in id_to_name.items()}
    return id_to_name, name_to_id


def safe_int(value):
    if pd.isna(value):
        return None

    return int(value)


def safe_float(value):
    if pd.isna(value):
        return None

    return float(value)


def get_team_name(team_id, id_to_name: dict[int, str]):
    if pd.isna(team_id):
        return None

    return id_to_name.get(int(team_id))


def get_manual_winner(match_id: int, winners: pd.DataFrame):
    if winners.empty:
        return None

    if "match_id" not in winners.columns or "winner_team_id" not in winners.columns:
        return None

    row = winners[winners["match_id"].astype(int) == int(match_id)]

    if row.empty:
        return None

    value = row.iloc[0]["winner_team_id"]

    if pd.isna(value):
        return None

    return int(value)


def derive_completed_winner(row: pd.Series, winners: pd.DataFrame):
    match_id = int(row["match_id"])

    manual_winner = get_manual_winner(match_id, winners)

    if manual_winner is not None:
        return manual_winner

    home_team_id = row.get("home_team_id")
    away_team_id = row.get("away_team_id")
    home_score = row.get("home_score")
    away_score = row.get("away_score")

    if pd.isna(home_team_id) or pd.isna(away_team_id):
        return None

    if pd.isna(home_score) or pd.isna(away_score):
        return None

    if float(home_score) > float(away_score):
        return int(home_team_id)

    if float(away_score) > float(home_score):
        return int(away_team_id)

    return None


def get_match_prediction_from_team_probabilities(
    home_team_id,
    away_team_id,
    team_probability_map: dict[int, dict],
):
    if home_team_id is None or away_team_id is None:
        return None

    home_data = team_probability_map.get(int(home_team_id), {})
    away_data = team_probability_map.get(int(away_team_id), {})

    home_winner_probability = float(home_data.get("winner_probability", 0))
    away_winner_probability = float(away_data.get("winner_probability", 0))

    if home_winner_probability >= away_winner_probability:
        predicted_winner_team_id = int(home_team_id)
    else:
        predicted_winner_team_id = int(away_team_id)

    return {
        "home_tournament_winner_probability": home_winner_probability,
        "away_tournament_winner_probability": away_winner_probability,
        "predicted_winner_team_id": predicted_winner_team_id,
    }


def build_team_probability_map(simulation: pd.DataFrame, name_to_id: dict[str, int]):
    probability_map = {}

    if simulation.empty:
        return probability_map

    for _, row in simulation.iterrows():
        team_name = row.get("team")

        if team_name not in name_to_id:
            continue

        team_id = name_to_id[team_name]

        probability_map[team_id] = {
            "status": row.get("status"),
            "winner_probability": float(row.get("winner_probability", 0)),
            "final_probability": float(row.get("final_probability", 0)),
            "semi_final_probability": float(row.get("semi_final_probability", 0)),
            "quarter_final_probability": float(row.get("quarter_final_probability", 0)),
            "round_of_16_probability": float(row.get("round_of_16_probability", 0)),
            "round_of_32_probability": float(row.get("round_of_32_probability", 0)),
        }

    return probability_map


def get_most_likely_team_for_source(
    source_match_id,
    source_type,
    projected_winners_by_match,
    projected_losers_by_match,
):
    if pd.isna(source_match_id):
        return None

    source_match_id = int(source_match_id)

    if source_type == "winner":
        return projected_winners_by_match.get(source_match_id)

    if source_type == "loser":
        return projected_losers_by_match.get(source_match_id)

    return None


def build_bracket() -> dict:
    matches = load_csv(LIVE_MATCHES_PATH)
    bracket = load_csv(BRACKET_PATH)
    teams = load_csv(TEAMS_PATH)
    winners = load_optional_csv(KNOCKOUT_WINNERS_PATH)
    simulation = load_optional_csv(LIVE_SIMULATION_PATH)

    id_to_name, name_to_id = get_team_maps(teams)
    team_probability_map = build_team_probability_map(simulation, name_to_id)

    matches_by_id = {
        int(row["match_id"]): row
        for _, row in matches.iterrows()
    }

    bracket_by_id = {
        int(row["match_id"]): row
        for _, row in bracket.iterrows()
    }

    projected_winners_by_match = {}
    projected_losers_by_match = {}

    bracket_matches = []

    for match_id in range(73, 105):
        match_row = matches_by_id.get(match_id)
        bracket_row = bracket_by_id.get(match_id)

        if match_row is None and bracket_row is None:
            continue

        if match_row is not None:
            stage_id = int(match_row["stage_id"])
            status = str(match_row.get("status", "Scheduled"))
            date = match_row.get("date")
            kickoff_time_utc = match_row.get("kickoff_time_utc")
            venue_id = safe_int(match_row.get("venue_id"))

            home_team_id = safe_int(match_row.get("home_team_id"))
            away_team_id = safe_int(match_row.get("away_team_id"))
            home_score = safe_float(match_row.get("home_score"))
            away_score = safe_float(match_row.get("away_score"))
        else:
            stage_id = int(bracket_row["stage_id"])
            status = str(bracket_row.get("status", "Scheduled"))
            date = bracket_row.get("date")
            kickoff_time_utc = bracket_row.get("kickoff_time_utc")
            venue_id = safe_int(bracket_row.get("venue_id"))

            home_team_id = safe_int(bracket_row.get("home_team_id"))
            away_team_id = safe_int(bracket_row.get("away_team_id"))
            home_score = None
            away_score = None

        home_source = None
        away_source = None

        if bracket_row is not None:
            home_source = {
                "source_match_id": safe_int(bracket_row.get("home_source_match_id")),
                "source_type": bracket_row.get("home_source_type"),
                "label": (
                    f"{str(bracket_row.get('home_source_type')).title()} of match "
                    f"{safe_int(bracket_row.get('home_source_match_id'))}"
                    if pd.notna(bracket_row.get("home_source_match_id"))
                    else None
                ),
            }

            away_source = {
                "source_match_id": safe_int(bracket_row.get("away_source_match_id")),
                "source_type": bracket_row.get("away_source_type"),
                "label": (
                    f"{str(bracket_row.get('away_source_type')).title()} of match "
                    f"{safe_int(bracket_row.get('away_source_match_id'))}"
                    if pd.notna(bracket_row.get("away_source_match_id"))
                    else None
                ),
            }

        # Resolve projected teams if the future match does not have fixed teams.
        if home_team_id is None and bracket_row is not None:
            home_team_id = get_most_likely_team_for_source(
                bracket_row.get("home_source_match_id"),
                bracket_row.get("home_source_type"),
                projected_winners_by_match,
                projected_losers_by_match,
            )

        if away_team_id is None and bracket_row is not None:
            away_team_id = get_most_likely_team_for_source(
                bracket_row.get("away_source_match_id"),
                bracket_row.get("away_source_type"),
                projected_winners_by_match,
                projected_losers_by_match,
            )

        winner_team_id = None
        loser_team_id = None

        is_completed = status.lower() == "completed"

        if is_completed and match_row is not None:
            winner_team_id = derive_completed_winner(match_row, winners)

            if winner_team_id is not None and home_team_id is not None and away_team_id is not None:
                loser_team_id = away_team_id if winner_team_id == home_team_id else home_team_id
        else:
            prediction = get_match_prediction_from_team_probabilities(
                home_team_id,
                away_team_id,
                team_probability_map,
            )

            if prediction is not None:
                winner_team_id = prediction["predicted_winner_team_id"]

                if home_team_id is not None and away_team_id is not None:
                    loser_team_id = away_team_id if winner_team_id == home_team_id else home_team_id

        if winner_team_id is not None:
            projected_winners_by_match[match_id] = winner_team_id

        if loser_team_id is not None:
            projected_losers_by_match[match_id] = loser_team_id

        home_probabilities = team_probability_map.get(home_team_id, {}) if home_team_id else {}
        away_probabilities = team_probability_map.get(away_team_id, {}) if away_team_id else {}

        bracket_matches.append(
            {
                "match_id": match_id,
                "stage_id": stage_id,
                "stage_name": STAGE_NAMES.get(stage_id, "Unknown"),
                "date": None if pd.isna(date) else str(date),
                "kickoff_time_utc": None if pd.isna(kickoff_time_utc) else str(kickoff_time_utc),
                "venue_id": venue_id,
                "status": status,
                "is_completed": is_completed,
                "home_team": {
                    "team_id": home_team_id,
                    "team_name": get_team_name(home_team_id, id_to_name),
                    "score": home_score,
                    "source": home_source,
                    "probabilities": home_probabilities,
                },
                "away_team": {
                    "team_id": away_team_id,
                    "team_name": get_team_name(away_team_id, id_to_name),
                    "score": away_score,
                    "source": away_source,
                    "probabilities": away_probabilities,
                },
                "winner": {
                    "team_id": winner_team_id,
                    "team_name": get_team_name(winner_team_id, id_to_name),
                    "is_projected": not is_completed,
                },
                "loser": {
                    "team_id": loser_team_id,
                    "team_name": get_team_name(loser_team_id, id_to_name),
                    "is_projected": not is_completed,
                },
            }
        )

    grouped_by_stage = defaultdict(list)

    for item in bracket_matches:
        grouped_by_stage[str(item["stage_id"])].append(item)

    return {
        "source_files": {
            "live_matches": str(LIVE_MATCHES_PATH),
            "bracket": str(BRACKET_PATH),
            "teams": str(TEAMS_PATH),
            "simulation": str(LIVE_SIMULATION_PATH),
        },
        "count": len(bracket_matches),
        "matches": bracket_matches,
        "grouped_by_stage": dict(grouped_by_stage),
    }