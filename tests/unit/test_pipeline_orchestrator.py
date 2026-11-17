from datetime import date

import pytest

from nba_ingest.date_range import DateRange, seasons_for_range
from nba_pipeline.orchestrator import resolve_date_range, run_pipeline


class StageRecorder:
    """Etapa falsa que registra (nombre, argv) en una lista compartida y devuelve códigos preconfigurados."""

    def __init__(self, name, calls, exit_codes=None, raises=None):
        self.name = name
        self.calls = calls
        self.exit_codes = list(exit_codes or [])
        self.raises = raises

    def __call__(self, argv):
        self.calls.append((self.name, list(argv)))
        if self.raises is not None:
            raise self.raises
        return self.exit_codes.pop(0) if self.exit_codes else 0


def make_stages(calls, **overrides):
    return {
        name: overrides.get(name) or StageRecorder(name, calls)
        for name in ("ingest", "silver", "gold")
    }


def seasons_for(today, days_back=10):
    return seasons_for_range(resolve_date_range(today, days_back))


# --- resolución de temporadas ----------------------------------------------


@pytest.mark.parametrize(
    ("today", "expected"),
    [
        (date(2024, 11, 20), ["2024-25"]),
        (date(2025, 1, 5), ["2024-25"]),
        (date(2025, 7, 14), ["2024-25"]),
        (date(2024, 10, 5), ["2023-24", "2024-25"]),
        (date(2024, 10, 10), ["2023-24", "2024-25"]),
        (date(2024, 10, 11), ["2024-25"]),
    ],
)
def test_seasons_are_resolved_from_the_executed_window(today, expected):
    assert seasons_for(today) == expected


def test_date_range_ends_today_and_starts_days_back_before():
    assert resolve_date_range(date(2024, 11, 20), 10) == DateRange(
        start=date(2024, 11, 10), end=date(2024, 11, 20)
    )


# --- orden y argumentos -----------------------------------------------------


def test_stages_run_in_order_bronze_then_silver_then_gold():
    calls = []
    date_range = resolve_date_range(date(2024, 10, 5), 10)

    exit_code = run_pipeline(date_range, *make_stages(calls).values())

    assert exit_code == 0
    assert calls == [
        ("ingest", ["--date-from", "2024-09-25", "--date-to", "2024-10-05"]),
        ("silver", ["--season", "2023-24"]),
        ("silver", ["--season", "2024-25"]),
        ("gold", ["--season", "2023-24"]),
        ("gold", ["--season", "2024-25"]),
    ]


def test_normal_week_reprocesses_only_the_active_season():
    calls = []
    date_range = resolve_date_range(date(2024, 11, 20), 10)

    run_pipeline(date_range, *make_stages(calls).values())

    assert [name for name, _ in calls] == ["ingest", "silver", "gold"]
    assert calls[1][1] == ["--season", "2024-25"]


# --- fail-fast --------------------------------------------------------------


def test_bronze_failure_stops_before_silver_and_gold():
    calls = []
    stages = make_stages(calls, ingest=StageRecorder("ingest", calls, [1]))

    exit_code = run_pipeline(
        resolve_date_range(date(2024, 11, 20), 10), *stages.values()
    )

    assert exit_code == 1
    assert [name for name, _ in calls] == ["ingest"]


def test_silver_failure_stops_remaining_silver_and_gold():
    calls = []
    stages = make_stages(calls, silver=StageRecorder("silver", calls, [2]))

    exit_code = run_pipeline(
        resolve_date_range(date(2024, 10, 5), 10), *stages.values()
    )

    assert exit_code == 1
    assert [name for name, _ in calls] == ["ingest", "silver"]


def test_gold_failure_returns_error_and_skips_remaining_gold():
    calls = []
    stages = make_stages(calls, gold=StageRecorder("gold", calls, [1]))

    exit_code = run_pipeline(
        resolve_date_range(date(2024, 10, 5), 10), *stages.values()
    )

    assert exit_code == 1
    assert [name for name, _ in calls].count("gold") == 1


def test_exception_in_a_stage_propagates_and_stops_the_pipeline():
    calls = []
    stages = make_stages(
        calls, silver=StageRecorder("silver", calls, raises=RuntimeError("boom"))
    )

    with pytest.raises(RuntimeError, match="boom"):
        run_pipeline(resolve_date_range(date(2024, 11, 20), 10), *stages.values())

    assert [name for name, _ in calls] == ["ingest", "silver"]
