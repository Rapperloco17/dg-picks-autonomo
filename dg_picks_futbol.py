import requests
import datetime
import os
import pandas as pd

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

LIGAS_VALIDAS = [
    1, 2, 3, 4, 9, 11, 13, 16, 39, 40, 61, 62, 71, 72, 73, 45, 78, 79, 88, 94,
    103, 106, 113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162,
    164, 169, 172, 179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253, 257,
    262, 263, 265, 268, 271, 281, 345, 357
]

CUOTA_MIN = 1.50
CUOTA_MAX = 3.25

hoy = datetime.datetime.now().strftime("%Y-%m-%d")
picks_excel = []
total_fixtures = 0
fixtures_with_odds = 0
fixtures_with_overunder = 0
fixtures_with_btts = 0
fixtures_with_dobleo = 0
fixtures_with_ml = 0


def get_fixtures(date):
    url = f"{BASE_URL}/fixtures?date={date}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    return [f for f in data['response'] if f['league']['id'] in LIGAS_VALIDAS]

def get_odds(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()['response']
    if data:
        global fixtures_with_odds
        fixtures_with_odds += 1
    return data

def analizar_partido(fixture):
    global fixtures_with_overunder, fixtures_with_btts, fixtures_with_dobleo, fixtures_with_ml

    fixture_id = fixture['fixture']['id']
    home_team = fixture['teams']['home']['name']
    away_team = fixture['teams']['away']['name']
    league = fixture['league']['name']

    odds_data = get_odds(fixture_id)
    for bookmaker in odds_data:
        for bk in bookmaker.get('bookmakers', []):
            for bet in bk.get('bets', []):
                if bet['name'] == "Over/Under":
                    fixtures_with_overunder += 1
                elif bet['name'] == "Both Teams To Score":
                    fixtures_with_btts += 1
                elif bet['name'] == "Double Chance":
                    fixtures_with_dobleo += 1
                elif bet['name'] == "Match Winner":
                    fixtures_with_ml += 1


def main():
    global total_fixtures
    fixtures = get_fixtures(hoy)
    total_fixtures = len(fixtures)
    print(f"Partidos encontrados: {total_fixtures}")
    for fixture in fixtures:
        print(f"Analizando: {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']} ({fixture['league']['name']})")
        analizar_partido(fixture)

    print("\nResumen de cobertura de cuotas:")
    print(f"🧩 Partidos totales analizados: {total_fixtures}")
    print(f"📊 Partidos con cuotas disponibles: {fixtures_with_odds}")
    print(f"🎯 Partidos con mercado Over/Under: {fixtures_with_overunder}")
    print(f"🤝 Partidos con mercado Ambos Anotan: {fixtures_with_btts}")
    print(f"🔐 Partidos con Doble Oportunidad: {fixtures_with_dobleo}")
    print(f"🏆 Partidos con Ganador ML: {fixtures_with_ml}")

    if picks_excel:
        df = pd.DataFrame(picks_excel)
        df.to_excel("/mnt/data/picks_over_under.xlsx", index=False)
        print("\n✅ Archivo Excel generado: picks_over_under.xlsx")
    else:
        print("\n❌ No se detectaron picks con cuota para exportar.")

if __name__ == "__main__":
    main()
