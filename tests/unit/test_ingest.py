from datetime import date

import pytest

from nba_ingest.catalog import EndpointDefinition
from nba_ingest.client import NbaApiError
from nba_ingest.date_range import DateRange
from nba_ingest.ingest import (
    IngestionTask,
    TaskResult,
    all_succeeded,
    build_tasks,
    run_task,
    run_tasks,
)

ENDPOINT_A = EndpointDefinition("a", "https://stats.nba.com/stats/a", "Season", {})
ENDPOINT_B = EndpointDefinition("b", "https://stats.nba.com/stats/b", "Season", {})
SEASONS = ["2024-25", "2025-26"]


def test_build_tasks_creates_one_task_per_endpoint_and_season():
    tasks = build_tasks([ENDPOINT_A, ENDPOINT_B], SEASONS)

    assert len(tasks) == 4
    assert tasks[0] == IngestionTask(ENDPOINT_A, "2024-25")
    assert tasks[-1] == IngestionTask(ENDPOINT_B, "2025-26")


def test_run_task_fetches_then_uploads_to_bronze_path():
    uploads = []

    run_task(
        IngestionTask(ENDPOINT_A, "2025-26"),
        fetch=lambda endpoint, season, **kwargs: b"{}",
        upload=lambda path, body: uploads.append((path, body)),
        download_date=date(2026, 11, 11),
    )

    assert uploads == [
        (
            "bronze/a/season=2025-26/download_date=2026-11-11/a.json",
            b"{}",
        )
    ]


def test_run_tasks_continues_after_failure_and_reports_each_result():
    def failing_for_first_task(task):
        if task.season == "2024-25" and task.endpoint.id == "a":
            raise NbaApiError("boom")

    tasks = build_tasks([ENDPOINT_A], SEASONS)

    results = run_tasks(tasks, failing_for_first_task)

    assert [result.success for result in results] == [False, True]
    assert "boom" in results[0].error


@pytest.mark.parametrize("programming_error", [TypeError("bug"), KeyError("bug")])
def test_run_tasks_propagates_programming_errors(programming_error):
    def buggy_task(task):
        raise programming_error

    tasks = build_tasks([ENDPOINT_A], SEASONS)

    with pytest.raises(type(programming_error)):
        run_tasks(tasks, buggy_task)


def test_all_succeeded_requires_every_task_to_succeed():
    ok = TaskResult(IngestionTask(ENDPOINT_A, "2025-26"), success=True, error=None)
    failed = TaskResult(IngestionTask(ENDPOINT_A, "2024-25"), success=False, error="x")

    assert all_succeeded([ok, ok])
    assert not all_succeeded([ok, failed])


def test_all_succeeded_is_false_when_there_is_no_work():
    assert not all_succeeded([])


def test_run_tasks_pauses_between_tasks_but_not_after_the_last_one():
    pauses = []
    tasks = build_tasks([ENDPOINT_A], SEASONS)

    run_tasks(tasks, lambda task: None, pause_seconds=1.5, sleep=pauses.append)

    assert pauses == [1.5]


def test_pause_adds_random_jitter_on_top_of_base_pause():
    pauses = []
    tasks = build_tasks([ENDPOINT_A], SEASONS)

    run_tasks(
        tasks,
        lambda task: None,
        pause_seconds=1.0,
        jitter_seconds=0.5,
        sleep=pauses.append,
        uniform=lambda low, high: high,
    )

    assert pauses == [1.5]


def test_jitter_is_drawn_from_zero_to_jitter_seconds():
    drawn_ranges = []
    tasks = build_tasks([ENDPOINT_A], SEASONS)

    run_tasks(
        tasks,
        lambda task: None,
        pause_seconds=1.0,
        jitter_seconds=0.5,
        sleep=lambda seconds: None,
        uniform=lambda low, high: drawn_ranges.append((low, high)) or 0.0,
    )

    assert drawn_ranges == [(0.0, 0.5)]


def test_build_tasks_attaches_date_range_to_every_task():
    date_range = DateRange(date(2024, 1, 8), date(2024, 1, 14))

    tasks = build_tasks([ENDPOINT_A], ["2023-24"], date_range)

    assert tasks == [IngestionTask(ENDPOINT_A, "2023-24", date_range)]


def test_run_task_with_range_uploads_to_incremental_path_and_passes_range():
    uploads = []
    received_ranges = []
    date_range = DateRange(date(2024, 1, 8), date(2024, 1, 14))

    def fake_fetch(endpoint, season, *, date_range):
        received_ranges.append(date_range)
        return b"{}"

    run_task(
        IngestionTask(ENDPOINT_A, "2023-24", date_range),
        fetch=fake_fetch,
        upload=lambda path, body: uploads.append(path),
        download_date=date(2024, 1, 15),
    )

    assert received_ranges == [date_range]
    expected_path = (
        "bronze_incremental/a/season=2023-24/date_from=2024-01-08/"
        "date_to=2024-01-14/download_date=2024-01-15/a.json"
    )
    assert uploads == [expected_path]
