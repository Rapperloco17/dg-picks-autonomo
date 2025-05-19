# dg_picks_mlb.py - Análisis REAL con datos vivos desde MLB Stats API y The Odds API

import requests
from datetime import datetime

ODDS_API_KEY = "tu_api_key_aqui"

# 1. Obtener partidos MLB del día desde MLB Stats API
def get_today_games():
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&date={today}"
    res = requests.get(url)
    games = res.json().get("dates", [])[0].get("games", [])
    return games

# 2. Obtener cuotas reales desde The Odds API

def get_odds_mlb():
    url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?regions=us&markets=h2h,spreads,totals&oddsFormat=decimal&apiKey={ODDS_API_KEY}"
    res = requests.get(url)
    return res.json()

# 3. Buscar cuotas por equipo

def encontrar_cuotas(game, odds):
    home = game['teams']['home']['team']['name']
    away = game['teams']['away']['team']['name']
    for odd in odds:
        if (home.lower() in odd['home_team'].lower()) and (away.lower() in odd['away_team'].lower()):
            return odd
    return None

# 4. Análisis por partido

def analizar_partido(game, odds_data):
    home = game['teams']['home']['team']['name']
    away = game['teams']['away']['team']['name']
    juego_id = game['gamePk']
    status = game['status']['detailedState']

    if status not in ["Scheduled", "Pre-Game"]:
        return None

    # Cuotas
    cuotas = encontrar_cuotas(game, odds_data)
    if not cuotas:
        return None

    resumen = [f"⚾ {home} vs {away}"]
    resumen.append(f"📍 Estado: {status}")

    # Mostrar cuotas ML y Run Line
    for m in cuotas.get("bookmakers", [])[0].get("markets", []):
        if m["key"] == "h2h":
            for o in m["outcomes"]:
                resumen.append(f"💰 ML {o['name']}: @ {o['price']}")
        if m["key"] == "spreads":
            for o in m["outcomes"]:
                resumen.append(f"📉 Spread {o['name']} {o['point']}: @ {o['price']}")
        if m["key"] == "totals":
            for o in m["outcomes"]:
                resumen.append(f"📈 Over/Under {o['point']} - {o['name']} @ {o['price']}")

    return "\n".join(resumen)

# 5. Ejecutar análisis real

def main():
    print("🟢 Análisis MLB en curso con datos REALES...")
    games = get_today_games()
    odds_data = get_odds_mlb()

    for game in games:
        analisis = analizar_partido(game, odds_data)
        if analisis:
            print("\n━━━━━━━━━━━━━━━━━━━━━━")
            print(analisis)
            print("━━━━━━━━━━━━━━━━━━━━━━")

if __name__ == "__main__":
    main()
