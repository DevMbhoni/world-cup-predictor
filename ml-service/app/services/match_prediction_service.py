from pathlib import Path
import sys


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.append(str(SRC_DIR))

from prediction.predict_full_match import predict_full_match


def get_full_match_prediction(home_team: str, away_team: str) -> dict:
    prediction = predict_full_match(home_team, away_team)

    return {
        "home_team": home_team,
        "away_team": away_team,
        "prediction": prediction,
    }