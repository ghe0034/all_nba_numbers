"""Carga y validación del catálogo de endpoints (`endpoints.json`)."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_CATALOG_PATH = Path(__file__).with_name("endpoints.json")
REQUIRED_FIELDS = ("id", "path", "season_param_name", "fixed_params")


@dataclass(frozen=True)
class EndpointDefinition:
    """Endpoint de stats.nba.com; la temporada se inyecta por tarea, no en `fixed_params`."""

    id: str
    path: str
    season_param_name: str
    fixed_params: dict[str, str]


def build_endpoint(raw_entry: dict[str, Any]) -> EndpointDefinition:
    """Valida una entrada del JSON y la convierte en `EndpointDefinition`."""
    missing_fields = [field for field in REQUIRED_FIELDS if field not in raw_entry]
    if missing_fields:
        raise ValueError(f"Endpoint sin campos obligatorios: {missing_fields}")

    endpoint = EndpointDefinition(
        id=raw_entry["id"],
        path=raw_entry["path"],
        season_param_name=raw_entry["season_param_name"],
        fixed_params=dict(raw_entry["fixed_params"]),
    )
    if endpoint.season_param_name in endpoint.fixed_params:
        raise ValueError(
            f"'{endpoint.season_param_name}' no puede estar en fixed_params "
            f"del endpoint '{endpoint.id}'; la temporada se inyecta por tarea"
        )
    return endpoint


def parse_endpoints(raw_entries: list[dict[str, Any]]) -> list[EndpointDefinition]:
    """Convierte y valida todas las entradas, rechazando ids duplicados."""
    endpoints = [build_endpoint(entry) for entry in raw_entries]
    ids = [endpoint.id for endpoint in endpoints]
    duplicated_ids = {endpoint_id for endpoint_id in ids if ids.count(endpoint_id) > 1}
    if duplicated_ids:
        raise ValueError(f"Ids de endpoint duplicados: {sorted(duplicated_ids)}")
    return endpoints


def load_endpoints(catalog_path: Path = DEFAULT_CATALOG_PATH) -> list[EndpointDefinition]:
    """Lee el catálogo JSON desde disco y devuelve los endpoints validados."""
    raw_entries = json.loads(catalog_path.read_text(encoding="utf-8"))
    return parse_endpoints(raw_entries)
