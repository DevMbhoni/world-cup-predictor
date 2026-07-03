from pathlib import Path
import sys
import pandas as pd

CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]
sys.path.append(str(SRC_DIR))

from data.load_data import load_historic_data, load_worldcup_2026_data

def section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def check_missing_values(name: str, df: pd.DataFrame) -> None:
    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)

    print(f"\n{name} Missing Values:")

    if missing.empty:
        print("No missing values found.")
    else:
        print(missing.to_string())


def check_duplicates(name: str, df: pd.DataFrame) -> None:
    duplicate_count = df.duplicated().sum()
    print(f"\n{name} Duplicate Rows: {duplicate_count}")


def check_historic_results(results: pd.DataFrame) -> None:
    section("Historic Results Validation")

    print(f"Rows: {len(results):,}")
    print(f"Date range: {results['date'].min()} to {results['date'].max()}")

    required_columns = [
        "date",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "tournament",
        "city",
        "country",
        "neutral",
    ]

    missing_columns = [col for col in required_columns if col not in results.columns]
    print(f"Missing required columns: {missing_columns if missing_columns else 'None'}")

    results["date"] = pd.to_datetime(results["date"], errors="coerce")

    invalid_dates = results["date"].isna().sum()
    print(f"Invalid dates: {invalid_dates}")

    negative_scores = results[
        (results["home_score"] < 0) | (results["away_score"] < 0)
    ]

    print(f"Negative score rows: {len(negative_scores)}")

    same_team_matches = results[
        results["home_team"].str.lower() == results["away_team"].str.lower()
    ]

    print(f"Home team same as away team rows: {len(same_team_matches)}")

    print(f"Unique teams: {pd.concat([results['home_team'], results['away_team']]).nunique():,}")
    print(f"Unique tournaments: {results['tournament'].nunique():,}")

    print("\nTop 15 tournaments:")
    print(results["tournament"].value_counts().head(15).to_string())

def check_goalscorers(goalscorers: pd.DataFrame) -> None:
    section("Historic Goalscorers Validation")

    print(f"Rows: {len(goalscorers):,}")

    required_columns = [
        "date",
        "home_team",
        "away_team",
        "team",
        "scorer",
        "minute",
        "own_goal",
        "penalty",
    ]

    missing_columns = [col for col in required_columns if col not in goalscorers.columns]
    print(f"Missing required columns: {missing_columns if missing_columns else 'None'}")

    goalscorers["date"] = pd.to_datetime(goalscorers["date"], errors="coerce")

    invalid_dates = goalscorers["date"].isna().sum()
    print(f"Invalid dates: {invalid_dates}")

    print(f"Unique scorers: {goalscorers['scorer'].nunique():,}")
    print(f"Own goals: {goalscorers['own_goal'].sum() if 'own_goal' in goalscorers else 'N/A'}")
    print(f"Penalties: {goalscorers['penalty'].sum() if 'penalty' in goalscorers else 'N/A'}")

def check_shootouts(shootouts: pd.DataFrame) -> None:
    section("Historic Shootouts Validation")

    print(f"Rows: {len(shootouts):,}")

    required_columns = [
        "date",
        "home_team",
        "away_team",
        "winner",
        "first_shooter",
    ]

    missing_columns = [col for col in required_columns if col not in shootouts.columns]
    print(f"Missing required columns: {missing_columns if missing_columns else 'None'}")

    shootouts["date"] = pd.to_datetime(shootouts["date"], errors="coerce")

    invalid_dates = shootouts["date"].isna().sum()
    print(f"Invalid dates: {invalid_dates}")

    invalid_winners = shootouts[
        ~shootouts["winner"].isin(shootouts["home_team"])
        & ~shootouts["winner"].isin(shootouts["away_team"])
    ]

    print(f"Potential invalid winner rows: {len(invalid_winners)}")

def check_worldcup_2026_foreign_keys(data: dict[str, pd.DataFrame]) -> None:
    section("World Cup 2026 Foreign Key Validation")

    teams = data["teams"]
    venues = data["venues"]
    stages = data["tournament_stages"]
    referees = data["referees"]
    matches = data["matches"]
    players = data["squads_and_players"]
    match_events = data["match_events"]
    match_lineups = data["match_lineups"]
    match_team_stats = data["match_team_stats"]
    player_stats = data["player_stats"]

    team_ids = set(teams["team_id"])
    venue_ids = set(venues["venue_id"])
    stage_ids = set(stages["stage_id"])
    referee_ids = set(referees["referee_id"])
    match_ids = set(matches["match_id"])
    player_ids = set(players["player_id"])

    checks = {
        "matches.home_team_id": set(matches["home_team_id"].dropna()) - team_ids,
        "matches.away_team_id": set(matches["away_team_id"].dropna()) - team_ids,
        "matches.venue_id": set(matches["venue_id"].dropna()) - venue_ids,
        "matches.stage_id": set(matches["stage_id"].dropna()) - stage_ids,
        "matches.referee_id": set(matches["referee_id"].dropna()) - referee_ids,
        "squads_and_players.team_id": set(players["team_id"].dropna()) - team_ids,
        "match_events.match_id": set(match_events["match_id"].dropna()) - match_ids,
        "match_events.team_id": set(match_events["team_id"].dropna()) - team_ids,
        "match_events.player_id": set(match_events["player_id"].dropna()) - player_ids,
        "match_lineups.match_id": set(match_lineups["match_id"].dropna()) - match_ids,
        "match_lineups.player_id": set(match_lineups["player_id"].dropna()) - player_ids,
        "match_lineups.team_id": set(match_lineups["team_id"].dropna()) - team_ids,
        "match_team_stats.match_id": set(match_team_stats["match_id"].dropna()) - match_ids,
        "match_team_stats.team_id": set(match_team_stats["team_id"].dropna()) - team_ids,
        "player_stats.player_id": set(player_stats["player_id"].dropna()) - player_ids,
        "player_stats.team_id": set(player_stats["team_id"].dropna()) - team_ids,
    }

    for check_name, invalid_values in checks.items():
        if invalid_values:
            print(f"{check_name}: INVALID values found -> {sorted(invalid_values)}")
        else:
            print(f"{check_name}: OK")


def check_worldcup_2026_tables(data: dict[str, pd.DataFrame]) -> None:
    section("World Cup 2026 Table Validation")

    for name, df in data.items():
        print(f"\n{name}: {df.shape[0]:,} rows x {df.shape[1]:,} columns")
        check_missing_values(name, df)
        check_duplicates(name, df)


def main() -> None:
    historic = load_historic_data()
    worldcup_2026 = load_worldcup_2026_data()

    section("Basic Dataset Checks")

    for name, df in historic.items():
        print(f"\nhistoric/{name}: {df.shape[0]:,} rows x {df.shape[1]:,} columns")
        check_missing_values(f"historic/{name}", df)
        check_duplicates(f"historic/{name}", df)

    check_historic_results(historic["results"])
    check_goalscorers(historic["goalscorers"])
    check_shootouts(historic["shootouts"])

    check_worldcup_2026_tables(worldcup_2026)
    check_worldcup_2026_foreign_keys(worldcup_2026)


if __name__ == "__main__":
    main()