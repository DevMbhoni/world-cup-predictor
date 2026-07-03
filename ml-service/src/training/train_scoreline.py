from pathlib import Path
import json

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]

PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "match_training_data.csv"
SAVED_MODELS_DIR = PROJECT_ROOT / "ml-service" / "saved_models"

HOME_GOALS_MODEL_PATH = SAVED_MODELS_DIR / "home_goals_model.pkl"
AWAY_GOALS_MODEL_PATH = SAVED_MODELS_DIR / "away_goals_model.pkl"
SCORELINE_METADATA_PATH = SAVED_MODELS_DIR / "scoreline_model_metadata.json"


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

    return pd.read_csv(PROCESSED_DATA_PATH)


def time_based_split(df: pd.DataFrame, test_year: int = 2018) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_df = df[df["year"] < test_year].copy()
    test_df = df[df["year"] >= test_year].copy()

    return train_df, test_df


def build_poisson_pipeline() -> Pipeline:
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

    model = PoissonRegressor(
        alpha=0.1,
        max_iter=1000,
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

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=18,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )


def evaluate_regression_model(
    name: str,
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict:
    predictions = model.predict(X_test)

    # Goals cannot be negative.
    predictions = predictions.clip(min=0)

    mae = mean_absolute_error(y_test, predictions)
    rmse = mean_squared_error(y_test, predictions) ** 0.5

    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)
    print(f"MAE:  {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")

    preview = pd.DataFrame(
        {
            "actual": y_test.values[:10],
            "predicted": predictions[:10].round(2),
        }
    )

    print("\nPreview:")
    print(preview.to_string(index=False))

    return {
        "model_name": name,
        "mae": float(mae),
        "rmse": float(rmse),
    }


def train_target_model(
    target_column: str,
    model_label: str,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> tuple[Pipeline, dict]:
    models = {
    f"{model_label} Poisson Regressor": build_poisson_pipeline(),
    }

    best_model = None
    best_result = None

    for model_name, model in models.items():
        print(f"\nTraining {model_name}...")
        model.fit(X_train, y_train)

        result = evaluate_regression_model(
            name=model_name,
            model=model,
            X_test=X_test,
            y_test=y_test,
        )

        if best_result is None or result["rmse"] < best_result["rmse"]:
            best_result = result
            best_model = model

    return best_model, best_result


def main() -> None:
    SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_training_data()

    df = df.dropna(subset=["home_score", "away_score"]).copy()

    train_df, test_df = time_based_split(df, test_year=2018)

    print(f"Training rows: {len(train_df):,}")
    print(f"Testing rows: {len(test_df):,}")
    print(f"Training period: {train_df['year'].min()} to {train_df['year'].max()}")
    print(f"Testing period: {test_df['year'].min()} to {test_df['year'].max()}")

    X_train = train_df[FEATURE_COLUMNS]
    X_test = test_df[FEATURE_COLUMNS]

    home_model, home_result = train_target_model(
        target_column="home_score",
        model_label="Home Goals",
        X_train=X_train,
        y_train=train_df["home_score"],
        X_test=X_test,
        y_test=test_df["home_score"],
    )

    away_model, away_result = train_target_model(
        target_column="away_score",
        model_label="Away Goals",
        X_train=X_train,
        y_train=train_df["away_score"],
        X_test=X_test,
        y_test=test_df["away_score"],
    )

    joblib.dump(home_model, HOME_GOALS_MODEL_PATH)
    joblib.dump(away_model, AWAY_GOALS_MODEL_PATH)

    metadata = {
        "feature_columns": FEATURE_COLUMNS,
        "categorical_features": CATEGORICAL_FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "targets": ["home_score", "away_score"],
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "train_year_min": int(train_df["year"].min()),
        "train_year_max": int(train_df["year"].max()),
        "test_year_min": int(test_df["year"].min()),
        "test_year_max": int(test_df["year"].max()),
        "selected_home_goals_model": home_result,
        "selected_away_goals_model": away_result,
    }

    with open(SCORELINE_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("\n" + "=" * 80)
    print("Saved scoreline models")
    print("=" * 80)
    print(f"Home goals model saved to: {HOME_GOALS_MODEL_PATH}")
    print(f"Away goals model saved to: {AWAY_GOALS_MODEL_PATH}")
    print(f"Metadata saved to: {SCORELINE_METADATA_PATH}")
    print(f"Selected home model: {home_result['model_name']}")
    print(f"Selected away model: {away_result['model_name']}")


if __name__ == "__main__":
    main()