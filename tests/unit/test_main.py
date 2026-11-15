from types import SimpleNamespace
from typing import ClassVar

import pytest

from nba_ingest import __main__ as entrypoint
from nba_ingest.catalog import EndpointDefinition
from nba_ingest.client import NbaApiError

ENDPOINT = EndpointDefinition("demo", "https://stats.nba.com/stats/demo", "Season", {})


class FakeSession:
    """Sesión falsa que registra si se cerró."""

    instances: ClassVar[list["FakeSession"]] = []

    def __init__(self):
        self.closed = False
        FakeSession.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.closed = True


class FakeBucket:
    def __init__(self):
        self.uploaded_names = []

    def blob(self, name):
        self.uploaded_names.append(name)
        return SimpleNamespace(upload_from_string=lambda body, content_type: None)


@pytest.fixture
def fake_bucket(monkeypatch):
    bucket = FakeBucket()
    FakeSession.instances = []
    monkeypatch.setenv("NBA_GCS_BUCKET", "bucket-test")
    monkeypatch.setenv("NBA_PAUSE_SECONDS", "0")
    monkeypatch.delenv("NBA_SEASONS_COUNT", raising=False)
    monkeypatch.setattr(entrypoint, "requests", SimpleNamespace(Session=FakeSession))
    monkeypatch.setattr(entrypoint, "make_bucket", lambda project, name: bucket)
    monkeypatch.setattr(entrypoint, "load_endpoints", lambda: [ENDPOINT])
    monkeypatch.setattr(entrypoint, "fetch_endpoint", lambda *args, **kwargs: b"{}")
    return bucket


def test_main_returns_zero_and_uploads_one_object_per_season(fake_bucket):
    assert entrypoint.main([]) == 0
    assert len(fake_bucket.uploaded_names) == 10


def test_main_closes_http_session(fake_bucket):
    entrypoint.main([])

    assert FakeSession.instances[0].closed


def test_main_returns_one_when_any_task_fails(fake_bucket, monkeypatch):
    def failing_fetch(*args, **kwargs):
        raise NbaApiError("boom")

    monkeypatch.setattr(entrypoint, "fetch_endpoint", failing_fetch)

    assert entrypoint.main([]) == 1


def test_seasons_cli_option_limits_the_run(fake_bucket):
    assert entrypoint.main(["--seasons", "1"]) == 0
    assert len(fake_bucket.uploaded_names) == 1


def test_seasons_env_var_limits_the_run_and_cli_overrides_it(fake_bucket, monkeypatch):
    monkeypatch.setenv("NBA_SEASONS_COUNT", "2")
    entrypoint.main([])
    assert len(fake_bucket.uploaded_names) == 2

    fake_bucket.uploaded_names.clear()
    entrypoint.main(["--seasons", "3"])
    assert len(fake_bucket.uploaded_names) == 3
