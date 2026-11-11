"""Cliente HTTP para stats.nba.com: headers, rate limit, reintentos y validación."""

import json
import random
import time
from collections.abc import Callable
from typing import Any

from nba_ingest.catalog import EndpointDefinition
from nba_ingest.headers import build_headers
from nba_ingest.retry import compute_delay_seconds, parse_retry_after, should_retry

BASE_URL = "https://stats.nba.com"
SUCCESS_STATUS_CODE = 200
DEFAULT_TIMEOUT_SECONDS = (10.0, 60.0)  # (conexión, lectura)
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_BASE_DELAY_SECONDS = 2.0
DEFAULT_MAX_DELAY_SECONDS = 60.0


class NbaApiError(Exception):
    """La petición no pudo completarse (estado no recuperable o reintentos agotados)."""


def build_request_params(endpoint: EndpointDefinition, season: str) -> dict[str, str]:
    """Une los parámetros fijos del endpoint con la temporada de la tarea."""
    return {**endpoint.fixed_params, endpoint.season_param_name: season}


def fetch_endpoint(
    endpoint: EndpointDefinition,
    season: str,
    *,
    session: Any,
    acquire_slot: Callable[[], None],
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    base_delay: float = DEFAULT_BASE_DELAY_SECONDS,
    max_delay: float = DEFAULT_MAX_DELAY_SECONDS,
    timeout: tuple[float, float] = DEFAULT_TIMEOUT_SECONDS,
    user_agent: str | None = None,
) -> bytes:
    """Descarga un endpoint para una temporada y devuelve los bytes originales.

    `acquire_slot` se invoca antes de cada intento. El cuerpo se valida como JSON
    pero se devuelve sin re-serializar.
    """
    url = BASE_URL + endpoint.path
    params = build_request_params(endpoint, season)
    headers = build_headers(user_agent)
    attempt = 1

    while True:
        acquire_slot()
        response = session.get(url, params=params, headers=headers, timeout=timeout)

        if response.status_code == SUCCESS_STATUS_CODE:
            json.loads(response.content)
            return response.content

        if not should_retry(response.status_code, attempt, max_attempts):
            raise NbaApiError(
                f"{endpoint.id} {season}: HTTP {response.status_code} "
                f"tras {attempt} intento(s)"
            )

        retry_after = parse_retry_after(response.headers.get("Retry-After"))
        sleep(compute_delay_seconds(attempt, base_delay, max_delay, rng=rng, retry_after=retry_after))
        attempt += 1
