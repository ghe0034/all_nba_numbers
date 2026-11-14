# Arquitectura — Fase 1: Ingesta Histórica a Bronze Layer

## Resumen

Esta fase implementa un script batch en Python 3.10+ que descarga las últimas 10
temporadas desde `stats.nba.com` y sube los JSON crudos (sin transformar) a un bucket
de Google Cloud Storage, organizados como capa Bronze particionada por endpoint,
temporada y fecha de descarga.

Se ejecuta como un único proceso de línea de comandos (`python -m nba_ingest`), sin
servicios ni framework. Dependencias: `curl_cffi` (HTTP con `impersonate="chrome"`), `tenacity` (reintentos),
`google-cloud-storage` (GCS) y `pytest` (tests). Los tests usan exclusivamente pytest
(funciones `test_*`, `assert`, `pytest.raises`, fixtures y `parametrize`); no se usa `unittest`.

El reto técnico central es evitar bloqueos del servidor de la NBA. Se combinan tres
mecanismos:
- **Huella de navegador**: `curl_cffi` con `impersonate="chrome"` aporta TLS, User-Agent y `Sec-Ch-Ua*`; `headers.py` añade solo `Accept`, `Origin` y `Referer`.
- **Pausa con jitter entre tareas**: el orquestador espera `NBA_PAUSE_SECONDS` más un
  aleatorio en [0, `NBA_PAUSE_JITTER_SECONDS`] entre peticiones con `time.sleep`. Es un batch secuencial, así que no hace falta un
  limitador más sofisticado.
- **Reintentos con backoff exponencial** (`tenacity`) ante 403, 429 y 5xx, sin
  abortar el resto del batch.

El volumen de datos del jugador se obtiene con una sola petición por temporada al
endpoint `leaguegamelog` usando `PlayerOrTeam=P` (en vez de iterar por `PlayerID`).

## Flujo de una tarea de ingesta

```mermaid
flowchart TD
    Start([Inicio: run_tasks]) --> Loop{Para cada<br/>endpoint x temporada}
    Loop --> Pause[time.sleep<br/>pausa + jitter entre tareas]
    Pause --> Task[run_task]

    Task --> Headers[build_headers<br/>Accept, Origin, Referer<br/>(UA y Sec-Ch-Ua los pone impersonate)]
    Headers --> Send[_get_once<br/>session.get(impersonate=chrome)<br/>a endpoint.url]

    Send --> Status{Codigo de<br/>respuesta}

    Status -->|200 OK| Validate[validar JSON]

    Status -->|403 / 429 / 5xx| Retry{tenacity<br/>quedan intentos?}
    Retry -->|si| Backoff[wait_exponential_jitter<br/>backoff + jitter]
    Backoff --> Send
    Retry -->|no, reintentos agotados| Fail[error de tarea]

    Status -->|otro codigo| Fail

    Validate -->|JSON valido| BuildPath[build_bronze_path<br/>bronze/endpoint/season=.../download_date=.../archivo.json]
    BuildPath --> Upload[upload_bytes<br/>sube bytes crudos a GCS]
    Upload --> Success[resultado exitoso]

    Fail --> ResultFail[resultado fallido]

    Success --> Loop
    ResultFail --> Loop

    Loop -->|todas las tareas procesadas| Summary[Resumen final:<br/>total / exitos / fallos]
    Summary --> End([Fin: exit code 0 o 1])
```

## Organización del código

Paquete `src/nba_ingest/`, con módulos de funciones:

- **`config`** — variables de entorno: bucket, proyecto, User-Agent opcional, pausa,
  jitter y número de temporadas (`NBA_SEASONS_COUNT`, por defecto 10).
- **`catalog` / `endpoints.json`** — qué se descarga. Cada entrada define `url`
  absoluta, `fixedParams` y `seasonParamName`. La temporada no va en `fixedParams`.
- **`seasons`** — últimas 10 temporadas en formato `YYYY-YY`.
- **`headers`** — cabeceras de dominio (`Accept`, `Origin`, `Referer`). Único sitio a tocar si la NBA
  cambia sus requisitos.
- **`client`** — petición con la sesión `curl_cffi` (inyectada), timeout explícito y reintentos con
  `@retry` de tenacity sobre un intento (`_get_once`). Valida JSON sin re-serializar.
- **`bronze_path`** — ruta particionada en GCS.
- **`gcs_uploader`** — subida con `google-cloud-storage`.
- **`__main__`** — CLI (`--seasons N` prevalece sobre `NBA_SEASONS_COUNT`); abre la sesión HTTP con
  context manager y la cierra al terminar. Credenciales GCS por ADC (`gcloud auth application-default login`).
- **`ingest`** — orquestación: una tarea por endpoint × temporada, pausa con jitter entre tareas
  y continuación ante fallos parciales.

## Decisiones

- **Sin rate limiter propio.** Un `time.sleep` con jitter entre tareas basta para un batch
  secuencial. Evita una dependencia y una clase de código que mantener.
- **Sin parseo de `Retry-After`.** El backoff exponencial de tenacity con jitter es
  suficiente para los 429.
- **Reintentos solo sobre estados transitorios.** Los 404 y otros códigos de error
  fallan de inmediato para no gastar peticiones.

## Estado actual

Módulos y tests unitarios implementados (44 tests pytest en `tests/unit/`, con HTTP y GCS simulados). Ejecución: `pytest`. Prueba real contra la API: `pytest -m integration`.

El catálogo `endpoints.json` contiene solo `leaguegamelog`, verificado con HTTP 200
(ver `docs/spike_endpoints.md`). El cierre de conexión TLS que daba `requests` se
resolvió con `curl_cffi` e `impersonate="chrome"`. Pendiente: ensayo de 1 temporada
contra un bucket de desarrollo y backfill completo.
