import requests
import json
from datetime import datetime

API_URL = "https://v3.football.api-sports.io"
API_KEY = "71786cde41a9ad043bde3849f906ef1377"  # Tu API Key válida

headers = {
    "x-apisports-key": API_KEY
}

# Leer ligas válidas desde JSON externo
with open("utils/leagues_whitelist_ids.json") as f:
    ligas_validas = json.load(f)

# Leer temporadas por liga desde JSON
with open("utils/league_seasons.json") as f:
    temporadas_por_liga = json.load(f)

# Fecha actual en formato 'YYYY-MM-DD'
fecha_hoy = datetime.now().strftime("%Y-%m-%d")

def obtener_partidos_de_liga(liga_id, fecha):
    temporada = temporadas_por_liga.get(str(liga_id), 2025)  # Por defecto 2025 si no se encuentra
    params = {
        "league": liga_id,
        "season": temporada,
        "date": fecha
    }
    try:
        response = requests.get(f"{API_URL}/fixtures", headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al conectar con la API para liga {liga_id}: {e}")
        return {"response": []}

def get_team_statistics(fixture_id):
    """
    Obtiene estadísticas detalladas de los equipos en un fixture.
    """
    try:
        response = requests.get(f"{API_URL}/fixtures/statistics?fixture={fixture_id}", headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get("response", [])
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al obtener estadísticas del fixture {fixture_id}: {e}")
        return []

def get_predictions(fixture_id):
    """
    Obtiene predicciones del sistema de API-FOOTBALL para el fixture.
    """
    try:
        response = requests.get(f"{API_URL}/predictions?fixture={fixture_id}", headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json().get("response")
        return data[0] if data else None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al obtener predicción del fixture {fixture_id}: {e}")
        return None

