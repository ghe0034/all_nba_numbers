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
- Otras temporadas (solo 2023-24 para los endpoints nuevos) y otros endpoints.

## leaguegamelog_teams

Spike 2026-11-15, temporada 2023-24, vía `client.fetch_endpoint`. Misma URL que `leaguegamelog`, con `PlayerOrTeam=T`.

| Elemento | Valor |
|---|---|
| URL | `https://stats.nba.com/stats/leaguegamelog` |
| Query params fijos | `PlayerOrTeam=T`, `Direction=DESC`, `LeagueID=00`, `Sorter=PTS`, `SeasonType=Regular Season` |
| Param de temporada | `Season` (`2023-24`) |
| Estado HTTP | 200 |
| Tamaño | 390 337 bytes |
| Latencia | 1,3 s |
| `resource` | `leaguegamelog` |
| `resultSets` | 1 (`LeagueGameLog`), 2 460 filas, 29 columnas |

Respuesta (primeros 300 bytes): `{"resource":"leaguegamelog","parameters":{"LeagueID":"00","Season":"2023-24","SeasonType":"Regular Season","PlayerOrTeam":"T","Counter":0,"Sorter":"PTS","Direction":"DESC","DateFrom":"","DateTo":""},"resultSets":[{"name":"LeagueGameLog","headers":["SEASON_ID","TEAM_ID","TEAM_ABBREVIATION","TEAM_NAME`

Columnas: `SEASON_ID, TEAM_ID, TEAM_ABBREVIATION, TEAM_NAME, GAME_ID, GAME_DATE, MATCHUP, WL, MIN, FGM, FGA, FG_PCT, FG3M, FG3A, FG3_PCT, FTM, FTA, FT_PCT, OREB, DREB, REB, AST, STL, BLK, TOV, PF, PTS, PLUS_MINUS, VIDEO_AVAILABLE`.

## teamgamelogs_advanced

Spike 2026-11-15, temporada 2023-24, vía `client.fetch_endpoint`.

| Elemento | Valor |
|---|---|
| URL | `https://stats.nba.com/stats/teamgamelogs` |
| Query params fijos | `LeagueID=00`, `SeasonType=Regular Season`, `MeasureType=Advanced`, `PerMode=Totals`, `PlusMinus=N`, `PaceAdjust=N`, `Rank=N`, `Outcome=""`, `Location=""`, `Month=0`, `SeasonSegment=""`, `DateFrom=""`, `DateTo=""`, `OpponentTeamID=0`, `VsConference=""`, `VsDivision=""`, `GameSegment=""`, `Period=0`, `ShotClockRange=""`, `LastNGames=0` |
| Param de temporada | `Season` (`2023-24`) |
| Estado HTTP | 200 |
| Tamaño | 732 583 bytes |
| Latencia | 1,8 s |
| `resource` | `gamelogs` |
| `resultSets` | 1 (`TeamGameLogs`), 2 460 filas, 49 columnas |
| `parameters` devueltos | la API los renombra: `SeasonYear=2023-24` (por `Season`), `OppTeamID=0` (por `OpponentTeamID`); los vacíos vuelven como `null`; añade `PORound`, `TeamID`, `PlayerID`, `IstRound` |

Verificación de temporada: petición aparte con solo `LeagueID`, `SeasonType`, `MeasureType`, `PerMode` y `Season=2023-24` → 200, 2 460 filas, `SEASON_YEAR` único `2023-24`, `GAME_DATE` de 2023-10-24 a 2024-04-14. Confirma que `Season` es aceptado como param de temporada. No se probó si `PlusMinus`, `PaceAdjust` y `Rank` alteran la respuesta (no aparecen en `parameters`; las columnas `*_RANK` vienen presentes con `Rank=N`).

Respuesta (primeros 300 bytes): `{"resource":"gamelogs","parameters":{"MeasureType":"Advanced","PerMode":"Totals","LeagueID":"00","SeasonYear":"2023-24","SeasonType":"Regular Season","PORound":null,"TeamID":0,"PlayerID":0,"Outcome":null,"Location":null,"Month":0,"SeasonSegment":null,"DateFrom":"","DateTo":"","OppTeamID":0,"VsConfer`

Columnas: `SEASON_YEAR, TEAM_ID, TEAM_ABBREVIATION, TEAM_NAME, GAME_ID, GAME_DATE, MATCHUP, WL, MIN, E_OFF_RATING, OFF_RATING, E_DEF_RATING, DEF_RATING, E_NET_RATING, NET_RATING, AST_PCT, AST_TO, AST_RATIO, OREB_PCT, DREB_PCT, REB_PCT, TM_TOV_PCT, EFG_PCT, TS_PCT, E_PACE, PACE, PACE_PER40, POSS, PIE` y 20 columnas de ranking (`GP_RANK, W_RANK, L_RANK, W_PCT_RANK, MIN_RANK, OFF_RATING_RANK, … PIE_RANK`) más `AVAILABLE_FLAG`.

## Ensayo end-to-end contra GCS (tarea 10)

- Comando: `python -m nba_ingest --seasons 1`
- Objeto generado: `gs://nba-bronze-dev-ghe0034/bronze/leaguegamelog/season=2026-27/download_date=2026-11-14/leaguegamelog.json`
- Tamaño: 706 267 bytes (689,71 KiB).
- Idempotencia: verificada en una segunda ejecución; se sobrescribe el mismo objeto, sin duplicados.
