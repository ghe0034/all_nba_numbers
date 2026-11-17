"""Orquestación Bronze incremental -> Silver -> Gold con parada inmediata (fail-fast)."""

import sys
from collections.abc import Callable, Sequence
from datetime import date

from nba_ingest.date_range import DateRange, days_back_range, seasons_for_range

StageMain = Callable[[Sequence[str]], int]


def resolve_date_range(today: date, days_back: int) -> DateRange:
    """Ventana de la ejecución, calculada una sola vez para todas las etapas."""
    return days_back_range(today, days_back)


def build_steps(
    date_range: DateRange,
    ingest: StageMain,
    silver: StageMain,
    gold: StageMain,
) -> list[tuple[str, StageMain, list[str]]]:
    """Pasos en orden estricto: Bronze, Silver por temporada afectada, Gold por temporada afectada."""
    seasons = seasons_for_range(date_range)
    ingest_argv = [
        "--date-from",
        date_range.start.isoformat(),
        "--date-to",
        date_range.end.isoformat(),
    ]
    steps = [("bronze", ingest, ingest_argv)]
    steps += [(f"silver {season}", silver, ["--season", season]) for season in seasons]
    steps += [(f"gold {season}", gold, ["--season", season]) for season in seasons]
    return steps


def run_pipeline(
    date_range: DateRange,
    ingest: StageMain,
    silver: StageMain,
    gold: StageMain,
) -> int:
    """Ejecuta los pasos; devuelve 1 en el primer código de salida distinto de 0.

    Las excepciones no se capturan: cortan la ejecución y Cloud Run la marca como fallida.
    """
    for label, stage_main, argv in build_steps(date_range, ingest, silver, gold):
        print(f"== {label} ==")
        exit_code = stage_main(argv)
        if exit_code != 0:
            print(
                f"FALLO en {label} (código {exit_code}); se detiene el pipeline",
                file=sys.stderr,
            )
            return 1
    print("Pipeline completado")
    return 0
