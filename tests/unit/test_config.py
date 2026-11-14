import pytest

from nba_ingest.config import load_settings


def test_settings_read_bucket_and_user_agent_from_environment():
    settings = load_settings(
        {"NBA_GCS_BUCKET": "mi-bucket", "NBA_USER_AGENT": "agente/1.0"}
    )

    assert settings.bucket_name == "mi-bucket"
    assert settings.user_agent == "agente/1.0"


def test_missing_bucket_is_rejected():
    with pytest.raises(ValueError, match="NBA_GCS_BUCKET"):
        load_settings({})


def test_pause_seconds_has_default_and_can_be_overridden():
    assert load_settings({"NBA_GCS_BUCKET": "b"}).pause_seconds > 0
    assert load_settings({"NBA_GCS_BUCKET": "b", "NBA_PAUSE_SECONDS": "2.5"}).pause_seconds == 2.5


def test_seasons_count_defaults_to_ten_and_can_be_overridden():
    assert load_settings({"NBA_GCS_BUCKET": "b"}).seasons_count == 10
    assert load_settings({"NBA_GCS_BUCKET": "b", "NBA_SEASONS_COUNT": "1"}).seasons_count == 1


def test_pause_jitter_has_default_and_can_be_overridden():
    assert load_settings({"NBA_GCS_BUCKET": "b"}).pause_jitter_seconds > 0
    settings = load_settings({"NBA_GCS_BUCKET": "b", "NBA_PAUSE_JITTER_SECONDS": "0.2"})
    assert settings.pause_jitter_seconds == 0.2
