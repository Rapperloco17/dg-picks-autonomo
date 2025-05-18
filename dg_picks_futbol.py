import requests
import os
from datetime import datetime

API_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"
FECHA_HOY = datetime.today().strftime("%Y-%m-%d")

LIGAS_VALIDAS_IDS = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88, 94, 103, 106,
    113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162, 164, 169, 172, 179,
    188, 197, 203, 207, 210, 218, 239, 242, 244, 253, 257, 262, 263, 265, 268, 271, 281,
    345, 357
]

def obtener_fixtures_del_dia():
    url = f"{BASE_URL}/fixtures?date={FECHA_HOY}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    return [f for f in data.get("response", []) if f["league"]["id"] in LIGAS_VALIDAS_IDS]

def obtener_datos_fixture(fixture_id):
    stats_url = f"{BASE_URL}/fixtures/statistics?fixture={fixture_id}"
    h2h_url = f"{BASE_URL}/fixtures/headtohead?h2h={fixture_id}"
    pred_url = f"{BASE_URL}/predictions?fixture={fixture_id}"
    odds_url = f"{BASE_URL}/odds?fixture={fixture_id}"

    stats = requests.get(stats_url, headers=HEADERS).json()
    h2h = requests.get(h2h_url, headers=HEADERS).json()
    pred = requests.get(pred_url, headers=HEADERS).json()
    odds = requests.get(odds_url, headers=HEADERS).json()

    return stats, h2h, pred, odds

def obtener_cuotas_recomendadas(data):
    cuotas = {}
    for bookmaker in data.get("response", [{}])[0].get("bookmakers", []):
        for bet in bookmaker.get("bets", []):
            if bet["name"] == "Match Winner":
                for val in bet.get("values", []):
                    if val["value"] == "Home":
                        cuotas["local"] = val["odd"]
                    elif val["value"] == "Draw":
                        cuotas["empate"] = val["odd"]
                    elif val["value"] == "Away":
                        cuotas["visitante"] = val["odd"]
            elif bet["name"] == "Over/Under 2.5 goals":
                for val in bet.get("values", []):
                    if val["value"] == "Over 2.5":
                        cuotas["over_2.5"] = val["odd"]
                    elif val["value"] == "Under 2.5":
                        cuotas["under_2.5"] = val["odd"]
            elif bet["name"] == "Both Teams To Score":
                for val in bet.get("values", []):
                    if val["value"] == "Yes":
                        cuotas["btts"] = val["odd"]
    return cuotas

def main():
    fixtures = obtener_fixtures_del_dia()
    print(f"\U0001f4c5 Análisis de partidos del día {FECHA_HOY}")
    print(f"\U0001f4cc Total partidos encontrados: {len(fixtures)}")

    for f in fixtures:
        fixture_id = f["fixture"]["id"]
        teams = f["teams"]
        league = f["league"]
        print(f"\n{teams['home']['name']} vs {teams['away']['name']} ({league['name']})")

        stats, h2h, pred, odds = obtener_datos_fixture(fixture_id)
        cuotas = obtener_cuotas_recomendadas(odds)

        print(f"\U0001f4ca ML: -- | BTTS: -- | Over 2.5: --")
        print(f"\U0001f4ab Cuotas ML: Local {cuotas.get('local', '-')}, Empate {cuotas.get('empate', '-')}, Visitante {cuotas.get('visitante', '-')} | Over 2.5: {cuotas.get('over_2.5', '-')} | BTTS Sí: {cuotas.get('btts', '-')}\n")

if __name__ == "__main__":
    main()
