# PLAN_FASE2 — Ergonomía, ingesta incremental y capa Silver

Alcance: (a) instalación editable y `.env` local, (b) ingesta incremental semanal a Bronze por rango de fechas, (c) capa Silver (Bronze JSON → Parquet en GCS). Fuera de alcance: Playoffs (`SeasonType` sigue fijo en `Regular Season`), orquestación/automatización (cron, Airflow), capa Gold.

Punto de partida: backfill completo de Fase 1 en GCS (3 endpoints × 31 temporadas = 93 tareas, 0 fallos).

Reglas de trabajo (de [CLAUDE.md](CLAUDE.md)): TDD (test primero, verlo fallar) y no inventar parámetros de la API; todo parámetro nuevo se verifica con una respuesta real en [spike_endpoints.md](spike_endpoints.md).

## Paso 0 — Spike previo

Antes de escribir código, con peticiones reales:

1. `DateFrom`/`DateTo` en `MM/DD/YYYY` en los 3 endpoints (ventana de ejemplo 01/08/2024–01/14/2024, `Season=2023-24`): HTTP, filas, si ambos extremos son inclusivos, si hay filas fuera de ventana y si una ventana sin partidos devuelve 200 con `rowSet` vacío.
2. Perfilado de Bronze existente (1 objeto por endpoint en la temporada más antigua, una intermedia y la actual): columnas presentes por época, formato de `GAME_DATE` (en `teamgamelogs` es `2023-10-24T00:00:00`; comprobar `leaguegamelog`), tipos, nulos (`MIN`, `WL`, `PLUS_MINUS`) y `MATCHUP`. Las temporadas antiguas probablemente carecen de columnas (p. ej. `E_*_RATING`).

El esquema Silver (columnas obligatorias vs. opcionales) se fija con esta evidencia.

## Bloque A — Ergonomía de entorno

- `pyproject.toml` (setuptools, layout `src`): `requires-python>=3.10`; dependencias `curl_cffi`, `google-cloud-storage`, `tenacity`, `python-dotenv`; extras `silver` (`pandas`, `pyarrow`) y `dev` (`pytest`, `ruff`, `pre-commit`); paquetes `nba_ingest` y `nba_silver`.
- Se quita `pythonpath = src` de `pytest.ini` y `PYTHONPATH: src` de `ci.yml`; CI instala con `pip install -e ".[silver,dev]"`. Comprobar que `pyarrow` tiene wheel para la versión de Python de CI (3.14); si no, fijar 3.13.
- `requirements.txt` se mantiene con pines para reproducibilidad (decisión a confirmar).
- `.env`: `python-dotenv` con `load_dotenv(override=False)` llamado en `__main__.main()`, no en `load_settings` (que sigue siendo pura). Las variables reales del entorno prevalecen sobre `.env`. `.env` se añade a `.gitignore` y se versiona `.env.example` sin secretos.
- Tests: `.env` en `tmp_path` + `monkeypatch`; el entorno real gana a `.env`; un `.env` ausente no falla.

## Bloque B — Ingesta incremental semanal (Bronze)

CLI: grupo mutuamente excluyente `--seasons N` (histórico, intacto) | `--days-back N` | `--date-from/--date-to` (`YYYY-MM-DD` en CLI; se convierte a `MM/DD/YYYY` al construir la petición; `date_from <= date_to`). Sin argumentos, comportamiento actual.

Módulos:
- `date_range.py` (nuevo, funciones puras): `DateRange`, `days_back_range`, `format_nba_date`, `seasons_for_range` (una ventana que cruza el 1 de octubre produce 2 temporadas).
- `catalog.py`: `EndpointDefinition` gana `date_from_param_name="DateFrom"` y `date_to_param_name="DateTo"` (con valor por defecto); claves opcionales `dateFromParamName`/`dateToParamName` en el JSON.
- `client.py`: `build_request_params(endpoint, season, date_range=None)` y `fetch_endpoint(..., date_range=None)`. El rango sobrescribe los `DateFrom=""`/`DateTo=""` de `teamgamelogs_advanced`; `endpoints.json` no cambia.
- `ingest.py`: `IngestionTask.date_range` opcional; `build_tasks(..., date_range=None)`; `run_task` elige la ruta Bronze según el rango.
- `bronze_path.py`: `build_incremental_bronze_path`.

Ruta incremental (prefijo propio, nunca escribe bajo `bronze/`):

```
bronze_incremental/{endpoint}/season={s}/date_from={YYYY-MM-DD}/date_to={YYYY-MM-DD}/download_date={YYYY-MM-DD}/{endpoint}.json
```

Idempotencia: misma ventana y mismo día → mismo objeto (se sobrescribe). Recomendación operativa: `--days-back 10` semanal (solape de 3 días) para absorber correcciones tardías; el solape es seguro porque Silver deduplica por clave.

Tests: `test_date_range.py`, `test_bronze_path.py`, `test_client.py`, `test_ingest.py`, `test_main.py`, `test_catalog.py`.

## Bloque C — Capa Silver (`src/nba_silver/`)

Paquete hermano de `nba_ingest` con dependencias pesadas aisladas en el extra `silver`. CLI: `python -m nba_silver [--seasons 2023-24 ...] [--all]`. Reutiliza `nba_ingest.gcs_uploader.make_bucket`, `config.load_settings` y el patrón de resumen y exit code de `nba_ingest`.

| Bronze (`endpoint`) | Silver (tabla) | Clave primaria |
|---|---|---|
| `leaguegamelog` | `player_game_logs` | `GAME_ID`, `PLAYER_ID` |
| `leaguegamelog_teams` | `team_game_logs` | `GAME_ID`, `TEAM_ID` |
| `teamgamelogs_advanced` | `team_advanced_logs` | `GAME_ID`, `TEAM_ID` |

Módulos:
- `tables.py`: `SilverTable` (dataclass frozen) con nombre, endpoint Bronze, clave, esquema pyarrow y columnas obligatorias/opcionales.
- `bronze_reader.py`: lista blobs de `bronze/` y `bronze_incremental/` de la temporada, extrae `download_date` de la ruta y devuelve `(bytes, download_date, blob.updated)`.
- `parsing.py`: `headers` + `rowSet` → DataFrame; vacío si no hay filas (el payload se ignora).
- `transform.py`: valida esquema (falta obligatoria → `SchemaValidationError`; opcional ausente → nula), castea (`GAME_DATE`→`date`, métricas numéricas, `SEASON_ID`/`GAME_ID` como `string`), deriva `is_home` desde `MATCHUP` (`vs.` local, `@` visitante) e `is_win` desde `WL`, y renombra a `snake_case`.
- `dedupe.py`: ordena por `download_date` y `blob.updated` y aplica `drop_duplicates(primary_key, keep="last")`. La deduplicación es a nivel de fila porque los ficheros incrementales solo traen un subconjunto de partidos.
- `silver_path.py`: `silver/{table}/season={s}/{table}.parquet` (nombre fijo).
- `parquet_writer.py`: `pyarrow.Table` con esquema explícito → `BytesIO` (snappy) → subida con `google-cloud-storage` (sin `gcsfs`).
- `pipeline.py`: una tarea por tabla × temporada (leer → parsear → ignorar vacíos → validar → castear → deduplicar → escribir); un fallo parcial no detiene el resto.

Particionado e idempotencia: partición Hive `season=` (sin sobrepartir por fecha). Cada ejecución reconstruye la partición completa de la temporada desde todo su Bronze y sobrescribe un único objeto de nombre fijo; filas ordenadas por clave. Por defecto procesa la temporada actual (y la previa justo tras el cambio de temporada); `--all` reconstruye las 31.

Tests: payloads JSON mínimos con forma real en `tests/fixtures/` y `FakeBucket` al estilo de `test_main.py`; un archivo por módulo. Casos clave de dedupe: la fecha más reciente gana, el incremental pisa al completo y un completo posterior pisa al incremental. Round-trip Parquet con `pyarrow`. Idempotencia: dos ejecuciones producen el mismo objeto. Un test `integration` opcional contra una temporada real.

## Orden de implementación

0. Spike y perfilado → 1. Bloque A → 2. Bloque B (`date_range` → `catalog`/`client` → `bronze_path` → `ingest` → CLI) → 3. Bloque C (`tables`/`parsing` → `transform` → `dedupe` → `writer` → `pipeline` → CLI) → 4. Documentación. Un commit por bloque.

## Verificación

- `pip install -e ".[silver,dev]"` en venv limpio; `python -m nba_ingest --help` sin `PYTHONPATH`.
- `ruff check src tests` y `pytest -m "not integration"` en cada bloque.
- Incremental real: `python -m nba_ingest --days-back 7` dos veces → mismos objetos bajo `bronze_incremental/` y sin cambios en `bronze/`.
- Silver real: `python -m nba_silver --seasons 2023-24` dos veces → mismo objeto Parquet; 0 duplicados por clave; 2 460 filas en las tablas de equipo de 2023-24.
