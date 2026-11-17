import io

import pandas as pd

from nba_gold.gcs_io import build_gold_object_name
from nba_gold.pipeline import process_season, run_pipeline

GAMES = [
    ("0022400001", "2024-10-22", "A", "B", 110, 100),
    ("0022400002", "2024-10-24", "B", "A", 95, 105),
    ("0022400003", "2024-10-26", "A", "B", 99, 101),
]
TABLE_NAMES = ("team_game_logs", "team_advanced_logs", "player_game_logs")


def seed_silver(bucket, frames, season="2024-25", skip=()):
    for table_name, frame in zip(TABLE_NAMES, frames):
        if table_name in skip:
            continue
        buffer = io.BytesIO()
        frame.to_parquet(buffer, index=False)
        bucket.objects[f"silver/{table_name}/season={season}/data.parquet"] = (
            buffer.getvalue()
        )


def test_process_season_writes_one_row_per_game(fake_bucket, make_silver_frames):
    seed_silver(fake_bucket, make_silver_frames(GAMES))

    result = process_season(fake_bucket, "2024-25")

    assert (result.row_count, result.written) == (3, True)
    written = pd.read_parquet(
        io.BytesIO(fake_bucket.objects[build_gold_object_name("2024-25")])
    )
    assert written["game_id"].tolist() == [game[0] for game in GAMES]


def test_process_season_is_idempotent(fake_bucket, make_silver_frames):
    seed_silver(fake_bucket, make_silver_frames(GAMES))
    gold_name = build_gold_object_name("2024-25")

    process_season(fake_bucket, "2024-25")
    first = pd.read_parquet(io.BytesIO(fake_bucket.objects[gold_name]))
    process_season(fake_bucket, "2024-25")
    second = pd.read_parquet(io.BytesIO(fake_bucket.objects[gold_name]))

    pd.testing.assert_frame_equal(first, second)
    assert sum(name.startswith("gold/") for name in fake_bucket.objects) == 1


def test_process_season_skips_when_a_silver_table_is_missing(
    fake_bucket, make_silver_frames
):
    seed_silver(fake_bucket, make_silver_frames(GAMES), skip=("player_game_logs",))

    result = process_season(fake_bucket, "2024-25")

    assert (result.row_count, result.written) == (0, False)
    assert build_gold_object_name("2024-25") not in fake_bucket.objects


def test_run_pipeline_processes_each_season(fake_bucket, make_silver_frames):
    seed_silver(fake_bucket, make_silver_frames(GAMES))

    results = run_pipeline(fake_bucket, ["2023-24", "2024-25"])

    assert [(r.season, r.written) for r in results] == [
        ("2023-24", False),
        ("2024-25", True),
    ]
