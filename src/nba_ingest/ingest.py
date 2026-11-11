"""Orquestación del batch: una tarea por par endpoint × temporada."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date

from nba_ingest.bronze_path import build_bronze_path
from nba_ingest.catalog import EndpointDefinition


@dataclass(frozen=True)
class IngestionTask:
    endpoint: EndpointDefinition
    season: str


@dataclass(frozen=True)
class TaskResult:
    task: IngestionTask
    success: bool
    error: str | None


def build_tasks(
    endpoints: Iterable[EndpointDefinition], seasons: Iterable[str]
) -> list[IngestionTask]:
    """Produce todas las combinaciones endpoint × temporada."""
    season_list = list(seasons)
    return [
        IngestionTask(endpoint, season)
        for endpoint in endpoints
        for season in season_list
    ]


def run_task(
    task: IngestionTask,
    *,
    fetch: Callable[[EndpointDefinition, str], bytes],
    upload: Callable[[str, bytes], None],
    download_date: date,
) -> None:
    """Descarga una tarea y la sube a su ruta Bronze."""
    body = fetch(task.endpoint, task.season)
    object_path = build_bronze_path(task.endpoint.id, task.season, download_date)
    upload(object_path, body)


def run_tasks(
    tasks: Iterable[IngestionTask],
    run_one: Callable[[IngestionTask], None],
) -> list[TaskResult]:
    """Ejecuta cada tarea sin detenerse ante fallos y devuelve el resultado de todas.

    Requisito del batch: un fallo parcial no debe impedir el resto de descargas.
    """
    results = []
    for task in tasks:
        try:
            run_one(task)
        except Exception as error:
            results.append(TaskResult(task, success=False, error=str(error)))
        else:
            results.append(TaskResult(task, success=True, error=None))
    return results


def all_succeeded(results: Iterable[TaskResult]) -> bool:
    """True solo si hubo al menos una tarea y todas tuvieron éxito."""
    result_list = list(results)
    return bool(result_list) and all(result.success for result in result_list)
