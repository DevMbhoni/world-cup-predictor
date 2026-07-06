# World Cup Predictor — Dataset Update Workflow

Follow this process whenever the 2026 World Cup dataset is updated.

---

## IMPORTANT RULE

Before replacing the dataset, save predictions for all currently confirmed upcoming knockout matches.

```powershell
cd ml-service
python src\prediction\snapshot_knockout_predictions.py
```

This preserves the predictions made before real match results are known.

Do not skip this step.

---

# 1. Replace Updated Raw Dataset Files

Copy the latest World Cup 2026 dataset CSV files into:

```text
data/raw/worldcup_2026/
```

Replace the existing versions.

Typical updated files:

```text
matches.csv
matches_detailed.csv
player_stats.csv
match_events.csv
match_lineups.csv
match_team_stats.csv
squads_and_players.csv
```

Do not automatically delete:

```text
knockout_bracket.csv
knockout_winners.csv
```

These are manually maintained project helper files.

---

# 2. Inspect Dataset State

From the project root:

```powershell
@'
import pandas as pd

matches = pd.read_csv("data/raw/worldcup_2026/matches.csv")

print("ROWS:", len(matches))
print("MATCH ID RANGE:", matches["match_id"].min(), "-", matches["match_id"].max())

print()
print("STATUS COUNTS")
print(matches["status"].value_counts(dropna=False))

print()
print("KNOCKOUT MATCHES")
print(
    matches[matches["match_id"] >= 73][
        [
            "match_id",
            "date",
            "stage_id",
            "home_team_id",
            "away_team_id",
            "home_score",
            "away_score",
            "status",
        ]
    ].to_string(index=False)
)
'@ | python
```

Check:

- New completed matches
- New scheduled matches
- Whether the source dataset now contains more knockout fixtures
- Whether match IDs 89–104 are present

---

# 3. Check Completed Knockout Draws

Run:

```powershell
@'
import pandas as pd

matches = pd.read_csv("data/raw/worldcup_2026/matches.csv")

draws = matches[
    (matches["match_id"] >= 73)
    & matches["status"].eq("Completed")
    & matches["home_score"].eq(matches["away_score"])
]

print(
    draws[
        [
            "match_id",
            "home_team_id",
            "away_team_id",
            "home_score",
            "away_score",
        ]
    ].to_string(index=False)
)
'@ | python
```

Every completed knockout draw must have an explicit winner in:

```text
data/raw/worldcup_2026/knockout_winners.csv
```

Example:

```csv
match_id,winner_team_id,winner_team_name,source,last_updated,notes
75,14,Paraguay,FIFA,2026-07-04,Paraguay advanced after a draw
76,10,Morocco,FIFA,2026-07-04,Morocco advanced after a draw
86,26,Egypt,FIFA,2026-07-04,Egypt advanced after a draw
```

Never let the simulator randomly decide the winner of a completed knockout match.

---

# 4. Check knockout_bracket.csv

File:

```text
data/raw/worldcup_2026/knockout_bracket.csv
```

This file is currently the source of truth for matches 89–104 until the upstream dataset provides a complete and correct knockout schedule.

Current bracket mapping:

```text
89 = Winner 75 vs Winner 78
90 = Winner 73 vs Winner 76
91 = Winner 84 vs Winner 83
92 = Winner 82 vs Winner 81

93 = Winner 74 vs Winner 77
94 = Winner 79 vs Winner 80
95 = Winner 87 vs Winner 86
96 = Winner 85 vs Winner 88

97 = Winner 89 vs Winner 90
98 = Winner 91 vs Winner 92
99 = Winner 93 vs Winner 94
100 = Winner 95 vs Winner 96

101 = Winner 97 vs Winner 98
102 = Winner 99 vs Winner 100

103 = Loser 101 vs Loser 102
104 = Winner 101 vs Winner 102
```

Only replace this helper when the upstream dataset contains the full official bracket mapping.

---

# 5. Rebuild Live Tournament State

From:

```text
ml-service/
```

run:

```powershell
python src\data\build_live_matches.py
```

Expected:

```text
Rows: 104
```

Check status and stage counts.

---

# 6. Update Prediction History With Actual Results

Run:

```powershell
python src\prediction\update_prediction_results.py
```

This updates archived pre-match predictions with actual scores and whether the prediction was correct.

---

# 7. Rerun Tournament Simulation

```powershell
python src\simulation\simulate_live_tournament.py
```

Completed matches are locked.

Only future matches are simulated.

---

# 8. Rerun Golden Boot Predictions

```powershell
python src\models\golden_boot_model.py
python src\simulation\simulate_golden_boot.py
```

This refreshes current goals, expected final goals, Golden Boot probability and Top 3 probability.

---

# 9. Core ML Models

Do NOT retrain the core ML models every time the World Cup dataset changes.

Only retrain when the historic training data changes or the model itself is intentionally updated.

Core retraining commands:

```powershell
python src\features\build_match_features.py
python src\models\elo_model.py
python src\training\train_match_result.py
python src\training\train_scoreline.py
python src\training\train_market_models.py
```

For a normal World Cup dataset update, skip these commands.

---

# 10. Run Tests

```powershell
pytest -q
```

Do not deploy if tests fail.

---

# 11. Test API

```powershell
uvicorn app.main:app --reload
```

Check:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/v1/tournament/bracket
http://127.0.0.1:8000/api/v1/tournament/live-simulation
http://127.0.0.1:8000/api/v1/scorers/golden-boot-simulation
http://127.0.0.1:8000/api/v1/predictions/history
```

---

# 12. Test Frontend

From:

```text
frontend/
```

run:

```powershell
npm run dev
```

Verify:

```text
Dashboard
Predictor
Tournament
Bracket
Golden Boot
Rankings
```

Check that completed knockout matches show prediction vs actual result.

Then:

```powershell
npm run build
```

---

# 13. Commit and Deploy

From the project root:

```powershell
git status
git add .
git commit -m "Update World Cup tournament data and predictions"
git push
```

Render and Vercel redeploy from the main branch.

---

# Quick Update Commands

Before replacing dataset:

```powershell
cd ml-service
python src\prediction\snapshot_knockout_predictions.py
```

After replacing dataset:

```powershell
python src\data\build_live_matches.py
python src\prediction\update_prediction_results.py
python src\simulation\simulate_live_tournament.py
python src\models\golden_boot_model.py
python src\simulation\simulate_golden_boot.py
pytest -q
```

Then:

```powershell
cd ..\frontend
npm run build
```

Then:

```powershell
cd ..
git add .
git commit -m "Update World Cup tournament data and predictions"
git push
```