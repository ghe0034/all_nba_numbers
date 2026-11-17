import io

import pandas as pd
import pyarrow.parquet as pq

from nba_silver.gcs_io import (
    build_silver_object_name,
    discover_seasons,
    extract_download_date,
    read_season_fragments,
    upload_parquet,
)

BRONZE_PATH = (
    "bronze/leaguegamelog/season=2024-25/download_date=2024-10-23/leaguegamelog.json"
)
INCREMENTAL_PATH = (
    "bronze_incremental/leaguegamelog/season=2024-25/date_from=2024-10-01/"
    "date_to=2024-10-07/download_date=2024-10-08/leaguegamelog.json"
)


def test_extract_download_date_from_bronze_path():
    assert extract_download_date(BRONZE_PATH) == "2024-10-23"


def test_extract_download_date_from_incremental_path():
    assert extract_download_date(INCREMENTAL_PATH) == "2024-10-08"


def test_extract_download_date_raises_when_path_has_no_download_date():
    try:
        extract_download_date("bronze/leaguegamelog/season=2024-25/leaguegamelog.json")
    except ValueError as error:
        assert "download_date" in str(error)
    else:
        raise AssertionError("Debería lanzar ValueError")


def test_read_season_fragments_reads_bronze_and_incremental_files(fake_bucket):
    fake_bucket.objects[BRONZE_PATH] = b'{"bronze": true}'
    fake_bucket.objects[INCREMENTAL_PATH] = b'{"incremental": true}'

    fragments = read_season_fragments(fake_bucket, "leaguegamelog", "2024-25")

    assert [fragment.download_date for fragment in fragments] == [
        "2024-10-23",
        "2024-10-08",
    ]
    assert fragments[0].raw_json == b'{"bronze": true}'
    assert fragments[1].raw_json == b'{"incremental": true}'


def test_read_season_fragments_ignores_other_seasons_endpoints_and_non_json(
    fake_bucket,
):
    fake_bucket.objects[
        "bronze/leaguegamelog/season=2023-24/download_date=2024-01-01/leaguegamelog.json"
    ] = b"{}"
    fake_bucket.objects[
        "bronze/leaguegamelog_teams/season=2024-25/download_date=2024-10-23/leaguegamelog_teams.json"
    ] = b"{}"
    fake_bucket.objects[
        "bronze/leaguegamelog/season=2024-25/download_date=2024-10-23/notes.txt"
    ] = b"x"

    fragments = read_season_fragments(fake_bucket, "leaguegamelog", "2024-25")

    assert fragments == []


def test_read_season_fragments_returns_empty_list_when_season_has_no_files(fake_bucket):
    assert read_season_fragments(fake_bucket, "leaguegamelog", "2024-25") == []


def test_discover_seasons_returns_sorted_unique_seasons_from_both_prefixes(fake_bucket):
    fake_bucket.objects[BRONZE_PATH] = b"{}"
    fake_bucket.objects[INCREMENTAL_PATH] = b"{}"
    fake_bucket.objects[
        "bronze/leaguegamelog/season=2023-24/download_date=2024-01-01/leaguegamelog.json"
    ] = b"{}"

    assert discover_seasons(fake_bucket, "leaguegamelog") == ["2023-24", "2024-25"]


def test_build_silver_object_name_uses_table_and_season_partition():
    assert (
        build_silver_object_name("team_game_logs", "2024-25")
        == "silver/team_game_logs/season=2024-25/data.parquet"
    )


def test_upload_parquet_writes_snappy_parquet_readable_back(fake_bucket):
    df = pd.DataFrame(
        {"game_id": ["0022400001"], "pts": pd.array([120], dtype="Int64")}
    )

    object_name = upload_parquet(fake_bucket, "team_game_logs", "2024-25", df)

    payload = fake_bucket.objects[object_name]
    restored = pd.read_parquet(io.BytesIO(payload))
    compression = (
        pq.ParquetFile(io.BytesIO(payload)).metadata.row_group(0).column(0).compression
    )
    assert object_name == "silver/team_game_logs/season=2024-25/data.parquet"
    assert restored["game_id"].iloc[0] == "0022400001"
    assert restored["pts"].iloc[0] == 120
    assert compression == "SNAPPY"
