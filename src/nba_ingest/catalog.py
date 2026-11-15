"""Carga y validación del catálogo de endpoints (`endpoints.json`)."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_CATALOG_PATH = Path(__file__).parent / "endpoints.json"
REQUIRED_FIELDS = ("url", "fixedParams", "seasonParamName")


@dataclass(frozen=True)
class EndpointDefinition:
    """Endpoint de stats.nba.com; la temporada se inyecta por tarea, no en `fixed_params`."""

    id: str
    url: str
    season_param_name: str
    fixed_params: dict[str, str]
    date_from_param_name: str = "DateFrom"
    date_to_param_name: str = "DateTo"


def build_endpoint(endpoint_id: str, raw_entry: dict[str, Any]) -> EndpointDefinition:
    """Valida una entrada del catálogo y la convierte en `EndpointDefinition`."""
    missing_fields = [field for field in REQUIRED_FIELDS if field not in raw_entry]
    if missing_fields:
        raise ValueError(
            f"Endpoint '{endpoint_id}' sin campos obligatorios: {missing_fields}"
        )

    endpoint = EndpointDefinition(
        id=endpoint_id,
        url=raw_entry["url"],
        season_param_name=raw_entry["seasonParamName"],
        fixed_params=dict(raw_entry["fixedParams"]),
        date_from_param_name=raw_entry.get("dateFromParamName", "DateFrom"),
        date_to_param_name=raw_entry.get("dateToParamName", "DateTo"),
    )
    if endpoint.season_param_name in endpoint.fixed_params:
        raise ValueError(
            f"'{endpoint.season_param_name}' no puede estar en fixedParams "
            f"del endpoint '{endpoint.id}'; la temporada se inyecta por tarea"
        )
    return endpoint


def parse_endpoints(catalog: dict[str, Any]) -> list[EndpointDefinition]:
    """Convierte el catálogo completo; la clave de cada entrada es su id."""
    return [
        build_endpoint(endpoint_id, entry) for endpoint_id, entry in catalog.items()
    ]


def load_endpoints(
    catalog_path: Path = DEFAULT_CATALOG_PATH,
) -> list[EndpointDefinition]:
    """Lee el catálogo JSON desde disco y devuelve los endpoints validados."""
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    return parse_endpoints(catalog)
