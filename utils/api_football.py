import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
API_FOOTBALL_HOST = "https://v3.football.api-sports.io"

headers = {
    "x-apisports-key": API_FOOTBALL_KEY
}

def obtener_partidos_de_liga(liga_id, fecha, temporada):
    """
    Consulta los partidos de una liga para una fecha específica usando API-FOOTBALL
    """
    url = f"{API_FOOTBALL_HOST}/fixtures"
    params = {
        "league": liga_id,
        "season": temporada,
        "date": fecha,
        "timezone": "America/Mexico_City"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if data["response"]:
            partidos = []
            for fixture in data["response"]:
                partidos.append({
                    "fixture": fixture["fixture"],
                    "teams": fixture["teams"],
                    "league": fixture["league"]
                })
            return partidos
        else:
            print(f"No se encontraron partidos para liga {liga_id} en {fecha}")
            return []

    except Exception as e:
        print(f"Error al obtener partidos de la liga {liga_id} en {fecha}: {str(e)}")
        return []

