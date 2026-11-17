import pandas as pd
import pytest

from nba_gold.features import add_rolling_features, build_team_game_base


def build_games(count, start_pts=100, season_prefix="00224"):
    """Equipo A (local) anota 100, 101, ... y B (visitante) siempre 90."""
    return [
        (
            f"{season_prefix}{i:05d}",
            pd.Timestamp("2024-10-22") + pd.Timedelta(days=2 * i),
            "A",
            "B",
            start_pts + i,
            90,
        )
        for i in range(count)
    ]


@pytest.fixture
def base_for(make_silver_frames):
    def build(games, season_id="22024"):
        team_logs, adv_logs, _ = make_silver_frames(games, season_id)
        return build_team_game_base(team_logs, adv_logs)

    return build


def team_series(rolled, team_id, column):
    team_rows = rolled[rolled["team_id"] == team_id].sort_values("game_date")
    return team_rows[column].reset_index(drop=True)


def test_first_game_of_season_has_no_history(base_for):
    rolled = add_rolling_features(base_for(build_games(3)), ("pts",), (5,))

    assert pd.isna(team_series(rolled, "A", "pts_l5").iloc[0])


def test_rolling_excludes_current_game(base_for):
    rolled = add_rolling_features(base_for(build_games(6)), ("pts",), (5,))

    pts_l5 = team_series(rolled, "A", "pts_l5")
    assert pts_l5.iloc[1] == 100
    assert pts_l5.iloc[3] == pytest.approx((100 + 101 + 102) / 3)


def test_changing_current_game_does_not_change_its_own_feature(base_for):
    original = build_games(8)
    mutated = [*original[:5], (*original[5][:4], 999, 90), *original[6:]]

    rolled_original = add_rolling_features(base_for(original), ("pts",), (5,))
    rolled_mutated = add_rolling_features(base_for(mutated), ("pts",), (5,))

    before = team_series(rolled_original, "A", "pts_l5")
    after = team_series(rolled_mutated, "A", "pts_l5")
    assert before.iloc[5] == after.iloc[5]
    assert before.iloc[6] != after.iloc[6]


def test_min_periods_one_uses_partial_window(base_for):
    rolled = add_rolling_features(base_for(build_games(4)), ("pts",), (10,))

    pts_l10 = team_series(rolled, "A", "pts_l10")
    assert pts_l10.iloc[2] == pytest.approx((100 + 101) / 2)


def test_window_sizes_differ_once_history_exceeds_window(base_for):
    rolled = add_rolling_features(base_for(build_games(12)), ("pts",), (5, 10))

    assert team_series(rolled, "A", "pts_l5").iloc[11] == pytest.approx(108)
    assert team_series(rolled, "A", "pts_l10").iloc[11] == pytest.approx(105.5)


def test_teams_do_not_share_history(base_for):
    rolled = add_rolling_features(base_for(build_games(5)), ("pts",), (5,))

    assert (team_series(rolled, "B", "pts_l5").iloc[1:] == 90).all()


def test_season_debut_does_not_carry_over_previous_season(make_silver_frames):
    old_season = build_games(3, season_prefix="00223")
    new_season = build_games(3, start_pts=200, season_prefix="00224")
    old_team, old_adv, _ = make_silver_frames(old_season, "22023")
    new_team, new_adv, _ = make_silver_frames(new_season, "22024")
    base = build_team_game_base(
        pd.concat([old_team, new_team]), pd.concat([old_adv, new_adv])
    )

    rolled = add_rolling_features(base, ("pts",), (5,))

    new_rows = rolled[(rolled["team_id"] == "A") & (rolled["season_id"] == "22024")]
    new_rows = new_rows.sort_values("game_date")
    assert pd.isna(new_rows["pts_l5"].iloc[0])
    assert new_rows["pts_l5"].iloc[1] == 200


def test_shuffled_input_gives_same_features(base_for):
    base = base_for(build_games(8))

    expected = add_rolling_features(base, ("pts",), (5,))
    shuffled = add_rolling_features(base.sample(frac=1, random_state=0), ("pts",), (5,))

    def indexed(frame):
        return frame.set_index(["game_id", "team_id"]).sort_index()["pts_l5"]

    pd.testing.assert_series_equal(indexed(expected), indexed(shuffled))
