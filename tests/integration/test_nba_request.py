import json
import sys
from pathlib import Path

import pytest
from curl_cffi import requests

from nba_ingest.catalog import EndpointDefinition
from nba_ingest.client import fetch_endpoint

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.mark.integration
def test_nba_live_connection():
    endpoint = EndpointDefinition(
        id="leaguegamelog",
        url="https://stats.nba.com/stats/leaguegamelog",
        season_param_name="Season",
        fixed_params={
            "PlayerOrTeam": "P",
            "Direction": "DESC",
            "LeagueID": "00",
            "Sorter": "PTS",
            "SeasonType": "Regular Season"
        }
    )
    session = requests.Session()
    
    respuesta_bytes = fetch_endpoint(
        endpoint=endpoint,
        season="2023-24",
        session=session
    )
    
    json_data = json.loads(respuesta_bytes)
    
    assert json_data["resource"] == "leaguegamelog"
    assert "resultSets" in json_data
    assert len(json_data["resultSets"]) > 0
    assert len(json_data["resultSets"][0]["rowSet"]) > 0