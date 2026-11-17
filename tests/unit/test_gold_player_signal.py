import math

import pandas as pd
import pytest

from nba_gold.features import add_player_signal


def team_base(team_pts):
    return pd.DataFrame({"game_id": ["g1"], "team_id": ["A"], "pts": [team_pts]})


def players(points, team_id="A"):
    return pd.DataFrame(
        {
            "game_id": "g1",
            "team_id": team_id,
            "pts": pd.array(points, dtype="Int64"),
        }
    )


def test_share_uses_only_the_two_top_scorers():
    result = add_player_signal(team_base(100.0), players([40, 30, 20, 10]))

    assert result["top2_pts_share"].iloc[0] == pytest.approx(0.7)


def test_null_player_points_count_as_zero():
    result = add_player_signal(team_base(100.0), players([None, 50, 30]))

    assert result["top2_pts_share"].iloc[0] == pytest.approx(0.8)


def test_single_player_uses_what_is_available():
    result = add_player_signal(team_base(100.0), players([25]))

    assert result["top2_pts_share"].iloc[0] == pytest.approx(0.25)


def test_zero_team_points_gives_nan_instead_of_division_error():
    result = add_player_signal(team_base(0.0), players([0, 0]))

    assert math.isnan(result["top2_pts_share"].iloc[0])


def test_game_without_player_rows_gives_nan():
    result = add_player_signal(team_base(100.0), players([40, 30], team_id="Z"))

    assert math.isnan(result["top2_pts_share"].iloc[0])


def test_players_of_unknown_teams_do_not_add_rows():
    both_teams = pd.concat([players([40, 30]), players([50, 10], team_id="Z")])

    result = add_player_signal(team_base(100.0), both_teams)

    assert len(result) == 1
    assert result["top2_pts_share"].iloc[0] == pytest.approx(0.7)
