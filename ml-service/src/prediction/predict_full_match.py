from pathlib import Path
import sys
from typing import Dict, Any


CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]
PROJECT_ROOT = CURRENT_FILE.parents[3]

sys.path.append(str(SRC_DIR))

from prediction.predict_match import predict_match
from prediction.predict_scoreline import predict_scoreline
from prediction.predict_markets import predict_markets


CLASSIFIER_WEIGHT = 0.60
POISSON_WEIGHT = 0.40


def normalize_result_label(label: str) -> str:
    label = str(label).upper().strip()

    mapping = {
        "HOME_WIN": "HOME_WIN",
        "DRAW": "DRAW",
        "AWAY_WIN": "AWAY_WIN",
        "HOME": "HOME_WIN",
        "AWAY": "AWAY_WIN",
    }

    return mapping.get(label, label)


def percentage(value: float) -> float:
    return round(float(value) * 100, 2)


def get_probability(probabilities: Dict[str, float], key: str) -> float:
    return float(probabilities.get(key, 0.0))


def build_final_probabilities(
    classifier_probabilities: Dict[str, float],
    poisson_markets: Dict[str, float],
) -> Dict[str, float]:
    classifier_home = get_probability(classifier_probabilities, "HOME_WIN")
    classifier_draw = get_probability(classifier_probabilities, "DRAW")
    classifier_away = get_probability(classifier_probabilities, "AWAY_WIN")

    poisson_home = float(poisson_markets.get("home_win_probability", 0.0))
    poisson_draw = float(poisson_markets.get("draw_probability", 0.0))
    poisson_away = float(poisson_markets.get("away_win_probability", 0.0))

    final_probs = {
        "HOME_WIN": CLASSIFIER_WEIGHT * classifier_home + POISSON_WEIGHT * poisson_home,
        "DRAW": CLASSIFIER_WEIGHT * classifier_draw + POISSON_WEIGHT * poisson_draw,
        "AWAY_WIN": CLASSIFIER_WEIGHT * classifier_away + POISSON_WEIGHT * poisson_away,
    }

    total = sum(final_probs.values())

    if total > 0:
        final_probs = {
            key: value / total
            for key, value in final_probs.items()
        }

    return final_probs


def get_prediction_label(probabilities: Dict[str, float]) -> str:
    return max(probabilities, key=probabilities.get)


def get_confidence_level(probability: float) -> str:
    if probability >= 0.60:
        return "High"

    if probability >= 0.45:
        return "Medium"

    return "Low"


def get_model_agreement(
    classifier_prediction: str,
    poisson_prediction: str,
    final_prediction: str,
) -> Dict[str, Any]:
    classifier_prediction = normalize_result_label(classifier_prediction)
    poisson_prediction = normalize_result_label(poisson_prediction)

    agree = classifier_prediction == poisson_prediction

    return {
        "agree": agree,
        "classifier_prediction": classifier_prediction,
        "poisson_prediction": poisson_prediction,
        "final_prediction": final_prediction,
        "message": "Models agree" if agree else "Models disagree, final prediction uses blended probabilities",
    }


def clean_scorelines(scorelines: list[dict]) -> list[dict]:
    cleaned = []

    for item in scorelines:
        home_score = item.get(
            "home_score",
            item.get("home_goals", item.get("home", 0)),
        )

        away_score = item.get(
            "away_score",
            item.get("away_goals", item.get("away", 0)),
        )

        # Some scoreline models may store the score as "1-1"
        if "scoreline" in item and (home_score == 0 and away_score == 0):
            scoreline = str(item["scoreline"])

            if "-" in scoreline:
                left, right = scoreline.split("-", 1)
                home_score = int(left.strip())
                away_score = int(right.strip())

        probability = float(item.get("probability", 0.0))

        cleaned.append(
            {
                "home_score": int(home_score),
                "away_score": int(away_score),
                "scoreline": f"{int(home_score)}-{int(away_score)}",
                "probability": probability,
                "probability_percent": percentage(probability),
            }
        )

    return cleaned


def predict_full_match(home_team: str, away_team: str) -> Dict[str, Any]:
    classifier_result = predict_match(home_team, away_team)
    scoreline_result = predict_scoreline(home_team, away_team)
    market_result = predict_markets(home_team, away_team)

    classifier_probabilities = classifier_result["probabilities"]
    poisson_markets = scoreline_result["markets"]

    final_probabilities = build_final_probabilities(
        classifier_probabilities=classifier_probabilities,
        poisson_markets=poisson_markets,
    )

    final_prediction = get_prediction_label(final_probabilities)
    final_prediction_probability = final_probabilities[final_prediction]

    poisson_probabilities = {
        "HOME_WIN": float(poisson_markets.get("home_win_probability", 0.0)),
        "DRAW": float(poisson_markets.get("draw_probability", 0.0)),
        "AWAY_WIN": float(poisson_markets.get("away_win_probability", 0.0)),
    }

    poisson_prediction = get_prediction_label(poisson_probabilities)

    model_agreement = get_model_agreement(
        classifier_prediction=classifier_result["predicted_result"],
        poisson_prediction=poisson_prediction,
        final_prediction=final_prediction,
    )

    response = {
        "match": {
            "home_team": home_team,
            "away_team": away_team,
        },
        "final_prediction": {
            "result": final_prediction,
            "confidence": get_confidence_level(final_prediction_probability),
            "probability": final_prediction_probability,
            "probability_percent": percentage(final_prediction_probability),
            "probabilities": {
                "home_win": final_probabilities["HOME_WIN"],
                "draw": final_probabilities["DRAW"],
                "away_win": final_probabilities["AWAY_WIN"],
            },
            "probabilities_percent": {
                "home_win": percentage(final_probabilities["HOME_WIN"]),
                "draw": percentage(final_probabilities["DRAW"]),
                "away_win": percentage(final_probabilities["AWAY_WIN"]),
            },
            "blend": {
                "classifier_weight": CLASSIFIER_WEIGHT,
                "poisson_weight": POISSON_WEIGHT,
            },
        },
        "model_agreement": model_agreement,
        "classifier_model": {
            "prediction": normalize_result_label(classifier_result["predicted_result"]),
            "probabilities": classifier_probabilities,
            "probabilities_percent": {
                "home_win": percentage(classifier_probabilities.get("HOME_WIN", 0.0)),
                "draw": percentage(classifier_probabilities.get("DRAW", 0.0)),
                "away_win": percentage(classifier_probabilities.get("AWAY_WIN", 0.0)),
            },
        },
        "scoreline_model": {
            "prediction": poisson_prediction,
            "expected_goals": {
                "home": round(float(scoreline_result["home_expected_goals"]), 2),
                "away": round(float(scoreline_result["away_expected_goals"]), 2),
            },
            "top_scorelines": clean_scorelines(scoreline_result["top_scorelines"]),
            "probabilities": poisson_probabilities,
            "probabilities_percent": {
                "home_win": percentage(poisson_probabilities["HOME_WIN"]),
                "draw": percentage(poisson_probabilities["DRAW"]),
                "away_win": percentage(poisson_probabilities["AWAY_WIN"]),
            },
        },
        "markets": {
            "poisson": {
                "over_1_5": poisson_markets.get("over_1_5_probability"),
                "over_2_5": poisson_markets.get("over_2_5_probability"),
                "over_3_5": poisson_markets.get("over_3_5_probability"),
                "both_teams_score": poisson_markets.get("both_teams_score_probability"),
                "home_clean_sheet": poisson_markets.get("home_clean_sheet_probability"),
                "away_clean_sheet": poisson_markets.get("away_clean_sheet_probability"),
            },
            "poisson_percent": {
                "over_1_5": percentage(poisson_markets.get("over_1_5_probability", 0.0)),
                "over_2_5": percentage(poisson_markets.get("over_2_5_probability", 0.0)),
                "over_3_5": percentage(poisson_markets.get("over_3_5_probability", 0.0)),
                "both_teams_score": percentage(poisson_markets.get("both_teams_score_probability", 0.0)),
                "home_clean_sheet": percentage(poisson_markets.get("home_clean_sheet_probability", 0.0)),
                "away_clean_sheet": percentage(poisson_markets.get("away_clean_sheet_probability", 0.0)),
            },
            "ml_market_models": market_result,
        },
    }

    return response


if __name__ == "__main__":
    result = predict_full_match("Brazil", "Germany")

    from pprint import pprint
    pprint(result)