# CLAUDE.md

Guía para Claude Code al trabajar en este repositorio.

## Proyecto

Script batch en Python 3.10+ que descarga las últimas 10 temporadas de `stats.nba.com` y sube los JSON crudos a una capa Bronze en Google Cloud Storage. Diseño completo en [ARCHITECTURE.md](ARCHITECTURE.md).

Stack (obligatorio):
- **HTTP:** `requests`. No usar `urllib`, `httpx` ni `aiohttp`.
- **Tests:** `pytest` (funciones `test_*` con `assert`, fixtures y `pytest.raises`). No usar `unittest`.
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
pytest                                              # todos los tests
pytest tests/unit/test_seasons.py                   # un archivo
pytest tests/unit/test_seasons.py::test_name        # un test
```

No hay linter configurado.

## Estructura

```
src/nba_ingest/      # paquete principal (__init__.py)
tests/unit/          # tests pytest unitarios
tests/integration/   # prueba manual contra stats.nba.com (no es test pytest)
requirements.txt
```

`secrets/`, `*.local.properties`, `.venv/` y `__pycache__/` están en `.gitignore`. Las credenciales de GCP nunca van en el repositorio.

## Estado y flujo de trabajo

Fase 1 implementada según [PLAN_FASE1.md](PLAN_FASE1.md) en sus tareas 1 a 11 (módulos y tests). Pendiente: tarea 0 (spike de endpoints; `endpoints.json` está vacío hasta completarlo) y tareas 12-13 (ejecución real contra GCS). No añadir parámetros de API sin evidencia en `docs/spike_endpoints.md`.
