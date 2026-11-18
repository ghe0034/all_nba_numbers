# PLAN_FASE4 — Orquestación, contenedor y despliegue semanal en Google Cloud

Alcance: punto de entrada único `python -m nba_pipeline` que ejecuta Bronze incremental → Silver → Gold con parada inmediata ante fallo (fail-fast); imagen Docker; Cloud Run Job programado semanalmente con Cloud Scheduler. Fuera de alcance: alertas (Cloud Monitoring), backfill histórico (sigue con `python -m nba_ingest --seasons N`), CI/CD automático.

Punto de partida: Fases 1–3 implementadas (Gold en `c253403`).

Reglas de trabajo (de [CLAUDE.md](CLAUDE.md)): TDD y no inventar parámetros de la API. Los comandos de despliegue están en [deploy_gcp.md](deploy_gcp.md), que es la guía operativa; este documento recoge el diseño y las decisiones.

## Decisiones

1. **Ventana única.** El orquestador calcula el rango una vez, en UTC, con `days_back_range` y lo pasa a Bronze como `--date-from/--date-to`. Así Bronze y la resolución de temporadas no discrepan si la ejecución cruza medianoche.
2. **Temporadas derivadas del rango.** `seasons_for_range` (de `nba_ingest.date_range`) decide qué temporadas reprocesar en Silver y Gold. Semana normal → 1 temporada. Ventana que cruza el 1 de octubre → 2.
3. **Fail-fast.** Orden estricto. Un código de salida distinto de 0 corta y devuelve 1. Las excepciones se propagan sin `try/except`, coherente con el resto del proyecto; Cloud Run marca la ejecución como fallida.
4. **Silver tolera semanas sin partidos.** `clean_dataframe` devuelve el frame vacío antes de validar columnas. Sin esto, una ventana de verano o de parón tumbaría todo el pipeline.
5. **Reintentos del job: 1.** Seguro porque Bronze acumula por `download_date`, Silver deduplica por clave y Gold sobrescribe un objeto determinista.

## Orquestador (`src/nba_pipeline/`)

| Módulo | Responsabilidad |
|---|---|
| `orchestrator.py` | Lógica pura: `resolve_date_range`, `build_steps` (lista ordenada de pasos con su argv) y `run_pipeline` (recibe las tres etapas como parámetros) |
| `__main__.py` | CLI: `--days-back` (por defecto 10, `positive_int` de `nba_ingest`), `utc_today`, cableado con `nba_ingest.main`, `nba_silver.main` y `nba_gold.main` |

Pasos generados para una ventana que cruza el 1 de octubre:

```
bronze  --date-from 2024-09-25 --date-to 2024-10-05
silver  --season 2023-24
silver  --season 2024-25
gold    --season 2023-24
gold    --season 2024-25
```

`pyproject.toml`: `nba_pipeline*` en `include` y versión 0.4.0.

## Contenedor

- `Dockerfile`: `python:3.12-slim` con `--platform=linux/amd64`. Copia `pyproject.toml` y `src/`, instala con `pip install ".[silver]"` (incluye `endpoints.json` por package-data). Usuario `appuser` (uid 10001), sin login. `ENTRYPOINT ["python","-m","nba_pipeline"]`, `CMD ["--days-back","10"]`.
- `.dockerignore`: excluye `.env*`, `.venv`, `.git`, credenciales (`*key*.json`, `*credentials*.json`), `tests`, `docs` y cachés. **No** excluye `endpoints.json`, que vive en `src/`.
- Sin credenciales en la imagen. En GCP se usa la identidad de la Service Account del job; en local, el ADC se monta en tiempo de ejecución.

## Despliegue en Google Cloud

| Recurso | Valor | Motivo |
|---|---|---|
| APIs | `run`, `artifactregistry`, `cloudscheduler` | Imprescindibles para job, imagen y disparo |
| Artifact Registry | repo `nba` (docker) | Imágenes versionadas |
| Imagen | tag = SHA corto de git | Tag inmutable; no se usa `latest` |
| SA `nba-pipeline-sa` | `roles/storage.objectAdmin` **sobre el bucket** | Mínimo privilegio: nada a nivel proyecto |
| SA `nba-scheduler-sa` | `roles/run.invoker` **sobre el job** | Solo puede disparar este job |
| Cloud Run Job `nba-pipeline` | 2 Gi, 1 CPU, timeout 3600 s, `--max-retries 1`, `NBA_GCS_PROJECT`, `NBA_GCS_BUCKET` | Memoria para pandas/pyarrow; timeout por reintentos y pausas hacia stats.nba.com |
| Cloud Scheduler `nba-pipeline-weekly` | `0 8 * * 1`, zona UTC, POST a la API de `jobs:run` | Lunes 08:00 UTC |

Los valores de memoria y timeout son de partida: se ajustan tras la primera ejecución real.

## Tests (TDD)

`tests/unit/test_pipeline_orchestrator.py` (sin red ni GCS, con etapas falsas que registran llamadas):
- Temporadas por ventana: semana normal → 1 temporada; 5 y 10 de octubre → 2; 11 de octubre → 1; verano → temporada previa.
- Orden: `bronze → silver(s1) → silver(s2) → gold(s1) → gold(s2)`.
- Argumentos: Bronze recibe `--date-from/--date-to`; Silver y Gold reciben `--season`.
- Fail-fast: fallo en Bronze → no se llama a Silver ni Gold; fallo en Silver → no hay más Silver ni Gold; fallo en Gold → sin más Gold; excepción → se propaga y corta.

`tests/unit/test_pipeline_main.py`:
- `--days-back` por defecto 10; rechaza 0, negativos y no numéricos.
- `main` cablea las etapas reales con la ventana resuelta (con `utc_today` y etapas sustituidas).
- Un fallo de etapa devuelve código 1.

## Verificación

1. `python -m pytest -m "not integration" -v` y `ruff check src tests`.
2. Imagen local: `docker build --platform linux/amd64 -t <imagen> .`; `docker run --rm --entrypoint id <imagen>` debe dar uid 10001; `docker run --rm --entrypoint ls <imagen> -a /app` no debe mostrar `.env` ni `.git`.
3. Ejecución local contra un bucket de pruebas con ADC montado en tiempo de ejecución: `docker run ... <imagen> --days-back 3`.
4. Cloud Run: `gcloud run jobs execute nba-pipeline --region <REGION> --wait` y revisar logs.
5. GCS, los 3 niveles con fecha de la ejecución: `bronze_incremental/…/download_date=<hoy>/`, `silver/*/season=<activa>/data.parquet` y `gold/matchup_features/season=<activa>/data.parquet`. Una segunda ejecución deja el mismo número de filas en Silver y Gold.
6. Disparo programado: `gcloud scheduler jobs run nba-pipeline-weekly --location <REGION>`.

## Riesgo principal

stats.nba.com puede bloquear o ralentizar IPs de centros de datos, y Cloud Run las usa. Que funcione en local no garantiza que funcione en GCP. Si la etapa Bronze falla en el job, seguir el diagnóstico de [deploy_gcp.md](deploy_gcp.md#8-diagnóstico-stats-nba-com-bloquea-ips-de-gcp): pausas y reintentos, IP estática con Cloud NAT o ejecutar Bronze fuera de GCP.

## Estado

- [x] Silver tolera payloads vacíos (`clean_dataframe`) con test de regresión
- [x] Orquestador `nba_pipeline` con tests
- [x] `pyproject.toml` a 0.4.0 con `nba_pipeline*`
- [x] `Dockerfile` y `.dockerignore` (sin construir todavía)
- [x] `docs/deploy_gcp.md`
- [ ] Commits. Propuesta: (1) fix Silver vacío, (2) orquestador, (3) Dockerfile y `.dockerignore`, (4) documentación. Pendiente: el comando `git commit` fue bloqueado por permisos.
- [ ] `docker build` y ejecución local de la imagen
- [ ] Despliegue en GCP (APIs, Artifact Registry, SA, job, scheduler)
- [ ] Ejecución real del job y comprobación de las 3 capas en GCS
