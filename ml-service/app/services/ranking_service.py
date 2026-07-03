from pathlib import Path
import pandas as pd


CURRENT_FILE = Path(__file__).resolve()

# ranking_service.py is inside:
# ml-service/app/services/ranking_service.py
# parents[3] points to the full project root:
# world-cup-predictor/
PROJECT_ROOT = CURRENT_FILE.parents[3]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TEAM_ELO_PATH = PROCESSED_DIR / "team_elo_ratings.csv"


def get_team_rankings(limit: int = 50) -> dict:
    if not TEAM_ELO_PATH.exists():
        raise FileNotFoundError(
            f"Team Elo rankings not found at: {TEAM_ELO_PATH}. "
            "Run: python src\\models\\elo_model.py"
        )

    df = pd.read_csv(TEAM_ELO_PATH)

    if "elo_rating" in df.columns:
        sort_col = "elo_rating"
    elif "rating" in df.columns:
        sort_col = "rating"
    elif "current_elo" in df.columns:
        sort_col = "current_elo"
    else:
        raise ValueError(
            f"Could not find Elo rating column. Available columns: {df.columns.tolist()}"
        )

    df = df.sort_values(sort_col, ascending=False).head(limit)

    return {
        "source_file": str(TEAM_ELO_PATH),
        "count": len(df),
        "results": df.to_dict(orient="records"),
    }