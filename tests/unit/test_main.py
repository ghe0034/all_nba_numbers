from datetime import date
from types import SimpleNamespace
from typing import ClassVar

import pytest

from nba_ingest import __main__ as entrypoint
from nba_ingest.catalog import EndpointDefinition
from nba_ingest.client import NbaApiError
from nba_ingest.date_range import DateRange

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
def fake_bucket(monkeypatch, tmp_path):
    bucket = FakeBucket()
    FakeSession.instances = []
    monkeypatch.chdir(tmp_path)  # evita leer el .env real del repositorio
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


def test_days_back_selects_seasons_covering_the_window():
    args = entrypoint.parse_args(["--days-back", "10"])

    seasons, date_range = entrypoint.resolve_run_scope(args, date(2024, 10, 3), 10)

    assert date_range == DateRange(date(2024, 9, 23), date(2024, 10, 3))
    assert seasons == ["2023-24", "2024-25"]


def test_date_flags_select_explicit_window():
    args = entrypoint.parse_args(
        ["--date-from", "2024-01-08", "--date-to", "2024-01-14"]
    )

    seasons, date_range = entrypoint.resolve_run_scope(args, date(2026, 11, 15), 10)

    assert date_range == DateRange(date(2024, 1, 8), date(2024, 1, 14))
    assert seasons == ["2023-24"]


def test_no_range_arguments_keep_full_season_mode():
    args = entrypoint.parse_args([])

    seasons, date_range = entrypoint.resolve_run_scope(args, date(2026, 11, 15), 2)

    assert date_range is None
    assert seasons == ["2025-26", "2026-27"]


@pytest.mark.parametrize(
    "argv",
    [
        ["--seasons", "2", "--days-back", "7"],
        ["--seasons", "2", "--date-from", "2024-01-08", "--date-to", "2024-01-14"],
        ["--days-back", "7", "--date-from", "2024-01-08", "--date-to", "2024-01-14"],
    ],
)
def test_seasons_and_incremental_modes_are_mutually_exclusive(argv):
    with pytest.raises(SystemExit):
        entrypoint.parse_args(argv)


def test_date_to_requires_date_from():
    with pytest.raises(SystemExit):
        entrypoint.parse_args(["--date-to", "2024-01-14"])


def test_date_from_requires_date_to():
    with pytest.raises(SystemExit):
        entrypoint.parse_args(["--date-from", "2024-01-08"])


def test_date_from_after_date_to_is_rejected():
    with pytest.raises(SystemExit):
        entrypoint.parse_args(["--date-from", "2024-01-15", "--date-to", "2024-01-14"])


@pytest.mark.parametrize("value", ["01/08/2024", "2024-02-30", "ayer"])
def test_dates_must_be_iso_and_real(value):
    with pytest.raises(SystemExit):
        entrypoint.parse_args(["--date-from", value, "--date-to", "2024-01-14"])


@pytest.mark.parametrize("value", ["0", "-3", "abc"])
def test_days_back_must_be_a_positive_integer(value):
    with pytest.raises(SystemExit):
        entrypoint.parse_args(["--days-back", value])


def test_main_incremental_run_writes_only_under_bronze_incremental(
    fake_bucket, monkeypatch
):
    received_ranges = []

    def fake_fetch(endpoint, season, *, date_range=None, **kwargs):
        received_ranges.append(date_range)
        return b"{}"

    monkeypatch.setattr(entrypoint, "fetch_endpoint", fake_fetch)

    assert (
        entrypoint.main(["--date-from", "2024-01-08", "--date-to", "2024-01-14"]) == 0
    )

    assert received_ranges == [DateRange(date(2024, 1, 8), date(2024, 1, 14))]
    assert len(fake_bucket.uploaded_names) == 1
    assert all(
        name.startswith("bronze_incremental/") for name in fake_bucket.uploaded_names
    )
