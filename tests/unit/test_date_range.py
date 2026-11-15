from datetime import date

import pytest

from nba_ingest.date_range import (
    DateRange,
    days_back_range,
    format_nba_date,
    parse_iso_date,
    seasons_for_range,
)


def test_days_back_range_ends_today_and_starts_n_days_earlier():
    assert days_back_range(date(2026, 1, 20), 10) == DateRange(
        start=date(2026, 1, 10), end=date(2026, 1, 20)
    )


def test_days_back_must_be_positive():
    with pytest.raises(ValueError, match="days_back"):
        days_back_range(date(2026, 1, 20), 0)


def test_date_range_rejects_start_after_end():
    with pytest.raises(ValueError, match="fecha inicial"):
        DateRange(start=date(2026, 1, 2), end=date(2026, 1, 1))


def test_date_range_accepts_single_day():
    assert DateRange(date(2026, 1, 1), date(2026, 1, 1)).start == date(2026, 1, 1)


def test_format_nba_date_uses_month_day_year():
    assert format_nba_date(date(2024, 1, 8)) == "01/08/2024"


def test_parse_iso_date_reads_year_month_day():
    assert parse_iso_date("2024-01-08") == date(2024, 1, 8)


@pytest.mark.parametrize("text", ["08/01/2024", "2024-13-01", "ayer", ""])
def test_parse_iso_date_rejects_invalid_text(text):
    with pytest.raises(ValueError):
        parse_iso_date(text)


def test_range_inside_one_season_yields_that_season():
    assert seasons_for_range(DateRange(date(2024, 1, 8), date(2024, 1, 14))) == [
        "2023-24"
    ]


def test_range_crossing_october_first_yields_two_seasons():
    date_range = DateRange(date(2024, 9, 28), date(2024, 10, 3))

    assert seasons_for_range(date_range) == ["2023-24", "2024-25"]
