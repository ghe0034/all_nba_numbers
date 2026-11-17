"""Orquestación Bronze -> Silver por (tabla, temporada)."""

from dataclasses import dataclass
from typing import Any

import pandas as pd

from nba_silver.gcs_io import read_season_fragments, upload_parquet
from nba_silver.schemas import TableSpec
from nba_silver.transform import clean_dataframe, deduplicate, parse_nba_json


@dataclass(frozen=True)
class SeasonResult:
    table_name: str
    season: str
    row_count: int
    written: bool


def process_season(bucket: Any, spec: TableSpec, season: str) -> SeasonResult:
    """Limpia y deduplica todos los fragmentos de una temporada y escribe su Parquet.

    Si no queda ninguna fila, no escribe nada: un Parquet vacío no aporta y confunde a los consumidores.
    """
    cleaned_frames = []
    for fragment in read_season_fragments(bucket, spec.bronze_endpoint, season):
        raw_df = parse_nba_json(fragment.raw_json, fragment.download_date)
        cleaned = clean_dataframe(raw_df, spec)
        if not cleaned.empty:
            cleaned_frames.append(cleaned)

    if not cleaned_frames:
        return SeasonResult(spec.table_name, season, row_count=0, written=False)

    combined = pd.concat(cleaned_frames, ignore_index=True)
    deduped = deduplicate(combined, spec)
    if deduped.empty:
        return SeasonResult(spec.table_name, season, row_count=0, written=False)

    upload_parquet(bucket, spec.table_name, season, deduped)
    return SeasonResult(spec.table_name, season, row_count=len(deduped), written=True)


def run_pipeline(
    bucket: Any, specs: list[TableSpec] | tuple[TableSpec, ...], seasons: list[str]
) -> list[SeasonResult]:
    """Procesa cada combinación (tabla, temporada) de forma secuencial."""
    return [
        process_season(bucket, spec, season) for spec in specs for season in seasons
    ]
