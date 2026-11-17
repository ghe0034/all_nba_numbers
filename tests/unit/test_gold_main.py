import io

import pytest

from nba_gold import __main__ as entrypoint
from nba_gold.gcs_io import build_gold_object_name

GAMES = [
    ("0022400001", "2024-10-22", "A", "B", 110, 100),
    ("0022400002", "2024-10-24", "B", "A", 95, 105),
]
TABLE_NAMES = ("team_game_logs", "team_advanced_logs", "player_game_logs")


@pytest.fixture
def configured_env(monkeypatch, fake_bucket):
    monkeypatch.setenv("NBA_GCS_BUCKET", "bucket-test")
    monkeypatch.delenv("NBA_GCS_PROJECT", raising=False)
    monkeypatch.setattr(entrypoint, "load_local_env", lambda: None)
    monkeypatch.setattr(entrypoint, "make_bucket", lambda project, name: fake_bucket)


@pytest.fixture
def seeded_bucket(fake_bucket, make_silver_frames):
    for season in ("2023-24", "2024-25"):
        for table_name, frame in zip(TABLE_NAMES, make_silver_frames(GAMES)):
            buffer = io.BytesIO()
            frame.to_parquet(buffer, index=False)
            fake_bucket.objects[f"silver/{table_name}/season={season}/data.parquet"] = (
                buffer.getvalue()
            )
    return fake_bucket


def test_parse_args_requires_season_or_all_seasons():
    with pytest.raises(SystemExit):
        entrypoint.parse_args([])


def test_parse_args_rejects_season_together_with_all_seasons():
    with pytest.raises(SystemExit):
        entrypoint.parse_args(["--season", "2024-25", "--all-seasons"])


def test_parse_args_rejects_malformed_season():
    with pytest.raises(SystemExit):
        entrypoint.parse_args(["--season", "2024/25"])


def test_main_with_season_writes_only_that_season(configured_env, seeded_bucket):
    exit_code = entrypoint.main(["--season", "2024-25"])

    assert exit_code == 0
    assert build_gold_object_name("2024-25") in seeded_bucket.objects
    assert build_gold_object_name("2023-24") not in seeded_bucket.objects


def test_main_all_seasons_discovers_seasons_from_silver(
    configured_env, seeded_bucket, capsys
):
    exit_code = entrypoint.main(["--all-seasons"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert build_gold_object_name("2023-24") in seeded_bucket.objects
    assert build_gold_object_name("2024-25") in seeded_bucket.objects
    assert "escritas: 2 | saltadas: 0" in output


def test_main_reports_skipped_season_without_silver(configured_env, capsys):
    entrypoint.main(["--season", "2024-25"])

    output = capsys.readouterr().out
    assert "SALTADO matchup_features 2024-25" in output
    assert "saltadas: 1" in output
