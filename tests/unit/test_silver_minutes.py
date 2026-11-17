import pandas as pd

from nba_silver.schemas import TableSpec
from nba_silver.transform import clean_dataframe, parse_minutes_to_decimal

PLAYER_MINUTES_SPEC = TableSpec(
    table_name="minutes_check",
    bronze_endpoint="leaguegamelog",
    natural_key=("game_id",),
    required_cols=("game_id", "min"),
    int_cols=(),
    float_cols=("min",),
)


def test_parse_minutes_converts_mm_ss_to_decimal_minutes():
    minutes = pd.Series(["32:30", "0:45"])

    result = parse_minutes_to_decimal(minutes)

    assert result.tolist() == [32.5, 0.75]
    assert result.dtype == "float64"


def test_parse_minutes_keeps_plain_numeric_values():
    minutes = pd.Series(["240", 31.5])

    assert parse_minutes_to_decimal(minutes).tolist() == [240.0, 31.5]


def test_parse_minutes_turns_missing_or_invalid_values_into_nan():
    minutes = pd.Series([None, "N/A", "12:xx"])

    assert parse_minutes_to_decimal(minutes).isna().all()


def test_clean_converts_mm_ss_before_casting_float_columns():
    df = pd.DataFrame({"game_id": ["0022400001"], "min": ["32:30"]})

    cleaned = clean_dataframe(df, PLAYER_MINUTES_SPEC)

    assert cleaned["min"].iloc[0] == 32.5
    assert cleaned["min"].dtype == "float64"
