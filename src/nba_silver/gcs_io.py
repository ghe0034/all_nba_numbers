"""Lectura de fragmentos Bronze y escritura de Parquet Silver en Google Cloud Storage."""

import io
import re
from dataclasses import dataclass
from typing import Any

import pandas as pd
from google.cloud import storage

BRONZE_PREFIX = "bronze"
INCREMENTAL_PREFIX = "bronze_incremental"
SILVER_PREFIX = "silver"
SILVER_OBJECT_NAME = "data.parquet"
PARQUET_CONTENT_TYPE = "application/octet-stream"

DOWNLOAD_DATE_PATTERN = re.compile(r"download_date=(\d{4}-\d{2}-\d{2})")
SEASON_PATTERN = re.compile(r"season=(\d{4}-\d{2})")


@dataclass(frozen=True)
class BronzeFragment:
    """Respuesta JSON cruda de una descarga, con la fecha en la que se hizo."""

    download_date: str
    raw_json: bytes


def make_bucket(project: str | None, bucket_name: str) -> Any:
    """Crea el cliente de GCS y devuelve el bucket de origen/destino."""
    return storage.Client(project=project).bucket(bucket_name)


def extract_download_date(object_name: str) -> str:
    """Extrae `YYYY-MM-DD` de `download_date=` en la ruta Bronze (bronze o incremental)."""
    match = DOWNLOAD_DATE_PATTERN.search(object_name)
    if match is None:
        raise ValueError(f"Ruta Bronze sin download_date: {object_name}")
    return match.group(1)


def read_season_fragments(
    bucket: Any, endpoint_id: str, season: str
) -> list[BronzeFragment]:
    """Descarga todos los JSON de una temporada, tanto de carga completa como incremental."""
    fragments = []
    for root_prefix in (BRONZE_PREFIX, INCREMENTAL_PREFIX):
        prefix = f"{root_prefix}/{endpoint_id}/season={season}/"
        for blob in bucket.list_blobs(prefix=prefix):
            if not blob.name.endswith(".json"):
                continue
            fragments.append(
                BronzeFragment(
                    download_date=extract_download_date(blob.name),
                    raw_json=bucket.blob(blob.name).download_as_bytes(),
                )
            )
    return fragments


def discover_seasons(bucket: Any, endpoint_id: str) -> list[str]:
    """Temporadas `YYYY-YY` presentes en Bronze para un endpoint, ordenadas."""
    seasons = set()
    for root_prefix in (BRONZE_PREFIX, INCREMENTAL_PREFIX):
        for blob in bucket.list_blobs(prefix=f"{root_prefix}/{endpoint_id}/"):
            match = SEASON_PATTERN.search(blob.name)
            if match is not None:
                seasons.add(match.group(1))
    return sorted(seasons)


def build_silver_object_name(table_name: str, season: str) -> str:
    """Ruta `silver/{tabla}/season={temporada}/data.parquet`; sobrescribir es idempotente."""
    return f"{SILVER_PREFIX}/{table_name}/season={season}/{SILVER_OBJECT_NAME}"


def upload_parquet(bucket: Any, table_name: str, season: str, df: pd.DataFrame) -> str:
    """Serializa `df` a Parquet en memoria (snappy, sin índice) y lo sube. Devuelve la ruta."""
    buffer = io.BytesIO()
    df.to_parquet(buffer, engine="pyarrow", compression="snappy", index=False)

    object_name = build_silver_object_name(table_name, season)
    bucket.blob(object_name).upload_from_string(
        buffer.getvalue(), content_type=PARQUET_CONTENT_TYPE
    )
    return object_name
