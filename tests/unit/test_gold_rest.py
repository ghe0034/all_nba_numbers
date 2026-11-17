import pandas as pd
import pytest

from nba_gold.features import add_rest_features, build_team_game_base

DATES = ["2024-10-22", "2024-10-23", "2024-10-26", "2024-10-29", "2024-11-05"]


@pytest.fixture
def rest_for(make_silver_frames):
    def build(dates, season_id="22024", prefix="00224"):
        games = [
            (f"{prefix}{i:05d}", date, "A", "B", 100, 90)
            for i, date in enumerate(dates)
        ]
        team_logs, adv_logs, _ = make_silver_frames(games, season_id)
        return build_team_game_base(team_logs, adv_logs)

    return build


def team_a(result):
    return (
        result[result["team_id"] == "A"].sort_values("game_date").reset_index(drop=True)
    )


def test_rest_days_between_consecutive_games(rest_for):
    result = team_a(add_rest_features(rest_for(DATES)))

    assert pd.isna(result["rest_days"].iloc[0])
    assert result["rest_days"].iloc[1:].tolist() == [1, 3, 3, 7]


def test_back_to_back_only_when_one_day_of_rest(rest_for):
    result = team_a(add_rest_features(rest_for(DATES)))

    assert result["is_b2b"].tolist() == [0, 1, 0, 0, 0]


def test_games_last_7d_counts_previous_window_only(rest_for):
    result = team_a(add_rest_features(rest_for(DATES)))

    assert result["games_last_7d"].tolist() == [0, 1, 2, 3, 1]


def test_games_last_7d_ignores_future_games(rest_for):
    with_future = team_a(add_rest_features(rest_for([*DATES, "2024-11-06"])))
    without_future = team_a(add_rest_features(rest_for(DATES)))

    assert (
        with_future["games_last_7d"].iloc[:5].tolist()
        == without_future["games_last_7d"].tolist()
    )


def test_season_debut_resets_rest_features(make_silver_frames):
    games_old = [("g1", "2024-04-10", "A", "B", 100, 90)]
    games_new = [("g2", "2024-04-11", "A", "B", 100, 90)]
    old_team, old_adv, _ = make_silver_frames(games_old, "22023")
    new_team, new_adv, _ = make_silver_frames(games_new, "22024")
    base = build_team_game_base(
        pd.concat([old_team, new_team]), pd.concat([old_adv, new_adv])
    )

    result = add_rest_features(base)

    new_season = result[(result["team_id"] == "A") & (result["season_id"] == "22024")]
    assert pd.isna(new_season["rest_days"].iloc[0])
    assert new_season["games_last_7d"].iloc[0] == 0


def test_scrambled_index_and_row_order_do_not_change_result(rest_for):
    base = rest_for(DATES)
    shuffled = base.sample(frac=1, random_state=1)

    expected = team_a(add_rest_features(base))
    result = team_a(add_rest_features(shuffled))

    pd.testing.assert_frame_equal(expected, result)
