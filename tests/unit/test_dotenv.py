import os

from nba_ingest.__main__ import load_local_env


def test_dotenv_file_provides_variables_missing_from_environment(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("NBA_GCS_BUCKET=desde-env\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NBA_GCS_BUCKET", "temporal")
    monkeypatch.delenv("NBA_GCS_BUCKET")

    load_local_env()

    assert os.environ["NBA_GCS_BUCKET"] == "desde-env"


def test_real_environment_wins_over_dotenv_file(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("NBA_GCS_BUCKET=desde-env\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NBA_GCS_BUCKET", "desde-entorno")

    load_local_env()

    assert os.environ["NBA_GCS_BUCKET"] == "desde-entorno"


def test_missing_dotenv_file_is_not_an_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    load_local_env()
