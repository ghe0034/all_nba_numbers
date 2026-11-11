"""Construcción de la ruta particionada de la capa Bronze en GCS."""

from datetime import date

BRONZE_PREFIX = "bronze"


def build_bronze_path(endpoint_id: str, season: str, download_date: date) -> str:
    """Ruta `bronze/{endpoint}/season={temporada}/download_date={fecha}/{endpoint}.json`.

    Repetir la misma descarga el mismo día sobrescribe el mismo objeto (idempotencia).
    """
    return (
        f"{BRONZE_PREFIX}/{endpoint_id}/season={season}/"
        f"download_date={download_date.isoformat()}/{endpoint_id}.json"
    )
