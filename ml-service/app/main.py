from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.match_routes import router as match_router
from app.routes.tournament_routes import router as tournament_router
from app.routes.scorer_routes import router as scorer_router
from app.routes.ranking_routes import router as ranking_router
from app.routes.team_routes import router as team_router
from app.routes.prediction_history_routes import (
    router as prediction_history_router,
)

app = FastAPI(
    title="World Cup Predictor ML Service",
    version="1.0.0",
    description="Machine learning service for match predictions, tournament simulations, rankings, and Golden Boot predictions.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(match_router)
app.include_router(tournament_router)
app.include_router(scorer_router)
app.include_router(ranking_router)
app.include_router(team_router)
app.include_router(prediction_history_router)

@app.get("/")
def root():
    return {
        "message": "World Cup Predictor ML Service is running",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }

