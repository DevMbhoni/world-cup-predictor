from pathlib import Path
import pandas as pd


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]

TEAMS_PATH = PROJECT_ROOT / "data" / "raw" / "worldcup_2026" / "teams.csv"


def get_teams() -> dict:
    if not TEAMS_PATH.exists():
        raise FileNotFoundError(f"teams.csv not found at: {TEAMS_PATH}")

    df = pd.read_csv(TEAMS_PATH)

    columns_to_keep = [
        "team_id",
        "team_name",
        "confederation",
        "group_name",
        "fifa_ranking",
        "elo_rating",
    ]

    existing_columns = [col for col in columns_to_keep if col in df.columns]

    df = df[existing_columns].copy()
    df = df.sort_values("team_name").reset_index(drop=True)

    return {
        "source_file": str(TEAMS_PATH),
        "count": len(df),
        "results": df.to_dict(orient="records"),
    }


def search_teams(query: str) -> dict:
    if not TEAMS_PATH.exists():
        raise FileNotFoundError(f"teams.csv not found at: {TEAMS_PATH}")

    df = pd.read_csv(TEAMS_PATH)

    if "team_name" not in df.columns:
        raise ValueError("team_name column not found in teams.csv")

    query = query.strip().lower()

    filtered = df[
        df["team_name"].astype(str).str.lower().str.contains(query, na=False)
    ].copy()

    filtered = filtered.sort_values("team_name").reset_index(drop=True)

    return {
        "source_file": str(TEAMS_PATH),
        "query": query,
        "count": len(filtered),
        "results": filtered.to_dict(orient="records"),
    }