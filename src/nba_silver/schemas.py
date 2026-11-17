from dataclasses import dataclass


@dataclass(frozen=True)
class TableSpec:
    table_name: str
    bronze_endpoint: str
    natural_key: tuple[str, ...]
    required_cols: tuple[str, ...]
    int_cols: tuple[str, ...]
    float_cols: tuple[str, ...]


TEAM_GAME_LOGS = TableSpec(
    table_name="team_game_logs",
    bronze_endpoint="leaguegamelog_teams",
    natural_key=("game_id", "team_id"),
    required_cols=(
        "season_id",
        "team_id",
        "team_abbreviation",
        "team_name",
        "game_id",
        "game_date",
        "matchup",
        "wl",
        "pts",
    ),
    int_cols=(
        "min",
        "fgm",
        "fga",
        "fg3m",
        "fg3a",
        "ftm",
        "fta",
        "oreb",
        "dreb",
        "reb",
        "ast",
        "stl",
        "blk",
        "tov",
        "pf",
        "pts",
        "plus_minus",
    ),
    float_cols=("fg_pct", "fg3_pct", "ft_pct"),
)


# `min` va en float_cols: en temporadas antiguas llega como "MM:SS" y transform lo convierte a decimal.
PLAYER_GAME_LOGS = TableSpec(
    table_name="player_game_logs",
    bronze_endpoint="leaguegamelog",
    natural_key=("game_id", "player_id"),
    required_cols=(
        "season_id",
        "player_id",
        "player_name",
        "team_id",
        "team_abbreviation",
        "game_id",
        "game_date",
        "matchup",
        "pts",
    ),
    int_cols=(
        "fgm",
        "fga",
        "fg3m",
        "fg3a",
        "ftm",
        "fta",
        "oreb",
        "dreb",
        "reb",
        "ast",
        "stl",
        "blk",
        "tov",
        "pf",
        "pts",
        "plus_minus",
    ),
    float_cols=("min", "fg_pct", "fg3_pct", "ft_pct"),
)


TEAM_ADVANCED_LOGS = TableSpec(
    table_name="team_advanced_logs",
    bronze_endpoint="teamgamelogs_advanced",
    natural_key=("game_id", "team_id"),
    required_cols=(
        "season_year",
        "team_id",
        "team_abbreviation",
        "game_id",
        "game_date",
        "matchup",
        "off_rating",
        "def_rating",
        "net_rating",
        "pace",
    ),
    int_cols=("poss",),
    float_cols=(
        "e_off_rating",
        "off_rating",
        "e_def_rating",
        "def_rating",
        "e_net_rating",
        "net_rating",
        "ast_pct",
        "ast_to",
        "ast_ratio",
        "oreb_pct",
        "dreb_pct",
        "reb_pct",
        "tm_tov_pct",
        "efg_pct",
        "ts_pct",
        "e_pace",
        "pace",
        "pace_per40",
        "pie",
    ),
)


ALL_SPECS = (TEAM_GAME_LOGS, PLAYER_GAME_LOGS, TEAM_ADVANCED_LOGS)
