from fastapi import APIRouter, HTTPException, Query

from app.services.scorer_prediction_service import (
    get_golden_boot_predictions,
    get_golden_boot_simulation,
)


router = APIRouter(prefix="/api/v1/scorers", tags=["Scorers"])


@router.get("/golden-boot")
def golden_boot_predictions(
    limit: int = Query(default=25, ge=1, le=100),
):
    try:
        return get_golden_boot_predictions(limit=limit)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/golden-boot-simulation")
def golden_boot_simulation(
    limit: int = Query(default=25, ge=1, le=100),
):
    try:
        return get_golden_boot_simulation(limit=limit)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))