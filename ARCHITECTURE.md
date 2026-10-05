# Arquitectura — Fase 1: Ingesta Histórica a Bronze Layer

## Resumen

Esta fase implementa una aplicación batch en Java puro que descarga las últimas 10
temporadas desde `stats.nba.com` y sube los JSON crudos (sin transformar) a un bucket
de Google Cloud Storage, organizados como capa Bronze particionada por endpoint,
temporada y fecha de descarga.

El reto técnico central es evitar bloqueos del servidor de la NBA: se resuelve con
headers HTTP específicos (`NbaStatsHeaders`), un *rate limiter* proactivo
(`RateLimiter`) que espacía todas las peticiones, y una política de reintentos con
backoff exponencial (`RetryPolicy`) que reacciona ante respuestas 429/403/5xx sin
abortar el resto del batch.

El volumen de datos del jugador se obtiene con una sola petición por temporada al
endpoint `leaguegamelog` usando `PlayerOrTeam=P` (en vez de iterar por `PlayerID`),
lo que mantiene el batch completo en el orden de ~40 peticiones totales
(4 variantes de endpoint × 10 temporadas).

## Flujo de una tarea de ingesta

```mermaid
flowchart TD
    Start([Inicio: IngestionOrchestrator.runAll]) --> Loop{Para cada<br/>endpoint x temporada}
    Loop --> Task[IngestionTask.execute]

    Task --> RateLimit[RateLimiter.acquire<br/>espera el delay minimo configurado]
    RateLimit --> Headers[NbaStatsHeaders.buildHeaders<br/>User-Agent, Referer, Origin,<br/>x-nba-stats-origin, x-nba-stats-token...]
    Headers --> Send[NbaStatsHttpClient.get<br/>HttpClient.send a stats.nba.com]

    Send --> Status{Codigo de<br/>respuesta}

    Status -->|200 OK| Gzip{Content-Encoding<br/>gzip?}
    Gzip -->|si| Decompress[Descomprimir con GZIPInputStream]
    Gzip -->|no| Validate
    Decompress --> Validate[JsonUtils.isValidJson]

    Status -->|429 / 403 / 5xx| Retry{RetryPolicy.shouldRetry<br/>intento, codigo}
    Retry -->|si, quedan intentos| Backoff[RetryPolicy.computeDelayMillis<br/>backoff exponencial + jitter]
    Backoff --> RateLimit
    Retry -->|no, reintentos agotados| Fail[NbaApiException]

    Validate -->|JSON valido| BuildPath[BronzePathBuilder.buildPath<br/>bronze/endpoint/season=.../download_date=.../archivo.json]
    BuildPath --> Upload[GcsUploader.upload<br/>sube bytes crudos a GCS]
    Upload --> Success[IngestionResult exitoso]

    Fail --> ResultFail[IngestionResult fallido]

    Success --> Loop
    ResultFail --> Loop

    Loop -->|todas las tareas procesadas| Summary[Resumen final:<br/>total / exitos / fallos]
    Summary --> End([Fin: exit code 0 o 1])
```

## Componentes por paquete

- **`config`** — qué se descarga: rango de temporadas (`SeasonRange`), catálogo de
  endpoints (`EndpointsCatalog`, `EndpointDefinition`) y configuración general
  (`AppConfig`).
- **`http`** — cómo hablarle a `stats.nba.com` sin bloqueo: headers (`NbaStatsHeaders`),
  rate limiting (`RateLimiter`), reintentos (`RetryPolicy`) y el cliente HTTP
  (`NbaStatsHttpClient`) que los integra.
- **`storage`** — dónde y cómo se guarda en GCS: construcción del path particionado
  (`BronzePathBuilder`) y subida (`GcsUploader`).
- **`ingest`** — orquestación: una tarea por combinación endpoint/temporada
  (`IngestionTask`, `IngestionResult`) coordinadas por `IngestionOrchestrator`, que
  continúa el batch ante fallos parciales.
- **`util`** — utilidades mínimas sin lógica de negocio (`JsonUtils`).

## Estado actual

Este documento corresponde al esqueleto inicial del proyecto: todas las clases
están definidas con sus firmas y JavaDoc, pero sin lógica interna implementada
(los métodos lanzan `UnsupportedOperationException`). La implementación se abordará
de forma iterativa en los siguientes pasos, siguiendo el orden de tareas de
`PLAN_FASE1.md`.
