from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

HISTORIC_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "historic"
WORLDCUP_2026_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "worldcup_2026"


def load_csv(file_path: Path) -> pd.DataFrame:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return pd.read_csv(file_path)


def load_historic_data() -> dict[str, pd.DataFrame]:
    return {
        "results": load_csv(HISTORIC_DATA_DIR / "results.csv"),
        "shootouts": load_csv(HISTORIC_DATA_DIR / "shootouts.csv"),
        "goalscorers": load_csv(HISTORIC_DATA_DIR / "goalscorers.csv"),
        "former_names": load_csv(HISTORIC_DATA_DIR / "former_names.csv"),
    }


def load_worldcup_2026_data() -> dict[str, pd.DataFrame]:
    return {
        "teams": load_csv(WORLDCUP_2026_DATA_DIR / "teams.csv"),
        "venues": load_csv(WORLDCUP_2026_DATA_DIR / "venues.csv"),
        "tournament_stages": load_csv(WORLDCUP_2026_DATA_DIR / "tournament_stages.csv"),
        "referees": load_csv(WORLDCUP_2026_DATA_DIR / "referees.csv"),
        "matches": load_csv(WORLDCUP_2026_DATA_DIR / "matches.csv"),
        "matches_detailed": load_csv(WORLDCUP_2026_DATA_DIR / "matches_detailed.csv"),
        "squads_and_players": load_csv(WORLDCUP_2026_DATA_DIR / "squads_and_players.csv"),
        "match_events": load_csv(WORLDCUP_2026_DATA_DIR / "match_events.csv"),
        "match_lineups": load_csv(WORLDCUP_2026_DATA_DIR / "match_lineups.csv"),
        "match_team_stats": load_csv(WORLDCUP_2026_DATA_DIR / "match_team_stats.csv"),
        "player_stats": load_csv(WORLDCUP_2026_DATA_DIR / "player_stats.csv"),
    }


def print_dataset_summary(name: str, data: dict[str, pd.DataFrame]) -> None:
    print(f"\n{name}")
    print("-" * len(name))

    for file_name, df in data.items():
        print(f"{file_name}: {df.shape[0]:,} rows x {df.shape[1]:,} columns")


if __name__ == "__main__":
    historic_data = load_historic_data()
    worldcup_2026_data = load_worldcup_2026_data()

    print_dataset_summary("Historic Data", historic_data)
    print_dataset_summary("World Cup 2026 Data", worldcup_2026_data)

    print("\nHistoric results preview:")
    print(historic_data["results"].head())

    print("\n2026 matches preview:")
    print(worldcup_2026_data["matches"].head())