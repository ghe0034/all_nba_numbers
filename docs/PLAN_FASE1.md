# PLAN_FASE1 — Ingesta histórica a capa Bronze

Written for: el equipo de desarrollo y el becario que implementa el proyecto.

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
│       ├── config.py               # configuración desde variables de entorno
│       ├── seasons.py              # cálculo de las últimas 10 temporadas
│       ├── endpoints.json          # catálogo de endpoints (datos, no código)
│       ├── catalog.py              # carga y validación de endpoints.json
│       ├── headers.py              # cabeceras HTTP que simulan un navegador
│       ├── client.py               # requests + timeout + reintentos con @retry (tenacity)
│       ├── bronze_path.py          # construcción de la ruta particionada en GCS
│       ├── gcs_uploader.py         # subida a GCS (google-cloud-storage)
│       └── ingest.py               # orquestación: tareas, pausa entre tareas, fallos parciales
├── tests/
│   ├── test_seasons.py
│   ├── test_catalog.py
│   ├── test_headers.py
│   ├── test_client.py
│   ├── test_bronze_path.py
│   ├── test_gcs_uploader.py
│   ├── test_ingest.py
│   └── test_config.py
└── docs/
    └── spike_endpoints.md          # respuestas reales verificadas (tarea 0)
```

Notas:
- `endpoints.json` es el único sitio donde viven los parámetros de la API. Añadir o cambiar una variante no requiere tocar código.
- `headers.py` es el único lugar a modificar si la NBA cambia los headers requeridos.

## Reto técnico: headers, pausas y reintentos

**Headers.** `stats.nba.com` rechaza o limita peticiones que no parecen venir de su web. `headers.py` construye en cada petición:
- `User-Agent`: navegador realista. Sobrescribible por configuración.
- `Referer` y `Origin`: dominio de `nba.com`, igual que en la web oficial.
- Cabeceras propias de la API (`x-nba-stats-origin`, `x-nba-stats-token`, etc.): valores verificados en la tarea 0 con una petición real del navegador. No se copian de memoria.
- `Accept`, `Accept-Language` y `Connection: keep-alive` coherentes con el User-Agent.

**Pausa entre peticiones.** `run_tasks` llama a `time.sleep(NBA_PAUSE_SECONDS)` entre tareas consecutivas. Batch secuencial, sin paralelismo. El valor inicial (1.0 s) es provisional y se ajusta en la tarea 0; no se inventa.

**Reintentos.** `client.py` usa `@retry` de `tenacity` sobre un intento HTTP:
- Reintenta solo 403, 429, 500, 502, 503 y 504, con `wait_exponential_jitter`.
- Máximo 5 intentos. Después la tarea falla sin abortar el batch.
- No se parsea `Retry-After`: el backoff exponencial basta.

**Timeouts.** Toda petición lleva `timeout` explícito (conexión y lectura). Sin timeout, el batch puede quedarse colgado.

## Tareas secuenciales

Cada tarea termina con `pytest` en verde y el criterio de hecho cumplido.

### Tarea 0 — Verificación de endpoints (spike, sin código de producción)
- Hacer peticiones reales a los endpoints candidatos desde el navegador o con un script manual.
- Anotar en `docs/spike_endpoints.md`: URL exacta, query params, headers que hacen falta y si fallan sin ellos, códigos de respuesta, tamaño y ritmo que tolera el servidor.
- Estado: **bloqueada**. Desde el entorno de desarrollo, `stats.nba.com` cierra la conexión (`ConnectionResetError`) sin devolver código HTTP.
- Criterio: cada parámetro de `endpoints.json` tiene una evidencia documentada.

### Tarea 1 — Rango de temporadas (`seasons.py`)
- Test: dada una fecha, devuelve exactamente 10 temporadas en formato `YYYY-YY`, incluida la actual, y cambia correctamente en octubre.
- Criterio: tests verdes con fechas límite (31 de diciembre, 1 de octubre).

### Tarea 2 — Catálogo de endpoints (`catalog.py`, `endpoints.json`)
- Formato: diccionario por id con `url`, `fixedParams` y `seasonParamName`.
- Test: valida campos obligatorios, rechaza `seasonParamName` dentro de `fixedParams`, carga el fichero.
- Criterio: el JSON contiene solo parámetros verificados en la tarea 0.

### Tarea 3 — Headers (`headers.py`)
- Test: el diccionario contiene `User-Agent`, `Referer`, `Origin` y las cabeceras de la API; el User-Agent se puede sobrescribir.
- Criterio: valores idénticos a los de la tarea 0.

### Tarea 4 — Cliente HTTP (`client.py`)
- Test con `Session` simulada: 200 devuelve bytes crudos; 403/429/5xx reintentan; 404 falla de inmediato; agotar reintentos lanza `NbaApiError`; timeout explícito en cada llamada; JSON inválido lanza error.
- Espera exponencial de tenacity desactivada en tests con `retry_with(wait=wait_none())`.
- Criterio: los bytes devueltos son exactamente los de la respuesta.

### Tarea 5 — Ruta Bronze (`bronze_path.py`)
- Ruta: `bronze/{endpoint_id}/season={season}/download_date={YYYY-MM-DD}/{endpoint_id}.json`.
- Test: formato exacto; misma entrada → misma ruta (determinismo).
- Justificación: particionado por temporada y fecha de descarga permite reejecutar un día sin duplicar datos (idempotencia: el mismo día sobrescribe el mismo objeto).

### Tarea 6 — Subida a GCS (`gcs_uploader.py`)
- Test con bucket falso: `content_type="application/json"`, nombre de objeto igual a la ruta de la tarea 5, y los bytes no se modifican.
- Criterio: ningún test toca GCS real.

### Tarea 7 — Orquestación (`ingest.py`)
- Test: se generan endpoints × temporadas tareas; un fallo en una tarea no detiene las demás; hay pausa entre tareas y no tras la última; el resultado agrega éxitos y fallos.
- Criterio: resumen con total, éxitos y fallos; el batch sigue ante fallos parciales.

### Tarea 8 — Configuración y entrada (`config.py`, `__main__.py`)
- Test: lee bucket, proyecto, user-agent y pausa de variables de entorno; `NBA_GCS_BUCKET` es obligatoria.
- `__main__.py` devuelve exit code 0 solo si todas las tareas tuvieron éxito.

### Tarea 9 — Prueba de fuego (prueba real, una sola petición)
- Script temporal que instancia el cliente, lee `leaguegamelog` de `endpoints.json`, envía las cabeceras de navegador y hace una única llamada para `2023-24`.
- Criterio: código de estado devuelto. Si es 200, primeros 300 caracteres de la respuesta.
- Estado: **bloqueada**. El servidor cierra la conexión (`ConnectionResetError 10054`) antes de responder; no hay código HTTP que reportar.

### Tarea 10 — Prueba end-to-end controlada
- Ejecutar contra un bucket de **desarrollo** con credenciales en `secrets/` (gitignored), limitado a una temporada y un endpoint.
- Verificar: objeto creado con la ruta correcta, JSON válido, bytes idénticos a la respuesta, y segunda ejecución del mismo día sin duplicados.
- Criterio: evidencia (ruta del objeto y tamaño) anotada en `docs/spike_endpoints.md`.

### Tarea 11 — Ejecución completa
- Ejecutar las 10 temporadas × todos los endpoints con la pausa validada.
- Criterio: todas las tareas en éxito o con fallos explicados y reintentables.

## Dependencias

`requirements.txt`:

```
requests
google-cloud-storage
pytest
tenacity
```
