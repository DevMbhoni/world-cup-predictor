import unicodedata
import pandas as pd


TEAM_NAME_ALIASES = {
    # Ivory Coast
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "Ivory Coast": "Ivory Coast",

    # Cape Verde
    "Cabo Verde": "Cape Verde",
    "Cape Verde": "Cape Verde",

    # USA
    "USA": "United States",
    "United States": "United States",
    "United States of America": "United States",

    # Korea
    "Korea Republic": "South Korea",
    "South Korea": "South Korea",
    "Korea DPR": "North Korea",
    "North Korea": "North Korea",

    # Iran
    "IR Iran": "Iran",
    "Iran": "Iran",

    # Turkey
    "Türkiye": "Turkey",
    "Turkey": "Turkey",

    # Congo
    "DR Congo": "Congo DR",
    "Democratic Republic of Congo": "Congo DR",
    "Congo DR": "Congo DR",

    # Czech Republic
    "Czechia": "Czech Republic",
    "Czech Republic": "Czech Republic",

    # Curacao
    "Curaçao": "Curacao",
    "Curacao": "Curacao",

    # Bosnia
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Bosnia and Herzegovina": "Bosnia and Herzegovina",

    # Common naming variants
    "Republic of Ireland": "Ireland",
    "Ireland": "Ireland",

    "North Macedonia": "North Macedonia",
    "Macedonia": "North Macedonia",
}


def normalize_text(value: str) -> str:
    value = str(value).strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.replace("&", "and")
    value = value.replace("-", " ")
    value = " ".join(value.split())
    return value


def get_all_historical_teams(training_df: pd.DataFrame) -> list[str]:
    return (
        pd.concat(
            [training_df["home_team"], training_df["away_team"]],
            ignore_index=True,
        )
        .dropna()
        .unique()
        .tolist()
    )


def resolve_team_name(training_df: pd.DataFrame, team_name: str) -> str:
    all_teams = get_all_historical_teams(training_df)
    all_teams_set = set(all_teams)

    candidates = [
        team_name,
        TEAM_NAME_ALIASES.get(team_name),
    ]

    for candidate in candidates:
        if candidate and candidate in all_teams_set:
            return candidate

    normalized_team_map = {
        normalize_text(team): team
        for team in all_teams
    }

    for candidate in candidates:
        if not candidate:
            continue

        normalized_candidate = normalize_text(candidate)

        if normalized_candidate in normalized_team_map:
            return normalized_team_map[normalized_candidate]

    raise ValueError(
        f"No historical data found for team: {team_name}. "
        f"Add a mapping for it in TEAM_NAME_ALIASES inside team_name_resolver.py."
    )


def resolve_team_name_safe(training_df: pd.DataFrame, team_name: str, fallback: str = "United States") -> str:
    try:
        return resolve_team_name(training_df, team_name)
    except ValueError:
        return fallback