
import requests
import os
from datetime import datetime, timedelta
import pytz

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# Lista de ligas válidas (integrada)
LIGAS_VALIDAS = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88, 94,
    103, 106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162,
    164, 169, 172, 179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253, 257,
    262, 263, 265, 268, 271, 281, 345, 357
]

def obtener_partidos_hoy():
    hoy = datetime.now(pytz.timezone("America/Mexico_City")).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    partidos_validos = []
    for fixture in data.get("response", []):
        liga_id = fixture["league"]["id"]
        if liga_id in LIGAS_VALIDAS:
            partidos_validos.append({
                "liga": fixture["league"]["name"],
                "local": fixture["teams"]["home"]["name"],
                "visitante": fixture["teams"]["away"]["name"],
                "hora": fixture["fixture"]["date"],
                "id_fixture": fixture["fixture"]["id"]
            })

    return partidos_validos

if __name__ == "__main__":
    partidos = obtener_partidos_hoy()
    for p in partidos:
        print(f'{p["liga"]}: {p["local"]} vs {p["visitante"]} — {p["hora"]}')
