# dg_picks_mlb.py

import requests
from datetime import datetime
import pytz
import time

# === CONFIGURACIONES ===
ODDS_API_KEY = "137992569bc2352366c01e6928577b2d"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"
HEADERS = {"User-Agent": "DG Picks"}

# Zona horaria México para partidos del día
MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")


def get_today_mlb_games():
    """Consulta los partidos de MLB programados para hoy desde MLB Stats API."""
    params = {
        "sportId": 1,
        "date": HOY,
        "hydrate": "team,linescore,probablePitcher"
    }
    response = requests.get(MLB_STATS_BASE_URL, headers=HEADERS, params=params)
    data = response.json()
    games = []

    for date_info in data.get("dates", []):
        for game in date_info.get("games", []):
            games.append({
                "gamePk": game["gamePk"],
                "home_team": game["teams"]["home"]["team"]["name"],
                "away_team": game["teams"]["away"]["team"]["name"],
                "home_pitcher": game["teams"]["home"].get("probablePitcher", {}).get("fullName", "No confirmado"),
                "away_pitcher": game["teams"]["away"].get("probablePitcher", {}).get("fullName", "No confirmado"),
                "start_time": game.get("gameDate")
            })
    return games


def get_odds_for_mlb():
    """Obtiene cuotas para partidos MLB del día desde The Odds API."""
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h,totals",
        "oddsFormat": "decimal"
    }
    response = requests.get(ODDS_API_URL, headers=HEADERS, params=params)
    if response.status_code != 200:
        print("Error al obtener cuotas:", response.text)
        return []
    return response.json()


def emparejar_partidos(games, odds):
    """Une los partidos obtenidos de MLB Stats API con sus cuotas desde The Odds API."""
    partidos = []
    for game in games:
        for odd in odds:
            if (game['home_team'].lower() in odd['home_team'].lower() or odd['home_team'].lower() in game['home_team'].lower()) and \
               (game['away_team'].lower() in odd['away_team'].lower() or odd['away_team'].lower() in game['away_team'].lower()):

                cuota_ml = odd.get("bookmakers", [])[0].get("markets", [])[0].get("outcomes", [])
                cuotas_dict = {o['name']: o['price'] for o in cuota_ml}

                total_market = next((m for m in odd.get("bookmakers", [])[0].get("markets", []) if m['key'] == 'totals'), None)
                over_under = total_market['outcomes'][0] if total_market else {}

                partidos.append({
                    "enfrentamiento": f"{game['away_team']} vs {game['home_team']}",
                    "pitchers": f"{game['away_pitcher']} vs {game['home_pitcher']}",
                    "inicio": game['start_time'],
                    "cuotas": cuotas_dict,
                    "total": over_under
                })
                break
    return partidos


def main():
    print("⏳ Obteniendo partidos de MLB para hoy...")
    games = get_today_mlb_games()
    print(f"✅ {len(games)} partidos encontrados.")

    print("⏳ Obteniendo cuotas reales de apuestas...")
    odds = get_odds_for_mlb()
    print(f"✅ {len(odds)} cuotas recibidas.")

    print("🔄 Emparejando partidos con cuotas...")
    partidos_finales = emparejar_partidos(games, odds)

    for partido in partidos_finales:
        print("\n🧾", partido['enfrentamiento'])
        print("   Pitchers:", partido['pitchers'])
        print("   Cuotas ML:", partido['cuotas'])
        if partido['total']:
            print("   Over/Under:", partido['total'])


if __name__ == "__main__":
    main()
