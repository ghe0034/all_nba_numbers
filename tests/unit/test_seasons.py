from datetime import date

from nba_ingest.seasons import last_seasons, season_label


def test_season_label_formats_start_year_as_nba_season():
    assert season_label(2025) == "2025-26"


def test_season_label_handles_century_rollover():
    assert season_label(1999) == "1999-00"


def test_last_seasons_returns_ten_seasons_oldest_first():
    seasons = last_seasons(date(2025, 11, 11))

    assert len(seasons) == 10
    assert seasons[0] == "2016-17"
    assert seasons[-1] == "2025-26"


def test_season_changes_on_october_first():
    assert last_seasons(date(2025, 10, 1))[-1] == "2025-26"


def test_previous_season_still_current_on_september_30():
    assert last_seasons(date(2025, 9, 30))[-1] == "2024-25"


def test_december_31_belongs_to_season_starting_that_year():
    assert last_seasons(date(2025, 12, 31))[-1] == "2025-26"
