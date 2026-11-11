from datetime import date

from nba_ingest.bronze_path import build_bronze_path


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
