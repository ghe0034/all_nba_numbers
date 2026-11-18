# CLAUDE.md

Guía para Claude Code al trabajar en este repositorio.

## Proyecto

Pipeline batch en Python 3.10+ sobre `stats.nba.com` con tres capas en Google Cloud Storage: Bronze (JSON crudo), Silver (Parquet limpio por partido) y Gold (features por partido sin data leakage). Se ejecuta semanalmente en Cloud Run. Diseño completo en [ARCHITECTURE.md](docs/ARCHITECTURE.md); planes por fase en [PLAN_FASE1.md](docs/PLAN_FASE1.md), [PLAN_FASE2.md](docs/PLAN_FASE2.md), [PLAN_FASE3.md](docs/PLAN_FASE3.md) y [PLAN_FASE4.md](docs/PLAN_FASE4.md).

Stack (obligatorio):
- **HTTP:** `curl_cffi` con `impersonate="chrome"` (el TLS de `requests` es rechazado por stats.nba.com). No usar `requests`, `urllib`, `httpx` ni `aiohttp`.
- **Tests:** `pytest` (funciones `test_*` con `assert`, fixtures, `parametrize` y `pytest.raises`). No usar `unittest`.
- **Estilo:** módulos con funciones puras; la E/S va en módulos finos aparte. Clases solo para excepciones propias y `dataclasses` inmutables.
- **Storage:** `google-cloud-storage`. No usar `gcsfs`.
- **Silver y Gold:** `pandas` + `pyarrow` (extra `silver` de `pyproject.toml`).
- **Configuración local:** `python-dotenv` (`.env`, ignorado por git; plantilla en `.env.example`). Las variables reales del entorno prevalecen sobre `.env`.

Código e identificadores en inglés. Docstrings y comentarios indispensables en español.

## Reglas estrictas

- **NUNCA inventar parámetros de la API** (endpoints, query params, headers, valores). Si un parámetro no está verificado en `docs/spike_endpoints.md` o en una respuesta real, pedirlo en lugar de suponerlo.
- **Tests primero (TDD).** Escribir el test en `tests/`, verificar que falla y solo después implementar.
- **Gold: sin data leakage.** Toda feature de un partido se calcula con datos anteriores. Cualquier cambio en `features.py` debe mantener `shift(1)` antes de `rolling` y los tests de anti-leakage en verde.
- No añadir `try/except`, logging exhaustivo ni aserciones complejas salvo petición explícita.

## Comandos

```
.venv\Scripts\activate                                   # activar entorno (Windows)
pip install -e ".[silver,dev]"                           # instalación editable
pytest                                                   # tests unitarios (integration excluidos por pytest.ini)
pytest -m integration                                    # prueba real contra stats.nba.com
pytest tests/unit/test_gold_rolling.py::test_name        # un test
ruff check src tests                                     # linter (también en pre-commit y CI)

python -m nba_ingest --seasons 1                         # Bronze: 1 temporada completa
python -m nba_ingest --days-back 10                      # Bronze: incremental -> bronze_incremental/
python -m nba_ingest --date-from 2024-01-08 --date-to 2024-01-14

python -m nba_silver --season 2024-25                    # Silver de una temporada
python -m nba_silver --all-seasons [--table team_game_logs]

python -m nba_gold --season 2024-25                      # Gold de una temporada
python -m nba_gold --all-seasons

python -m nba_pipeline --days-back 10                    # Bronze -> Silver -> Gold, fail-fast
```

Variables de entorno: `NBA_GCS_BUCKET` (obligatoria), `NBA_GCS_PROJECT`, `NBA_USER_AGENT`, `NBA_PAUSE_SECONDS`, `NBA_PAUSE_JITTER_SECONDS`, `NBA_SEASONS_COUNT`.

Credenciales GCS: Application Default Credentials (`gcloud auth application-default login`). Nunca hay credenciales en el repositorio ni en la imagen Docker.

## Estructura

```
src/nba_ingest/      # Bronze: descarga desde la API y subida a GCS
src/nba_silver/      # Silver: Bronze JSON -> Parquet por tabla y temporada
src/nba_gold/        # Gold: features por partido (features.py = lógica pura)
src/nba_pipeline/    # orquestador: Bronze -> Silver -> Gold con fail-fast
tests/unit/          # tests unitarios (sin red ni GCS)
tests/integration/   # pruebas reales (marcador `integration`)
docs/                # CLAUDE.md, ARCHITECTURE.md, PLAN_FASE*.md, deploy_gcp.md, spike_endpoints.md
Dockerfile           # imagen linux/amd64, usuario no-root
pyproject.toml       # paquete instalable y extras (`silver`, `dev`)
```

## Capas en GCS

```
bronze/{endpoint}/season=/download_date=/{endpoint}.json                                  # carga completa
bronze_incremental/{endpoint}/season=/date_from=/date_to=/download_date=/{endpoint}.json  # carga por rango
silver/{player_game_logs|team_game_logs|team_advanced_logs}/season=/data.parquet          # reconstruido por temporada
gold/matchup_features/season=/data.parquet                                                # reconstruido por temporada
```

- Las cargas incrementales nunca escriben bajo `bronze/`.
- Silver lee ambos prefijos y, ante la misma clave, conserva la fila con `download_date` más reciente.
- Cada objeto de Silver y Gold se sobrescribe de forma determinista: reejecutar es seguro.

## Estado

- Fase 1 (ingesta histórica): completada. Backfill de 3 endpoints × 31 temporadas en GCS, 0 fallos.
- Fase 2 (incremental y Silver): implementada.
- Fase 3 (Gold): implementada. Pendiente de ejecución real en GCP.
- Fase 4 (orquestación y despliegue): código y tests hechos. Pendiente: build de la imagen, despliegue y ejecución real. Ver [PLAN_FASE4.md](docs/PLAN_FASE4.md) y [deploy_gcp.md](docs/deploy_gcp.md).

Catálogo de endpoints verificado en [spike_endpoints.md](docs/spike_endpoints.md): `leaguegamelog`, `leaguegamelog_teams` y `teamgamelogs_advanced`. No añadir parámetros de API sin esa evidencia.
