import requests
import datetime
import os

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
CUOTA_MAX = 2.50

hoy = datetime.datetime.now().strftime("%Y-%m-%d")

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
    for match in ultimos_partidos:
        goles = match['goals']['home'] + match['goals']['away']
        if goles > 2.5:
            count += 1
        if match['goals']['home'] > 0 and match['goals']['away'] > 0:
            btts_count += 1
    total = len(ultimos_partidos)
    return {
        'over_25_pct': (count / total) * 100 if total else 0,
        'btts_pct': (btts_count / total) * 100 if total else 0
    }

def get_odds(fixture_id):
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    for bookmaker in response.json()['response']:
        for bk in bookmaker.get('bookmakers', []):
            for bet in bk.get('bets', []):
                if bet['name'] == "Over/Under":
                    for option in bet['values']:
                        if option['value'] in ["Over 1.5", "Over 2.5", "Under 2.5", "Under 3.5"]:
                            yield option['value'], float(option['odd'])

def analizar_partido(fixture):
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

    picks = []
    for market, cuota in get_odds(fixture_id):
        if CUOTA_MIN <= cuota <= CUOTA_MAX:
            if "Over 2.5" in market and total_avg_goals > 2.6 and \
               stats_form_home['over_25_pct'] >= 60 and stats_form_away['over_25_pct'] >= 60:
                picks.append((market, cuota, total_avg_goals, stats_form_home['over_25_pct'], 
                              stats_form_away['over_25_pct'], marcador_tentativo, btts_prob))
            elif "Under 2.5" in market and total_avg_goals < 2.2 and \
                 stats_form_home['over_25_pct'] <= 40 and stats_form_away['over_25_pct'] <= 40:
                picks.append((market, cuota, total_avg_goals, stats_form_home['over_25_pct'], 
                              stats_form_away['over_25_pct'], marcador_tentativo, btts_prob))

    return picks

def main():
    fixtures = get_fixtures(hoy)
    print(f"Partidos encontrados: {len(fixtures)}")
    for fixture in fixtures:
        resultado = analizar_partido(fixture)
        if resultado:
            for pick in resultado:
                print("\n====================================")
                print(f"{fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
                print(f"Liga: {fixture['league']['name']}")
                print(f"Pick sugerido: {pick[0]} | Cuota: {pick[1]} | Prom. goles: {pick[2]:.2f}")
                print(f"Over 2.5 últimos 5 partidos: Local {pick[3]:.0f}% | Visitante {pick[4]:.0f}%")
                print(f"Marcador tentativo: {pick[5]} | BTTS Prob: {pick[6]}%")

if __name__ == "__main__":
    main()
