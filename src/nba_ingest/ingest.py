"""Orquestación del batch: una tarea por par endpoint × temporada."""

import json
import random
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date

from curl_cffi.requests.exceptions import RequestException as CurlRequestError
from google.api_core.exceptions import GoogleAPIError
from google.auth.exceptions import GoogleAuthError
from requests.exceptions import RequestException as GcsTransportError

from nba_ingest.bronze_path import build_bronze_path
from nba_ingest.catalog import EndpointDefinition
from nba_ingest.client import NbaApiError

# Errores operativos (red, HTTP, GCS, JSON) que no deben detener el batch.
# Los errores de programación (TypeError, KeyError...) se dejan propagar.
OPERATIONAL_ERRORS = (
    NbaApiError,
    CurlRequestError,
    json.JSONDecodeError,
    UnicodeDecodeError,
    GoogleAPIError,
    GoogleAuthError,
    GcsTransportError,
)


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
    pause_seconds: float = 0.0,
    jitter_seconds: float = 0.0,
    sleep: Callable[[float], None] = time.sleep,
    uniform: Callable[[float, float], float] = random.uniform,
) -> list[TaskResult]:
    """Ejecuta cada tarea sin detenerse ante fallos y devuelve el resultado de todas.

    Espera `pause_seconds` más un jitter aleatorio en [0, `jitter_seconds`] entre tareas
    para espaciar las peticiones sin un patrón fijo. Requisito del batch: un fallo
    parcial no debe impedir el resto de descargas.
    """
    task_list = list(tasks)
    results = []
    for position, task in enumerate(task_list):
        if position > 0 and pause_seconds > 0:
            sleep(pause_seconds + uniform(0.0, jitter_seconds))
        try:
            run_one(task)
        except OPERATIONAL_ERRORS as error:
            results.append(TaskResult(task, success=False, error=str(error)))
        else:
            results.append(TaskResult(task, success=True, error=None))
    return results


def all_succeeded(results: Iterable[TaskResult]) -> bool:
    """True solo si hubo al menos una tarea y todas tuvieron éxito."""
    result_list = list(results)
    return bool(result_list) and all(result.success for result in result_list)
