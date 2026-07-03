from pathlib import Path
import json
import sys

import joblib
import pandas as pd


CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]
PROJECT_ROOT = CURRENT_FILE.parents[3]

sys.path.append(str(SRC_DIR))

from models.scoreline_model import predict_scorelines_from_expected_goals
from prediction.predict_match import build_prediction_row


HOME_GOALS_MODEL_PATH = PROJECT_ROOT / "ml-service" / "saved_models" / "home_goals_model.pkl"
AWAY_GOALS_MODEL_PATH = PROJECT_ROOT / "ml-service" / "saved_models" / "away_goals_model.pkl"
SCORELINE_METADATA_PATH = PROJECT_ROOT / "ml-service" / "saved_models" / "scoreline_model_metadata.json"
TRAINING_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "match_training_data.csv"


def load_scoreline_models():
    if not HOME_GOALS_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Home goals model not found: {HOME_GOALS_MODEL_PATH}\n"
            "Run: python src\\training\\train_scoreline.py"
        )

    if not AWAY_GOALS_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Away goals model not found: {AWAY_GOALS_MODEL_PATH}\n"
            "Run: python src\\training\\train_scoreline.py"
        )

    home_model = joblib.load(HOME_GOALS_MODEL_PATH)
    away_model = joblib.load(AWAY_GOALS_MODEL_PATH)

    return home_model, away_model


def load_training_data() -> pd.DataFrame:
    if not TRAINING_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Training data not found: {TRAINING_DATA_PATH}\n"
            "Run: python src\\features\\build_match_features.py"
        )

    return pd.read_csv(TRAINING_DATA_PATH)


def predict_scoreline(home_team: str, away_team: str) -> dict:
    home_model, away_model = load_scoreline_models()
    training_df = load_training_data()

    X = build_prediction_row(
        training_df=training_df,
        home_team=home_team,
        away_team=away_team,
    )

    home_expected_goals = float(home_model.predict(X)[0])
    away_expected_goals = float(away_model.predict(X)[0])

    home_expected_goals = max(0, home_expected_goals)
    away_expected_goals = max(0, away_expected_goals)

    scoreline_result = predict_scorelines_from_expected_goals(
        home_expected_goals=home_expected_goals,
        away_expected_goals=away_expected_goals,
        max_goals=6,
        top_n=10,
    )

    return {
        "home_team": home_team,
        "away_team": away_team,
        **scoreline_result,
    }


if __name__ == "__main__":
    result = predict_scoreline("Brazil", "Germany")

    print("\nScoreline prediction")
    print("=" * 80)
    print(f"{result['home_team']} vs {result['away_team']}")

    print("\nExpected goals:")
    print(f"{result['home_team']}: {result['home_expected_goals']:.2f}")
    print(f"{result['away_team']}: {result['away_expected_goals']:.2f}")

    print("\nTop scorelines:")
    for row in result["top_scorelines"]:
        print(f"{row['scoreline']}: {row['probability']:.2%}")

    markets = result["markets"]

    print("\nMarkets:")
    print(f"{result['home_team']} win: {markets['home_win_probability']:.2%}")
    print(f"Draw: {markets['draw_probability']:.2%}")
    print(f"{result['away_team']} win: {markets['away_win_probability']:.2%}")
    print(f"Over 1.5: {markets['over_1_5_probability']:.2%}")
    print(f"Over 2.5: {markets['over_2_5_probability']:.2%}")
    print(f"Over 3.5: {markets['over_3_5_probability']:.2%}")
    print(f"Both teams to score: {markets['both_teams_score_probability']:.2%}")
    print(f"{result['home_team']} clean sheet: {markets['home_clean_sheet_probability']:.2%}")
    print(f"{result['away_team']} clean sheet: {markets['away_clean_sheet_probability']:.2%}")