from fastapi import APIRouter, HTTPException, Query

from app.services.match_prediction_service import get_full_match_prediction


router = APIRouter(prefix="/api/v1/matches", tags=["Matches"])


@router.get("/predict")
def predict_match(
    home_team: str = Query(..., min_length=2),
    away_team: str = Query(..., min_length=2),
):
    try:
        return get_full_match_prediction(home_team=home_team, away_team=away_team)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))