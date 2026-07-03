from pathlib import Path
import sys
import pandas as pd
import numpy as np

CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]
PROJECT_ROOT = CURRENT_FILE.parents[3]

sys.path.append(str(SRC_DIR))

from data.load_data import load_historic_data


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "match_training_data.csv"


def get_result_label(home_score: int, away_score: int) -> str:
    if home_score > away_score:
        return "HOME_WIN"
    if home_score < away_score:
        return "AWAY_WIN"
    return "DRAW"


def add_basic_targets(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)

    df["result"] = df.apply(
        lambda row: get_result_label(row["home_score"], row["away_score"]),
        axis=1,
    )

    df["home_win"] = (df["result"] == "HOME_WIN").astype(int)
    df["draw"] = (df["result"] == "DRAW").astype(int)
    df["away_win"] = (df["result"] == "AWAY_WIN").astype(int)

    df["total_goals"] = df["home_score"] + df["away_score"]
    df["goal_difference"] = df["home_score"] - df["away_score"]

    df["over_1_5"] = (df["total_goals"] > 1.5).astype(int)
    df["over_2_5"] = (df["total_goals"] > 2.5).astype(int)
    df["over_3_5"] = (df["total_goals"] > 3.5).astype(int)

    df["both_teams_score"] = (
        (df["home_score"] > 0) & (df["away_score"] > 0)
    ).astype(int)

    df["home_clean_sheet"] = (df["away_score"] == 0).astype(int)
    df["away_clean_sheet"] = (df["home_score"] == 0).astype(int)

    return df


def add_date_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day_of_week"] = df["date"].dt.dayofweek

    return df


def build_team_history_features(df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """
    Creates pre-match rolling team features.

    Uses match_key so merges do not duplicate rows when one team has multiple
    matches on the same date.
    """

    df = df.copy()
    df = df.sort_values(["date", "match_key"]).reset_index(drop=True)

    home_rows = df[
        [
            "match_key",
            "date",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "result",
        ]
    ].copy()

    home_rows = home_rows.rename(
        columns={
            "home_team": "team",
            "away_team": "opponent",
            "home_score": "goals_for",
            "away_score": "goals_against",
        }
    )

    home_rows["side"] = "home"
    home_rows["is_home"] = 1
    home_rows["points"] = np.select(
        [
            home_rows["result"] == "HOME_WIN",
            home_rows["result"] == "DRAW",
            home_rows["result"] == "AWAY_WIN",
        ],
        [3, 1, 0],
    )

    away_rows = df[
        [
            "match_key",
            "date",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "result",
        ]
    ].copy()

    away_rows = away_rows.rename(
        columns={
            "away_team": "team",
            "home_team": "opponent",
            "away_score": "goals_for",
            "home_score": "goals_against",
        }
    )

    away_rows["side"] = "away"
    away_rows["is_home"] = 0
    away_rows["points"] = np.select(
        [
            away_rows["result"] == "AWAY_WIN",
            away_rows["result"] == "DRAW",
            away_rows["result"] == "HOME_WIN",
        ],
        [3, 1, 0],
    )

    long_df = pd.concat([home_rows, away_rows], ignore_index=True)
    long_df = long_df.sort_values(["team", "date", "match_key"]).reset_index(drop=True)

    feature_groups = []

    for team, group in long_df.groupby("team", sort=False):
        group = group.copy()

        group["team_matches_before"] = np.arange(len(group))

        group["avg_goals_for_last_10"] = (
            group["goals_for"].shift(1).rolling(window, min_periods=1).mean()
        )
        group["avg_goals_against_last_10"] = (
            group["goals_against"].shift(1).rolling(window, min_periods=1).mean()
        )
        group["avg_points_last_10"] = (
            group["points"].shift(1).rolling(window, min_periods=1).mean()
        )
        group["win_rate_last_10"] = (
            (group["points"] == 3)
            .astype(int)
            .shift(1)
            .rolling(window, min_periods=1)
            .mean()
        )
        group["clean_sheet_rate_last_10"] = (
            (group["goals_against"] == 0)
            .astype(int)
            .shift(1)
            .rolling(window, min_periods=1)
            .mean()
        )
        group["failed_to_score_rate_last_10"] = (
            (group["goals_for"] == 0)
            .astype(int)
            .shift(1)
            .rolling(window, min_periods=1)
            .mean()
        )

        feature_groups.append(group)

    features_long = pd.concat(feature_groups, ignore_index=True)

    feature_cols = [
        "match_key",
        "side",
        "team_matches_before",
        "avg_goals_for_last_10",
        "avg_goals_against_last_10",
        "avg_points_last_10",
        "win_rate_last_10",
        "clean_sheet_rate_last_10",
        "failed_to_score_rate_last_10",
    ]

    features_long = features_long[feature_cols]

    home_features = features_long[features_long["side"] == "home"].drop(columns=["side"])
    away_features = features_long[features_long["side"] == "away"].drop(columns=["side"])

    home_features = home_features.add_prefix("home_")
    away_features = away_features.add_prefix("away_")

    df = df.merge(
        home_features,
        left_on="match_key",
        right_on="home_match_key",
        how="left",
        validate="one_to_one",
    )

    df = df.merge(
        away_features,
        left_on="match_key",
        right_on="away_match_key",
        how="left",
        validate="one_to_one",
    )

    df = df.drop(columns=["home_match_key", "away_match_key"], errors="ignore")

    return df


def add_difference_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    diff_pairs = [
        ("team_matches_before", "experience_diff"),
        ("avg_goals_for_last_10", "goals_for_diff_last_10"),
        ("avg_goals_against_last_10", "goals_against_diff_last_10"),
        ("avg_points_last_10", "points_diff_last_10"),
        ("win_rate_last_10", "win_rate_diff_last_10"),
        ("clean_sheet_rate_last_10", "clean_sheet_rate_diff_last_10"),
        ("failed_to_score_rate_last_10", "failed_to_score_rate_diff_last_10"),
    ]

    for base_col, diff_col in diff_pairs:
        home_col = f"home_{base_col}"
        away_col = f"away_{base_col}"

        if home_col in df.columns and away_col in df.columns:
            df[diff_col] = df[home_col] - df[away_col]

    return df

def add_elo_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds pre-match Elo features.

    Uses match_key to avoid duplicate merge problems when the same teams play
    more than once on the same date.
    """

    from models.elo_model import calculate_elo_ratings

    base_results = df[
        [
            "match_key",
            "date",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "tournament",
            "city",
            "country",
            "neutral",
        ]
    ].copy()

    elo_history = calculate_elo_ratings(base_results)

    elo_features = elo_history[
        [
            "match_key",
            "home_elo_before",
            "away_elo_before",
            "elo_diff_before",
            "home_expected_score",
            "away_expected_score",
        ]
    ].copy()

    df = df.merge(
        elo_features,
        on="match_key",
        how="left",
        validate="one_to_one",
    )

    return df

def build_match_training_data() -> pd.DataFrame:
    historic = load_historic_data()
    results = historic["results"].copy()

    print(f"Original historic results rows: {len(results):,}")

    results = results.dropna(subset=["home_score", "away_score"]).copy()
    print(f"After dropping missing scores: {len(results):,}")

    results["date"] = pd.to_datetime(results["date"], errors="coerce")
    results = results.dropna(subset=["date"]).copy()

    results = results.sort_values("date").reset_index(drop=True)
    results["match_key"] = np.arange(len(results))

    results = add_basic_targets(results)
    results = add_date_features(results)
    results = build_team_history_features(results, window=10)
    results = add_difference_features(results)
    results = add_elo_features(results)

    results["neutral"] = results["neutral"].astype(int)

    numeric_cols = results.select_dtypes(include=["number"]).columns
    results[numeric_cols] = results[numeric_cols].fillna(0)

    if len(results) != results["match_key"].nunique():
        raise ValueError("Duplicate match_key values found after feature building.")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved match training data to: {OUTPUT_FILE}")
    print(f"Final shape: {results.shape[0]:,} rows x {results.shape[1]:,} columns")

    print("\nTarget distribution:")
    print(results["result"].value_counts(normalize=True).round(3).to_string())

    print("\nPreview:")
    print(results.head())

    return results


if __name__ == "__main__":
    build_match_training_data()