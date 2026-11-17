import pandas as pd
import pytest


class FakeBlob:
    """Blob en memoria con la misma interfaz mínima que google.cloud.storage.Blob."""

    def __init__(self, bucket: "FakeBucket", name: str):
        self._bucket = bucket
        self.name = name

    def download_as_bytes(self) -> bytes:
        return self._bucket.objects[self.name]

    def upload_from_string(self, body: bytes, content_type: str | None = None) -> None:
        self._bucket.objects[self.name] = body


class FakeBucket:
    """Bucket en memoria: `objects` mapea nombre de objeto -> bytes."""

    def __init__(self):
        self.objects: dict[str, bytes] = {}

    def blob(self, name: str) -> FakeBlob:
        return FakeBlob(self, name)

    def list_blobs(self, prefix: str = "") -> list[FakeBlob]:
        return [
            FakeBlob(self, name)
            for name in sorted(self.objects)
            if name.startswith(prefix)
        ]


@pytest.fixture
def fake_bucket() -> FakeBucket:
    return FakeBucket()


@pytest.fixture
def make_silver_frames():
    """Fábrica de tablas Silver sintéticas a partir de partidos (game_id, fecha, local, visitante, pts_local, pts_visitante)."""

    def factory(games, season_id="22024"):
        team_rows, adv_rows, player_rows = [], [], []
        for game_id, game_date, home_id, away_id, home_pts, away_pts in games:
            sides = (
                (home_id, home_pts, away_pts, True),
                (away_id, away_pts, home_pts, False),
            )
            for team_id, own_pts, rival_pts, is_home in sides:
                team_rows.append(
                    {
                        "season_id": season_id,
                        "game_id": game_id,
                        "game_date": pd.Timestamp(game_date).date(),
                        "team_id": team_id,
                        "is_home": is_home,
                        "wl": "W" if own_pts > rival_pts else "L",
                        "pts": own_pts,
                        "plus_minus": own_pts - rival_pts,
                    }
                )
                adv_rows.append(
                    {
                        "game_id": game_id,
                        "team_id": team_id,
                        "off_rating": float(own_pts),
                        "def_rating": float(rival_pts),
                        "net_rating": float(own_pts - rival_pts),
                        "pace": 100.0,
                        "efg_pct": 0.5,
                        "ts_pct": 0.55,
                        "tm_tov_pct": 0.13,
                        "oreb_pct": 0.25,
                        "pie": 0.5,
                    }
                )
                for player_number, player_pts in enumerate((own_pts - 10, 6, 4)):
                    player_rows.append(
                        {
                            "game_id": game_id,
                            "team_id": team_id,
                            "player_id": f"{team_id}-{player_number}",
                            "pts": player_pts,
                        }
                    )

        team_logs = pd.DataFrame(team_rows).astype(
            {"pts": "Int64", "plus_minus": "Int64"}
        )
        return team_logs, pd.DataFrame(adv_rows), pd.DataFrame(player_rows)

    return factory
