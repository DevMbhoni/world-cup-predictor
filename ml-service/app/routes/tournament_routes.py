from fastapi import APIRouter, HTTPException, Query

from app.services.tournament_simulation_service import get_live_tournament_simulation
from app.services.tournament_bracket_service import build_bracket


router = APIRouter(prefix="/api/v1/tournament", tags=["Tournament"])


@router.get("/live-simulation")
def live_tournament_simulation(
    limit: int = Query(default=25, ge=1, le=48),
):
    try:
        return get_live_tournament_simulation(limit=limit)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/bracket")
def tournament_bracket():
    try:
        return build_bracket()
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))