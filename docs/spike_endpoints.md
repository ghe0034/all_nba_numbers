# Spike de endpoints — evidencia verificada

Fecha: 2026-11-14. Cliente: `curl_cffi` 0.17.0 con `impersonate="chrome"`, desde el entorno de desarrollo (Windows).

## leaguegamelog

Petición real única (misma construcción que `client.fetch_endpoint`: `build_request_params` + `build_headers`).

| Elemento | Valor |
|---|---|
| URL | `https://stats.nba.com/stats/leaguegamelog` |
| Query params fijos | `PlayerOrTeam=P`, `Direction=DESC`, `LeagueID=00`, `Sorter=PTS`, `SeasonType=Regular Season` |
| Param de temporada | `Season` (ej. `2023-24`) |
| Headers enviados | `Accept: application/json, text/plain, */*`, `Origin: https://www.nba.com`, `Referer: https://www.nba.com/` |
| Headers gestionados por `impersonate="chrome"` | `User-Agent`, `Sec-Ch-Ua*`, `Sec-Fetch-*`, `Accept-Language`, etc. |
| Estado HTTP | 200 |
| `Content-Type` | `application/json; charset=utf-8` |
| Tamaño (2023-24) | 4 516 141 bytes |
| Latencia | 3,5 s |
| `resource` | `leaguegamelog` |
| `resultSets` | 1 (`LeagueGameLog`), 26 401 filas |
| `parameters` devueltos | los enviados más `Counter=0`, `DateFrom=""`, `DateTo=""` |

Respuesta (primeros 300 bytes): `{"resource":"leaguegamelog","parameters":{"LeagueID":"00","Season":"2023-24","SeasonType":"Regular Season","PlayerOrTeam":"P","Counter":0,"Sorter":"PTS","Direction":"DESC","DateFrom":"","DateTo":""},"resultSets":[{"name":"LeagueGameLog","headers":["SEASON_ID","PLAYER_ID","PLAYER_NAME","TEAM_ID","TEA`

## Historial del bloqueo TLS

Con `requests` el servidor cerraba la conexión (`ConnectionResetError 10054`) antes de devolver código HTTP. Con `curl_cffi` + `impersonate="chrome"` responde 200. Cabeceras `x-nba-stats-origin`, `x-nba-stats-token`, `Accept-Language`, `Connection` y `Sec-Fetch-*` manuales se retiraron: la petición con solo `Accept`/`Origin`/`Referer` devuelve 200.

## No verificado todavía

- Si `Origin`/`Referer`/`Accept` son imprescindibles (no se probó la petición sin ellos).
- Ritmo que tolera el servidor: solo se ha hecho 1 petición; la pausa `NBA_PAUSE_SECONDS=1.5` + jitter hasta 2.0 s es provisional hasta la ejecución de 1 temporada y el backfill.
- Otras temporadas y otros endpoints.

## Ensayo end-to-end contra GCS (tarea 10)

Pendiente: anotar aquí la ruta del objeto y su tamaño tras `python -m nba_ingest --seasons 1`.
