import json

import pandas as pd

from nba_silver.schemas import TableSpec


class SchemaValidationError(ValueError):
    """Error que lanzo si la API de la NBA cambia o quita columnas esperadas."""


def parse_nba_json(raw_json: str | bytes, download_date: str) -> pd.DataFrame:
    """Convierte un JSON de stats.nba.com en un DataFrame con nombres en minúsculas"""

    payload = json.loads(raw_json)
    result_set = payload["resultSets"][0]
    headers = [col.lower() for col in result_set["headers"]]
    rows = result_set["rowSet"]

    if not rows:
        return pd.DataFrame(columns=[*headers, "_download_date"])

    df = pd.DataFrame(rows, columns=headers)

    df["_download_date"] = download_date
    return df


def parse_minutes_to_decimal(minutes: pd.Series) -> pd.Series:
    """Convierte minutos 'MM:SS' a decimales (p. ej. '32:30' -> 32.5); valores inválidos pasan a NaN."""
    return minutes.map(_minutes_text_to_float).astype("float64")


def _minutes_text_to_float(value) -> float:
    if pd.isna(value):
        return float("nan")

    text = str(value).strip()
    if ":" not in text:
        return float(pd.to_numeric(text, errors="coerce"))

    minutes_part, seconds_part = text.split(":", maxsplit=1)
    minutes = pd.to_numeric(minutes_part, errors="coerce")
    seconds = pd.to_numeric(seconds_part, errors="coerce")
    return float(minutes) + float(seconds) / 60


def clean_dataframe(df: pd.DataFrame, spec: TableSpec) -> pd.DataFrame:
    """Valida columnas, limpia tipos de datos y añade campos derivados.

    Un payload sin filas (p. ej. una semana sin partidos) se devuelve tal cual: no hay datos que validar.
    """
    if df.empty:
        return df

    missing = set(spec.required_cols) - set(df.columns)
    if missing:
        raise SchemaValidationError(
            f"Faltan columnas en {spec.table_name}: {sorted(missing)}"
        )

    cleaned = df.copy()

    # Transformo los id a string para no perder 0s a la izquierda
    for id_col in ("game_id", "team_id", "player_id", "season_id"):
        if id_col in cleaned.columns:
            cleaned[id_col] = cleaned[id_col].astype(str)

    # Convierto fecha del partido a tipo fecha real
    if "game_date" in cleaned.columns:
        cleaned["game_date"] = pd.to_datetime(
            cleaned["game_date"], format="mixed"
        ).dt.date

    # Si juega en casa o no
    if "matchup" in cleaned.columns:
        cleaned["is_home"] = cleaned["matchup"].str.contains("vs.", regex=False)

    # Los minutos pueden venir como 'MM:SS' en temporadas antiguas; se pasan a decimal antes de castear
    if "min" in cleaned.columns:
        cleaned["min"] = parse_minutes_to_decimal(cleaned["min"])

    # Transformar datos numéricos a enteros y floats
    for col in spec.int_cols:
        if col in cleaned.columns:
            cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce").astype("Int64")

    for col in spec.float_cols:
        if col in cleaned.columns:
            cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce").astype(
                "float64"
            )
    return cleaned


def deduplicate(df: pd.DataFrame, spec: TableSpec) -> pd.DataFrame:
    """Elimina filas duplicadas conservando la versión con _download_date más reciente."""
    if df.empty:
        return df.drop(columns=["_download_date"], errors="ignore")

    ordered = df.sort_values("_download_date", ascending=True)
    deduped = ordered.drop_duplicates(subset=list(spec.natural_key), keep="last")
    return deduped.drop(columns=["_download_date"]).reset_index(drop=True)
