"""Orquestación Silver -> Gold por temporada."""

from dataclasses import dataclass
from typing import Any

from nba_gold.features import build_matchup_features
from nba_gold.gcs_io import read_silver_table, upload_parquet
from nba_silver.schemas import PLAYER_GAME_LOGS, TEAM_ADVANCED_LOGS, TEAM_GAME_LOGS


@dataclass(frozen=True)
class SeasonResult:
    season: str
    row_count: int
    written: bool


def process_season(bucket: Any, season: str) -> SeasonResult:
    """Construye y escribe el Parquet Gold de una temporada.

    Si falta alguna tabla Silver o no queda ninguna fila, no escribe nada.
    """
    team_logs = read_silver_table(bucket, TEAM_GAME_LOGS.table_name, season)
    adv_logs = read_silver_table(bucket, TEAM_ADVANCED_LOGS.table_name, season)
    player_logs = read_silver_table(bucket, PLAYER_GAME_LOGS.table_name, season)

    silver_tables = (team_logs, adv_logs, player_logs)
    if any(table is None or table.empty for table in silver_tables):
        return SeasonResult(season, row_count=0, written=False)

    matchup = build_matchup_features(team_logs, adv_logs, player_logs)
    if matchup.empty:
        return SeasonResult(season, row_count=0, written=False)

    upload_parquet(bucket, season, matchup)
    return SeasonResult(season, row_count=len(matchup), written=True)


def run_pipeline(bucket: Any, seasons: list[str]) -> list[SeasonResult]:
    """Procesa cada temporada de forma secuencial."""
    return [process_season(bucket, season) for season in seasons]
