import requests
import os
from datetime import datetime

API_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

FECHA_HOY = datetime.today().strftime("%Y-%m-%d")

LIGAS_VALIDAS_IDS = {
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73,
    45, 78, 79, 88, 94, 103, 106, 113, 119, 128, 129, 130,
    135, 136, 137, 140, 141, 143, 144, 162, 164, 169, 172,
    179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253,
    257, 262, 263, 265, 268, 271, 281, 345, 357
}

def obtener_fixtures():
    url = f"{BASE_URL}/fixtures?date={FECHA_HOY}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print("Error al obtener fixtures")
        return []
    all_fixtures = response.json().get("response", [])
    return [fx for fx in all_fixtures if fx["league"]["id"] in LIGAS_VALIDAS_IDS]

def obtener_predicciones(fixture_id):
    url = f"{BASE_URL}/predictions?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return None
    data = response.json().get("response", [])
    return data[0] if data else None

def obtener_estadisticas_equipo(team_id, league_id):
    url = f"{BASE_URL}/teams/statistics?team={team_id}&league={league_id}&season=2024"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return None
    return response.json().get("response", {})

def obtener_h2h(team1_id, team2_id):
    url = f"{BASE_URL}/fixtures/headtohead?h2h={team1_id}-{team2_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return []
    return response.json().get("response", [])

def analizar_partido(fixture):
    fixture_id = fixture["fixture"]["id"]
    equipos = fixture["teams"]
    local = equipos["home"]
    visitante = equipos["away"]
    liga = fixture["league"]

    prediccion = obtener_predicciones(fixture_id)
    stats_local = obtener_estadisticas_equipo(local["id"], liga["id"])
    stats_visitante = obtener_estadisticas_equipo(visitante["id"], liga["id"])
    h2h = obtener_h2h(local["id"], visitante["id"])

    print(f"\n📊 {local['name']} vs {visitante['name']} ({liga['name']})")

    if prediccion:
        pred = prediccion["predictions"]
        ganador = pred.get("winner", {}).get("name", "N/D")
        btts = pred.get("both_teams_to_score", {}).get("yes", "0")
        over25 = pred.get("goals", {}).get("over_2_5", {}).get("percentage", "0")
        confianza = pred.get("winner", {}).get("comment", "")

        print(f"📈 ML: {ganador} ({confianza}) | BTTS: {btts}% | Over 2.5: {over25}%")

    if stats_local and stats_visitante:
        gf_local = stats_local["goals"]["for"]["average"].get("total", 0)
        gc_local = stats_local["goals"]["against"]["average"].get("total", 0)
        gf_visit = stats_visitante["goals"]["for"]["average"].get("total", 0)
        gc_visit = stats_visitante["goals"]["against"]["average"].get("total", 0)

        exp_local = (float(gf_local) + float(gc_visit)) / 2
        exp_visit = (float(gf_visit) + float(gc_local)) / 2
        print(f"🔢 Marcador tentativo: {round(exp_local, 1)} - {round(exp_visit, 1)}")

    if h2h:
        ultimos = h2h[:5]
        marcador_h2h = [f"{x['teams']['home']['name']} {x['goals']['home']} - {x['goals']['away']} {x['teams']['away']['name']}" for x in ultimos]
        print("📚 Últimos enfrentamientos:")
        for h in marcador_h2h:
            print("  -", h)

def main():
    print(f"\n🗓️ Análisis de partidos del día {FECHA_HOY}")
    fixtures = obtener_fixtures()
    print(f"📌 Total partidos encontrados: {len(fixtures)}")

    for partido in fixtures:
        analizar_partido(partido)

if __name__ == "__main__":
    main()
