from pathlib import Path
import json
import sys

import joblib
import pandas as pd

from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]

DATA_PATH = PROJECT_ROOT / "data" / "processed" / "match_training_data.csv"
MODEL_DIR = PROJECT_ROOT / "ml-service" / "saved_models"

MODEL_PATH = MODEL_DIR / "match_result_model.pkl"
METADATA_PATH = MODEL_DIR / "match_result_model_metadata.json"


TARGET_COLUMN = "result"


CATEGORICAL_FEATURES = [
    "home_team",
    "away_team",
    "tournament",
    "city",
    "country",
]


NUMERIC_FEATURES = [
    "neutral",
    "year",
    "month",
    "day_of_week",

    "home_team_matches_before",
    "away_team_matches_before",

    "home_avg_goals_for_last_10",
    "away_avg_goals_for_last_10",

    "home_avg_goals_against_last_10",
    "away_avg_goals_against_last_10",

    "home_avg_points_last_10",
    "away_avg_points_last_10",

    "home_win_rate_last_10",
    "away_win_rate_last_10",

    "home_clean_sheet_rate_last_10",
    "away_clean_sheet_rate_last_10",

    "home_failed_to_score_rate_last_10",
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


def load_training_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Training data not found: {DATA_PATH}\n"
            "Run: python src\\features\\build_match_features.py"
        )

    df = pd.read_csv(DATA_PATH)

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found.")

    if "year" not in df.columns:
        raise ValueError("Column 'year' not found. Rebuild match features.")

    return df


def select_existing_features(df: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
    categorical_features = [
        col for col in CATEGORICAL_FEATURES
        if col in df.columns
    ]

    numeric_features = [
        col for col in NUMERIC_FEATURES
        if col in df.columns
    ]

    feature_columns = categorical_features + numeric_features

    if not feature_columns:
        raise ValueError("No usable feature columns found.")

    return feature_columns, categorical_features, numeric_features


def prepare_data(df: pd.DataFrame, feature_columns: list[str]) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    df = df.copy()

    df = df.dropna(subset=[TARGET_COLUMN])

    train_df = df[df["year"] < 2018].copy()
    test_df = df[df["year"] >= 2018].copy()

    if train_df.empty or test_df.empty:
        raise ValueError("Train/test split failed. Check the year column.")

    X_train = train_df[feature_columns].copy()
    y_train = train_df[TARGET_COLUMN].copy()

    X_test = test_df[feature_columns].copy()
    y_test = test_df[TARGET_COLUMN].copy()

    return X_train, y_train, X_test, y_test


def build_preprocessor(
    categorical_features: list[str],
    numeric_features: list[str],
) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features,
            ),
            (
                "numeric",
                StandardScaler(),
                numeric_features,
            ),
        ],
        remainder="drop",
    )


def build_logistic_regression_pipeline(
    categorical_features: list[str],
    numeric_features: list[str],
) -> Pipeline:
    preprocessor = build_preprocessor(
        categorical_features=categorical_features,
        numeric_features=numeric_features,
    )

    model = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        solver="lbfgs",
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )


def build_random_forest_pipeline(
    categorical_features: list[str],
    numeric_features: list[str],
) -> Pipeline:
    preprocessor = build_preprocessor(
        categorical_features=categorical_features,
        numeric_features=numeric_features,
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=18,
        min_samples_split=8,
        min_samples_leaf=3,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )


def build_calibrated_random_forest_pipeline(
    categorical_features: list[str],
    numeric_features: list[str],
) -> CalibratedClassifierCV:
    rf_pipeline = build_random_forest_pipeline(
        categorical_features=categorical_features,
        numeric_features=numeric_features,
    )

    calibrated_model = CalibratedClassifierCV(
        estimator=rf_pipeline,
        method="sigmoid",
        cv=3,
    )

    return calibrated_model


def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series, model_name: str) -> dict:
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    labels = list(model.classes_)

    accuracy = accuracy_score(y_test, y_pred)
    model_log_loss = log_loss(y_test, y_proba, labels=labels)

    print(f"\n── {model_name} ────────────────────────")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Log loss: {model_log_loss:.4f}")
    print("\nClassification report:")
    print(classification_report(y_test, y_pred))

    return {
        "model_name": model_name,
        "accuracy": accuracy,
        "log_loss": model_log_loss,
        "labels": labels,
    }


def train_models() -> None:
    df = load_training_data()

    feature_columns, categorical_features, numeric_features = select_existing_features(df)

    X_train, y_train, X_test, y_test = prepare_data(
        df=df,
        feature_columns=feature_columns,
    )

    print(f"Training rows: {len(X_train):,}")
    print(f"Testing rows: {len(X_test):,}")
    print(f"Features used: {len(feature_columns)}")
    print(f"Classes: {sorted(y_train.unique().tolist())}")

    models = {
        "Logistic Regression": build_logistic_regression_pipeline(
            categorical_features=categorical_features,
            numeric_features=numeric_features,
        ),
        "Random Forest": build_random_forest_pipeline(
            categorical_features=categorical_features,
            numeric_features=numeric_features,
        ),
        "Calibrated Random Forest": build_calibrated_random_forest_pipeline(
            categorical_features=categorical_features,
            numeric_features=numeric_features,
        ),
    }

    results = []
    trained_models = {}

    for model_name, model in models.items():
        print(f"\nTraining {model_name}...")
        model.fit(X_train, y_train)

        evaluation = evaluate_model(
            model=model,
            X_test=X_test,
            y_test=y_test,
            model_name=model_name,
        )

        results.append(evaluation)
        trained_models[model_name] = model

    # Lower log loss is better for probability reliability.
    best_result = sorted(results, key=lambda item: item["log_loss"])[0]
    best_model_name = best_result["model_name"]
    best_model = trained_models[best_model_name]

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(best_model, MODEL_PATH)

    metadata = {
        "selected_model": best_model_name,
        "selection_metric": "log_loss",
        "accuracy": best_result["accuracy"],
        "log_loss": best_result["log_loss"],
        "classes": best_result["labels"],
        "target_column": TARGET_COLUMN,
        "feature_columns": feature_columns,
        "categorical_features": categorical_features,
        "numeric_features": numeric_features,
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "time_split": {
            "train": "year < 2018",
            "test": "year >= 2018",
        },
        "calibration": {
            "included": True,
            "method": "sigmoid",
            "cv": 3,
            "note": "Best model is selected by log loss, not accuracy.",
        },
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)

    print("\nBest model")
    print("=" * 60)
    print(f"Selected: {best_model_name}")
    print(f"Accuracy: {best_result['accuracy']:.4f}")
    print(f"Log loss: {best_result['log_loss']:.4f}")
    print(f"Saved model to: {MODEL_PATH}")
    print(f"Saved metadata to: {METADATA_PATH}")


if __name__ == "__main__":
    train_models()