# PLAN_FASE1 — Ingesta histórica a capa Bronze

Alcance: script batch en Python que descarga las últimas 10 temporadas de `stats.nba.com` y sube los JSON crudos a GCS. Fuera de alcance: bases de datos relacionales, transformaciones y automatización semanal.

Gestor de dependencias: `requirements.txt` (Maven descartado tras el pivote a Python).

Reglas de trabajo (de [CLAUDE.md](CLAUDE.md)):
- TDD: test en `tests/` primero, verificar que falla, después el código.
- No inventar parámetros de la API. Todo parámetro o header se verifica con una respuesta real antes de codificarlo.

## Estructura de directorios

```
proyecto_baloncesto/
├── requirements.txt
├── pytest.ini                      # testpaths=tests, pythonpath=src
├── src/
│   └── nba_ingest/
│       ├── __init__.py
│       ├── __main__.py             # entrada: python -m nba_ingest
│       ├── config.py               # lectura de configuración (variables de entorno)
│       ├── seasons.py              # cálculo de las últimas 10 temporadas
│       ├── endpoints.json          # catálogo de endpoints (datos, no código)
│       ├── catalog.py              # carga y validación de endpoints.json
│       ├── headers.py              # construcción de headers HTTP
│       ├── rate_limiter.py         # espaciado mínimo entre peticiones
│       ├── retry.py                # decisión y cálculo de reintentos
│       ├── client.py               # requests.Session: petición con headers + rate limit + retry
│       ├── bronze_path.py          # construcción de la ruta particionada en GCS
│       ├── gcs_uploader.py         # subida a GCS (google-cloud-storage)
│       └── ingest.py               # orquestación: tareas endpoint × temporada
├── tests/
│   ├── test_seasons.py
│   ├── test_catalog.py
│   ├── test_headers.py
│   ├── test_rate_limiter.py
│   ├── test_retry.py
│   ├── test_client.py
│   ├── test_bronze_path.py
│   ├── test_gcs_uploader.py
│   └── test_ingest.py
└── docs/
    └── spike_endpoints.md          # respuestas reales verificadas (tarea 0)
```

Notas:
- `endpoints.json` es el único sitio donde viven los parámetros de la API. Añadir o cambiar una variante no requiere tocar código.
- `headers.py` es el único lugar a modificar si la NBA cambia los headers requeridos.

## Reto técnico: headers y rate limiting

**Headers.** `stats.nba.com` rechaza o limita peticiones que no parecen venir de su web. `headers.py` construye en cada petición:
- `User-Agent`: navegador realista. Sobrescribible por configuración.
- `Referer` y `Origin`: dominio de `nba.com`, igual que en la web oficial.
- Cabeceras propias de la API (`x-nba-stats-origin`, `x-nba-stats-token`, etc.): valores verificados en la tarea 0 con una petición real del navegador. No se copian de memoria.
- `Accept`, `Accept-Language` y `Connection: keep-alive` coherentes con el User-Agent.
- Una `requests.Session` reutilizada mantiene cookies y conexión entre peticiones.

**Rate limiting.** `rate_limiter.py` garantiza un intervalo mínimo entre peticiones usando `time.monotonic()`. Reglas:
- Se aplica antes de **cada** petición, incluidos los reintentos.
- El intervalo es configurable. Su valor inicial se fija empíricamente en la tarea 0, no se inventa.
- El reloj y `sleep` se inyectan para que los tests sean deterministas y rápidos.

**Reintentos.** `retry.py` reacciona a 429, 403 y 5xx:
- Espera `min(base · 2^(intento−1) + jitter(0, base), max)` con intento 1-indexado.
- Si la respuesta trae `Retry-After`, se respeta en lugar de la fórmula. Requiere test propio.
- Tras agotar los intentos, la tarea falla sin abortar el batch.

**Timeouts.** Toda petición lleva `timeout` explícito (conexión y lectura). Sin timeout, el batch puede quedarse colgado.

## Tareas secuenciales

Cada tarea termina con `pytest` en verde y el criterio de hecho cumplido.

### Tarea 0 — Verificación de endpoints (spike, sin código de producción)
- Hacer peticiones reales a los endpoints candidatos (`leaguegamelog` con `PlayerOrTeam=P`, y los demás de la lista del proyecto) desde el navegador o con un script manual.
- Anotar en `docs/spike_endpoints.md`: URL exacta, query params, headers que hacen falta y si fallan sin ellos, códigos de respuesta, tamaño y ritmo que tolera el servidor.
- Criterio: cada parámetro de `endpoints.json` tiene una evidencia documentada.

### Tarea 1 — Rango de temporadas (`seasons.py`)
- Test: dada una fecha, devuelve exactamente 10 temporadas en formato `YYYY-YY` (p. ej. `2025-26`), incluida la actual, y cambia correctamente en octubre.
- Criterio: tests verdes con fechas límite (31 de diciembre, 1 de octubre).

### Tarea 2 — Catálogo de endpoints (`catalog.py`, `endpoints.json`)
- Test: carga el JSON, valida campos obligatorios (`id`, `path`, `fixed_params`, `season_param_name`), rechaza ids duplicados y rechaza `season` dentro de `fixed_params`.
- Criterio: el JSON contiene solo parámetros verificados en la tarea 0.

### Tarea 3 — Headers (`headers.py`)
- Test: el diccionario contiene `User-Agent`, `Referer`, `Origin` y las cabeceras de la API; el User-Agent se puede sobrescribir.
- Criterio: valores idénticos a los de la tarea 0.

### Tarea 4 — Rate limiter (`rate_limiter.py`)
- Test con reloj falso: dos llamadas seguidas duermen el tiempo restante del intervalo; una llamada tras un intervalo completo no duerme.
- Criterio: nunca dos peticiones con menos del intervalo configurado.

### Tarea 5 — Política de reintentos (`retry.py`)
- Test: 429, 403 y 5xx reintentan; 404 y 200 no; la espera nunca supera `max`; `Retry-After` tiene prioridad; intentos 1-indexados.
- Criterio: tests de propiedades sobre el límite superior y la no negatividad del delay.

### Tarea 6 — Cliente HTTP (`client.py`)
- Test con `requests` simulado (p. ej. `responses` o mock de `Session.get`): flujo 429 → rate limit → 200 devuelve bytes crudos; timeout explícito en cada llamada; agotar reintentos lanza error controlado.
- Criterio: el cliente nunca hace una petición sin pasar por el rate limiter.

### Tarea 7 — Validación JSON
- Test: el cuerpo se valida con `json.loads` pero **los bytes originales** son los que se devuelven (sin re-serializar).
- Criterio: `sha256` de los bytes subidos igual al de la respuesta.

### Tarea 8 — Ruta Bronze (`bronze_path.py`)
- Ruta: `bronze/{endpoint_id}/season={season}/download_date={YYYY-MM-DD}/{endpoint_id}.json`.
- Test: formato exacto; misma entrada → misma ruta (determinismo).
- Justificación: particionado por temporada y fecha de descarga permite reejecutar un día sin duplicar datos (idempotencia: el mismo día sobrescribe el mismo objeto).

### Tarea 9 — Subida a GCS (`gcs_uploader.py`)
- Test con bucket falso: `content_type="application/json"`, nombre de objeto igual a la ruta de la tarea 8, y los bytes no se modifican.
- Criterio: ningún test toca GCS real.

### Tarea 10 — Orquestación (`ingest.py`)
- Test: se generan endpoints × temporadas tareas; un fallo en una tarea no detiene las demás; el resultado agrega éxitos y fallos.
- Criterio: resumen con total, éxitos y fallos; el batch sigue ante fallos parciales.

### Tarea 11 — Configuración y entrada (`config.py`, `__main__.py`)
- Test: lee bucket, user-agent y delays de variables de entorno (sin credenciales en código); valores por defecto seguros.
- `__main__.py` devuelve exit code 0 solo si todas las tareas tuvieron éxito.
- Criterio: `python -m nba_ingest --help` funciona (si se añade CLI) y el exit code es el esperado en los tests.

### Tarea 12 — Prueba end-to-end controlada
- Ejecutar contra un bucket de **desarrollo** con credenciales en `secrets/` (gitignored), limitado a una temporada y un endpoint.
- Verificar: objeto creado con la ruta correcta, JSON válido, bytes idénticos a la respuesta, y segunda ejecución del mismo día sin duplicados.
- Criterio: evidencia (ruta del objeto y tamaño) anotada en `docs/spike_endpoints.md` o en el README.

### Tarea 13 — Ejecución completa
- Ejecutar las 10 temporadas × todos los endpoints con el rate limit validado.
- Criterio: todas las tareas en éxito o con fallos explicados y reintentables.

## Dependencias

`requirements.txt` (ya creado):

```
requests
google-cloud-storage
pytest
```

Para los tests de respuestas HTTP simuladas se puede añadir `responses` en la tarea 6, solo si se justifica frente a un mock simple de `Session.get`.
