from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]

HISTORY_PATH = (
    PROJECT_ROOT
    / "data"
    / "predictions"
    / "knockout_prediction_history.csv"
)


def _to_json_safe(value: Any) -> Any:
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def _normalise_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: _to_json_safe(value)
        for key, value in record.items()
    }


def get_prediction_history() -> dict[str, Any]:
    if not HISTORY_PATH.exists():
        return {
            "count": 0,
            "completed_count": 0,
            "correct_count": 0,
            "incorrect_count": 0,
            "accuracy": None,
            "results": [],
        }

    history = pd.read_csv(HISTORY_PATH)

    if history.empty:
        return {
            "count": 0,
            "completed_count": 0,
            "correct_count": 0,
            "incorrect_count": 0,
            "accuracy": None,
            "results": [],
        }

    completed_mask = history["actual_winner"].notna()
    completed = history[completed_mask].copy()

    correct_count = 0

    if not completed.empty:
        correct_count = int(
            completed["prediction_correct"]
            .astype(str)
            .str.lower()
            .eq("true")
            .sum()
        )

    completed_count = len(completed)

    incorrect_count = completed_count - correct_count

    accuracy = (
        round(
            (correct_count / completed_count) * 100,
            2,
        )
        if completed_count > 0
        else None
    )

    results = [
        _normalise_record(record)
        for record in history
        .sort_values("match_id")
        .to_dict(orient="records")
    ]

    return {
        "count": len(history),
        "completed_count": completed_count,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "accuracy": accuracy,
        "results": results,
    }