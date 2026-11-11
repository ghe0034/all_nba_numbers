import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from curl_cffi import requests
from nba_ingest.client import fetch_endpoint
from nba_ingest.catalog import EndpointDefinition

def run_test():
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

    print("Iniciando sesión con TLS Fingerprint de Chrome...")
    session = requests.Session()

    print("Lanzando petición HTTP a stats.nba.com...")
    try:
        respuesta_bytes = fetch_endpoint(
            endpoint=endpoint,
            season="2023-24",
            session=session
        )
        
        print("\n✅ ¡ÉXITO! Conexión establecida (200 OK).")
        json_data = json.loads(respuesta_bytes)
        
        print("\nRespuesta de la NBA (primeros 300 caracteres):")
        print("-" * 50)
        print(str(json_data)[:300] + "...")
        print("-" * 50)
        
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {e}")

if __name__ == "__main__":
    run_test()