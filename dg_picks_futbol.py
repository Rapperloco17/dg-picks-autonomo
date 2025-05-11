
from equipo_stats_dgpicks import comparar_estadisticas_equipos
import requests
import json
from datetime import datetime

API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io"
}

LIGAS_WHITELIST = { "2": 2024, "3": 2024, "9": 2024, "16": 2024, "39": 2024, "45": 2024,
  "61": 2024, "62": 2024, "71": 2024, "78": 2024, "88": 2024, "94": 2024,
  "98": 2024, "106": 2024, "113": 2024, "118": 2024, "129": 2024, "130": 2024,
  "135": 2024, "140": 2024, "144": 2024, "195": 2024, "203": 2024, "210": 2024,
  "233": 2024, "239": 2024, "245": 2024, "253": 2024, "262": 2024, "271": 2024,
  "292": 2024, "1129": 2024, "1379": 2024, "1439": 2024 }

def obtener_fixtures_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}&status=NS"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    return data.get("response", [])

def obtener_prediccion_fixture(fixture_id):
    url = f"{BASE_URL}/predictions?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    return data.get("response", [{}])[0]

def analizar_fixture(fixture):
    fixture_id = fixture["fixture"]["id"]
    liga_id = str(fixture["league"]["id"])
    home = fixture["teams"]["home"]["name"]
    away = fixture["teams"]["away"]["name"]
    home_id = fixture["teams"]["home"]["id"]
    away_id = fixture["teams"]["away"]["id"]
    print(f"\n\U0001F4C5 Partido: {home} vs {away} (Liga {liga_id})")

    # Comparar estadísticas reales por equipo
    comparar_estadisticas_equipos(home, home_id, away, away_id, liga_id)

    # El resto del análisis continúa aquí...
    return None

def main():
    print("\U0001F50D Buscando partidos del día...")
    fixtures = obtener_fixtures_hoy()
    picks = []
    for fixture in fixtures:
        pick = analizar_fixture(fixture)
        if pick:
            picks.append(pick)
    with open("output/picks_futbol.json", "w", encoding="utf-8") as f:
        json.dump(picks, f, ensure_ascii=False, indent=4)
    print("\n\U0001F3AF Análisis finalizado. Picks guardados en output/picks_futbol.json")

if __name__ == "__main__":
    main()
