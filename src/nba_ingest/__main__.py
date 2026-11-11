"""Punto de entrada: `python -m nba_ingest`. Exit code 0 solo si todas las tareas tuvieron éxito."""

import sys
from datetime import date
from functools import partial

import requests

from nba_ingest.catalog import load_endpoints
from nba_ingest.client import fetch_endpoint
from nba_ingest.config import load_settings
from nba_ingest.gcs_uploader import make_bucket, upload_bytes
from nba_ingest.ingest import all_succeeded, build_tasks, run_task, run_tasks
from nba_ingest.rate_limiter import make_rate_limiter
from nba_ingest.seasons import last_seasons


def main() -> int:
    settings = load_settings()
    today = date.today()
    tasks = build_tasks(load_endpoints(), last_seasons(today))

    session = requests.Session()
    acquire_slot = make_rate_limiter(settings.min_interval_seconds)
    bucket = make_bucket(settings.gcs_project, settings.bucket_name)

    fetch = partial(
        fetch_endpoint,
        session=session,
        acquire_slot=acquire_slot,
        user_agent=settings.user_agent,
    )
    upload = partial(upload_bytes, bucket)
    results = run_tasks(
        tasks,
        partial(run_task, fetch=fetch, upload=upload, download_date=today),
    )

    failures = [result for result in results if not result.success]
    for failure in failures:
        print(f"FALLO {failure.task.endpoint.id} {failure.task.season}: {failure.error}", file=sys.stderr)
    print(f"Tareas: {len(results)} | fallos: {len(failures)}")
    return 0 if all_succeeded(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
