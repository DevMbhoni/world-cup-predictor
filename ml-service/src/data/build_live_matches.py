from __future__ import annotations

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

EXPECTED_MATCH_IDS = set(range(1, 105))


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    return pd.read_csv(path)


def align_columns(
    left: pd.DataFrame,
    right: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_columns = list(
        dict.fromkeys(
            [
                *left.columns.tolist(),
                *right.columns.tolist(),
            ]
        )
    )

    left = left.copy()
    right = right.copy()

    for column in all_columns:
        if column not in left.columns:
            left[column] = pd.NA

        if column not in right.columns:
            right[column] = pd.NA

    return (
        left[all_columns],
        right[all_columns],
    )


def enrich_upstream_with_bracket_metadata(
    matches: pd.DataFrame,
    bracket: pd.DataFrame,
) -> pd.DataFrame:
    """
    Preserve source-match metadata from knockout_bracket.csv.

    The upstream matches.csv may contain a real scheduled or completed
    fixture without home_source_match_id / away_source_match_id fields.

    The bracket helper still knows how that fixture connects to the
    previous round, so copy only missing metadata into upstream rows.
    """

    metadata_columns = [
        "stage_name",
        "home_source_match_id",
        "away_source_match_id",
        "home_source_type",
        "away_source_type",
        "notes",
    ]

    bracket_by_id = (
        bracket
        .drop_duplicates(
            subset=["match_id"],
            keep="last",
        )
        .set_index("match_id")
    )

    matches = matches.copy()

    for index, match in matches.iterrows():
        match_id = int(match["match_id"])

        if match_id not in bracket_by_id.index:
            continue

        bracket_match = bracket_by_id.loc[match_id]

        for column in metadata_columns:
            if column not in matches.columns:
                matches[column] = pd.NA

            current_value = matches.at[index, column]

            if pd.isna(current_value):
                matches.at[index, column] = (
                    bracket_match.get(column)
                )

    return matches


def build_live_matches() -> pd.DataFrame:
    print("Loading World Cup matches...")
    matches = load_csv(MATCHES_PATH)

    print(f"Upstream matches: {len(matches):,}")
    print(
        "Upstream match range: "
        f"{int(matches['match_id'].min())}-"
        f"{int(matches['match_id'].max())}"
    )

    print()
    print("Loading knockout bracket helper...")
    bracket = load_csv(BRACKET_PATH)

    print(f"Bracket helper rows: {len(bracket):,}")

    matches["match_id"] = (
        matches["match_id"]
        .astype(int)
    )

    bracket["match_id"] = (
        bracket["match_id"]
        .astype(int)
    )

    upstream_match_ids = set(
        matches["match_id"].tolist()
    )

    # Only use helper rows that the upstream dataset
    # does not contain yet.
    missing_bracket_rows = bracket[
        ~bracket["match_id"].isin(
            upstream_match_ids
        )
    ].copy()

    print()
    print(
        "Bracket helper rows required: "
        f"{len(missing_bracket_rows):,}"
    )

    if not missing_bracket_rows.empty:
        print(
            "Helper match IDs: "
            + ", ".join(
                str(match_id)
                for match_id
                in missing_bracket_rows[
                    "match_id"
                ].tolist()
            )
        )

    # Keep bracket source metadata even when an upstream
    # match row now exists.
    matches, bracket = align_columns(
        matches,
        bracket,
    )

    matches = (
        enrich_upstream_with_bracket_metadata(
            matches,
            bracket,
        )
    )

    matches, missing_bracket_rows = align_columns(
        matches,
        missing_bracket_rows,
    )

    live_matches = pd.concat(
        [
            matches,
            missing_bracket_rows,
        ],
        ignore_index=True,
    )

    duplicate_match_ids = (
        live_matches[
            live_matches["match_id"]
            .duplicated(keep=False)
        ]["match_id"]
        .astype(int)
        .tolist()
    )

    if duplicate_match_ids:
        raise ValueError(
            "Duplicate match IDs found: "
            f"{sorted(set(duplicate_match_ids))}"
        )

    live_matches = (
        live_matches
        .sort_values("match_id")
        .reset_index(drop=True)
    )

    actual_match_ids = set(
        live_matches["match_id"]
        .astype(int)
        .tolist()
    )

    missing_match_ids = sorted(
        EXPECTED_MATCH_IDS
        - actual_match_ids
    )

    if missing_match_ids:
        raise ValueError(
            "Live tournament file is missing "
            f"match IDs: {missing_match_ids}"
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
    print("STATUS COUNTS")
    print(
        live_matches["status"]
        .value_counts(dropna=False)
        .to_string()
    )

    print()
    print("STAGE COUNTS")
    print(
        live_matches["stage_id"]
        .value_counts(dropna=False)
        .sort_index()
        .to_string()
    )

    display_columns = [
        "match_id",
        "stage_id",
        "stage_name",
        "home_team_id",
        "away_team_id",
        "home_score",
        "away_score",
        "home_source_match_id",
        "away_source_match_id",
        "status",
    ]

    print()
    print("KNOCKOUT MATCHES 89-104")
    print(
        live_matches[
            live_matches["match_id"]
            .between(89, 104)
        ][display_columns]
        .to_string(index=False)
    )

    return live_matches


if __name__ == "__main__":
    build_live_matches()