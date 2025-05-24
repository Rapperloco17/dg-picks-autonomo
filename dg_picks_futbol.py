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
fixtures_with_ml = 0


def get_fixtures(date):
    url = f"{BASE_URL}/fixtures?date={date}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    return [f for f in data['response'] if f['league']['id'] in LIGAS_VALIDAS]

def get_last_fixtures(team_id):
    url = f"{BASE_URL}/fixtures?team={team_id}&last=5"
    response = requests.get(url, headers=HEADERS)
    return response.json()['response']

def calcular_forma_y_goles(partidos, condicion_localidad):
    ganados = empatados = perdidos = goles_favor = goles_contra = 0
    for match in partidos:
        if not match['teams']['home']['id'] or not match['teams']['away']['id']:
            continue
        goles_local = match['goals']['home']
        goles_visitante = match['goals']['away']
        if goles_local is None or goles_visitante is None:
            continue

        if condicion_localidad == "local":
            if match['teams']['home']['winner']:
                ganados += 1
            elif match['teams']['away']['winner']:
                perdidos += 1
            else:
                empatados += 1
            goles_favor += goles_local
            goles_contra += goles_visitante
        else:
            if match['teams']['away']['winner']:
                ganados += 1
            elif match['teams']['home']['winner']:
                perdidos += 1
            else:
                empatados += 1
            goles_favor += goles_visitante
            goles_contra += goles_local

    return {
        'ganados': ganados,
        'empatados': empatados,
        'perdidos': perdidos,
        'gf': goles_favor,
        'gc': goles_contra
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
    global fixtures_with_ml

    fixture_id = fixture['fixture']['id']
    home_id = fixture['teams']['home']['id']
    away_id = fixture['teams']['away']['id']
    home_team = fixture['teams']['home']['name']
    away_team = fixture['teams']['away']['name']
    league = fixture['league']['name']

    try:
        ultimos_home = get_last_fixtures(home_id)
        ultimos_away = get_last_fixtures(away_id)
    except:
        return

    stats_home = calcular_forma_y_goles(ultimos_home, "local")
    stats_away = calcular_forma_y_goles(ultimos_away, "visitante")

    odds_data = get_odds(fixture_id)
    for bookmaker in odds_data:
        for bk in bookmaker.get('bookmakers', []):
            for bet in bk.get('bets', []):
                if bet['name'] == "Match Winner":
                    opciones = {o['value']: float(o['odd']) for o in bet['values'] if o['value'] in ["Home", "Draw", "Away"] and CUOTA_MIN <= float(o['odd']) <= CUOTA_MAX}

                    if len(opciones) < 2:
                        continue

                    pick_generado = False
                    if "Home" in opciones and stats_home['ganados'] >= 3 and stats_away['perdidos'] >= 2:
                        fixtures_with_ml += 1
                        print(f"\n🏆 PICK ML: {home_team} vs {away_team}")
                        print(f"🎯 Pick: Home | Cuota: {opciones['Home']}")
                        picks_excel.append({
                            "Partido": f"{home_team} vs {away_team}",
                            "Liga": league,
                            "Pick": "Home",
                            "Cuota": opciones['Home'],
                            "Mercado": "Ganador ML"
                        })
                        pick_generado = True
                    elif "Away" in opciones and stats_away['ganados'] >= 3 and stats_home['perdidos'] >= 2:
                        fixtures_with_ml += 1
                        print(f"\n🏆 PICK ML: {home_team} vs {away_team}")
                        print(f"🎯 Pick: Away | Cuota: {opciones['Away']}")
                        picks_excel.append({
                            "Partido": f"{home_team} vs {away_team}",
                            "Liga": league,
                            "Pick": "Away",
                            "Cuota": opciones['Away'],
                            "Mercado": "Ganador ML"
                        })
                        pick_generado = True
                    elif "Draw" in opciones:
                        if stats_home['empatados'] >= 2 and stats_away['empatados'] >= 2:
                            if stats_home['ganados'] <= 2 and stats_away['ganados'] <= 2:
                                if abs(stats_home['gf'] - stats_away['gf']) <= 1:
                                    fixtures_with_ml += 1
                                    print(f"\n🏆 PICK ML: {home_team} vs {away_team}")
                                    print(f"🎯 Pick: Draw | Cuota: {opciones['Draw']}")
                                    picks_excel.append({
                                        "Partido": f"{home_team} vs {away_team}",
                                        "Liga": league,
                                        "Pick": "Draw",
                                        "Cuota": opciones['Draw'],
                                        "Mercado": "Ganador ML"
                                    })
                                    pick_generado = True
                    if pick_generado:
                        return

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
    print(f"🏆 Partidos con Pick ML filtrado: {fixtures_with_ml}")

    if picks_excel:
        df = pd.DataFrame(picks_excel)
        df.to_excel("/mnt/data/picks_ml_filtrados.xlsx", index=False)
        print("\n✅ Archivo Excel generado: picks_ml_filtrados.xlsx")
    else:
        print("\n❌ No se detectaron picks ML con lógica para exportar.")

if __name__ == "__main__":
    main()
