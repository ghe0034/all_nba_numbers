"""Construcción de la ruta particionada de la capa Bronze en GCS."""

from datetime import date

from nba_ingest.date_range import DateRange

BRONZE_PREFIX = "bronze"
INCREMENTAL_PREFIX = "bronze_incremental"


def build_bronze_path(endpoint_id: str, season: str, download_date: date) -> str:
    """Ruta `bronze/{endpoint}/season={temporada}/download_date={fecha}/{endpoint}.json`.

    Repetir la misma descarga el mismo día sobrescribe el mismo objeto (idempotencia).
    """
    return (
        f"{BRONZE_PREFIX}/{endpoint_id}/season={season}/"
        f"download_date={download_date.isoformat()}/{endpoint_id}.json"
    )


def build_incremental_bronze_path(
    endpoint_id: str,
    season: str,
    date_range: DateRange,
    download_date: date,
) -> str:
    """Ruta de carga por rango, separada de `bronze/` para no mezclarse con la temporada completa.

    Misma ventana y mismo día sobrescriben el mismo objeto (idempotencia).
    """
    return (
        f"{INCREMENTAL_PREFIX}/{endpoint_id}/season={season}/"
        f"date_from={date_range.start.isoformat()}/"
        f"date_to={date_range.end.isoformat()}/"
        f"download_date={download_date.isoformat()}/{endpoint_id}.json"
    )
