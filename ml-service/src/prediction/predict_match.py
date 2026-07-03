from pathlib import Path
import json
import sys

import joblib
import pandas as pd


CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]
PROJECT_ROOT = CURRENT_FILE.parents[3]

sys.path.append(str(SRC_DIR))

from prediction.team_name_resolver import resolve_team_name

MODEL_PATH = PROJECT_ROOT / "ml-service" / "saved_models" / "match_result_model.pkl"
METADATA_PATH = PROJECT_ROOT / "ml-service" / "saved_models" / "match_result_model_metadata.json"
TRAINING_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "match_training_data.csv"


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}\n"
            "Run: python src\\training\\train_match_result.py"
        )

    return joblib.load(MODEL_PATH)


def load_metadata() -> dict:
    if not METADATA_PATH.exists():
        raise FileNotFoundError(f"Metadata not found: {METADATA_PATH}")

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_training_data() -> pd.DataFrame:
    if not TRAINING_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Training data not found: {TRAINING_DATA_PATH}\n"
            "Run: python src\\features\\build_match_features.py"
        )

    return pd.read_csv(TRAINING_DATA_PATH)

def get_latest_team_features(df: pd.DataFrame, team_name: str, prefix: str) -> dict:
    home_rows = df[df["home_team"] == team_name].copy()
    away_rows = df[df["away_team"] == team_name].copy()

    rows = []

    for _, row in home_rows.iterrows():
        rows.append(
            {
                "date": row["date"],
                "team_matches_before": row["home_team_matches_before"],
                "avg_goals_for_last_10": row["home_avg_goals_for_last_10"],
                "avg_goals_against_last_10": row["home_avg_goals_against_last_10"],
                "avg_points_last_10": row["home_avg_points_last_10"],
                "win_rate_last_10": row["home_win_rate_last_10"],
                "clean_sheet_rate_last_10": row["home_clean_sheet_rate_last_10"],
                "failed_to_score_rate_last_10": row["home_failed_to_score_rate_last_10"],
            }
        )

    for _, row in away_rows.iterrows():
        rows.append(
            {
                "date": row["date"],
                "team_matches_before": row["away_team_matches_before"],
                "avg_goals_for_last_10": row["away_avg_goals_for_last_10"],
                "avg_goals_against_last_10": row["away_avg_goals_against_last_10"],
                "avg_points_last_10": row["away_avg_points_last_10"],
                "win_rate_last_10": row["away_win_rate_last_10"],
                "clean_sheet_rate_last_10": row["away_clean_sheet_rate_last_10"],
                "failed_to_score_rate_last_10": row["away_failed_to_score_rate_last_10"],
            }
        )

    if not rows:
        raise ValueError(f"No historical data found for team: {team_name}")

    team_df = pd.DataFrame(rows)
    team_df["date"] = pd.to_datetime(team_df["date"], errors="coerce")
    latest = team_df.sort_values("date").iloc[-1].to_dict()

    return {
        f"{prefix}_team_matches_before": latest["team_matches_before"],
        f"{prefix}_avg_goals_for_last_10": latest["avg_goals_for_last_10"],
        f"{prefix}_avg_goals_against_last_10": latest["avg_goals_against_last_10"],
        f"{prefix}_avg_points_last_10": latest["avg_points_last_10"],
        f"{prefix}_win_rate_last_10": latest["win_rate_last_10"],
        f"{prefix}_clean_sheet_rate_last_10": latest["clean_sheet_rate_last_10"],
        f"{prefix}_failed_to_score_rate_last_10": latest["failed_to_score_rate_last_10"],
    }


def build_prediction_row(
    training_df: pd.DataFrame,
    home_team: str,
    away_team: str,
    tournament: str = "FIFA World Cup",
    city: str = "Neutral",
    country: str = "United States",
    neutral: bool = True,
) -> pd.DataFrame:
    metadata = load_metadata()
    feature_columns = metadata["feature_columns"]

    home_training_name = resolve_team_name(training_df, home_team)
    away_training_name = resolve_team_name(training_df, away_team)

    home_features = get_latest_team_features(
        training_df,
        home_training_name,
        "home",
    )

    away_features = get_latest_team_features(
        training_df,
        away_training_name,
        "away",
    )

    row = {
        "home_team": home_training_name,
        "away_team": away_training_name,
        "tournament": tournament,
        "city": city,
        "country": country,
        "neutral": neutral,
    }

    row.update(home_features)
    row.update(away_features)

    # Date defaults for future match prediction.
    row["year"] = 2026
    row["month"] = 7
    row["day_of_week"] = 5

    # Ensure important rolling fields exist before calculating diffs.
    defaults = {
        "home_team_matches_before": 0,
        "away_team_matches_before": 0,

        "home_avg_goals_for_last_10": 0,
        "away_avg_goals_for_last_10": 0,

        "home_avg_goals_against_last_10": 0,
        "away_avg_goals_against_last_10": 0,

        "home_avg_points_last_10": 0,
        "away_avg_points_last_10": 0,

        "home_win_rate_last_10": 0,
        "away_win_rate_last_10": 0,

        "home_clean_sheet_rate_last_10": 0,
        "away_clean_sheet_rate_last_10": 0,

        "home_failed_to_score_rate_last_10": 0,
        "away_failed_to_score_rate_last_10": 0,
    }

    for key, value in defaults.items():
        if key not in row or pd.isna(row[key]):
            row[key] = value

    # Difference features.
    row["experience_diff"] = (
        row["home_team_matches_before"] - row["away_team_matches_before"]
    )

    row["goals_for_diff_last_10"] = (
        row["home_avg_goals_for_last_10"] - row["away_avg_goals_for_last_10"]
    )

    row["goals_against_diff_last_10"] = (
        row["home_avg_goals_against_last_10"] - row["away_avg_goals_against_last_10"]
    )

    row["points_diff_last_10"] = (
        row["home_avg_points_last_10"] - row["away_avg_points_last_10"]
    )

    row["win_rate_diff_last_10"] = (
        row["home_win_rate_last_10"] - row["away_win_rate_last_10"]
    )

    row["clean_sheet_rate_diff_last_10"] = (
        row["home_clean_sheet_rate_last_10"] - row["away_clean_sheet_rate_last_10"]
    )

    row["failed_to_score_rate_diff_last_10"] = (
        row["home_failed_to_score_rate_last_10"] - row["away_failed_to_score_rate_last_10"]
    )

    # Elo features.
    elo_path = PROJECT_ROOT / "data" / "processed" / "team_elo_ratings.csv"

    if elo_path.exists():
        elo_df = pd.read_csv(elo_path)

        if "elo_rating" in elo_df.columns:
            rating_col = "elo_rating"
        elif "rating" in elo_df.columns:
            rating_col = "rating"
        elif "current_elo" in elo_df.columns:
            rating_col = "current_elo"
        else:
            rating_col = None

        if rating_col is not None:
            home_elo_row = elo_df[elo_df["team"] == home_training_name]
            away_elo_row = elo_df[elo_df["team"] == away_training_name]

            home_elo = (
                float(home_elo_row.iloc[0][rating_col])
                if not home_elo_row.empty
                else 1500.0
            )

            away_elo = (
                float(away_elo_row.iloc[0][rating_col])
                if not away_elo_row.empty
                else 1500.0
            )
        else:
            home_elo = 1500.0
            away_elo = 1500.0
    else:
        home_elo = 1500.0
        away_elo = 1500.0

    row["home_elo_before"] = home_elo
    row["away_elo_before"] = away_elo
    row["elo_diff_before"] = home_elo - away_elo

    row["home_expected_score"] = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
    row["away_expected_score"] = 1 - row["home_expected_score"]

    prediction_df = pd.DataFrame([row])

    # Final safety: create any missing model feature.
    for col in feature_columns:
        if col not in prediction_df.columns:
            prediction_df[col] = 0

    return prediction_df[feature_columns]

def predict_match(home_team: str, away_team: str) -> dict:
    model = load_model()
    training_df = load_training_data()

    X = build_prediction_row(
        training_df=training_df,
        home_team=home_team,
        away_team=away_team,
    )

    probabilities = model.predict_proba(X)[0]
    classes = model.classes_

    result_probs = {
        label: round(float(prob), 4)
        for label, prob in zip(classes, probabilities)
    }

    predicted_result = max(result_probs, key=result_probs.get)

    return {
        "home_team": home_team,
        "away_team": away_team,
        "predicted_result": predicted_result,
        "probabilities": result_probs,
    }


if __name__ == "__main__":
    result = predict_match("Canada", "Morocco")

    print("\nMatch prediction")
    print("=" * 80)
    print(f"{result['home_team']} vs {result['away_team']}")
    print(f"Predicted result: {result['predicted_result']}")

    print("\nProbabilities:")
    for label, probability in result["probabilities"].items():
        print(f"{label}: {probability:.2%}")