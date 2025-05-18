import requests
import os
from datetime import datetime

API_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

FECHA_HOY = datetime.today().strftime("%Y-%m-%d")

LIGAS_VALIDAS_IDS = {
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 45, 61, 62, 71, 72, 73, 78, 79, 88, 94,
    103, 106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144,
    162, 164, 169, 172, 179, 188, 197, 203, 207, 210, 218, 239, 242, 244,
    253, 257, 262, 263, 265, 268, 271, 281, 345, 357
}

def obtener_fixtures():
    url = f"{BASE_URL}/fixtures?date={FECHA_HOY}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    return data.get("response", [])

def obtener_estadisticas_equipo(team_id, league_id):
    url = f"{BASE_URL}/teams/statistics?team={team_id}&league={league_id}&season=2024"
    response = requests.get(url, headers=HEADERS)
    return response.json().get("response", {})

def obtener_enfrentamientos(local_id, visitante_id):
    url = f"{BASE_URL}/fixtures/headtohead?h2h={local_id}-{visitante_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json().get("response", [])

def obtener_prediccion(fixture_id):
    url = f"{BASE_URL}/predictions?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json().get("response", [])

def analizar_partido(partido):
    fixture_id = partido["fixture"]["id"]
    league_id = partido["league"]["id"]
    local = partido["teams"]["home"]
    visitante = partido["teams"]["away"]

    if league_id not in LIGAS_VALIDAS_IDS:
        return

    stats_local = obtener_estadisticas_equipo(local["id"], league_id)
    stats_visitante = obtener_estadisticas_equipo(visitante["id"], league_id)

    gf_local = stats_local.get("goals", {}).get("for", {}).get("average", {}).get("home", 0)
    gf_visitante = stats_visitante.get("goals", {}).get("for", {}).get("average", {}).get("away", 0)
    marcador_tentativo = f"{gf_local:.1f} - {gf_visitante:.1f}"

    print(f"\n\U0001F4C5 {local['name']} vs {visitante['name']} ({partido['league']['name']})")

    prediccion = obtener_prediccion(fixture_id)
    pred = prediccion[0].get("predictions", {}) if prediccion else {}
    winner = pred.get("winner", {}).get("name", "-")
    win_or_draw = pred.get("win_or_draw", False)
    btts = pred.get("both_teams_to_score", {}).get("yes", "0%")
    over25 = pred.get("goals", {}).get("over_2_5", {}).get("percentage", "0%")

    print(f"\U0001F3AF ML: {winner} {'(Win or draw)' if win_or_draw else ''} | BTTS: {btts} | Over 2.5: {over25}")
    print(f"\U0001F4A1 Marcador tentativo: {marcador_tentativo}")

    h2h = obtener_enfrentamientos(local["id"], visitante["id"])
    print("\U0001F4CA \u00daltimos enfrentamientos:")
    for partido in h2h[:5]:
        g1 = partido["goals"]["home"]
        g2 = partido["goals"]["away"]
        equipo1 = partido["teams"]["home"]["name"]
        equipo2 = partido["teams"]["away"]["name"]
        print(f"- {equipo1} {g1} - {g2} {equipo2}")

def main():
    print(f"\n\U0001F4C6 Análisis de partidos del día {FECHA_HOY}")
    fixtures = obtener_fixtures()
    print(f"\U0001F4CC Total partidos encontrados: {len([f for f in fixtures if f['league']['id'] in LIGAS_VALIDAS_IDS])}")
    for partido in fixtures:
        analizar_partido(partido)

if __name__ == "__main__":
    main()
