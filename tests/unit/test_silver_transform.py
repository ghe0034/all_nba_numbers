import json
from datetime import date

import pandas as pd
import pytest

from nba_silver.schemas import TEAM_GAME_LOGS
from nba_silver.transform import (
    SchemaValidationError,
    clean_dataframe,
    deduplicate,
    parse_nba_json,
)

DOWNLOAD_OLD = "2024-10-23"
DOWNLOAD_NEW = "2024-10-24"


def make_record(**overrides) -> dict:
    """Fila de LeagueGameLog con las cabeceras reales de stats.nba.com."""
    record = {
        "SEASON_ID": "22024",
        "TEAM_ID": 1610612747,
        "TEAM_ABBREVIATION": "LAL",
        "TEAM_NAME": "Los Angeles Lakers",
        "GAME_ID": "0022400001",
        "GAME_DATE": "2024-10-22",
        "MATCHUP": "LAL vs. DEN",
        "WL": "W",
        "MIN": 240,
        "FGM": 40,
        "FGA": 85,
        "FG_PCT": 0.471,
        "FG3M": 12,
        "FG3A": 30,
        "FG3_PCT": 0.4,
        "FTM": 15,
        "FTA": 20,
        "FT_PCT": 0.75,
        "OREB": 9,
        "DREB": 35,
        "REB": 44,
        "AST": 25,
        "STL": 7,
        "BLK": 4,
        "TOV": 12,
        "PF": 20,
        "PTS": 120,
        "PLUS_MINUS": 5.0,
    }
    record.update(overrides)
    return record


def build_raw_json(records: list[dict]) -> str:
    """Simula la respuesta JSON de la API con resultSets[0]."""
    headers = list(records[0].keys())
    rows = [[record[header] for header in headers] for record in records]
    payload = {
        "resultSets": [{"name": "LeagueGameLog", "headers": headers, "rowSet": rows}]
    }
    return json.dumps(payload)


def make_silver_frame(*records: dict) -> pd.DataFrame:
    """Atajo: JSON crudo -> DataFrame bronze, como lo recibe clean_dataframe."""
    return parse_nba_json(build_raw_json(list(records)), DOWNLOAD_OLD)


# --- parse_nba_json ---------------------------------------------------------


def test_parse_lowercases_headers_and_adds_download_date():
    df = parse_nba_json(build_raw_json([make_record()]), DOWNLOAD_OLD)

    assert "team_abbreviation" in df.columns
    assert "TEAM_ABBREVIATION" not in df.columns
    assert df["_download_date"].tolist() == [DOWNLOAD_OLD]


def test_parse_accepts_bytes_input():
    raw_bytes = build_raw_json([make_record()]).encode("utf-8")

    df = parse_nba_json(raw_bytes, DOWNLOAD_OLD)

    assert len(df) == 1


def test_parse_empty_rowset_returns_empty_frame_with_expected_columns():
    payload = json.dumps(
        {
            "resultSets": [
                {"name": "LeagueGameLog", "headers": ["GAME_ID", "PTS"], "rowSet": []}
            ]
        }
    )

    df = parse_nba_json(payload, DOWNLOAD_OLD)

    assert df.empty
    assert list(df.columns) == ["game_id", "pts", "_download_date"]


# --- clean_dataframe: validación de esquema --------------------------------


def test_clean_raises_when_required_column_is_missing():
    df = make_silver_frame(make_record()).drop(columns=["matchup"])

    with pytest.raises(SchemaValidationError, match="matchup"):
        clean_dataframe(df, TEAM_GAME_LOGS)


def test_clean_returns_empty_frame_without_error_when_no_rows():
    df = parse_nba_json(
        json.dumps(
            {
                "resultSets": [
                    {"name": "x", "headers": list(make_record().keys()), "rowSet": []}
                ]
            }
        ),
        DOWNLOAD_OLD,
    )

    cleaned = clean_dataframe(df, TEAM_GAME_LOGS)

    assert cleaned.empty


def test_clean_does_not_mutate_input_frame():
    df = make_silver_frame(make_record())
    original_game_date = df["game_date"].iloc[0]

    clean_dataframe(df, TEAM_GAME_LOGS)

    assert df["game_date"].iloc[0] == original_game_date
    assert "is_home" not in df.columns


# --- clean_dataframe: tipos -------------------------------------------------


def test_clean_keeps_leading_zeros_in_game_id():
    cleaned = clean_dataframe(
        make_silver_frame(make_record(GAME_ID="0022400001")), TEAM_GAME_LOGS
    )

    assert cleaned["game_id"].iloc[0] == "0022400001"


def test_clean_casts_numeric_ids_to_string():
    cleaned = clean_dataframe(
        make_silver_frame(make_record(TEAM_ID=1610612747)), TEAM_GAME_LOGS
    )

    assert cleaned["team_id"].iloc[0] == "1610612747"
    assert isinstance(cleaned["team_id"].iloc[0], str)


def test_clean_converts_game_date_to_python_date():
    cleaned = clean_dataframe(
        make_silver_frame(make_record(GAME_DATE="2024-10-22")), TEAM_GAME_LOGS
    )

    assert cleaned["game_date"].iloc[0] == date(2024, 10, 22)


def test_clean_casts_int_cols_to_nullable_int64():
    cleaned = clean_dataframe(
        make_silver_frame(make_record(PTS=120, PLUS_MINUS=5.0)), TEAM_GAME_LOGS
    )

    assert cleaned["pts"].dtype == "Int64"
    assert cleaned["pts"].iloc[0] == 120
    assert cleaned["plus_minus"].iloc[0] == 5


def test_clean_casts_float_cols_to_float64():
    cleaned = clean_dataframe(
        make_silver_frame(make_record(FG_PCT=0.471)), TEAM_GAME_LOGS
    )

    assert cleaned["fg_pct"].dtype == "float64"
    assert cleaned["fg_pct"].iloc[0] == pytest.approx(0.471)


def test_clean_coerces_invalid_numeric_values_to_null():
    cleaned = clean_dataframe(make_silver_frame(make_record(PTS="N/A")), TEAM_GAME_LOGS)

    assert pd.isna(cleaned["pts"].iloc[0])


# --- clean_dataframe: campos derivados --------------------------------------


@pytest.mark.parametrize(
    ("matchup", "expected_is_home"),
    [
        ("LAL vs. DEN", True),
        ("LAL @ DEN", False),
    ],
)
def test_clean_derives_is_home_from_matchup(matchup, expected_is_home):
    cleaned = clean_dataframe(
        make_silver_frame(make_record(MATCHUP=matchup)), TEAM_GAME_LOGS
    )

    assert bool(cleaned["is_home"].iloc[0]) is expected_is_home


# --- deduplicate ------------------------------------------------------------


def test_deduplicate_keeps_most_recent_download_for_same_natural_key():
    old = make_record(PTS=100)
    new = make_record(PTS=120)
    old_df = parse_nba_json(build_raw_json([old]), DOWNLOAD_OLD)
    new_df = parse_nba_json(build_raw_json([new]), DOWNLOAD_NEW)
    combined = pd.concat(
        [new_df, old_df], ignore_index=True
    )  # orden invertido a propósito

    deduped = deduplicate(clean_dataframe(combined, TEAM_GAME_LOGS), TEAM_GAME_LOGS)

    assert len(deduped) == 1
    assert deduped["pts"].iloc[0] == 120


def test_deduplicate_keeps_distinct_games_and_teams():
    df = make_silver_frame(
        make_record(GAME_ID="0022400001", TEAM_ID=1610612747),
        make_record(GAME_ID="0022400001", TEAM_ID=1610612743),
        make_record(GAME_ID="0022400002", TEAM_ID=1610612747),
    )

    deduped = deduplicate(clean_dataframe(df, TEAM_GAME_LOGS), TEAM_GAME_LOGS)

    assert len(deduped) == 3


def test_deduplicate_drops_download_date_and_resets_index():
    df = make_silver_frame(make_record(), make_record(GAME_ID="0022400002"))

    deduped = deduplicate(clean_dataframe(df, TEAM_GAME_LOGS), TEAM_GAME_LOGS)

    assert "_download_date" not in deduped.columns
    assert list(deduped.index) == [0, 1]


def test_deduplicate_empty_frame_drops_download_date_column():
    empty = parse_nba_json(
        json.dumps(
            {"resultSets": [{"name": "x", "headers": ["GAME_ID"], "rowSet": []}]}
        ),
        DOWNLOAD_OLD,
    )

    deduped = deduplicate(empty, TEAM_GAME_LOGS)

    assert deduped.empty
    assert "_download_date" not in deduped.columns
