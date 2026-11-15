from datetime import date

from nba_ingest.bronze_path import build_bronze_path, build_incremental_bronze_path
from nba_ingest.date_range import DateRange


def test_path_is_partitioned_by_endpoint_season_and_download_date():
    path = build_bronze_path("leaguegamelog_player", "2025-26", date(2026, 11, 11))

    assert path == (
        "bronze/leaguegamelog_player/season=2025-26/"
        "download_date=2026-11-11/leaguegamelog_player.json"
    )


def test_same_inputs_produce_same_path():
    first = build_bronze_path("demo", "2024-25", date(2026, 1, 2))
    second = build_bronze_path("demo", "2024-25", date(2026, 1, 2))

    assert first == second


def test_incremental_path_is_partitioned_by_range_and_download_date():
    path = build_incremental_bronze_path(
        "teamgamelogs_advanced",
        "2023-24",
        DateRange(date(2024, 1, 8), date(2024, 1, 14)),
        date(2024, 1, 15),
    )

    assert path == (
        "bronze_incremental/teamgamelogs_advanced/season=2023-24/"
        "date_from=2024-01-08/date_to=2024-01-14/download_date=2024-01-15/"
        "teamgamelogs_advanced.json"
    )


def test_incremental_path_never_lives_under_full_bronze_prefix():
    path = build_incremental_bronze_path(
        "demo",
        "2023-24",
        DateRange(date(2024, 1, 8), date(2024, 1, 14)),
        date(2024, 1, 15),
    )

    assert not path.startswith("bronze/")
    assert path != build_bronze_path("demo", "2023-24", date(2024, 1, 15))
