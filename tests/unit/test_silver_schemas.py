from nba_silver.schemas import (
    ALL_SPECS,
    PLAYER_GAME_LOGS,
    TEAM_ADVANCED_LOGS,
    TEAM_GAME_LOGS,
)


def test_all_specs_exports_the_three_silver_tables():
    assert ALL_SPECS == (TEAM_GAME_LOGS, PLAYER_GAME_LOGS, TEAM_ADVANCED_LOGS)


def test_table_names_are_unique():
    names = [spec.table_name for spec in ALL_SPECS]

    assert len(names) == len(set(names))


def test_natural_keys_are_required_columns():
    for spec in ALL_SPECS:
        assert set(spec.natural_key) <= set(spec.required_cols), spec.table_name


def test_no_column_is_both_int_and_float():
    for spec in ALL_SPECS:
        assert not set(spec.int_cols) & set(spec.float_cols), spec.table_name


def test_player_minutes_are_float_so_mm_ss_survives_casting():
    assert "min" in PLAYER_GAME_LOGS.float_cols
    assert "min" not in PLAYER_GAME_LOGS.int_cols


def test_player_spec_points_to_leaguegamelog_endpoint():
    assert PLAYER_GAME_LOGS.bronze_endpoint == "leaguegamelog"
    assert PLAYER_GAME_LOGS.natural_key == ("game_id", "player_id")


def test_team_advanced_spec_uses_season_year_and_int_poss():
    assert TEAM_ADVANCED_LOGS.bronze_endpoint == "teamgamelogs_advanced"
    assert "season_year" in TEAM_ADVANCED_LOGS.required_cols
    assert TEAM_ADVANCED_LOGS.int_cols == ("poss",)
    assert {"off_rating", "def_rating", "net_rating", "pace"} <= set(
        TEAM_ADVANCED_LOGS.float_cols
    )
