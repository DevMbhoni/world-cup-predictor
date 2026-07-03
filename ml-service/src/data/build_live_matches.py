from pathlib import Path
import pandas as pd


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]

RAW_2026_DIR = PROJECT_ROOT / "data" / "raw" / "worldcup_2026"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

MATCHES_PATH = RAW_2026_DIR / "matches.csv"
MANUAL_UPDATES_PATH = RAW_2026_DIR / "manual_match_updates.csv"
KNOCKOUT_BRACKET_PATH = RAW_2026_DIR / "knockout_bracket.csv"

OUTPUT_PATH = PROCESSED_DIR / "worldcup_2026_matches_live.csv"


BASE_MATCH_COLUMNS = [
    "match_id",
    "date",
    "kickoff_time_utc",
    "stage_id",
    "venue_id",
    "home_team_id",
    "away_team_id",
    "home_score",
    "away_score",
    "status",
    "home_xg",
    "away_xg",
    "referee_id",
    "player_of_the_match_id",
]


def load_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"Optional file not found: {path}")
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        print(f"Optional file is empty: {path}")
        return pd.DataFrame()


def normalize_match_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in BASE_MATCH_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    return df


def apply_manual_updates(matches: pd.DataFrame, updates: pd.DataFrame) -> pd.DataFrame:
    if updates.empty:
        return matches

    matches = matches.copy()
    updates = normalize_match_columns(updates)

    for _, update in updates.iterrows():
        match_id = update["match_id"]

        if pd.isna(match_id):
            continue

        match_id = int(match_id)

        if match_id not in set(matches["match_id"]):
            new_row = {col: update.get(col, pd.NA) for col in BASE_MATCH_COLUMNS}
            matches = pd.concat([matches, pd.DataFrame([new_row])], ignore_index=True)
            continue

        idx = matches.index[matches["match_id"] == match_id][0]

        for col in BASE_MATCH_COLUMNS:
            value = update.get(col, pd.NA)

            if pd.notna(value) and str(value).strip() != "":
                matches.at[idx, col] = value

    return matches


def add_missing_knockout_rows(matches: pd.DataFrame, bracket: pd.DataFrame) -> pd.DataFrame:
    if bracket.empty:
        return matches

    matches = matches.copy()
    existing_ids = set(matches["match_id"])

    rows_to_add = []

    for _, row in bracket.iterrows():
        match_id = int(row["match_id"])

        if match_id in existing_ids:
            continue

        rows_to_add.append(
            {
                "match_id": match_id,
                "date": row.get("date", pd.NA),
                "kickoff_time_utc": row.get("kickoff_time_utc", pd.NA),
                "stage_id": row.get("stage_id", pd.NA),
                "venue_id": row.get("venue_id", pd.NA),
                "home_team_id": row.get("home_team_id", pd.NA),
                "away_team_id": row.get("away_team_id", pd.NA),
                "home_score": pd.NA,
                "away_score": pd.NA,
                "status": row.get("status", "Scheduled"),
                "home_xg": pd.NA,
                "away_xg": pd.NA,
                "referee_id": pd.NA,
                "player_of_the_match_id": pd.NA,
            }
        )

    if rows_to_add:
        matches = pd.concat([matches, pd.DataFrame(rows_to_add)], ignore_index=True)

    return matches


def build_live_matches() -> pd.DataFrame:
    if not MATCHES_PATH.exists():
        raise FileNotFoundError(f"matches.csv not found: {MATCHES_PATH}")

    matches = pd.read_csv(MATCHES_PATH)
    matches = normalize_match_columns(matches)

    updates = load_csv_if_exists(MANUAL_UPDATES_PATH)
    bracket = load_csv_if_exists(KNOCKOUT_BRACKET_PATH)

    print(f"Original matches rows: {len(matches)}")

    matches = apply_manual_updates(matches, updates)
    print(f"After manual updates: {len(matches)} rows")

    matches = add_missing_knockout_rows(matches, bracket)
    print(f"After adding bracket rows: {len(matches)} rows")

    matches = matches[BASE_MATCH_COLUMNS].copy()
    matches = matches.sort_values("match_id").reset_index(drop=True)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    matches.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved live matches to: {OUTPUT_PATH}")

    print("\nStage counts:")
    print(matches["stage_id"].value_counts().sort_index().to_string())

    print("\nStatus counts:")
    print(matches["status"].value_counts(dropna=False).to_string())

    print("\nLast 20 rows:")
    print(matches.tail(20).to_string(index=False))

    return matches


if __name__ == "__main__":
    build_live_matches()