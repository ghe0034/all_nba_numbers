# CLAUDE.md

Guía para Claude Code al trabajar en este repositorio.

## Proyecto

Script batch en Python 3.10+ que descarga las últimas 10 temporadas de `stats.nba.com` y sube los JSON crudos a una capa Bronze en Google Cloud Storage. Diseño completo en [ARCHITECTURE.md](ARCHITECTURE.md).

Stack (obligatorio):
- **HTTP:** `requests`. No usar `urllib`, `httpx` ni `aiohttp`.
- **Tests:** `pytest`. No usar `unittest`.
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
pytest tests/test_rate_limiter.py                   # un archivo
pytest tests/test_rate_limiter.py::test_name        # un test
```

No hay linter configurado.

## Estructura

```
src/nba_ingest/      # paquete principal (__init__.py)
tests/               # tests pytest
requirements.txt
```

`secrets/`, `*.local.properties`, `.venv/` y `__pycache__/` están en `.gitignore`. Las credenciales de GCP nunca van en el repositorio.

## Estado y flujo de trabajo

El proyecto acaba de pivotar desde Java a Python. Hasta ahora solo existe el esqueleto (paquete vacío y `tests/` vacío). Los módulos se implementan de forma iterativa: el usuario indica explícitamente qué implementar en cada paso y no se deben adelantar módulos fuera de ese alcance (p. ej. clientes HTTP o lógica de GCS).
