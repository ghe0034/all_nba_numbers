"""Lógica pura de features pre-partido (sin I/O). Nada de lo que sale usa datos del propio partido."""

import numpy as np
import pandas as pd

GROUP_KEYS = ["team_id", "season_id"]
MATCH_KEYS = ["game_id", "season_id"]
WINDOWS = (5, 10)
ADVANCED_METRICS = (
    "off_rating",
    "def_rating",
    "net_rating",
    "pace",
    "efg_pct",
    "ts_pct",
    "tm_tov_pct",
    "oreb_pct",
    "pie",
)
ROLLING_METRICS = (
    "win",
    "pts",
    "plus_minus",
    *ADVANCED_METRICS,
    "top2_pts_share",
)
ROLLING_COLS = [
    f"{metric}_l{window}" for metric in ROLLING_METRICS for window in WINDOWS
]
REST_COLS = ["rest_days", "is_b2b", "games_last_7d"]
FEATURE_COLS = ROLLING_COLS + REST_COLS
TARGET_COLS = ["home_win", "target_point_diff"]
OUTPUT_COLUMNS = (
    ["game_id", "season_id", "game_date", "home_team_id", "away_team_id"]
    + [f"home_{col}" for col in FEATURE_COLS]
    + [f"away_{col}" for col in FEATURE_COLS]
    + [f"diff_{col}" for col in FEATURE_COLS]
    + TARGET_COLS
)


def build_team_game_base(
    team_logs: pd.DataFrame, adv_logs: pd.DataFrame
) -> pd.DataFrame:
    """Une logs básicos y avanzados por (game_id, team_id); descarta filas sin `wl`."""
    basic = team_logs[
        [
            "season_id",
            "game_id",
            "game_date",
            "team_id",
            "is_home",
            "wl",
            "pts",
            "plus_minus",
        ]
    ]
    advanced = adv_logs[["game_id", "team_id", *ADVANCED_METRICS]]

    base = basic.merge(advanced, on=["game_id", "team_id"], how="inner")
    base = base[base["wl"].notna()].drop_duplicates(["game_id", "team_id"]).copy()

    base["game_date"] = pd.to_datetime(base["game_date"])
    base["win"] = (base["wl"] == "W").astype("float64")
    base["is_home"] = base["is_home"].astype(bool)
    for numeric_col in ("pts", "plus_minus", *ADVANCED_METRICS):
        base[numeric_col] = base[numeric_col].astype("float64")
    return base.drop(columns="wl").reset_index(drop=True)


def add_player_signal(
    team_base: pd.DataFrame, player_logs: pd.DataFrame
) -> pd.DataFrame:
    """Añade `top2_pts_share` del propio partido: puntos de sus 2 máximos anotadores / puntos del equipo."""
    team_game_keys = ["game_id", "team_id"]
    players = player_logs[[*team_game_keys, "pts"]].copy()
    players["pts"] = players["pts"].fillna(0).astype("float64")

    top2_points = (
        players.sort_values("pts", ascending=False)
        .groupby(team_game_keys)
        .head(2)
        .groupby(team_game_keys, as_index=False)["pts"]
        .sum()
        .rename(columns={"pts": "top2_pts"})
    )

    merged = team_base.merge(top2_points, on=team_game_keys, how="left")
    merged["top2_pts_share"] = merged["top2_pts"] / merged["pts"].where(
        merged["pts"] > 0
    )
    return merged.drop(columns="top2_pts")


def _sort_chronologically(team_base: pd.DataFrame) -> pd.DataFrame:
    return team_base.sort_values([*GROUP_KEYS, "game_date", "game_id"]).reset_index(
        drop=True
    )


def add_rolling_features(
    team_base: pd.DataFrame,
    metrics: tuple[str, ...] = ROLLING_METRICS,
    windows: tuple[int, ...] = WINDOWS,
) -> pd.DataFrame:
    """Medias móviles `{metric}_l{window}` por (team_id, season_id).

    `shift(1)` va ANTES del rolling: la ventana nunca contiene el partido actual.
    """
    ordered = _sort_chronologically(team_base)
    grouped = ordered.groupby(GROUP_KEYS)
    for metric in metrics:
        for window in windows:
            ordered[f"{metric}_l{window}"] = grouped[metric].transform(
                lambda series, w=window: (
                    series.shift(1).rolling(w, min_periods=1).mean()
                )
            )
    return ordered


def _count_games_in_previous_days(game_dates: pd.Series, days: int) -> pd.Series:
    """Partidos en [fecha - days, fecha): excluye el actual y cualquier partido del mismo día o posterior."""
    dates = game_dates.to_numpy(dtype="datetime64[ns]")
    window_start = dates - np.timedelta64(days, "D")
    counts = np.searchsorted(dates, dates, side="left") - np.searchsorted(
        dates, window_start, side="left"
    )
    return pd.Series(counts, index=game_dates.index)


def add_rest_features(team_base: pd.DataFrame, window_days: int = 7) -> pd.DataFrame:
    """Añade `rest_days`, `is_b2b` y `games_last_7d` por (team_id, season_id)."""
    ordered = _sort_chronologically(team_base)
    grouped = ordered.groupby(GROUP_KEYS)

    ordered["rest_days"] = grouped["game_date"].diff().dt.days
    ordered["is_b2b"] = (ordered["rest_days"] == 1).astype(int)
    ordered["games_last_7d"] = grouped["game_date"].transform(
        lambda dates: _count_games_in_previous_days(dates, window_days)
    )
    return ordered


def pivot_home_away(
    team_features: pd.DataFrame, feature_cols: list[str]
) -> pd.DataFrame:
    """1 fila por game_id con prefijos home_/away_; descarta partidos sin exactamente 1 local y 1 visitante."""
    sides_per_game = team_features.groupby("game_id")["is_home"].agg(
        home_rows="sum", total_rows="size"
    )
    complete_game_ids = sides_per_game.index[
        (sides_per_game["home_rows"] == 1) & (sides_per_game["total_rows"] == 2)
    ]
    complete = team_features[team_features["game_id"].isin(complete_game_ids)]

    carried_cols = ["team_id", "pts", "win", *feature_cols]
    home = complete.loc[complete["is_home"], [*MATCH_KEYS, "game_date", *carried_cols]]
    away = complete.loc[~complete["is_home"], [*MATCH_KEYS, *carried_cols]]

    home = home.rename(columns={col: f"home_{col}" for col in carried_cols})
    away = away.rename(columns={col: f"away_{col}" for col in carried_cols})
    return home.merge(away, on=MATCH_KEYS, validate="one_to_one")


def add_diffs_and_targets(matchup: pd.DataFrame) -> pd.DataFrame:
    """Añade `diff_*` (home - away) y los targets. Los puntos del partido solo se usan para el target."""
    result = matchup.copy()
    for col in FEATURE_COLS:
        result[f"diff_{col}"] = result[f"home_{col}"] - result[f"away_{col}"]
    result["target_point_diff"] = result["home_pts"] - result["away_pts"]
    return result


def build_matchup_features(
    team_logs: pd.DataFrame, adv_logs: pd.DataFrame, player_logs: pd.DataFrame
) -> pd.DataFrame:
    """Dataset Gold de una temporada: 1 fila por partido, features pre-partido y targets."""
    base = build_team_game_base(team_logs, adv_logs)
    if base.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    with_players = add_player_signal(base, player_logs)
    with_rolling = add_rolling_features(with_players)
    with_rest = add_rest_features(with_rolling)

    matchup = pivot_home_away(with_rest, FEATURE_COLS)
    matchup = add_diffs_and_targets(matchup)
    # `home_win` es el resultado real del partido, solo válido como target
    matchup["home_win"] = matchup["home_win"].astype(int)

    return (
        matchup[OUTPUT_COLUMNS]
        .sort_values(["game_date", "game_id"])
        .reset_index(drop=True)
    )
