"""Rangos de fechas inclusivos para la ingesta incremental (funciones puras)."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from nba_ingest.seasons import SEASON_START_MONTH, season_label

ISO_DATE_FORMAT = "%Y-%m-%d"
NBA_DATE_FORMAT = "%m/%d/%Y"  # formato que espera stats.nba.com en DateFrom/DateTo


@dataclass(frozen=True)
class DateRange:
    """Ventana de fechas con ambos extremos inclusivos."""

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError("La fecha inicial no puede ser posterior a la final")


def days_back_range(today: date, days_back: int) -> DateRange:
    """Ventana que termina hoy y empieza `days_back` días antes."""
    if days_back < 1:
        raise ValueError("days_back debe ser al menos 1")
    return DateRange(start=today - timedelta(days=days_back), end=today)


def format_nba_date(day: date) -> str:
    """Formatea una fecha como `MM/DD/YYYY`, el formato de la API."""
    return day.strftime(NBA_DATE_FORMAT)


def parse_iso_date(text: str) -> date:
    """Lee una fecha `YYYY-MM-DD`; lanza ValueError si no es válida."""
    return datetime.strptime(text, ISO_DATE_FORMAT).date()


def seasons_for_range(date_range: DateRange) -> list[str]:
    """Temporadas que tocan la ventana, de la más antigua a la más reciente."""
    first_start_year = _season_start_year(date_range.start)
    last_start_year = _season_start_year(date_range.end)
    return [season_label(year) for year in range(first_start_year, last_start_year + 1)]


def _season_start_year(day: date) -> int:
    if day.month >= SEASON_START_MONTH:
        return day.year
    return day.year - 1
