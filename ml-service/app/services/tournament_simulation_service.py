from pathlib import Path
import pandas as pd


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]

PREDICTIONS_DIR = PROJECT_ROOT / "data" / "predictions"

LIVE_TOURNAMENT_RESULTS_PATH = PREDICTIONS_DIR / "live_tournament_simulation_results.csv"


def get_live_tournament_simulation(limit: int = 25) -> dict:
    if not LIVE_TOURNAMENT_RESULTS_PATH.exists():
        raise FileNotFoundError(
            "Live tournament simulation results not found. "
            "Run: python src\\simulation\\simulate_live_tournament.py"
        )

    df = pd.read_csv(LIVE_TOURNAMENT_RESULTS_PATH)

    df = df.sort_values(
        ["winner_probability", "final_probability", "semi_final_probability"],
        ascending=False,
    )

    records = df.head(limit).to_dict(orient="records")

    return {
        "source_file": str(LIVE_TOURNAMENT_RESULTS_PATH),
        "count": len(records),
        "results": records,
    }