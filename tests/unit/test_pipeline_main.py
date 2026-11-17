from datetime import date

import pytest

from nba_pipeline import __main__ as entrypoint


def test_days_back_defaults_to_ten():
    assert entrypoint.parse_args([]).days_back == 10


def test_days_back_accepts_explicit_positive_value():
    assert entrypoint.parse_args(["--days-back", "3"]).days_back == 3


@pytest.mark.parametrize("value", ["0", "-3", "abc"])
def test_days_back_must_be_a_positive_integer(value):
    with pytest.raises(SystemExit):
        entrypoint.parse_args(["--days-back", value])


def test_main_wires_real_stages_with_the_resolved_window(monkeypatch):
    calls = []

    def fake_stage(name):
        def stage(argv):
            calls.append((name, list(argv)))
            return 0

        return stage

    monkeypatch.setattr(entrypoint, "utc_today", lambda: date(2024, 11, 20))
    monkeypatch.setattr(entrypoint, "ingest_main", fake_stage("ingest"))
    monkeypatch.setattr(entrypoint, "silver_main", fake_stage("silver"))
    monkeypatch.setattr(entrypoint, "gold_main", fake_stage("gold"))

    exit_code = entrypoint.main(["--days-back", "10"])

    assert exit_code == 0
    assert calls == [
        ("ingest", ["--date-from", "2024-11-10", "--date-to", "2024-11-20"]),
        ("silver", ["--season", "2024-25"]),
        ("gold", ["--season", "2024-25"]),
    ]


def test_main_returns_error_when_a_stage_fails(monkeypatch):
    monkeypatch.setattr(entrypoint, "utc_today", lambda: date(2024, 11, 20))
    monkeypatch.setattr(entrypoint, "ingest_main", lambda argv: 1)

    assert entrypoint.main([]) == 1
