# Spike de endpoints (tarea 0)

Estado: **pendiente**. Desde el entorno de desarrollo, `stats.nba.com` cierra la conexión (timeout y reset) incluso con headers de navegador. No hay evidencia real de parámetros ni headers.

Pendiente de verificar desde un navegador o una red distinta:
- URL y query params exactos de `leaguegamelog` (`PlayerOrTeam=P`) y demás endpoints.
- Headers mínimos que evitan 403 y valores de `x-nba-stats-*`.
- Intervalo mínimo entre peticiones que no provoca bloqueo.

Hasta completar este spike, `src/nba_ingest/endpoints.json` está vacío y la ejecución no genera tareas.
