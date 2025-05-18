import requests
import os
import time
from datetime import datetime

API_KEY = os.getenv("API_FOOTBALL_KEY")

# IDs de ligas filtradas (ligas válidas según imagen)
LIGAS_VALIDAS = [
    2, 3, 11, 13, 16, 39, 40, 45, 61, 62, 71, 72, 73, 78, 79, 88, 94, 103, 106,
    113, 119, 128, 129, 130, 135, 136, 137, 140, 141, 143, 144, 162, 164, 169,
    172, 179, 188, 197, 203, 207, 210, 218, 239, 242, 244, 253, 257, 262, 263,
    265, 268, 271, 281, 345, 357
]

hoy = datetime.now().strftime("%Y-%m-%d")
print("\U0001f52d Análisis de partidos del día", hoy)

# Obtener partidos del día
def obtener_fixtures():
    url = f"https://v3.football.api-sports.io/fixtures?date={hoy}"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    r = requests.get(url, headers=headers)
    data = r.json()
    fixtures = data.get("response", [])
    return fixtures

# Validar si liga está permitida
def es_liga_valida(league_id):
    return league_id in LIGAS_VALIDAS

# Obtener estadísticas de goles para predicción de marcador
def get_team_stats(team_id, league_id):
    url = f"https://v3.football.api-sports.io/teams/statistics?team={team_id}&league={league_id}&season=2024"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    r = requests.get(url, headers=headers)
    return r.json().get("response", {})

# Obtener cuotas del partido
def get_odds(fixture_id):
    url = f"https://v3.football.api-sports.io/odds?fixture={fixture_id}"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    r = requests.get(url, headers=headers)
    data = r.json().get("response", [])
    if not data:
        return "Cuotas ML: -- | Over 2.5: -- | BTTS Sí: --"

    apuestas = data[0].get("bookmakers", [])
    for casa in apuestas:
        for bet in casa.get("bets", []):
            if bet["name"] == "Match Winner":
                odds_ml = {o['value']: o['odd'] for o in bet['values']}
            if bet["name"] == "Over/Under":
                over_25 = next((o['odd'] for o in bet['values'] if o['value'] == 'Over 2.5'), "--")
            if bet["name"] == "Both Teams To Score":
                btts_yes = next((o['odd'] for o in bet['values'] if o['value'] == 'Yes'), "--")
        break

    return f"Cuotas ML: Local {odds_ml.get('Home', '--')}, Empate {odds_ml.get('Draw', '--')}, Visitante {odds_ml.get('Away', '--')} | Over 2.5: {over_25} | BTTS Sí: {btts_yes}"

# Análisis partido por partido
def analizar_partido(f):
    league_id = f['league']['id']
    if not es_liga_valida(league_id):
        return

    fixture_id = f['fixture']['id']
    local = f['teams']['home']['name']
    visitante = f['teams']['away']['name']
    id_local = f['teams']['home']['id']
    id_visitante = f['teams']['away']['id']

    print(f"\n{local} vs {visitante} ({f['league']['name']})")

    stats_local = get_team_stats(id_local, league_id)
    stats_visita = get_team_stats(id_visitante, league_id)

    gfl = stats_local.get("goals", {}).get("for", {}).get("average", {}).get("total", "0")
    gcl = stats_local.get("goals", {}).get("against", {}).get("average", {}).get("total", "0")
    gfv = stats_visita.get("goals", {}).get("for", {}).get("average", {}).get("total", "0")
    gcv = stats_visita.get("goals", {}).get("against", {}).get("average", {}).get("total", "0")

    try:
        marcador_local = round((float(gfl) + float(gcv)) / 2)
        marcador_visita = round((float(gfv) + float(gcl)) / 2)
        print(f"\U0001f4ca Marcador tentativo: {marcador_local} - {marcador_visita}")
    except:
        print("\U0001f4ca Marcador tentativo: No disponible")

    print("\U0001f4b8", get_odds(fixture_id))

# Ejecutar flujo principal
fixtures = obtener_fixtures()
print(f"\U0001f4cc Total partidos encontrados: {len(fixtures)}")
for f in fixtures:
    try:
        analizar_partido(f)
        time.sleep(1.2)
    except Exception as e:
        print("Error:", e)

