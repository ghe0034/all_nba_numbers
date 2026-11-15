# CLAUDE.md

Guía para Claude Code al trabajar en este repositorio.

## Proyecto

Script batch en Python 3.10+ que descarga las últimas 10 temporadas de `stats.nba.com` y sube los JSON crudos a una capa Bronze en Google Cloud Storage. Diseño completo en [ARCHITECTURE.md](ARCHITECTURE.md).

Stack (obligatorio):
- **HTTP:** `curl_cffi` con `impersonate="chrome"` (el TLS de `requests` es rechazado por stats.nba.com). No usar `requests`, `urllib`, `httpx` ni `aiohttp`.
- **Tests:** `pytest` (funciones `test_*` con `assert`, fixtures y `pytest.raises`). No usar `unittest` a no ser que sea estrictamente necesario.
- **Estilo:** módulos con funciones puras. Evitar clases salvo que haya una razón justificada (p. ej. excepciones propias o `dataclasses` para datos inmutables).
- **Storage:** `google-cloud-storage`.

Código e identificadores en inglés. Docstrings y comentarios indispensables en español.

## Reglas estrictas

- **NUNCA inventar parámetros de la API** (nombres de endpoint, query params, headers, valores). Si un parámetro no está verificado en la documentación o en una respuesta real, pedirlo al usuario en lugar de suponerlo.
- **Tests primero (TDD).** Antes de implementar cualquier función, escribir el test en `tests/` y verificar que falla. Solo después, el código que lo hace pasar.
- No añadir `try/except`, logging exhaustivo ni aserciones complejas salvo petición explícita.

## Comandos

```
.venv\Scripts\activate                              # activar entorno (Windows)
pip install -r requirements.txt                     # dependencias
pytest                                              # tests unitarios (integration excluidos por pytest.ini)
pytest -m integration                               # prueba real contra stats.nba.com
python -m nba_ingest --seasons 1                    # ensayo de 1 temporada (o NBA_SEASONS_COUNT=1)
python -m nba_ingest                                # backfill completo (10 temporadas)
pytest tests/unit/test_seasons.py                   # un archivo
pytest tests/unit/test_seasons.py::test_name        # un test
```

No hay linter configurado.

## Estructura

```
src/nba_ingest/      # paquete principal (__init__.py)
tests/unit/          # tests pytest unitarios
tests/integration/   # prueba real contra stats.nba.com (marcador `integration`)
docs/                # CLAUDE.md, PLAN_FASE1.md, ARCHITECTURE.md, spike_endpoints.md
requirements.txt
```

`secrets/`, `*.local.properties`, `.venv/` y `__pycache__/` están en `.gitignore`. Las credenciales de GCP nunca van en el repositorio.

**Credenciales GCS:** Application Default Credentials. Ejecutar `gcloud auth application-default login` (o apuntar `GOOGLE_APPLICATION_CREDENTIALS` a una cuenta de servicio en `secrets/`). Variables: `NBA_GCS_BUCKET` (obligatoria), `NBA_GCS_PROJECT`, `NBA_USER_AGENT`, `NBA_PAUSE_SECONDS`, `NBA_PAUSE_JITTER_SECONDS`, `NBA_SEASONS_COUNT`.

## Estado y flujo de trabajo

Fase 1 implementada según [PLAN_FASE1.md](PLAN_FASE1.md): módulos y tests unitarios completos, `leaguegamelog` verificado con 200 (ver [spike_endpoints.md](spike_endpoints.md)). Pendiente: ensayo de 1 temporada contra un bucket de desarrollo (tarea 10) y backfill completo (tarea 11). No añadir parámetros de API sin evidencia en `docs/spike_endpoints.md`.
