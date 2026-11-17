import io
import json

import pandas as pd

from nba_silver.pipeline import SeasonResult, process_season, run_pipeline
from nba_silver.schemas import PLAYER_GAME_LOGS, TEAM_GAME_LOGS

TEAM_BRONZE = "bronze/leaguegamelog_teams/season=2024-25/download_date=2024-10-23/leaguegamelog_teams.json"
TEAM_INCREMENTAL = (
    "bronze_incremental/leaguegamelog_teams/season=2024-25/date_from=2024-10-20/"
    "date_to=2024-10-23/download_date=2024-10-24/leaguegamelog_teams.json"
)
TEAM_SILVER = "silver/team_game_logs/season=2024-25/data.parquet"


def team_record(game_id: str, team_id: int, pts: int) -> dict:
    return {
        "SEASON_ID": "22024",
        "TEAM_ID": team_id,
        "TEAM_ABBREVIATION": "LAL",
        "TEAM_NAME": "Los Angeles Lakers",
        "GAME_ID": game_id,
        "GAME_DATE": "2024-10-22",
        "MATCHUP": "LAL vs. DEN",
        "WL": "W",
        "PTS": pts,
    }


def payload(records: list[dict]) -> bytes:
    headers = list(records[0].keys())
    rows = [[record[header] for header in headers] for record in records]
    return json.dumps(
        {"resultSets": [{"name": "x", "headers": headers, "rowSet": rows}]}
    ).encode()


def test_process_season_merges_bronze_and_incremental_keeping_latest_version(
    fake_bucket,
):
    fake_bucket.objects[TEAM_BRONZE] = payload(
        [team_record("0022400001", 1610612747, 100)]
    )
    fake_bucket.objects[TEAM_INCREMENTAL] = payload(
        [
            team_record("0022400001", 1610612747, 120),
            team_record("0022400002", 1610612747, 90),
        ]
    )

    result = process_season(fake_bucket, TEAM_GAME_LOGS, "2024-25")

    restored = pd.read_parquet(io.BytesIO(fake_bucket.objects[TEAM_SILVER]))
    assert result == SeasonResult(
        "team_game_logs", "2024-25", row_count=2, written=True
    )
    assert len(restored) == 2
    assert restored.loc[restored["game_id"] == "0022400001", "pts"].iloc[0] == 120
    assert "_download_date" not in restored.columns


def test_process_season_skips_write_when_season_has_no_files(fake_bucket):
    result = process_season(fake_bucket, TEAM_GAME_LOGS, "2024-25")

    assert result == SeasonResult(
        "team_game_logs", "2024-25", row_count=0, written=False
    )
    assert TEAM_SILVER not in fake_bucket.objects


def test_process_season_skips_write_when_all_fragments_have_zero_rows(fake_bucket):
    empty_payload = json.dumps(
        {
            "resultSets": [
                {"name": "x", "headers": ["SEASON_ID", "TEAM_ID"], "rowSet": []}
            ]
        }
    ).encode()
    fake_bucket.objects[TEAM_BRONZE] = empty_payload

    result = process_season(fake_bucket, TEAM_GAME_LOGS, "2024-25")

    assert result.written is False
    assert TEAM_SILVER not in fake_bucket.objects


def test_process_season_converts_player_minutes_mm_ss_to_decimal(fake_bucket):
    player_record = {
        "SEASON_ID": "22024",
        "PLAYER_ID": 2544,
        "PLAYER_NAME": "LeBron James",
        "TEAM_ID": 1610612747,
        "TEAM_ABBREVIATION": "LAL",
        "GAME_ID": "0022400001",
        "GAME_DATE": "2024-10-22",
        "MATCHUP": "LAL vs. DEN",
        "MIN": "32:30",
        "PTS": 25,
    }
    fake_bucket.objects[
        "bronze/leaguegamelog/season=2024-25/download_date=2024-10-23/leaguegamelog.json"
    ] = payload([player_record])
    silver_name = "silver/player_game_logs/season=2024-25/data.parquet"

    process_season(fake_bucket, PLAYER_GAME_LOGS, "2024-25")

    restored = pd.read_parquet(io.BytesIO(fake_bucket.objects[silver_name]))
    assert restored["min"].iloc[0] == 32.5


def test_run_pipeline_returns_one_result_per_spec_and_season(fake_bucket):
    fake_bucket.objects[TEAM_BRONZE] = payload(
        [team_record("0022400001", 1610612747, 100)]
    )

    results = run_pipeline(fake_bucket, [TEAM_GAME_LOGS], ["2024-25", "2023-24"])

    assert [(result.season, result.written) for result in results] == [
        ("2024-25", True),
        ("2023-24", False),
    ]
