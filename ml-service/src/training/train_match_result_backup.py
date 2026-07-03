from pathlib import Path
import json
import sys

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]

PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "match_training_data.csv"
SAVED_MODELS_DIR = PROJECT_ROOT / "ml-service" / "saved_models"

MATCH_MODEL_PATH = SAVED_MODELS_DIR / "match_result_model.pkl"
MATCH_METADATA_PATH = SAVED_MODELS_DIR / "match_result_model_metadata.json"


TARGET = "result"


FEATURE_COLUMNS = [
    "home_team",
    "away_team",
    "tournament",
    "country",
    "neutral",
    "year",
    "month",
    "day_of_week",

    "home_team_matches_before",
    "home_avg_goals_for_last_10",
    "home_avg_goals_against_last_10",
    "home_avg_points_last_10",
    "home_win_rate_last_10",
    "home_clean_sheet_rate_last_10",
    "home_failed_to_score_rate_last_10",

    "away_team_matches_before",
    "away_avg_goals_for_last_10",
    "away_avg_goals_against_last_10",
    "away_avg_points_last_10",
    "away_win_rate_last_10",
    "away_clean_sheet_rate_last_10",
    "away_failed_to_score_rate_last_10",

    "experience_diff",
    "goals_for_diff_last_10",
    "goals_against_diff_last_10",
    "points_diff_last_10",
    "win_rate_diff_last_10",
    "clean_sheet_rate_diff_last_10",
    "failed_to_score_rate_diff_last_10",

    "home_elo_before",
    "away_elo_before",
    "elo_diff_before",
    "home_expected_score",
    "away_expected_score",
]


CATEGORICAL_FEATURES = [
    "home_team",
    "away_team",
    "tournament",
    "country",
]


NUMERIC_FEATURES = [
    col for col in FEATURE_COLUMNS if col not in CATEGORICAL_FEATURES
]


def load_training_data() -> pd.DataFrame:
    if not PROCESSED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Training data not found: {PROCESSED_DATA_PATH}\n"
            "Run: python src\\features\\build_match_features.py"
        )

    df = pd.read_csv(PROCESSED_DATA_PATH)
    return df


def time_based_split(df: pd.DataFrame, test_year: int = 2018) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Uses older matches for training and newer matches for testing.
    This is better than random split because football data is time-based.
    """

    train_df = df[df["year"] < test_year].copy()
    test_df = df[df["year"] >= test_year].copy()

    return train_df, test_df


def build_logistic_regression_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                StandardScaler(),
                NUMERIC_FEATURES,
            ),
        ]
    )

    model = LogisticRegression(
    max_iter=2000,
    class_weight="balanced",
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )


def build_random_forest_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                "passthrough",
                NUMERIC_FEATURES,
            ),
        ]
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=18,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )


def evaluate_model(name: str, model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)

    accuracy = accuracy_score(y_test, predictions)
    loss = log_loss(y_test, probabilities, labels=model.classes_)

    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Log loss: {loss:.4f}")

    print("\nClassification report:")
    print(classification_report(y_test, predictions))

    print("Confusion matrix:")
    print(confusion_matrix(y_test, predictions, labels=model.classes_))

    return {
        "model_name": name,
        "accuracy": float(accuracy),
        "log_loss": float(loss),
        "classes": list(model.classes_),
    }


def main() -> None:
    SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_training_data()

    df = df.dropna(subset=[TARGET]).copy()

    train_df, test_df = time_based_split(df, test_year=2018)

    print(f"Training rows: {len(train_df):,}")
    print(f"Testing rows: {len(test_df):,}")
    print(f"Training period: {train_df['year'].min()} to {train_df['year'].max()}")
    print(f"Testing period: {test_df['year'].min()} to {test_df['year'].max()}")

    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[TARGET]

    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[TARGET]

    models = {
        "Logistic Regression": build_logistic_regression_pipeline(),
        "Random Forest": build_random_forest_pipeline(),
    }

    results = []

    best_model = None
    best_result = None

    for model_name, model in models.items():
        print(f"\nTraining {model_name}...")
        model.fit(X_train, y_train)

        result = evaluate_model(model_name, model, X_test, y_test)
        results.append(result)

        if best_result is None or result["log_loss"] < best_result["log_loss"]:
            best_result = result
            best_model = model

    joblib.dump(best_model, MATCH_MODEL_PATH)

    metadata = {
        "target": TARGET,
        "feature_columns": FEATURE_COLUMNS,
        "categorical_features": CATEGORICAL_FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "train_year_min": int(train_df["year"].min()),
        "train_year_max": int(train_df["year"].max()),
        "test_year_min": int(test_df["year"].min()),
        "test_year_max": int(test_df["year"].max()),
        "model_results": results,
        "selected_model": best_result,
    }

    with open(MATCH_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("\n" + "=" * 80)
    print("Saved model")
    print("=" * 80)
    print(f"Model saved to: {MATCH_MODEL_PATH}")
    print(f"Metadata saved to: {MATCH_METADATA_PATH}")
    print(f"Selected model: {best_result['model_name']}")
    print(f"Selected model log loss: {best_result['log_loss']:.4f}")


if __name__ == "__main__":
    main()