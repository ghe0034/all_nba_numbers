# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proyecto

Batch en Java 17 (Maven, sin framework) que descarga las últimas 10 temporadas de `stats.nba.com` y sube los JSON crudos a una capa Bronze en Google Cloud Storage. El diseño completo y el diagrama de flujo están en [ARCHITECTURE.md](ARCHITECTURE.md). Código, JavaDoc y documentación están en español.

## Comandos

```
mvn test                                   # todos los tests
mvn test -Dtest=RetryPolicyTest            # una clase
mvn test -Dtest=RetryPolicyTest#delayNeverExceedsMax   # un test
mvn package                                # jar ejecutable (shade) en target/ingesta-fase1.jar
```

No hay linter configurado.

## Arquitectura

Cada tarea es un par endpoint × temporada: `IngestionOrchestrator` itera las tareas y continúa ante fallos parciales; `IngestionTask` ejecuta `RateLimiter.acquire` → `NbaStatsHttpClient.get` (con `NbaStatsHeaders`) → validar JSON → `BronzePathBuilder` → `GcsUploader`. Ante 429/403/5xx, `RetryPolicy` decide el reintento y el flujo vuelve al rate limiter. El exit code de `App` es 0 solo si todas las tareas tuvieron éxito.

Puntos que no se ven leyendo un solo archivo:
- Los endpoints se definen en `src/main/resources/endpoints.json` (`EndpointDefinition`: `id`, `path` relativo, `fixedParams`, `seasonParamName`). La temporada **no** va en `fixedParams`; se inyecta por tarea bajo `seasonParamName`. Agregar o cambiar una variante no requiere recompilar código.
- Los datos de jugador salen de `leaguegamelog` con `PlayerOrTeam=P` (una petición por temporada), no iterando por `PlayerID`.
- `NbaStatsHeaders` es el único lugar a tocar si la NBA cambia los headers requeridos; el User-Agent se puede sobrescribir (por `AppConfig` o por parámetro).
- El `RateLimiter` se aplica siempre antes de cada request (también en reintentos); `RetryPolicy` usa `min(base·2^intento + jitter(0, base), max)` con intento 1-indexado.

## Estado y flujo de trabajo

Se implementa de forma iterativa con TDD (test primero, luego código). Implementado y con tests: `RateLimiter`, `RetryPolicy`, `NbaStatsHeaders`, `EndpointsCatalog`/`EndpointDefinition`. El resto de clases (`App`, `AppConfig.load`, `SeasonRange`, `NbaStatsHttpClient`, `storage/*`, `ingest/*`, `JsonUtils`) sigue siendo esqueleto que lanza `UnsupportedOperationException`. El usuario indica explícitamente qué implementar en cada paso; no adelantes clases fuera de ese alcance (p. ej. `NbaStatsHttpClient` y todo lo de GCS).

`secrets/` y `*.local.properties` están en `.gitignore` (credenciales de GCP y overrides locales); `target/` también.
