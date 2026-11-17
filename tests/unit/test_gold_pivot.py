import pandas as pd

from nba_gold.features import pivot_home_away


def team_row(game_id, team_id, is_home, feature_value, pts=100.0, win=1.0):
    return {
        "game_id": game_id,
        "season_id": "22024",
        "game_date": pd.Timestamp("2024-10-22"),
        "team_id": team_id,
        "is_home": is_home,
        "pts": pts,
        "win": win,
        "x": feature_value,
    }


def test_one_row_per_game_with_home_and_away_prefixes():
    rows = [team_row("g1", "A", True, 1.0), team_row("g1", "B", False, 2.0)]

    result = pivot_home_away(pd.DataFrame(rows), ["x"])

    assert len(result) == 1
    row = result.iloc[0]
    assert (row["home_team_id"], row["away_team_id"]) == ("A", "B")
    assert (row["home_x"], row["away_x"]) == (1.0, 2.0)


def test_orphan_game_with_single_team_is_dropped():
    rows = [
        team_row("g1", "A", True, 1.0),
        team_row("g1", "B", False, 2.0),
        team_row("g2", "A", True, 1.0),
    ]

    result = pivot_home_away(pd.DataFrame(rows), ["x"])

    assert result["game_id"].tolist() == ["g1"]


def test_game_with_two_home_teams_is_dropped():
    rows = [
        team_row("g1", "A", True, 1.0),
        team_row("g1", "B", False, 2.0),
        team_row("g2", "A", True, 1.0),
        team_row("g2", "B", True, 2.0),
    ]

    result = pivot_home_away(pd.DataFrame(rows), ["x"])

    assert result["game_id"].tolist() == ["g1"]


def test_game_with_duplicated_rows_does_not_multiply_output():
    rows = [
        team_row("g1", "A", True, 1.0),
        team_row("g1", "A", True, 1.0),
        team_row("g1", "B", False, 2.0),
    ]

    result = pivot_home_away(pd.DataFrame(rows), ["x"])

    assert result.empty
