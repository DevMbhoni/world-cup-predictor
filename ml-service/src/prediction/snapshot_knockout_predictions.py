from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]
ML_SERVICE_DIR = SRC_DIR.parent
PROJECT_ROOT = ML_SERVICE_DIR.parent

if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from prediction.predict_full_match import predict_full_match


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

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "predictions"
    / "knockout_prediction_history.csv"
)


HISTORY_COLUMNS = [
    "match_id",
    "stage_id",
    "stage_name",
    "home_team",
    "away_team",
    "predicted_result",
    "predicted_winner",
    "prediction_probability",
    "home_win_probability",
    "draw_probability",
    "away_win_probability",
    "predicted_scoreline",
    "predicted_home_score",
    "predicted_away_score",
    "predicted_at",
    "actual_home_score",
    "actual_away_score",
    "actual_winner",
    "prediction_correct",
    "result_updated_at",
]


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    return pd.read_csv(path)


def load_history() -> pd.DataFrame:
    if not OUTPUT_PATH.exists():
        return pd.DataFrame(columns=HISTORY_COLUMNS)

    history = pd.read_csv(OUTPUT_PATH)

    for column in HISTORY_COLUMNS:
        if column not in history.columns:
            history[column] = pd.NA

    return history[HISTORY_COLUMNS]


def resolve_completed_winner(
    match: pd.Series,
    manual_winner_map: dict[int, int],
) -> int | None:
    match_id = int(match["match_id"])

    if match_id in manual_winner_map:
        return manual_winner_map[match_id]

    home_score = match.get("home_score")
    away_score = match.get("away_score")

    if pd.isna(home_score) or pd.isna(away_score):
        return None

    if home_score > away_score:
        return int(match["home_team_id"])

    if away_score > home_score:
        return int(match["away_team_id"])

    return None


def main() -> None:
    matches = read_csv(LIVE_MATCHES_PATH)
    teams = read_csv(TEAMS_PATH)

    winners = (
        read_csv(KNOCKOUT_WINNERS_PATH)
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

    winner_cache: dict[int, int | None] = {}


    def resolve_winner(match_id: int) -> int | None:
        match_id = int(match_id)

        if match_id in winner_cache:
            return winner_cache[match_id]

        match = matches_by_id.get(match_id)

        if match is None:
            return None

        if str(match.get("status", "")).lower() == "completed":
            winner = resolve_completed_winner(
                match,
                manual_winner_map,
            )
            winner_cache[match_id] = winner
            return winner

        return None


    def resolve_slot(
        match: pd.Series,
        side: str,
    ) -> int | None:
        team_id = match.get(f"{side}_team_id")

        if pd.notna(team_id):
            return int(team_id)

        source_match_id = match.get(
            f"{side}_source_match_id"
        )
        source_type = match.get(
            f"{side}_source_type"
        )

        if pd.isna(source_match_id):
            return None

        source_match_id = int(source_match_id)

        if source_type == "winner":
            return resolve_winner(source_match_id)

        return None


    history = load_history()

    existing_match_ids = set(
        history["match_id"]
        .dropna()
        .astype(int)
        .tolist()
    )

    new_rows: list[dict] = []

    knockout_matches = matches[
        matches["stage_id"].between(3, 7)
    ].sort_values("match_id")

    for _, match in knockout_matches.iterrows():
        match_id = int(match["match_id"])

        if match_id in existing_match_ids:
            continue

        if str(match.get("status", "")).lower() == "completed":
            continue

        home_team_id = resolve_slot(match, "home")
        away_team_id = resolve_slot(match, "away")

        if home_team_id is None or away_team_id is None:
            continue

        home_team = team_map.get(home_team_id)
        away_team = team_map.get(away_team_id)

        if not home_team or not away_team:
            continue

        print(
            f"Predicting M{match_id}: "
            f"{home_team} vs {away_team}"
        )

        prediction = predict_full_match(
            home_team,
            away_team,
        )

        final = prediction["final_prediction"]
        scoreline = prediction["scoreline_model"]

        predicted_result = final["result"]

        if predicted_result == "HOME_WIN":
            predicted_winner = home_team
        elif predicted_result == "AWAY_WIN":
            predicted_winner = away_team
        else:
            predicted_winner = "Draw"

        top_scorelines = scoreline.get(
            "top_scorelines",
            []
        )

        top_scoreline = (
            top_scorelines[0]
            if top_scorelines
            else {}
        )

        new_rows.append(
            {
                "match_id": match_id,
                "stage_id": int(match["stage_id"]),
                "stage_name": match.get(
                    "stage_name",
                    f"Stage {int(match['stage_id'])}",
                ),
                "home_team": home_team,
                "away_team": away_team,
                "predicted_result": predicted_result,
                "predicted_winner": predicted_winner,
                "prediction_probability": final[
                    "probability_percent"
                ],
                "home_win_probability": final[
                    "probabilities_percent"
                ]["home_win"],
                "draw_probability": final[
                    "probabilities_percent"
                ]["draw"],
                "away_win_probability": final[
                    "probabilities_percent"
                ]["away_win"],
                "predicted_scoreline": top_scoreline.get(
                    "scoreline"
                ),
                "predicted_home_score": top_scoreline.get(
                    "home_score"
                ),
                "predicted_away_score": top_scoreline.get(
                    "away_score"
                ),
                "predicted_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "actual_home_score": pd.NA,
                "actual_away_score": pd.NA,
                "actual_winner": pd.NA,
                "prediction_correct": pd.NA,
                "result_updated_at": pd.NA,
            }
        )

    if not new_rows:
        print(
            "No new confirmed knockout matches "
            "need prediction snapshots."
        )
        return

    new_data = pd.DataFrame(
        new_rows,
        columns=HISTORY_COLUMNS,
    )

    history = pd.concat(
        [history, new_data],
        ignore_index=True,
    )

    history = (
        history
        .sort_values("match_id")
        .drop_duplicates(
            subset=["match_id"],
            keep="first",
        )
        .reset_index(drop=True)
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    history.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print(
        f"Saved {len(new_rows)} new "
        "pre-match predictions."
    )
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()