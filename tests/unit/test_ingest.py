from datetime import date

from nba_ingest.catalog import EndpointDefinition
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
        fetch=lambda endpoint, season: b"{}",
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
            raise RuntimeError("boom")

    tasks = build_tasks([ENDPOINT_A], SEASONS)

    results = run_tasks(tasks, failing_for_first_task)

    assert [result.success for result in results] == [False, True]
    assert "boom" in results[0].error


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
