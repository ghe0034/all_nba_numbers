"""Espaciado mínimo entre peticiones a stats.nba.com."""

import time
from collections.abc import Callable


def make_rate_limiter(
    min_interval_seconds: float,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> Callable[[], None]:
    """Crea una función `acquire()` que bloquea hasta que pueda salir otra petición.

    Se llama antes de cada petición, incluidos los reintentos. El reloj y `sleep`
    se inyectan para que los tests no esperen de verdad.
    """
    if min_interval_seconds < 0:
        raise ValueError("El intervalo mínimo no puede ser negativo")

    next_request_allowed_at = float("-inf")

    def acquire() -> None:
        nonlocal next_request_allowed_at
        now = clock()
        if now < next_request_allowed_at:
            sleep(next_request_allowed_at - now)
        next_request_allowed_at = clock() + min_interval_seconds

    return acquire
