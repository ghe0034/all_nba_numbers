"""Punto de entrada: `python -m nba_silver`. Convierte Bronze a Parquet en la capa Silver."""

import argparse
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv

from nba_silver.gcs_io import discover_seasons, make_bucket
from nba_silver.pipeline import run_pipeline
from nba_silver.schemas import ALL_SPECS, TableSpec

SEASON_FORMAT = re.compile(r"^\d{4}-\d{2}$")
SPECS_BY_TABLE = {spec.table_name: spec for spec in ALL_SPECS}


@dataclass(frozen=True)
class SilverSettings:
    bucket_name: str
    gcs_project: str | None


def load_settings(environ: Mapping[str, str] = os.environ) -> SilverSettings:
    """Lee la configuración; `NBA_GCS_BUCKET` es obligatoria."""
    bucket_name = environ.get("NBA_GCS_BUCKET", "").strip()
    if not bucket_name:
        raise ValueError("Falta la variable de entorno NBA_GCS_BUCKET")

    return SilverSettings(
        bucket_name=bucket_name,
        gcs_project=environ.get("NBA_GCS_PROJECT") or None,
    )


def season_text(text: str) -> str:
    if not SEASON_FORMAT.match(text):
        raise argparse.ArgumentTypeError("la temporada debe tener formato YYYY-YY")
    return text


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="nba_silver")
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument(
        "--season", type=season_text, help="Temporada a procesar, p. ej. 2024-25"
    )
    scope.add_argument(
        "--all-seasons",
        action="store_true",
        help="Procesa todas las temporadas presentes en Bronze",
    )
    parser.add_argument(
        "--table",
        choices=sorted(SPECS_BY_TABLE),
        help="Tabla a generar (por defecto, todas)",
    )
    return parser.parse_args(argv)


def load_local_env() -> None:
    """Carga `.env` desde el directorio actual o sus padres; no sobrescribe el entorno real."""
    load_dotenv(find_dotenv(usecwd=True), override=False)


def selected_specs(table_name: str | None) -> tuple[TableSpec, ...]:
    if table_name is None:
        return ALL_SPECS
    return (SPECS_BY_TABLE[table_name],)


def resolve_seasons(
    bucket, args: argparse.Namespace, specs: tuple[TableSpec, ...]
) -> list[str]:
    if args.season is not None:
        return [args.season]
    discovered = {
        season
        for spec in specs
        for season in discover_seasons(bucket, spec.bronze_endpoint)
    }
    return sorted(discovered)


def main(argv: Sequence[str] | None = None) -> int:
    load_local_env()
    args = parse_args(argv)
    settings = load_settings()
    bucket = make_bucket(settings.gcs_project, settings.bucket_name)
    specs = selected_specs(args.table)
    seasons = resolve_seasons(bucket, args, specs)

    results = run_pipeline(bucket, specs, seasons)

    for result in results:
        if result.written:
            print(f"OK {result.table_name} {result.season}: {result.row_count} filas")
        else:
            print(f"SALTADO {result.table_name} {result.season}: 0 filas")

    written = sum(result.written for result in results)
    print(f"Resumen: escritas: {written} | saltadas: {len(results) - written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
