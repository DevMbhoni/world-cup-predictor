# World Cup Predictor 2026

A full-stack machine learning and football analytics platform for predicting international match outcomes, likely scorelines, match markets, tournament progression, team strength, and Golden Boot probabilities for the 2026 FIFA World Cup.

The project combines historical international football results with live-updated 2026 World Cup tournament data and exposes the prediction pipeline through a FastAPI backend and an interactive React frontend.

## Project Overview

World Cup Predictor 2026 is designed as more than a single match classifier.

It combines multiple predictive and simulation techniques:

- Calibrated Random Forest classification for match outcomes
- Poisson regression for expected goals
- Poisson scoreline probability modelling
- Random Forest market models
- Elo team strength ratings
- Monte Carlo tournament simulation
- Weighted player scoring models
- Monte Carlo Golden Boot simulation
- Archived pre-match knockout prediction tracking
- Prediction-versus-actual result evaluation
- Live knockout bracket resolution

The system supports completed, confirmed, scheduled, and projected tournament states.

## Core Features

### Match Predictor

Select two international teams and generate:

- Home win probability
- Draw probability
- Away win probability
- Final predicted result
- Expected home goals
- Expected away goals
- Most likely scorelines
- Over 2.5 goals probability
- Both Teams To Score probability
- Home clean sheet probability
- Away clean sheet probability

The final user-facing prediction blends the match result classifier with Poisson-derived match probabilities.

### Live Tournament Simulation

The tournament simulation:

- Locks completed matches to their real results
- Uses explicit knockout winners for matches decided after a level score
- Simulates remaining fixtures
- Resolves knockout progression
- Estimates championship probabilities
- Tracks each team's tournament status

### Knockout Bracket

The frontend includes a live knockout bracket covering:

- Round of 32
- Round of 16
- Quarter-finals
- Semi-finals
- Third-place match
- Final

The bracket distinguishes between:

- Completed matches
- Confirmed future fixtures
- Scheduled unresolved fixtures
- Model-projected future paths

### Knockout Prediction Tracking

From Match 93 onward, confirmed knockout predictions are archived before results become available.

The project stores:

- Predicted winner
- Prediction confidence
- Home win probability
- Draw probability
- Away win probability
- Predicted scoreline
- Prediction timestamp
- Actual score
- Actual winner
- Whether the prediction was correct

This allows the frontend to compare the original pre-match prediction against the real match result.

Historical matches completed before prediction tracking was introduced are not included in tracked prediction accuracy.

### Elo Team Rankings

A custom Elo rating system measures international team strength.

The rating pipeline considers:

- Opponent strength
- Expected match result
- Actual match result
- Goal difference
- Home advantage

Elo values are also used as features in the machine learning pipeline.

### Golden Boot Simulation

The Golden Boot system combines player statistics, scoring weights, expected tournament progression, and Monte Carlo simulation.

Outputs include:

- Current goals
- Expected final goals
- Golden Boot probability
- Top 3 probability
- Expected remaining matches

## Machine Learning Models

| Prediction Task | Model / Method |
|---|---|
| Home / Draw / Away | Calibrated Random Forest |
| Expected home goals | Poisson Regression |
| Expected away goals | Poisson Regression |
| Scoreline probabilities | Poisson distribution |
| Over 2.5 goals | Random Forest |
| Both Teams To Score | Random Forest |
| Home clean sheet | Random Forest |
| Away clean sheet | Random Forest |
| Team strength | Elo rating system |
| Tournament winner | Monte Carlo simulation |
| Golden Boot | Weighted scoring model + Monte Carlo simulation |
| Final match prediction | 60% classifier + 40% Poisson blend |

## Latest Model Results

### Match Result Model

Selected model:

```text
Calibrated Random Forest
```

Latest evaluation:

```text
Accuracy: 59.62%
Log Loss: 0.8897
```

The match-result pipeline compares Logistic Regression, Random Forest, and Calibrated Random Forest models and selects the preferred model using evaluation performance, with particular attention to probability quality.

### Scoreline Models

Home goals model:

```text
MAE: 1.0178
RMSE: 1.3661
```

Away goals model:

```text
MAE: 0.8343
RMSE: 1.1315
```

Both selected scoreline models use Poisson regression.

## Prediction Architecture

```text
Historical Match Data
        |
        v
Feature Engineering
        |
        +----------------------+
        |                      |
        v                      v
Match Result Model      Poisson Goal Models
        |                      |
        |                      v
        |               Scoreline Probabilities
        |                      |
        +----------+-----------+
                   |
                   v
        60% Classifier + 40% Poisson
                   |
                   v
           Final Match Prediction
```

Tournament simulation reuses the prediction pipeline to simulate future matches while preserving real completed results.

## Technology Stack

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- TanStack Query
- Axios
- Recharts
- Lucide React

### Backend

- Python
- FastAPI
- Uvicorn
- Pandas
- NumPy

### Machine Learning

- Scikit-learn
- Joblib
- Logistic Regression
- Random Forest
- Calibrated classifiers
- Poisson Regression
- Elo ratings
- Monte Carlo simulation

### Deployment

- Vercel — frontend
- Render — FastAPI backend
- GitHub — source control and deployment integration

## Project Structure

```text
world-cup-predictor/
|
|-- data/
|   |-- predictions/
|   |-- processed/
|   `-- raw/
|       |-- historic/
|       `-- worldcup_2026/
|
|-- frontend/
|   |-- public/
|   `-- src/
|       |-- api/
|       |-- assets/
|       |-- features/
|       |   |-- match/
|       |   |-- rankings/
|       |   |-- scorers/
|       |   `-- tournament/
|       |-- layouts/
|       `-- types/
|
|-- ml-service/
|   |-- app/
|   |   |-- routes/
|   |   |-- schemas/
|   |   `-- services/
|   |
|   |-- saved_models/
|   |
|   |-- src/
|   |   |-- data/
|   |   |-- features/
|   |   |-- models/
|   |   |-- prediction/
|   |   |-- simulation/
|   |   `-- training/
|   |
|   `-- tests/
|
|-- notebooks/
|-- reports/
`-- scripts/
```

## Dataset Sources

This project uses two primary football data sources.

### International Football Results

Historical international match data is sourced from the `martj42/international_results` dataset.

Source:

https://github.com/martj42/international_results

The dataset provides men's full international football results dating back to 1872 and is used as the historical foundation for feature engineering, Elo ratings, and model training.

Project files sourced from this dataset include:

```text
results.csv
shootouts.csv
goalscorers.csv
former_names.csv
```

Credit belongs to the original dataset maintainer and contributors.

### FIFA World Cup 2026 Dataset

The live 2026 tournament data is sourced from the Kaggle dataset:

https://www.kaggle.com/datasets/mominullptr/fifa-world-cup-2026-dataset/discussion?sort=hotness

The dataset provides updated World Cup 2026 tournament information, including relational tournament, match, squad, event, lineup, player, and team-stat data.

Project files may include:

```text
teams.csv
venues.csv
tournament_stages.csv
referees.csv
matches.csv
matches_detailed.csv
squads_and_players.csv
match_events.csv
match_lineups.csv
match_team_stats.csv
player_stats.csv
```

The project maintains additional helper files for knockout progression and matches decided after a level recorded score:

```text
knockout_bracket.csv
knockout_winners.csv
```

These helper files are project-maintained and are not presented as original source-dataset files.

## Data Processing

Historical data is transformed into a match-level machine learning dataset.

The feature pipeline includes:

- Date features
- Historical rolling form
- Rolling goals scored
- Rolling goals conceded
- Win-rate features
- Draw-rate features
- Home and away team comparisons
- Elo ratings
- Elo differences
- Elo expected scores
- Match targets
- Goal targets
- Match market targets

Rolling features are shifted so that the current match result is not used to construct its own pre-match features.

The processed training dataset contains approximately 49,000 international matches.

## Training and Test Split

The project uses a time-based split rather than a random split.

```text
Training:
Matches before 2018

Testing:
Matches from 2018 onward
```

This better reflects the real prediction problem because models are evaluated on later matches using historical information.

## Running the Project Locally

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd world-cup-predictor
```

### 2. Create the Python environment

```powershell
cd ml-service

python -m venv .venv

.\.venv\Scripts\Activate.ps1
```

### 3. Install backend dependencies

```powershell
pip install -r requirements.txt
```

### 4. Start FastAPI

```powershell
uvicorn app.main:app --reload
```

The API runs locally at:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

### 5. Start the frontend

Open another terminal:

```powershell
cd frontend

npm install

npm run dev
```

## Main API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | API health status |
| GET | `/api/v1/teams` | List teams |
| GET | `/api/v1/teams/search` | Search teams |
| GET | `/api/v1/matches/predict` | Predict a match |
| GET | `/api/v1/tournament/live-simulation` | Live tournament probabilities |
| GET | `/api/v1/tournament/bracket` | Knockout bracket |
| GET | `/api/v1/scorers/golden-boot` | Golden Boot data |
| GET | `/api/v1/scorers/golden-boot-simulation` | Golden Boot simulation |
| GET | `/api/v1/rankings/teams` | Elo team rankings |
| GET | `/api/v1/predictions/history` | Archived knockout prediction history |

## Example Match Prediction

Request:

```text
GET /api/v1/matches/predict?home_team=Brazil&away_team=Germany
```

The response includes:

```text
Final predicted result
Home / draw / away probabilities
Expected home goals
Expected away goals
Top scorelines
Over 2.5 probability
Both Teams To Score probability
Home clean sheet probability
Away clean sheet probability
```

## Tournament Update Workflow

Before replacing an updated World Cup dataset:

```powershell
cd ml-service

python src\prediction\snapshot_knockout_predictions.py
```

This freezes predictions for confirmed upcoming matches.

After replacing the source dataset:

1. Inspect the updated knockout fixtures.
2. Check completed knockout matches that ended level.
3. Update `knockout_winners.csv` when a match was decided on penalties or otherwise requires an explicit advancing team.
4. Rebuild live match data.
5. Update prediction history with real results.
6. Snapshot newly confirmed knockout matches.
7. Refresh tournament simulation.
8. Refresh Golden Boot models and simulations.
9. Run tests.
10. Build the frontend.
11. Commit and push.

Main commands:

```powershell
python src\data\build_live_matches.py

python src\prediction\update_prediction_results.py

python src\prediction\snapshot_knockout_predictions.py

python src\simulation\simulate_live_tournament.py

python src\models\golden_boot_model.py

python src\simulation\simulate_golden_boot.py

pytest -q
```

Frontend:

```powershell
cd ..\frontend

npm run build
```

## Testing

Backend tests:

```powershell
cd ml-service

pytest -q
```

Current test suite covers the main FastAPI endpoints, including prediction history.

## Prediction Tracking Integrity

The project intentionally does not retroactively generate historical predictions and present them as pre-match predictions.

A knockout prediction is counted in live prediction accuracy only when it was archived before the corresponding result became available.

For matches completed before prediction tracking was introduced, the frontend displays:

```text
Historical prediction unavailable
Pre-match prediction tracking started from M93.
```

This keeps prediction evaluation transparent.

## Limitations

- Football outcomes contain substantial randomness.
- Historical results may not fully capture current squad strength.
- Injuries, tactical changes, suspensions, and late squad information may not be represented.
- Poisson goal assumptions simplify real match dynamics.
- Penalty shootout winners require explicit advancement data when the source score remains level.
- Tournament probabilities change as new real results become available.
- Golden Boot probabilities depend on available player and tournament data.

This project is intended as a machine learning, statistics, software engineering, and football analytics portfolio project. Predictions should not be treated as guaranteed outcomes or betting advice.

## Future Improvements

Potential improvements include:

- Player availability and injury features
- Starting lineup strength
- FIFA ranking integration
- Confederation strength features
- Expected goals history
- Bayesian score models
- Dixon-Coles score modelling
- Model probability calibration analysis
- SHAP-based prediction explanations
- Automated tournament data ingestion
- CI/CD status checks with GitHub Actions
- Automated model monitoring
- Prediction calibration dashboards
- Model version tracking

## Developer

### Mbhoni Shipalana

Graduate Software Engineer and Data Analyst

BSc Computer Science and Statistics  
Nelson Mandela University

Former Student Assistant supporting:

- C#
- Java
- Data Structures
- Computing Fundamentals

LinkedIn:

https://www.linkedin.com/in/mbhoni-shipalana-83b9b826b

GitHub:

https://github.com/DevMbhoni

Email:

shipalanambhoniii@gmail.com

## Disclaimer

This project is an independent portfolio and educational project.

It is not affiliated with, endorsed by, or sponsored by FIFA.

All referenced datasets remain subject to their original owners' and publishers' terms, licences, and attribution requirements.

## License

This project is licensed under the MIT License.

See the `LICENSE` file for the full licence terms.

Dataset licences, attribution requirements, and usage terms are governed separately by the respective dataset publishers.Add a project licence before reuse or redistribution.

Dataset licences and usage terms are governed separately by the respective dataset publishers.
