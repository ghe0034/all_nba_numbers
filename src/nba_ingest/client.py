"""Cliente HTTP para stats.nba.com con reintentos exponenciales (tenacity)."""

import json
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from nba_ingest.catalog import EndpointDefinition
from nba_ingest.date_range import DateRange, format_nba_date
from nba_ingest.headers import build_headers

SUCCESS_STATUS_CODE = 200
RETRYABLE_STATUS_CODES = frozenset({403, 429, 500, 502, 503, 504})
DEFAULT_TIMEOUT_SECONDS = (10.0, 60.0)  # (conexión, lectura)
MAX_ATTEMPTS = 5


class NbaApiError(Exception):
    """La petición no pudo completarse."""


class NbaApiRetryableError(NbaApiError):
    """Respuesta con estado transitorio; es la única que se reintenta."""


@retry(
    retry=retry_if_exception_type(NbaApiRetryableError),
    stop=stop_after_attempt(MAX_ATTEMPTS),
    wait=wait_exponential_jitter(multiplier=2, max=60),
    reraise=True,
)
def _get_once(
    session: Any,
    url: str,
    params: dict[str, str],
    headers: dict[str, str],
    timeout: tuple[float, float],
    endpoint_id: str,
    season: str,
) -> bytes:
    """Un intento de petición; lanza un error reintentable si el estado es transitorio."""

    # Añadimos impersonate="chrome" para resolver el rechazo TLS (Error 10054)
    response = session.get(
        url, params=params, headers=headers, timeout=timeout, impersonate="chrome"
    )

    if response.status_code == SUCCESS_STATUS_CODE:
        json.loads(response.content)
        return response.content

    message = f"{endpoint_id} {season}: HTTP {response.status_code}"
    if response.status_code in RETRYABLE_STATUS_CODES:
        raise NbaApiRetryableError(message)
    raise NbaApiError(message)


def build_request_params(
    endpoint: EndpointDefinition,
    season: str,
    date_range: DateRange | None = None,
) -> dict[str, str]:
    """Une parámetros fijos, temporada y, si se pide, el rango de fechas (sobrescribe los vacíos)."""
    params = {**endpoint.fixed_params, endpoint.season_param_name: season}
    if date_range is not None:
        params[endpoint.date_from_param_name] = format_nba_date(date_range.start)
        params[endpoint.date_to_param_name] = format_nba_date(date_range.end)
    return params


def fetch_endpoint(
    endpoint: EndpointDefinition,
    season: str,
    *,
    session: Any,
    timeout: tuple[float, float] = DEFAULT_TIMEOUT_SECONDS,
    user_agent: str | None = None,
    date_range: DateRange | None = None,
) -> bytes:
    """Descarga un endpoint para una temporada (y rango opcional) y devuelve los bytes originales."""
    return _get_once(
        session,
        endpoint.url,
        build_request_params(endpoint, season, date_range),
        build_headers(user_agent),
        timeout,
        endpoint.id,
        season,
    )
