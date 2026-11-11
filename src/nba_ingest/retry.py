"""Política de reintentos con backoff exponencial y jitter.

Los intentos son 1-indexados: `attempt` es el número del intento que acaba de fallar.
"""

import random
import re

RETRYABLE_STATUS_CODES = frozenset({429, 403, 500, 502, 503, 504})
RETRY_AFTER_SECONDS_PATTERN = re.compile(r"\d+(\.\d+)?")


def should_retry(status_code: int, attempt: int, max_attempts: int) -> bool:
    """Indica si la respuesta justifica otro intento."""
    return status_code in RETRYABLE_STATUS_CODES and attempt < max_attempts


def parse_retry_after(header_value: str | None) -> float | None:
    """Lee `Retry-After` en formato de segundos; las fechas HTTP no se soportan."""
    if header_value is None or not RETRY_AFTER_SECONDS_PATTERN.fullmatch(header_value.strip()):
        return None
    return float(header_value)


def compute_delay_seconds(
    attempt: int,
    base_delay: float,
    max_delay: float,
    rng: random.Random | None = None,
    retry_after: float | None = None,
) -> float:
    """Espera antes del siguiente intento: `min(base·2^(intento-1) + jitter, max)`.

    Si el servidor indica `Retry-After`, ese valor sustituye a la fórmula; el tope
    `max_delay` se aplica igualmente.
    """
    if retry_after is not None:
        return min(retry_after, max_delay)

    generator = rng if rng is not None else random.Random()
    exponential_delay = base_delay * 2 ** (attempt - 1)
    jitter = generator.uniform(0, base_delay)
    return min(exponential_delay + jitter, max_delay)
