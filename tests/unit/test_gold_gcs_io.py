import io

import pandas as pd

from nba_gold.gcs_io import (
    build_gold_object_name,
    discover_silver_seasons,
    read_silver_table,
    upload_parquet,
)

TEAM_SILVER_2024 = "silver/team_game_logs/season=2024-25/data.parquet"


def parquet_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    return buffer.getvalue()


def test_gold_object_name_follows_partition_convention():
    assert (
        build_gold_object_name("2024-25")
        == "gold/matchup_features/season=2024-25/data.parquet"
    )


def test_read_silver_table_returns_none_when_missing(fake_bucket):
    assert read_silver_table(fake_bucket, "team_game_logs", "2024-25") is None


def test_read_silver_table_roundtrips_parquet(fake_bucket):
    df = pd.DataFrame({"game_id": ["1", "2"], "pts": [100, 90]})
    fake_bucket.objects[TEAM_SILVER_2024] = parquet_bytes(df)

    result = read_silver_table(fake_bucket, "team_game_logs", "2024-25")

    pd.testing.assert_frame_equal(result, df)


def test_discover_silver_seasons_is_sorted_and_unique(fake_bucket):
    for season in ("2024-25", "2023-24"):
        fake_bucket.objects[f"silver/team_game_logs/season={season}/data.parquet"] = b""
    fake_bucket.objects["silver/player_game_logs/season=2020-21/data.parquet"] = b""

    assert discover_silver_seasons(fake_bucket) == ["2023-24", "2024-25"]


def test_upload_parquet_overwrites_same_object(fake_bucket):
    first = pd.DataFrame({"game_id": ["1"]})
    second = pd.DataFrame({"game_id": ["1", "2"]})

    path_first = upload_parquet(fake_bucket, "2024-25", first)
    path_second = upload_parquet(fake_bucket, "2024-25", second)

    assert path_first == path_second == build_gold_object_name("2024-25")
    assert list(fake_bucket.objects) == [path_second]
    pd.testing.assert_frame_equal(
        pd.read_parquet(io.BytesIO(fake_bucket.objects[path_second])), second
    )
