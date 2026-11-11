"""Cálculo de las temporadas NBA a descargar."""

from datetime import date

SEASON_COUNT = 10
SEASON_START_MONTH = 10


def season_label(start_year: int) -> str:
    """Formatea el año de inicio como temporada NBA, p. ej. 2025 -> '2025-26'."""
    end_suffix = (start_year + 1) % 100
    return f"{start_year}-{end_suffix:02d}"


def current_season_start_year(today: date) -> int:
    """Año de inicio de la temporada en curso (la temporada empieza en octubre)."""
    if today.month >= SEASON_START_MONTH:
        return today.year
    return today.year - 1


def last_seasons(today: date, count: int = SEASON_COUNT) -> list[str]:
    """Devuelve las `count` temporadas más recientes, la más antigua primero."""
    newest_start_year = current_season_start_year(today)
    oldest_start_year = newest_start_year - count + 1
    return [season_label(year) for year in range(oldest_start_year, newest_start_year + 1)]
