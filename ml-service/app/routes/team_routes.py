from fastapi import APIRouter, HTTPException, Query

from app.services.team_service import get_teams, search_teams


router = APIRouter(prefix="/api/v1/teams", tags=["Teams"])


@router.get("")
def list_teams():
    try:
        return get_teams()
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/search")
def search_team_names(
    query: str = Query(..., min_length=1),
):
    try:
        return search_teams(query=query)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))