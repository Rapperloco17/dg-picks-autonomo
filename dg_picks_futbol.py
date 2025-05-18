
import requests
from datetime import datetime

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

FECHA_HOY = datetime.today().strftime("%Y-%m-%d")

UMBRAL_GOLES = 65
UMBRAL_BTTS = 60
UMBRAL_CORNERS = 9
UMBRAL_TARJETAS = 4

LIGAS_VALIDAS_IDS = {
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73,
    45, 78, 79, 88, 94, 103, 106, 113, 119, 128, 129, 130,
    135, 136, 137, 140, 141, 143, 144, 162, 164, 169, 172,
    179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253,
    257, 262, 263, 265, 268, 271, 281, 345, 357
}

def obtener_fixtures_del_dia():
    url = f"{BASE_URL}/fixtures?date={FECHA_HOY}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    partidos = []
    total_partidos = 0
    total_filtrados = 0

    for item in data.get("response", []):
        total_partidos += 1
        liga_id = item["league"]["id"]
        if liga_id not in LIGAS_VALIDAS_IDS:
            continue
        total_filtrados += 1
        partidos.append({
            "fixture_id": item["fixture"]["id"],
            "liga": item["league"]["name"],
            "liga_id": liga_id,
            "local": item["teams"]["home"]["name"],
            "visitante": item["teams"]["away"]["name"],
            "local_id": item["teams"]["home"]["id"],
            "visitante_id": item["teams"]["away"]["id"],
            "hora": item["fixture"]["date"]
        })

    print(f"\n📊 Total partidos recibidos: {total_partidos}")
    print(f"✅ Partidos en ligas válidas: {total_filtrados}")

    return partidos
