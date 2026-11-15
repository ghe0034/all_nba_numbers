# CLAUDE.md

Guía para Claude Code al trabajar en este repositorio.

## Proyecto

Script batch en Python 3.10+ que descarga temporadas de `stats.nba.com` y sube los JSON crudos a una capa Bronze en Google Cloud Storage. Fase 2 (en curso, ver [PLAN_FASE2.md](PLAN_FASE2.md)): ingesta incremental por rango de fechas (`bronze_incremental/`) y capa Silver (Bronze JSON → Parquet en `silver/`, paquete `nba_silver`). Diseño completo en [ARCHITECTURE.md](ARCHITECTURE.md).

Stack (obligatorio):
- **HTTP:** `curl_cffi` con `impersonate="chrome"` (el TLS de `requests` es rechazado por stats.nba.com). No usar `requests`, `urllib`, `httpx` ni `aiohttp`.
- **Tests:** `pytest` (funciones `test_*` con `assert`, fixtures y `pytest.raises`). No usar `unittest` a no ser que sea estrictamente necesario.
- **Estilo:** módulos con funciones puras. Evitar clases salvo que haya una razón justificada (p. ej. excepciones propias o `dataclasses` para datos inmutables).
- **Storage:** `google-cloud-storage`.
- **Silver (Fase 2):** `pandas` + `pyarrow` (extra `silver` de `pyproject.toml`). No usar `gcsfs`; la lectura/escritura en GCS va por `google-cloud-storage`.
- **Configuración local:** `python-dotenv` (`.env`, ignorado por git; plantilla en `.env.example`). Las variables reales del entorno prevalecen sobre `.env`.

Código e identificadores en inglés. Docstrings y comentarios indispensables en español.

## Reglas estrictas

- **NUNCA inventar parámetros de la API** (nombres de endpoint, query params, headers, valores). Si un parámetro no está verificado en la documentación o en una respuesta real, pedirlo al usuario en lugar de suponerlo.
- **Tests primero (TDD).** Antes de implementar cualquier función, escribir el test en `tests/` y verificar que falla. Solo después, el código que lo hace pasar.
- No añadir `try/except`, logging exhaustivo ni aserciones complejas salvo petición explícita.

## Comandos

```
.venv\Scripts\activate                              # activar entorno (Windows)
pip install -e ".[silver,dev]"                      # instalación editable (Fase 2: sin PYTHONPATH=src)
pytest                                              # tests unitarios (integration excluidos por pytest.ini)
pytest -m integration                               # prueba real contra stats.nba.com
ruff check src tests                                # linter
python -m nba_ingest --seasons 1                    # ensayo de 1 temporada (o NBA_SEASONS_COUNT=1)
python -m nba_ingest                                # backfill por temporadas (10 por defecto)
python -m nba_ingest --days-back 10                 # incremental semanal -> bronze_incremental/
python -m nba_ingest --date-from 2024-01-08 --date-to 2024-01-14   # incremental por rango
python -m nba_silver --seasons 2023-24              # Bronze -> Silver Parquet de una temporada
python -m nba_silver --all                          # reconstruye todas las temporadas
pytest tests/unit/test_seasons.py                   # un archivo
pytest tests/unit/test_seasons.py::test_name        # un test
```

Linter: `ruff` (también como hook de `pre-commit` y en CI).

## Estructura

```
src/nba_ingest/      # ingesta a Bronze (completa por temporada e incremental por fechas)
src/nba_silver/      # Fase 2: Bronze JSON -> Silver Parquet
tests/unit/          # tests pytest unitarios
tests/integration/   # pruebas reales (stats.nba.com / GCS, marcador `integration`)
docs/                # CLAUDE.md, PLAN_FASE1.md, PLAN_FASE2.md, ARCHITECTURE.md, spike_endpoints.md
pyproject.toml       # paquete instalable y extras (`silver`, `dev`)
requirements.txt
```

## Capas en GCS

```
bronze/{endpoint}/season=/download_date=/{endpoint}.json                                  # carga completa por temporada
bronze_incremental/{endpoint}/season=/date_from=/date_to=/download_date=/{endpoint}.json  # carga por rango de fechas
silver/{player_game_logs|team_game_logs|team_advanced_logs}/season=/{tabla}.parquet       # reconstruido por temporada
```

Las cargas incrementales nunca escriben bajo `bronze/`. Silver lee ambos prefijos y, ante la misma clave de partido, conserva la fila con `download_date` más reciente.

`secrets/`, `*.local.properties`, `.venv/` y `__pycache__/` están en `.gitignore`. Las credenciales de GCP nunca van en el repositorio.

**Credenciales GCS:** Application Default Credentials. Ejecutar `gcloud auth application-default login` (o apuntar `GOOGLE_APPLICATION_CREDENTIALS` a una cuenta de servicio en `secrets/`). Variables: `NBA_GCS_BUCKET` (obligatoria), `NBA_GCS_PROJECT`, `NBA_USER_AGENT`, `NBA_PAUSE_SECONDS`, `NBA_PAUSE_JITTER_SECONDS`, `NBA_SEASONS_COUNT`.

## Estado y flujo de trabajo

Fase 1 completada según [PLAN_FASE1.md](PLAN_FASE1.md): ensayo E2E y backfill histórico en GCS (3 endpoints × 31 temporadas, 0 fallos); catálogo con `leaguegamelog`, `leaguegamelog_teams` y `teamgamelogs_advanced` (ver [spike_endpoints.md](spike_endpoints.md)).

Fase 2 planificada en [PLAN_FASE2.md](PLAN_FASE2.md), sin implementar: spike de `DateFrom`/`DateTo` y perfilado de Bronze → ergonomía (`pyproject.toml`, `.env`) → ingesta incremental → Silver. No añadir parámetros de API sin evidencia en `docs/spike_endpoints.md`.
