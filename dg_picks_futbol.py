
import requests
import json
from datetime import datetime

# === CONFIGURACIÓN API ===
API_KEY = "178b66e41ba9d4d3b8549f096ef1e377"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io"
}

# === LIGAS PERMITIDAS ===
LIGAS_WHITELIST = { "2": 2024, "3": 2024, "9": 2024, "16": 2024, "39": 2024, "45": 2024,
  "61": 2024, "62": 2024, "71": 2024, "78": 2024, "88": 2024, "94": 2024,
  "98": 2024, "106": 2024, "113": 2024, "118": 2024, "129": 2024, "130": 2024,
  "135": 2024, "140": 2024, "144": 2024, "195": 2024, "203": 2024, "210": 2024,
  "233": 2024, "239": 2024, "245": 2024, "253": 2024, "262": 2024, "271": 2024,
  "292": 2024, "1129": 2024, "1379": 2024, "1439": 2024 }

# === FUNCIONES ===

def obtener_estadisticas_equipo(team_id, league_id, season=2024):
    url = f"{BASE_URL}/teams/statistics?team={team_id}&league={league_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return None
    data = response.json().get("response", {})
    return data

def comparar_estadisticas_equipos(home_name, home_id, away_name, away_id, league_id, season=2024):
    stats_home = obtener_estadisticas_equipo(home_id, league_id, season)
    stats_away = obtener_estadisticas_equipo(away_id, league_id, season)

    if not stats_home or not stats_away:
        print("\n❌ No se pudieron obtener estadísticas de ambos equipos.")
        return

    print(f"\n🤜 Comparativa {home_name} vs {away_name}")
    print(f"Goles promedio: {home_name} local {stats_home['goals']['average'].get('home')} | {away_name} visita {stats_away['goals']['average'].get('away')}")
    print(f"Tiros al arco: {home_name} {stats_home.get('shots')} | {away_name} {stats_away.get('shots')}")
    print(f"Clean sheets: {home_name} {stats_home.get('clean_sheet')} | {away_name} {stats_away.get('clean_sheet')}")
    print(f"Fallas al anotar: {home_name} {stats_home.get('failed_to_score')} | {away_name} {stats_away.get('failed_to_score')}")
    print(f"Tarjetas: {home_name} {stats_home.get('cards')} | {away_name} {stats_away.get('cards')}")
    print(f"Posesión: {home_name} {stats_home.get('biggest', {}).get('ball_possession')} | {away_name} {stats_away.get('biggest', {}).get('ball_possession')}")

def obtener_fixtures_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={hoy}&status=NS"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    return data.get("response", [])

def analizar_fixture(fixture):
    fixture_id = fixture["fixture"]["id"]
    liga_id = str(fixture["league"]["id"])
    home = fixture["teams"]["home"]["name"]
    away = fixture["teams"]["away"]["name"]
    home_id = fixture["teams"]["home"]["id"]
    away_id = fixture["teams"]["away"]["id"]
    print(f"\n📅 Partido: {home} vs {away} (Liga {liga_id})")

    if liga_id not in LIGAS_WHITELIST:
        print("❌ Liga no permitida.")
        return None

    comparar_estadisticas_equipos(home, home_id, away, away_id, liga_id)

    return None

def main():
    print("🔍 Buscando partidos del día...")
    fixtures = obtener_fixtures_hoy()
    picks = []
    for fixture in fixtures:
        pick = analizar_fixture(fixture)
        if pick:
            picks.append(pick)
    with open("output/picks_futbol.json", "w", encoding="utf-8") as f:
        json.dump(picks, f, ensure_ascii=False, indent=4)
    print("\n🎯 Análisis finalizado. Picks guardados en output/picks_futbol.json")

if __name__ == "__main__":
    main()
