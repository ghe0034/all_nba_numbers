"""Lectura de Parquet Silver y escritura de Parquet Gold en Google Cloud Storage."""

import io
from typing import Any

import pandas as pd

from nba_silver.gcs_io import (
    PARQUET_CONTENT_TYPE,
    SEASON_PATTERN,
    SILVER_OBJECT_NAME,
    SILVER_PREFIX,
    build_silver_object_name,
    make_bucket,
)

GOLD_PREFIX = "gold"
GOLD_TABLE_NAME = "matchup_features"
SEASON_DISCOVERY_TABLE = "team_game_logs"

__all__ = ["make_bucket"]


def build_gold_object_name(season: str) -> str:
    """Ruta `gold/matchup_features/season={temporada}/data.parquet`; sobrescribir es idempotente."""
    return f"{GOLD_PREFIX}/{GOLD_TABLE_NAME}/season={season}/{SILVER_OBJECT_NAME}"


def read_silver_table(bucket: Any, table_name: str, season: str) -> pd.DataFrame | None:
    """Lee el Parquet Silver de una tabla/temporada; devuelve None si no existe."""
    object_name = build_silver_object_name(table_name, season)
    exists = any(
        blob.name == object_name for blob in bucket.list_blobs(prefix=object_name)
    )
    if not exists:
        return None
    return pd.read_parquet(io.BytesIO(bucket.blob(object_name).download_as_bytes()))


def discover_silver_seasons(bucket: Any) -> list[str]:
    """Temporadas `YYYY-YY` presentes en Silver (según team_game_logs), ordenadas."""
    prefix = f"{SILVER_PREFIX}/{SEASON_DISCOVERY_TABLE}/"
    seasons = set()
    for blob in bucket.list_blobs(prefix=prefix):
        match = SEASON_PATTERN.search(blob.name)
        if match is not None:
            seasons.add(match.group(1))
    return sorted(seasons)


def upload_parquet(bucket: Any, season: str, df: pd.DataFrame) -> str:
    """Serializa `df` a Parquet en memoria (snappy, sin índice) y lo sube. Devuelve la ruta."""
    buffer = io.BytesIO()
    df.to_parquet(buffer, engine="pyarrow", compression="snappy", index=False)

    object_name = build_gold_object_name(season)
    bucket.blob(object_name).upload_from_string(
        buffer.getvalue(), content_type=PARQUET_CONTENT_TYPE
    )
    return object_name
