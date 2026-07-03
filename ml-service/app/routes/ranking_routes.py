from fastapi import APIRouter, HTTPException, Query

from app.services.ranking_service import get_team_rankings


router = APIRouter(prefix="/api/v1/rankings", tags=["Rankings"])


@router.get("/teams")
def team_rankings(
    limit: int = Query(default=50, ge=1, le=100),
):
    try:
        return get_team_rankings(limit=limit)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))