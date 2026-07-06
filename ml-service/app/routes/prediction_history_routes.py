from fastapi import APIRouter

from app.services.prediction_history_service import (
    get_prediction_history,
)


router = APIRouter(
    prefix="/api/v1/predictions",
    tags=["Prediction History"],
)


@router.get("/history")
def prediction_history():
    return get_prediction_history()