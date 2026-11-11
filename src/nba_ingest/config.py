"""Configuración leída desde variables de entorno (sin credenciales en código)."""

import os
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_PAUSE_SECONDS = 1.0  # provisional: se ajusta tras la prueba real


@dataclass(frozen=True)
class Settings:
    bucket_name: str
    gcs_project: str | None
    user_agent: str | None
    pause_seconds: float


def load_settings(environ: Mapping[str, str] = os.environ) -> Settings:
    """Lee la configuración; `NBA_GCS_BUCKET` es obligatoria."""
    bucket_name = environ.get("NBA_GCS_BUCKET", "").strip()
    if not bucket_name:
        raise ValueError("Falta la variable de entorno NBA_GCS_BUCKET")

    return Settings(
        bucket_name=bucket_name,
        gcs_project=environ.get("NBA_GCS_PROJECT") or None,
        user_agent=environ.get("NBA_USER_AGENT") or None,
        pause_seconds=float(environ.get("NBA_PAUSE_SECONDS", DEFAULT_PAUSE_SECONDS)),
    )
