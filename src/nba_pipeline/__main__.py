"""Punto de entrada único: `python -m nba_pipeline`. Bronze incremental -> Silver -> Gold."""

import argparse
from collections.abc import Sequence
from datetime import date, datetime, timezone

from nba_gold.__main__ import main as gold_main
from nba_ingest.__main__ import main as ingest_main
from nba_ingest.__main__ import positive_int
from nba_pipeline.orchestrator import resolve_date_range, run_pipeline
from nba_silver.__main__ import main as silver_main

DEFAULT_DAYS_BACK = 10


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="nba_pipeline")
    parser.add_argument(
        "--days-back",
        type=positive_int,
        default=DEFAULT_DAYS_BACK,
        help="Ventana incremental de Bronze en días hasta hoy (por defecto 10)",
    )
    return parser.parse_args(argv)


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    date_range = resolve_date_range(utc_today(), args.days_back)
    return run_pipeline(date_range, ingest_main, silver_main, gold_main)


if __name__ == "__main__":
    raise SystemExit(main())
