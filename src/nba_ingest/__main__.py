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
from nba_ingest.date_range import (
    DateRange,
    days_back_range,
    parse_iso_date,
    seasons_for_range,
)
from nba_ingest.gcs_uploader import make_bucket, upload_bytes
from nba_ingest.ingest import all_succeeded, build_tasks, run_task, run_tasks
from nba_ingest.seasons import last_seasons


def positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("debe ser un entero mayor que 0")
    return value


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="nba_ingest")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--seasons",
        type=int,
        help="Número de temporadas completas a descargar (prevalece sobre NBA_SEASONS_COUNT; por defecto 10)",
    )
    modes.add_argument(
        "--days-back",
        type=positive_int,
        help="Modo incremental: descarga los últimos N días hasta hoy a bronze_incremental/",
    )
    modes.add_argument(
        "--date-from",
        type=parse_iso_date,
        help="Modo incremental: fecha inicial YYYY-MM-DD (inclusive); requiere --date-to",
    )
    parser.add_argument(
        "--date-to",
        type=parse_iso_date,
        help="Modo incremental: fecha final YYYY-MM-DD (inclusive); requiere --date-from",
    )
    args = parser.parse_args(argv)
    if (args.date_from is None) != (args.date_to is None):
        parser.error("--date-from y --date-to deben usarse juntos")
    if args.date_from is not None and args.date_from > args.date_to:
        parser.error("--date-from no puede ser posterior a --date-to")
    return args


def resolve_run_scope(
    args: argparse.Namespace, today: date, default_seasons_count: int
) -> tuple[list[str], DateRange | None]:
    """Decide temporadas y rango: con rango es incremental; sin él, temporadas completas."""
    if args.days_back is not None:
        date_range = days_back_range(today, args.days_back)
    elif args.date_from is not None:
        date_range = DateRange(start=args.date_from, end=args.date_to)
    else:
        return last_seasons(today, args.seasons or default_seasons_count), None
    return seasons_for_range(date_range), date_range


def load_local_env() -> None:
    """Carga `.env` desde el directorio actual o sus padres; no sobrescribe el entorno real."""
    load_dotenv(find_dotenv(usecwd=True), override=False)


def main(argv: Sequence[str] | None = None) -> int:
    load_local_env()
    args = parse_args(argv)
    settings = load_settings()
    today = date.today()
    seasons, date_range = resolve_run_scope(args, today, settings.seasons_count)
    tasks = build_tasks(load_endpoints(), seasons, date_range)
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
