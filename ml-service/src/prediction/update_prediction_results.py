from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


CURRENT_FILE = Path(__file__).resolve()
ML_SERVICE_DIR = CURRENT_FILE.parents[2]
PROJECT_ROOT = ML_SERVICE_DIR.parent

LIVE_MATCHES_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "worldcup_2026_matches_live.csv"
)

TEAMS_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "worldcup_2026"
    / "teams.csv"
)

KNOCKOUT_WINNERS_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "worldcup_2026"
    / "knockout_winners.csv"
)

HISTORY_PATH = (
    PROJECT_ROOT
    / "data"
    / "predictions"
    / "knockout_prediction_history.csv"
)


STRING_COLUMNS = [
    "actual_winner",
    "result_updated_at",
]

BOOLEAN_COLUMNS = [
    "prediction_correct",
]

NUMERIC_RESULT_COLUMNS = [
    "actual_home_score",
    "actual_away_score",
]


def prepare_history_dtypes(
    history: pd.DataFrame,
) -> pd.DataFrame:
    """
    Ensure prediction result columns can safely receive
    strings, booleans and nullable numeric values.

    Empty CSV columns may otherwise be inferred as float64.
    """

    history = history.copy()

    for column in STRING_COLUMNS:
        if column not in history.columns:
            history[column] = pd.Series(
                pd.NA,
                index=history.index,
                dtype="object",
            )
        else:
            history[column] = history[column].astype(
                "object"
            )

    for column in BOOLEAN_COLUMNS:
        if column not in history.columns:
            history[column] = pd.Series(
                pd.NA,
                index=history.index,
                dtype="boolean",
            )
        else:
            history[column] = history[column].astype(
                "boolean"
            )

    for column in NUMERIC_RESULT_COLUMNS:
        if column not in history.columns:
            history[column] = pd.Series(
                pd.NA,
                index=history.index,
                dtype="Int64",
            )
        else:
            history[column] = pd.to_numeric(
                history[column],
                errors="coerce",
            ).astype("Int64")

    return history


def main() -> None:
    if not HISTORY_PATH.exists():
        print(
            "Prediction history does not exist yet."
        )
        print(
            "Run snapshot_knockout_predictions.py "
            "before the next dataset update."
        )
        return

    history = pd.read_csv(HISTORY_PATH)

    history = prepare_history_dtypes(history)

    matches = pd.read_csv(LIVE_MATCHES_PATH)
    teams = pd.read_csv(TEAMS_PATH)

    winners = (
        pd.read_csv(KNOCKOUT_WINNERS_PATH)
        if KNOCKOUT_WINNERS_PATH.exists()
        else pd.DataFrame()
    )

    team_map = dict(
        zip(
            teams["team_id"].astype(int),
            teams["team_name"],
        )
    )

    manual_winner_map: dict[int, int] = {}

    if not winners.empty:
        manual_winner_map = dict(
            zip(
                winners["match_id"].astype(int),
                winners["winner_team_id"].astype(int),
            )
        )

    matches_by_id = {
        int(row["match_id"]): row
        for _, row in matches.iterrows()
    }

    updated = 0

    for index, prediction in history.iterrows():
        match_id = int(prediction["match_id"])

        match = matches_by_id.get(match_id)

        if match is None:
            continue

        if (
            str(match.get("status", "")).lower()
            != "completed"
        ):
            continue

        home_score = match.get("home_score")
        away_score = match.get("away_score")

        if (
            pd.isna(home_score)
            or pd.isna(away_score)
        ):
            continue

        if match_id in manual_winner_map:
            actual_winner_id = manual_winner_map[
                match_id
            ]

        elif home_score > away_score:
            actual_winner_id = int(
                match["home_team_id"]
            )

        elif away_score > home_score:
            actual_winner_id = int(
                match["away_team_id"]
            )

        else:
            actual_winner_id = None

        actual_winner = (
            team_map.get(actual_winner_id)
            if actual_winner_id is not None
            else "Draw"
        )

        predicted_winner = str(
            prediction["predicted_winner"]
        )

        prediction_correct = (
            predicted_winner == actual_winner
        )

        history.at[
            index,
            "actual_home_score",
        ] = int(home_score)

        history.at[
            index,
            "actual_away_score",
        ] = int(away_score)

        history.at[
            index,
            "actual_winner",
        ] = actual_winner

        history.at[
            index,
            "prediction_correct",
        ] = prediction_correct

        history.at[
            index,
            "result_updated_at",
        ] = datetime.now(
            timezone.utc
        ).isoformat()

        updated += 1

        print(
            f"M{match_id}: "
            f"predicted={predicted_winner} | "
            f"actual={actual_winner} | "
            f"correct={prediction_correct}"
        )

    history.to_csv(
        HISTORY_PATH,
        index=False,
    )

    print()
    print(
        f"Updated {updated} completed "
        "prediction results."
    )

    completed = history[
        history["actual_winner"].notna()
    ].copy()

    if not completed.empty:
        correct = int(
            completed["prediction_correct"]
            .fillna(False)
            .astype(bool)
            .sum()
        )

        accuracy = (
            correct / len(completed)
        ) * 100

        print()
        print("PREDICTION PERFORMANCE")
        print(
            f"Completed predictions: "
            f"{len(completed)}"
        )
        print(
            f"Correct predictions: {correct}"
        )
        print(
            f"Incorrect predictions: "
            f"{len(completed) - correct}"
        )
        print(
            f"Accuracy: {accuracy:.2f}%"
        )


if __name__ == "__main__":
    main()