import json

import pytest

from nba_silver import __main__ as entrypoint

TEAM_BRONZE_2024 = "bronze/leaguegamelog_teams/season=2024-25/download_date=2024-10-23/leaguegamelog_teams.json"
TEAM_BRONZE_2023 = "bronze/leaguegamelog_teams/season=2023-24/download_date=2024-04-20/leaguegamelog_teams.json"


def team_payload(game_id: str) -> bytes:
    headers = [
        "SEASON_ID",
        "TEAM_ID",
        "TEAM_ABBREVIATION",
        "TEAM_NAME",
        "GAME_ID",
        "GAME_DATE",
        "MATCHUP",
        "WL",
        "PTS",
    ]
    row = [
        "22024",
        1610612747,
        "LAL",
        "Los Angeles Lakers",
        game_id,
        "2024-10-22",
        "LAL vs. DEN",
        "W",
        110,
    ]
    return json.dumps(
        {"resultSets": [{"name": "x", "headers": headers, "rowSet": [row]}]}
    ).encode()


@pytest.fixture
def configured_env(monkeypatch):
    monkeypatch.setenv("NBA_GCS_BUCKET", "bucket-test")
    monkeypatch.delenv("NBA_GCS_PROJECT", raising=False)
    monkeypatch.setattr(entrypoint, "load_local_env", lambda: None)


def test_parse_args_requires_season_or_all_seasons():
    with pytest.raises(SystemExit):
        entrypoint.parse_args([])


def test_parse_args_rejects_season_together_with_all_seasons():
    with pytest.raises(SystemExit):
        entrypoint.parse_args(["--season", "2024-25", "--all-seasons"])


def test_parse_args_rejects_malformed_season():
    with pytest.raises(SystemExit):
        entrypoint.parse_args(["--season", "2024/25"])


def test_parse_args_rejects_unknown_table():
    with pytest.raises(SystemExit):
        entrypoint.parse_args(["--all-seasons", "--table", "no_such_table"])


def test_parse_args_table_defaults_to_none_meaning_all_tables():
    args = entrypoint.parse_args(["--all-seasons"])

    assert args.table is None


def test_load_settings_requires_bucket_name(monkeypatch):
    monkeypatch.delenv("NBA_GCS_BUCKET", raising=False)

    with pytest.raises(ValueError, match="NBA_GCS_BUCKET"):
        entrypoint.load_settings()


def test_load_settings_reads_project_and_bucket():
    settings = entrypoint.load_settings({"NBA_GCS_BUCKET": "b", "NBA_GCS_PROJECT": "p"})

    assert (settings.bucket_name, settings.gcs_project) == ("b", "p")


def test_main_with_season_and_table_writes_only_that_table(
    monkeypatch, configured_env, fake_bucket
):
    fake_bucket.objects[TEAM_BRONZE_2024] = team_payload("0022400001")
    monkeypatch.setattr(entrypoint, "make_bucket", lambda project, name: fake_bucket)

    exit_code = entrypoint.main(["--season", "2024-25", "--table", "team_game_logs"])

    assert exit_code == 0
    assert "silver/team_game_logs/season=2024-25/data.parquet" in fake_bucket.objects
    assert len(fake_bucket.objects) == 2  # bronze original + silver


def test_main_all_seasons_discovers_seasons_from_bronze(
    monkeypatch, configured_env, fake_bucket, capsys
):
    fake_bucket.objects[TEAM_BRONZE_2024] = team_payload("0022400001")
    fake_bucket.objects[TEAM_BRONZE_2023] = team_payload("0022300001")
    monkeypatch.setattr(entrypoint, "make_bucket", lambda project, name: fake_bucket)

    exit_code = entrypoint.main(["--all-seasons", "--table", "team_game_logs"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "silver/team_game_logs/season=2023-24/data.parquet" in fake_bucket.objects
    assert "silver/team_game_logs/season=2024-25/data.parquet" in fake_bucket.objects
    assert "2023-24" in output and "2024-25" in output


def test_main_summary_reports_skipped_seasons(
    monkeypatch, configured_env, fake_bucket, capsys
):
    monkeypatch.setattr(entrypoint, "make_bucket", lambda project, name: fake_bucket)

    entrypoint.main(["--season", "2024-25", "--table", "team_game_logs"])

    output = capsys.readouterr().out
    assert "SALTADO team_game_logs 2024-25" in output
    assert "saltadas: 1" in output


def test_main_all_seasons_without_bronze_data_returns_zero(
    monkeypatch, configured_env, fake_bucket
):
    monkeypatch.setattr(entrypoint, "make_bucket", lambda project, name: fake_bucket)

    assert entrypoint.main(["--all-seasons", "--table", "team_game_logs"]) == 0
    assert not any(name.startswith("silver/") for name in fake_bucket.objects)
