"""Punto de entrada: `python -m nba_gold`. Genera el dataset de features por partido desde Silver."""

import argparse
from collections.abc import Sequence

from nba_gold.gcs_io import discover_silver_seasons, make_bucket
from nba_gold.pipeline import run_pipeline
from nba_silver.__main__ import load_local_env, load_settings, season_text


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="nba_gold")
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument(
        "--season", type=season_text, help="Temporada a procesar, p. ej. 2024-25"
    )
    scope.add_argument(
        "--all-seasons",
        action="store_true",
        help="Procesa todas las temporadas presentes en Silver",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    load_local_env()
    args = parse_args(argv)
    settings = load_settings()
    bucket = make_bucket(settings.gcs_project, settings.bucket_name)
    seasons = [args.season] if args.season else discover_silver_seasons(bucket)

    results = run_pipeline(bucket, seasons)

    for result in results:
        if result.written:
            print(f"OK matchup_features {result.season}: {result.row_count} filas")
        else:
            print(f"SALTADO matchup_features {result.season}: 0 filas")

    written = sum(result.written for result in results)
    print(f"Resumen: escritas: {written} | saltadas: {len(results) - written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
