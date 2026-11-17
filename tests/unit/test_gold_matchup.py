import pandas as pd
import pytest

from nba_gold.features import (
    FEATURE_COLS,
    OUTPUT_COLUMNS,
    TARGET_COLS,
    build_matchup_features,
)

RAW_CURRENT_GAME_COLS = {
    "pts",
    "wl",
    "plus_minus",
    "win",
    "home_pts",
    "away_pts",
    "away_win",
}


def build_games(count=8):
    """A y B alternan localía; A siempre anota 100+i y B 90."""
    games = []
    for i in range(count):
        home, away = ("A", "B") if i % 2 == 0 else ("B", "A")
        home_pts, away_pts = (100 + i, 90) if home == "A" else (90, 100 + i)
        date = pd.Timestamp("2024-10-22") + pd.Timedelta(days=2 * i)
        games.append((f"00224{i:05d}", date, home, away, home_pts, away_pts))
    return games


def test_grain_is_one_row_per_game_with_fixed_columns(make_silver_frames):
    result = build_matchup_features(*make_silver_frames(build_games()))

    assert len(result) == 8
    assert result["game_id"].is_unique
    assert list(result.columns) == OUTPUT_COLUMNS


def test_diffs_are_home_minus_away(make_silver_frames):
    result = build_matchup_features(*make_silver_frames(build_games()))

    for col in FEATURE_COLS:
        expected = result[f"home_{col}"] - result[f"away_{col}"]
        pd.testing.assert_series_equal(
            result[f"diff_{col}"], expected, check_names=False
        )


def test_targets_come_from_the_current_game_score(make_silver_frames):
    result = build_matchup_features(*make_silver_frames(build_games()))

    first = result.iloc[0]
    assert (first["home_win"], first["target_point_diff"]) == (1, 10)
    second = result.iloc[1]  # B local con 90 frente a A con 101
    assert (second["home_win"], second["target_point_diff"]) == (0, -11)


def test_no_raw_current_game_column_is_exposed(make_silver_frames):
    result = build_matchup_features(*make_silver_frames(build_games()))

    assert RAW_CURRENT_GAME_COLS.isdisjoint(result.columns)


def test_season_debut_features_are_empty(make_silver_frames):
    result = build_matchup_features(*make_silver_frames(build_games()))

    first = result.iloc[0]
    assert pd.isna(first["home_pts_l5"]) and pd.isna(first["away_pts_l5"])
    assert pd.isna(first["home_rest_days"])
    assert first["home_games_last_7d"] == 0


def test_changing_a_game_score_only_changes_its_targets(make_silver_frames):
    original = build_games()
    mutated_index = 4
    mutated = list(original)
    mutated[mutated_index] = (*original[mutated_index][:4], 150, 60)

    before = build_matchup_features(*make_silver_frames(original))
    after = build_matchup_features(*make_silver_frames(mutated))

    feature_cols = [col for col in OUTPUT_COLUMNS if col not in TARGET_COLS]
    pd.testing.assert_frame_equal(
        before[feature_cols].iloc[[mutated_index]],
        after[feature_cols].iloc[[mutated_index]],
    )
    assert (
        before["target_point_diff"].iloc[mutated_index]
        != after["target_point_diff"].iloc[mutated_index]
    )


def test_output_is_deterministic_regardless_of_input_order(make_silver_frames):
    team_logs, adv_logs, player_logs = make_silver_frames(build_games())

    expected = build_matchup_features(team_logs, adv_logs, player_logs)
    shuffled = build_matchup_features(
        team_logs.sample(frac=1, random_state=3),
        adv_logs.sample(frac=1, random_state=4),
        player_logs.sample(frac=1, random_state=5),
    )

    pd.testing.assert_frame_equal(expected, shuffled)


@pytest.mark.parametrize(
    "broken_side", ["missing_team_row", "null_wl", "missing_advanced"]
)
def test_suspended_or_orphan_games_are_dropped(make_silver_frames, broken_side):
    team_logs, adv_logs, player_logs = make_silver_frames(build_games(4))
    broken_game = "0022400002"
    broken_team = "A"
    team_game = (team_logs["game_id"] == broken_game) & (
        team_logs["team_id"] == broken_team
    )
    adv_game = (adv_logs["game_id"] == broken_game) & (
        adv_logs["team_id"] == broken_team
    )

    if broken_side == "missing_team_row":
        team_logs = team_logs[~team_game]
    elif broken_side == "null_wl":
        team_logs = team_logs.assign(wl=team_logs["wl"].mask(team_game, None))
    else:
        adv_logs = adv_logs[~adv_game]

    result = build_matchup_features(team_logs, adv_logs, player_logs)

    assert broken_game not in set(result["game_id"])
    assert len(result) == 3


def test_games_without_any_advanced_data_give_empty_output(make_silver_frames):
    team_logs, adv_logs, player_logs = make_silver_frames(build_games(2))

    result = build_matchup_features(team_logs, adv_logs.iloc[0:0], player_logs)

    assert result.empty
    assert list(result.columns) == OUTPUT_COLUMNS
