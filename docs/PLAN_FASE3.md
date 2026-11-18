# PLAN_FASE3 — Capa Gold: dataset de features por partido

Alcance: paquete `nba_gold` que lee las 3 tablas Silver de una temporada y escribe `gold/matchup_features/season={s}/data.parquet`: 1 fila por partido, features calculadas solo con información anterior al partido, y targets. Fuera de alcance: modelado y selección de variables, orquestación (Fase 4).

Punto de partida: Silver completa en GCS (`player_game_logs`, `team_game_logs`, `team_advanced_logs`).

Reglas de trabajo (de [CLAUDE.md](CLAUDE.md)): TDD y no inventar parámetros de la API. Gold no llama a la API: solo lee Silver.

Estado: **implementada** (commit `c253403`). Ver verificación al final.

## Grano y garantía anti-leakage

- **Grano:** 1 fila por `game_id`. Se cruza el lado local (`is_home == True`, prefijo `home_`) con el visitante (`is_home == False`, prefijo `away_`).
- **Descartes:** partidos sin `wl`, partidos sin ambos lados (huérfanos o suspendidos), partidos con dos locales o lados duplicados.
- **Cálculo por equipo:** agrupado por `(team_id, season_id)` y ordenado por `(game_date, game_id)`. Un equipo no hereda historial de la temporada anterior: su debut queda en NaN.
- **Orden de operaciones:** `shift(1)` **antes** de `rolling`. La ventana nunca contiene el partido actual. Es la garantía central de la fase.
- **Cruce home/away:** se hace después de calcular las features por equipo, así que cada lado solo ve su propio pasado.

## Features

| Familia | Columnas | Regla |
|---|---|---|
| Rolling | `{win,pts,plus_minus,off_rating,def_rating,net_rating,pace,efg_pct,ts_pct,tm_tov_pct,oreb_pct,pie,top2_pts_share}_l{5,10}` | Media de los últimos 5 y 10 partidos previos, `min_periods=1` |
| Señal de jugadores | `top2_pts_share` | Puntos de los 2 máximos anotadores / puntos del equipo en el partido. Se calcula sobre el propio partido y luego se desplaza como el resto. Puntos nulos = 0. Denominador 0 → NaN |
| Fatiga | `rest_days`, `is_b2b`, `games_last_7d` | `rest_days`: días desde el partido anterior (NaN en debut). `is_b2b`: `rest_days == 1`. `games_last_7d`: partidos en los 7 días naturales previos, sin el actual |
| Diferenciales | `diff_{feature}` | `home_{feature} - away_{feature}` para cada feature anterior |
| Targets | `home_win`, `target_point_diff` | Resultado y diferencia de puntos del propio partido. Solo se usan como target |

Los puntos y el resultado del partido actual **no** aparecen como features: `pts`, `wl` y `plus_minus` del partido solo entran en los targets.

## Módulos

| Módulo | Responsabilidad |
|---|---|
| `features.py` | Lógica pura (pandas, sin I/O). Funciones componibles: base, señal de jugadores, rolling, descanso, pivot, diferenciales, orquestador `build_matchup_features` |
| `gcs_io.py` | Lectura de Parquet Silver, descubrimiento de temporadas y escritura Gold. Reutiliza `make_bucket`, `SEASON_PATTERN` y `build_silver_object_name` de `nba_silver.gcs_io` |
| `pipeline.py` | Por temporada: leer 3 tablas → construir features → escribir. Si falta una tabla o no hay filas, no escribe |
| `__main__.py` | CLI. Reutiliza `load_local_env`, `load_settings` y `season_text` de `nba_silver.__main__` |

## Almacenamiento y CLI

```
python -m nba_gold --season 2024-25
python -m nba_gold --all-seasons
```

- Lectura: `silver/{tabla}/season={s}/data.parquet` para las 3 tablas.
- Escritura: `gold/matchup_features/season={s}/data.parquet` (snappy, sin índice).
- Idempotencia: un objeto determinista por temporada y orden estable. Mismo input → mismo contenido.
- `--all-seasons` descubre temporadas desde el prefijo `silver/team_game_logs/`.

## Tests (TDD)

Lógica pura (se ejecutan sin pyarrow):
- `test_gold_rolling.py`: el partido actual no entra en su ventana; cambiar su marcador no cambia su feature; debut NaN; `min_periods=1`; sin arrastre entre temporadas; independencia por equipo; orden de entrada irrelevante.
- `test_gold_player_signal.py`: top 2; nulos como 0; un solo jugador; denominador 0; equipo sin filas de jugadores.
- `test_gold_rest.py`: `rest_days`, `is_b2b`, `games_last_7d` en la frontera de 7 días; partidos futuros ignorados; debut; índice barajado.
- `test_gold_pivot.py`: 1 fila por partido; huérfanos y dobles locales descartados; duplicados no multiplican filas.
- `test_gold_matchup.py`: grano y columnas fijas; `diff_* == home - away`; targets correctos; contrato de columnas sin datos del partido actual; mutación de un marcador solo cambia sus targets; determinismo.

E/S y CLI (usan `FakeBucket` y la fixture `make_silver_frames` de `tests/unit/conftest.py`):
- `test_gold_gcs_io.py`: nombre del objeto, lectura inexistente → `None`, ida y vuelta Parquet, descubrimiento ordenado, sobrescritura.
- `test_gold_pipeline.py`: una fila por partido, idempotencia, tabla Silver ausente → no escribe, varias temporadas.
- `test_gold_main.py`: exclusión mutua de `--season`/`--all-seasons`, descubrimiento, resumen con `SALTADO`.

## Commits

Se hizo en **un único commit** (`c253403`), no uno por bloque como indicaba el orden de la Fase 2. Mensaje con typo (`eat:` en lugar de `feat:`); no se ha reescrito el historial.

## Verificación

- `ruff check src tests`: pasa.
- Lógica pura: 35 tests pasan con pandas.
- Suite completa (`python -m pytest -m "not integration" -v`): ejecutada por el usuario con pyarrow; 191 pasan y solo falla el test de Silver con payload vacío, ya corregido en `clean_dataframe`.
- Pendiente: ejecución real `python -m nba_gold --season 2024-25` contra el bucket. Comprobar `game_id` único, NaN solo en debuts, `diff_* == home_* - away_*`, y que una segunda ejecución deja el mismo objeto.

## Decisiones que no se han implementado

- Renombrar el extra `silver` a `data` o añadir `gold`: se mantiene `silver` (pandas y pyarrow ya cubren Gold).
- Playoffs: sin filtro. Entra lo que haya en Silver (hoy, solo temporada regular).
