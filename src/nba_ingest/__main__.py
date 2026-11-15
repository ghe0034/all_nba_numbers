"""Punto de entrada: `python -m nba_ingest`. Exit code 0 solo si todas las tareas tuvieron éxito."""

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from functools import partial

from curl_cffi import requests
from dotenv import find_dotenv, load_dotenv

from nba_ingest.catalog import load_endpoints
from nba_ingest.client import fetch_endpoint
from nba_ingest.config import load_settings
from nba_ingest.gcs_uploader import make_bucket, upload_bytes
from nba_ingest.ingest import all_succeeded, build_tasks, run_task, run_tasks
from nba_ingest.seasons import last_seasons


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="nba_ingest")
    parser.add_argument(
        "--seasons",
        type=int,
        help="Número de temporadas a descargar (prevalece sobre NBA_SEASONS_COUNT; por defecto 10)",
    )
    return parser.parse_args(argv)


def load_local_env() -> None:
    """Carga `.env` desde el directorio actual o sus padres; no sobrescribe el entorno real."""
    load_dotenv(find_dotenv(usecwd=True), override=False)


def main(argv: Sequence[str] | None = None) -> int:
    load_local_env()
    args = parse_args(argv)
    settings = load_settings()
    seasons_count = args.seasons or settings.seasons_count
    today = date.today()
    tasks = build_tasks(load_endpoints(), last_seasons(today, seasons_count))
    bucket = make_bucket(settings.gcs_project, settings.bucket_name)

    with requests.Session() as session:
        fetch = partial(
            fetch_endpoint,
            session=session,
            user_agent=settings.user_agent,
        )
        upload = partial(upload_bytes, bucket)
        results = run_tasks(
            tasks,
            partial(run_task, fetch=fetch, upload=upload, download_date=today),
            pause_seconds=settings.pause_seconds,
            jitter_seconds=settings.pause_jitter_seconds,
        )

    failures = [result for result in results if not result.success]
    for failure in failures:
        print(
            f"FALLO {failure.task.endpoint.id} {failure.task.season}: {failure.error}",
            file=sys.stderr,
        )
    print(f"Tareas: {len(results)} | fallos: {len(failures)}")
    return 0 if all_succeeded(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
