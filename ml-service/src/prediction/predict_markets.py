from pathlib import Path
import json
import sys

import joblib
import pandas as pd


CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]
PROJECT_ROOT = CURRENT_FILE.parents[3]

sys.path.append(str(SRC_DIR))

from prediction.predict_match import build_prediction_row


SAVED_MODELS_DIR = PROJECT_ROOT / "ml-service" / "saved_models"
MARKET_METADATA_PATH = SAVED_MODELS_DIR / "market_models_metadata.json"
TRAINING_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "match_training_data.csv"


def load_training_data() -> pd.DataFrame:
    if not TRAINING_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Training data not found: {TRAINING_DATA_PATH}\n"
            "Run: python src\\features\\build_match_features.py"
        )

    return pd.read_csv(TRAINING_DATA_PATH)


def load_market_metadata() -> dict:
    if not MARKET_METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Market metadata not found: {MARKET_METADATA_PATH}\n"
            "Run: python src\\training\\train_market_models.py"
        )

    with open(MARKET_METADATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def predict_markets(home_team: str, away_team: str) -> dict:
    metadata = load_market_metadata()
    training_df = load_training_data()

    X = build_prediction_row(
        training_df=training_df,
        home_team=home_team,
        away_team=away_team,
    )

    predictions = {}

    for target_column, target_info in metadata["targets"].items():
        model_path = SAVED_MODELS_DIR / target_info["file_name"]

        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        model = joblib.load(model_path)
        probability = float(model.predict_proba(X)[0][1])

        predictions[target_column] = {
            "label": target_info["positive_label"],
            "probability": probability,
        }

    return {
        "home_team": home_team,
        "away_team": away_team,
        "markets": predictions,
    }


if __name__ == "__main__":
    result = predict_markets("Brazil", "Germany")

    print("\nMarket prediction")
    print("=" * 80)
    print(f"{result['home_team']} vs {result['away_team']}")

    print("\nMarkets:")
    for key, value in result["markets"].items():
        print(f"{value['label']}: {value['probability']:.2%}")