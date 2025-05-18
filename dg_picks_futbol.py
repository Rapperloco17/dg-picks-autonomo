import requests
import os
from datetime import datetime

API_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"
FECHA_HOY = datetime.today().strftime("%Y-%m-%d")

# IDs de ligas filtradas
LIGAS_VALIDAS_IDS = [
    2, 3, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88, 94, 103,
    106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162, 164,
    169, 172, 179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253, 257,
    262, 263, 265, 268, 271, 281, 345, 357
]

def obtener_fixtures():
    url = f"{BASE_URL}/fixtures?date={FECHA_HOY}"
    res = requests.get(url, headers=HEADERS)
    data = res.json().get("response", [])
    return [f for f in data if f["league"]["id"] in LIGAS_VALIDAS_IDS]

def obtener_forma(team_id, league_id):
    url = f"{BASE_URL}/teams/statistics?team={team_id}&league={league_id}&season=2024"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        return None
    return res.json().get("response", {})

def procesar_fixture(fix):
    home = fix["teams"]["home"]["name"]
    away = fix["teams"]["away"]["name"]
    league = fix["league"]["name"]
    lid = fix["league"]["id"]
    hid = fix["teams"]["home"]["id"]
    aid = fix["teams"]["away"]["id"]

    stats_home = obtener_forma(hid, lid)
    stats_away = obtener_forma(aid, lid)
    if not stats_home or not stats_away:
        return

    gf_home = stats_home.get("goals", {}).get("for", {}).get("average", {}).get("total", 0)
    gf_away = stats_away.get("goals", {}).get("for", {}).get("average", {}).get("total", 0)
    gc_home = stats_home.get("goals", {}).get("against", {}).get("average", {}).get("total", 0)
    gc_away = stats_away.get("goals", {}).get("against", {}).get("average", {}).get("total", 0)

    try:
        gf1 = (float(gf_home) + float(gc_away)) / 2
        gf2 = (float(gf_away) + float(gc_home)) / 2
    except:
        gf1 = gf2 = 0

    marcador = f"{round(gf1)} - {round(gf2)}"
    print(f"\n{home} vs {away} ({league})")
    print(f"\U0001F4CA ML: -- | BTTS: -- | Over 2.5: --")
    print(f"\U0001F4A1 Marcador tentativo: {marcador}")

    # Lógica de pick
    recomendaciones = []
    if round(gf1) > round(gf2):
        recomendaciones.append("Gana Local")
    elif round(gf2) > round(gf1):
        recomendaciones.append("Gana Visitante")
    else:
        recomendaciones.append("Empate Probable")

    if gf1 + gf2 >= 2.8:
        recomendaciones.append("Over 2.5")
    elif gf1 + gf2 <= 2.0:
        recomendaciones.append("Under 2.5")

    if gf1 >= 1 and gf2 >= 1:
        recomendaciones.append("BTTS (Ambos anotan)")

    print(f"\U0001F4DD Recomendaciones: {', '.join(recomendaciones)}")

def main():
    print(f"\n🌟 Análisis de partidos del día {FECHA_HOY}")
    fixtures = obtener_fixtures()
    print(f"\u2728 Total partidos encontrados: {len(fixtures)}")
    for f in fixtures:
        procesar_fixture(f)

if __name__ == "__main__":
    main()
