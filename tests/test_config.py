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


def test_min_interval_has_default_and_can_be_overridden():
    default_settings = load_settings({"NBA_GCS_BUCKET": "b"})
    custom_settings = load_settings({"NBA_GCS_BUCKET": "b", "NBA_MIN_INTERVAL_SECONDS": "3.5"})

    assert default_settings.min_interval_seconds > 0
    assert custom_settings.min_interval_seconds == 3.5
