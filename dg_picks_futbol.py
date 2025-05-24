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


def get_fixtures(date):
    url = f"{BASE_URL}/fixtures?date={date}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    return [f for f in data['response'] if f['league']['id'] in LIGAS_VALIDAS]

def get_team_stats(team_id, league_id):
    url = f"{BASE_URL}/teams/statistics?team={team_id}&league={league_id}&season=2024"
    response = requests.get(url, headers=HEADERS)
    return response.json()['response']

def get_last_fixtures(team_id, league_id):
    url = f"{BASE_URL}/fixtures?team={team_id}&league={league_id}&season=2024&last=5"
    response = requests.get(url, headers=HEADERS)
    return response.json()['response']

def calcular_over_25_porcentaje(ultimos_partidos):
    count = 0
    btts_count = 0
    total_validos = 0
    for match in ultimos_partidos:
        home_goals = match['goals']['home']
        away_goals = match['goals']['away']
        if home_goals is not None and away_goals is not None:
            total_validos += 1
            goles = home_goals + away_goals
            if goles > 2.5:
                count += 1
            if home_goals > 0 and away_goals > 0:
                btts_count += 1
    return {
        'over_25_pct': (count / total_validos) * 100 if total_validos else 0,
        'btts_pct': (btts_count / total_validos) * 100 if total_validos else 0
    }

def get_odds(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()['response']
    if data:
        global fixtures_with_odds
        fixtures_with_odds += 1
    return data

def analizar_partido(fixture):
    global fixtures_with_overunder, fixtures_with_btts
    home_id = fixture['teams']['home']['id']
    away_id = fixture['teams']['away']['id']
    league_id = fixture['league']['id']
    fixture_id = fixture['fixture']['id']

    try:
        stats_home = get_team_stats(home_id, league_id)
        stats_away = get_team_stats(away_id, league_id)
        ultimos_home = get_last_fixtures(home_id, league_id)
        ultimos_away = get_last_fixtures(away_id, league_id)
    except:
        return None

    avg_goals_home = float(stats_home['goals']['for']['average']['total'])
    avg_goals_away = float(stats_away['goals']['for']['average']['total'])
    total_avg_goals = avg_goals_home + avg_goals_away

    stats_form_home = calcular_over_25_porcentaje(ultimos_home)
    stats_form_away = calcular_over_25_porcentaje(ultimos_away)

    pred_home_goals = round(avg_goals_home, 1)
    pred_away_goals = round(avg_goals_away, 1)
    marcador_tentativo = f"{pred_home_goals} - {pred_away_goals}"
    btts_prob = round((stats_form_home['btts_pct'] + stats_form_away['btts_pct']) / 2, 1)

    odds_data = get_odds(fixture_id)
    for bookmaker in odds_data:
        for bk in bookmaker.get('bookmakers', []):
            for bet in bk.get('bets', []):
                if bet['name'] == "Over/Under":
                    fixtures_with_overunder += 1
                if bet['name'] == "Both Teams To Score":
                    fixtures_with_btts += 1


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

    if picks_excel:
        df = pd.DataFrame(picks_excel)
        df.to_excel("/mnt/data/picks_over_under.xlsx", index=False)
        print("\n✅ Archivo Excel generado: picks_over_under.xlsx")
    else:
        print("\n❌ No se detectaron picks con cuota para exportar.")

if __name__ == "__main__":
    main()
