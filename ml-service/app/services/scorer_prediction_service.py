from pathlib import Path
import pandas as pd


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]

PREDICTIONS_DIR = PROJECT_ROOT / "data" / "predictions"

GOLDEN_BOOT_V1_PATH = PREDICTIONS_DIR / "golden_boot_predictions.csv"
GOLDEN_BOOT_SIMULATION_PATH = PREDICTIONS_DIR / "golden_boot_simulation_results.csv"


def get_golden_boot_predictions(limit: int = 25) -> dict:
    if not GOLDEN_BOOT_V1_PATH.exists():
        raise FileNotFoundError(
            "Golden Boot predictions not found. "
            "Run: python src\\models\\golden_boot_model.py"
        )

    df = pd.read_csv(GOLDEN_BOOT_V1_PATH)

    df = df.sort_values(
        ["golden_boot_probability", "tournament_goals", "team_final_probability"],
        ascending=False,
    )

    records = df.head(limit).to_dict(orient="records")

    return {
        "model_type": "weighted_score_v1",
        "source_file": str(GOLDEN_BOOT_V1_PATH),
        "count": len(records),
        "results": records,
    }


def get_golden_boot_simulation(limit: int = 25) -> dict:
    if not GOLDEN_BOOT_SIMULATION_PATH.exists():
        raise FileNotFoundError(
            "Golden Boot simulation results not found. "
            "Run: python src\\simulation\\simulate_golden_boot.py"
        )

    df = pd.read_csv(GOLDEN_BOOT_SIMULATION_PATH)

    df = df.sort_values(
        ["golden_boot_probability", "expected_final_goals", "current_goals"],
        ascending=False,
    )

    records = df.head(limit).to_dict(orient="records")

    return {
        "model_type": "monte_carlo_simulation_v2",
        "source_file": str(GOLDEN_BOOT_SIMULATION_PATH),
        "count": len(records),
        "results": records,
    }