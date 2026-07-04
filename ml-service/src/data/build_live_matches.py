from pathlib import Path

import pandas as pd


CURRENT_FILE = Path(__file__).resolve()
ML_SERVICE_DIR = CURRENT_FILE.parents[2]
PROJECT_ROOT = ML_SERVICE_DIR.parent

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "worldcup_2026"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

MATCHES_PATH = RAW_DATA_DIR / "matches.csv"
BRACKET_PATH = RAW_DATA_DIR / "knockout_bracket.csv"
OUTPUT_PATH = PROCESSED_DATA_DIR / "worldcup_2026_matches_live.csv"

MANUAL_BRACKET_START_MATCH_ID = 89
MANUAL_BRACKET_END_MATCH_ID = 104


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    return pd.read_csv(path)


def align_columns(
    left: pd.DataFrame,
    right: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Align two DataFrames to the union of their columns.

    This is important because matches.csv does not contain bracket source
    columns such as home_source_match_id, while knockout_bracket.csv does.
    """

    all_columns = list(dict.fromkeys([*left.columns, *right.columns]))

    left = left.copy()
    right = right.copy()

    for column in all_columns:
        if column not in left.columns:
            left[column] = pd.NA

        if column not in right.columns:
            right[column] = pd.NA

    return left[all_columns], right[all_columns]


def build_live_matches() -> pd.DataFrame:
    print("Loading World Cup matches...")
    matches = load_csv(MATCHES_PATH)

    print(f"Raw matches: {len(matches):,}")

    print("Loading manual knockout bracket...")
    bracket = load_csv(BRACKET_PATH)

    print(f"Bracket helper rows: {len(bracket):,}")

    # matches.csv currently contains a stale/incomplete match 89.
    #
    # The manually maintained knockout_bracket.csv is the source of truth
    # for matches 89-104 until the upstream dataset publishes the complete
    # and correctly mapped knockout schedule.
    matches = matches[
        ~matches["match_id"].between(
            MANUAL_BRACKET_START_MATCH_ID,
            MANUAL_BRACKET_END_MATCH_ID,
        )
    ].copy()

    print(
        "Removed raw matches "
        f"{MANUAL_BRACKET_START_MATCH_ID}-"
        f"{MANUAL_BRACKET_END_MATCH_ID}"
    )

    # Only use the bracket helper rows intended for the manual bracket range.
    bracket = bracket[
        bracket["match_id"].between(
            MANUAL_BRACKET_START_MATCH_ID,
            MANUAL_BRACKET_END_MATCH_ID,
        )
    ].copy()

    matches, bracket = align_columns(matches, bracket)

    live_matches = pd.concat(
        [matches, bracket],
        ignore_index=True,
    )

    # Safety check: there must only be one row per match.
    duplicate_match_ids = live_matches[
        live_matches["match_id"].duplicated(keep=False)
    ]["match_id"].tolist()

    if duplicate_match_ids:
        raise ValueError(
            "Duplicate match IDs found after building live matches: "
            f"{sorted(set(duplicate_match_ids))}"
        )

    live_matches = (
        live_matches
        .sort_values("match_id")
        .reset_index(drop=True)
    )

    expected_match_ids = set(range(1, 105))
    actual_match_ids = set(
        live_matches["match_id"]
        .dropna()
        .astype(int)
        .tolist()
    )

    missing_match_ids = sorted(expected_match_ids - actual_match_ids)

    if missing_match_ids:
        raise ValueError(
            "Live tournament file is missing match IDs: "
            f"{missing_match_ids}"
        )

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    live_matches.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print("Live matches built successfully.")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Rows: {len(live_matches):,}")
    print()

    if "status" in live_matches.columns:
        print("STATUS COUNTS")
        print(
            live_matches["status"]
            .value_counts(dropna=False)
            .to_string()
        )
        print()

    if "stage_id" in live_matches.columns:
        print("STAGE COUNTS")
        print(
            live_matches["stage_id"]
            .value_counts(dropna=False)
            .sort_index()
            .to_string()
        )
        print()

    print("MATCHES 89-104")
    print(
        live_matches[
            live_matches["match_id"].between(89, 104)
        ][
            [
                "match_id",
                "stage_id",
                "stage_name",
                "home_team_id",
                "away_team_id",
                "home_source_match_id",
                "away_source_match_id",
                "home_source_type",
                "away_source_type",
                "status",
                "notes",
            ]
        ].to_string(index=False)
    )

    return live_matches


if __name__ == "__main__":
    build_live_matches()