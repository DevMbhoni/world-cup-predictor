from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_teams():
    response = client.get("/api/v1/teams")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["count"] > 0


def test_search_teams():
    response = client.get("/api/v1/teams/search?query=can")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


def test_match_prediction():
    response = client.get(
        "/api/v1/matches/predict?home_team=Canada&away_team=Morocco"
    )
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "final_prediction" in data["prediction"]


def test_live_tournament_simulation():
    response = client.get("/api/v1/tournament/live-simulation?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


def test_golden_boot_simulation():
    response = client.get("/api/v1/scorers/golden-boot-simulation?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data

def test_tournament_bracket():
    response = client.get("/api/v1/tournament/bracket")
    assert response.status_code == 200
    data = response.json()
    assert "matches" in data
    assert "grouped_by_stage" in data
    assert data["count"] >= 32