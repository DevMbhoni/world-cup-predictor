from pathlib import Path
import json

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]

PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "match_training_data.csv"
SAVED_MODELS_DIR = PROJECT_ROOT / "ml-service" / "saved_models"

MARKET_METADATA_PATH = SAVED_MODELS_DIR / "market_models_metadata.json"


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


TARGETS = {
    "over_2_5": {
        "file_name": "over_2_5_model.pkl",
        "positive_label": "Over 2.5 goals",
    },
    "both_teams_score": {
        "file_name": "btts_model.pkl",
        "positive_label": "Both teams score",
    },
    "home_clean_sheet": {
        "file_name": "home_clean_sheet_model.pkl",
        "positive_label": "Home clean sheet",
    },
    "away_clean_sheet": {
        "file_name": "away_clean_sheet_model.pkl",
        "positive_label": "Away clean sheet",
    },
}


def load_training_data() -> pd.DataFrame:
    if not PROCESSED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Training data not found: {PROCESSED_DATA_PATH}\n"
            "Run: python src\\features\\build_match_features.py"
        )

    return pd.read_csv(PROCESSED_DATA_PATH)


def time_based_split(df: pd.DataFrame, test_year: int = 2018) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_df = df[df["year"] < test_year].copy()
    test_df = df[df["year"] >= test_year].copy()

    return train_df, test_df


def build_logistic_pipeline() -> Pipeline:
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
        n_estimators=200,
        max_depth=16,
        min_samples_leaf=8,
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


def evaluate_binary_model(
    name: str,
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict:
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, predictions)
    loss = log_loss(y_test, probabilities)
    auc = roc_auc_score(y_test, probabilities)

    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Log loss: {loss:.4f}")
    print(f"ROC AUC:  {auc:.4f}")

    print("\nClassification report:")
    print(classification_report(y_test, predictions))

    return {
        "model_name": name,
        "accuracy": float(accuracy),
        "log_loss": float(loss),
        "roc_auc": float(auc),
    }


def train_market_model(
    target_column: str,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> tuple[Pipeline, dict]:
    models = {
        f"{target_column} Logistic Regression": build_logistic_pipeline(),
        f"{target_column} Random Forest": build_random_forest_pipeline(),
    }

    best_model = None
    best_result = None

    for model_name, model in models.items():
        print(f"\nTraining {model_name}...")
        model.fit(X_train, y_train)

        result = evaluate_binary_model(
            name=model_name,
            model=model,
            X_test=X_test,
            y_test=y_test,
        )

        if best_result is None or result["log_loss"] < best_result["log_loss"]:
            best_result = result
            best_model = model

    return best_model, best_result


def main() -> None:
    SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_training_data()
    train_df, test_df = time_based_split(df, test_year=2018)

    print(f"Training rows: {len(train_df):,}")
    print(f"Testing rows: {len(test_df):,}")
    print(f"Training period: {train_df['year'].min()} to {train_df['year'].max()}")
    print(f"Testing period: {test_df['year'].min()} to {test_df['year'].max()}")

    X_train = train_df[FEATURE_COLUMNS]
    X_test = test_df[FEATURE_COLUMNS]

    metadata = {
        "feature_columns": FEATURE_COLUMNS,
        "categorical_features": CATEGORICAL_FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "targets": {},
    }

    for target_column, target_config in TARGETS.items():
        print("\n" + "#" * 80)
        print(f"Training market target: {target_column}")
        print("#" * 80)

        y_train = train_df[target_column]
        y_test = test_df[target_column]

        model, result = train_market_model(
            target_column=target_column,
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
        )

        model_path = SAVED_MODELS_DIR / target_config["file_name"]
        joblib.dump(model, model_path)

        metadata["targets"][target_column] = {
            "file_name": target_config["file_name"],
            "positive_label": target_config["positive_label"],
            "selected_model": result,
        }

        print(f"\nSaved {target_column} model to: {model_path}")

    with open(MARKET_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("\n" + "=" * 80)
    print("Saved market model metadata")
    print("=" * 80)
    print(f"Metadata saved to: {MARKET_METADATA_PATH}")


if __name__ == "__main__":
    main()