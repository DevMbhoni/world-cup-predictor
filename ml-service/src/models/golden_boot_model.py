from pathlib import Path
import pandas as pd
import numpy as np


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]

RAW_2026_DIR = PROJECT_ROOT / "data" / "raw" / "worldcup_2026"
PREDICTIONS_DIR = PROJECT_ROOT / "data" / "predictions"

SQUADS_PATH = RAW_2026_DIR / "squads_and_players.csv"
PLAYER_STATS_PATH = RAW_2026_DIR / "player_stats.csv"
TEAMS_PATH = RAW_2026_DIR / "teams.csv"
LIVE_TOURNAMENT_RESULTS_PATH = PREDICTIONS_DIR / "live_tournament_simulation_results.csv"

OUTPUT_PATH = PREDICTIONS_DIR / "golden_boot_predictions.csv"


ATTACKING_POSITION_WEIGHTS = {
    "Forward": 1.00,
    "FW": 1.00,
    "Striker": 1.00,
    "Winger": 0.90,
    "Midfielder": 0.45,
    "MF": 0.45,
    "Defender": 0.12,
    "DF": 0.12,
    "Goalkeeper": 0.01,
    "GK": 0.01,
}


def normalize_position(position: str) -> str:
    position = str(position).strip()

    if position in ATTACKING_POSITION_WEIGHTS:
        return position

    lowered = position.lower()

    if "forward" in lowered or "striker" in lowered or "winger" in lowered:
        return "Forward"

    if "mid" in lowered:
        return "Midfielder"

    if "def" in lowered or "back" in lowered:
        return "Defender"

    if "keeper" in lowered or "goalkeeper" in lowered:
        return "Goalkeeper"

    return position


def get_position_weight(position: str) -> float:
    normalized = normalize_position(position)
    return ATTACKING_POSITION_WEIGHTS.get(normalized, 0.25)


def load_golden_boot_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    squads = pd.read_csv(SQUADS_PATH)
    player_stats = pd.read_csv(PLAYER_STATS_PATH)
    teams = pd.read_csv(TEAMS_PATH)

    if not LIVE_TOURNAMENT_RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Live tournament results not found: {LIVE_TOURNAMENT_RESULTS_PATH}\n"
            "Run: python src\\simulation\\simulate_live_tournament.py"
        )

    tournament_results = pd.read_csv(LIVE_TOURNAMENT_RESULTS_PATH)

    return squads, player_stats, teams, tournament_results


def build_player_golden_boot_features() -> pd.DataFrame:
    squads, player_stats, teams, tournament_results = load_golden_boot_data()

    teams = teams[["team_id", "team_name"]].copy()

    players = squads.merge(
        player_stats,
        on=["player_id", "team_id"],
        how="left",
        suffixes=("", "_stats"),
    )

    # IMPORTANT:
    # squads_and_players.csv has career/international goals.
    # player_stats.csv has tournament goals after merge as goals_stats.
    # Golden Boot must use tournament goals.
    if "goals_stats" in players.columns:
        players["tournament_goals"] = players["goals_stats"]
    else:
        players["tournament_goals"] = players.get("goals", 0)

    if "assists_stats" in players.columns:
        players["tournament_assists"] = players["assists_stats"]
    else:
        players["tournament_assists"] = players.get("assists", 0)

    if "penalty_scored_stats" in players.columns:
        players["tournament_penalties"] = players["penalty_scored_stats"]
    else:
        players["tournament_penalties"] = players.get("penalty_scored", 0)
    
    players = players.merge(teams, on="team_id", how="left")

    tournament_results = tournament_results.rename(
        columns={
            "team": "team_name",
            "winner_probability": "team_winner_probability",
            "final_probability": "team_final_probability",
            "semi_final_probability": "team_semi_final_probability",
            "quarter_final_probability": "team_quarter_final_probability",
            "round_of_16_probability": "team_round_of_16_probability",
        }
    )

    keep_cols = [
        "team_name",
        "status",
        "team_winner_probability",
        "team_final_probability",
        "team_semi_final_probability",
        "team_quarter_final_probability",
        "team_round_of_16_probability",
    ]

    existing_cols = [col for col in keep_cols if col in tournament_results.columns]

    players = players.merge(
        tournament_results[existing_cols],
        on="team_name",
        how="left",
    )

    numeric_defaults = {
        "tournament_goals": 0,
        "tournament_assists": 0,
        "matches_played": 0,
        "matches_started": 0,
        "minutes_played": 0,
        "tournament_penalties": 0,
        "yellow_cards": 0,
        "red_cards": 0,
        "team_winner_probability": 0,
        "team_final_probability": 0,
        "team_semi_final_probability": 0,
        "team_quarter_final_probability": 0,
        "team_round_of_16_probability": 0,
        "market_value_eur": 0,
        "caps": 0,
    }

    for col, default_value in numeric_defaults.items():
        if col not in players.columns:
            players[col] = default_value

        players[col] = players[col].fillna(default_value)

    if "status" not in players.columns:
        players["status"] = "Unknown"

    players["status"] = players["status"].fillna("Unknown")

    players["position_weight"] = players["position"].apply(get_position_weight)

    players["raw_goals_per_90"] = np.where(
        players["minutes_played"] > 0,
        players["tournament_goals"] / players["minutes_played"] * 90,
        0,
    )

    # Reduce the impact of tiny sample sizes.
    players["minutes_reliability"] = np.minimum(players["minutes_played"] / 180, 1)

    players["goals_per_90"] = (
        players["raw_goals_per_90"] * players["minutes_reliability"]
    )

    # Cap extreme values.
    players["goals_per_90"] = players["goals_per_90"].clip(upper=3.0)

    players["starts_rate"] = np.where(
        players["matches_played"] > 0,
        players["matches_started"] / players["matches_played"],
        0,
    )

    players["team_progression_score"] = (
        players["team_round_of_16_probability"] * 0.15
        + players["team_quarter_final_probability"] * 0.20
        + players["team_semi_final_probability"] * 0.25
        + players["team_final_probability"] * 0.25
        + players["team_winner_probability"] * 0.15
    )

    players["availability_factor"] = np.where(
        players["status"] == "Active",
        1,
        0,
    )

    players["scoring_profile_score"] = (
        players["tournament_goals"] * 5.0
        + players["goals_per_90"] * 1.0
        + players["tournament_penalties"] * 0.5
        + players["starts_rate"] * 1.0
        + players["position_weight"] * 1.5
        + np.log1p(players["market_value_eur"]) * 0.05
        + np.log1p(players["caps"]) * 0.10
    )

    players["golden_boot_score"] = (
        players["scoring_profile_score"]
        * (1 + players["team_progression_score"])
        * players["availability_factor"]
    )

    players["golden_boot_score"] = players["golden_boot_score"].clip(lower=0)

    total_score = players["golden_boot_score"].sum()

    if total_score > 0:
        players["golden_boot_probability"] = players["golden_boot_score"] / total_score
    else:
        players["golden_boot_probability"] = 0

    output_cols = [
        "player_id",
        "player_name",
        "team_id",
        "team_name",
        "position",
        "status",
        "matches_played",
        "matches_started",
        "minutes_played",
        "tournament_goals",
        "tournament_assists",
        "tournament_penalties",
        "goals_per_90",
        "team_winner_probability",
        "team_final_probability",
        "team_semi_final_probability",
        "team_quarter_final_probability",
        "team_progression_score",
        "golden_boot_score",
        "golden_boot_probability",
    ]

    output_cols = [col for col in output_cols if col in players.columns]

    result = players[output_cols].copy()
    result = result.sort_values(
        ["golden_boot_probability", "tournament_goals", "team_final_probability"],
        ascending=False,
    ).reset_index(drop=True)

    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    return result


def print_golden_boot_predictions(predictions: pd.DataFrame, top_n: int = 25) -> None:
    display = predictions.head(top_n).copy()

    percentage_cols = [
        "golden_boot_probability",
        "team_winner_probability",
        "team_final_probability",
        "team_semi_final_probability",
        "team_quarter_final_probability",
        "team_progression_score",
    ]

    for col in percentage_cols:
        if col in display.columns:
            display[col] = (display[col] * 100).round(2)

    if "goals_per_90" in display.columns:
        display["goals_per_90"] = display["goals_per_90"].round(2)

    if "golden_boot_score" in display.columns:
        display["golden_boot_score"] = display["golden_boot_score"].round(2)

    print("\nGolden Boot Predictions")
    print("=" * 120)
    print(display.to_string(index=False))
    print(f"\nSaved predictions to: {OUTPUT_PATH}")


if __name__ == "__main__":
    predictions = build_player_golden_boot_features()
    print_golden_boot_predictions(predictions, top_n=25)