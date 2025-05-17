# dg_picks_mlb.py

import requests
from datetime import datetime, timedelta
import pytz
import time

# === CONFIGURACIONES ===
ODDS_API_KEY = "137992569bc2352366c01e6928577b2d"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_GAME_STATS_URL = "https://statsapi.mlb.com/api/v1.1/game/{}/feed/live"
MLB_TEAM_STATS_URL = "https://statsapi.mlb.com/api/v1/teams/{}/stats"
HEADERS = {"User-Agent": "DG Picks"}

MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")
AYER = (datetime.now(MX_TZ) - timedelta(days=1)).strftime("%Y-%m-%d")


def get_today_mlb_games():
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
                "home_team": game["teams"]["home"]["team"],
                "away_team": game["teams"]["away"]["team"],
                "home_pitcher": game["teams"]["home"].get("probablePitcher", {}).get("fullName", "No confirmado"),
                "away_pitcher": game["teams"]["away"].get("probablePitcher", {}).get("fullName", "No confirmado"),
                "home_team_id": game["teams"]["home"]["team"]["id"],
                "away_team_id": game["teams"]["away"]["team"]["id"],
                "start_time": game.get("gameDate")
            })
    return games[:5]


def get_odds_for_mlb():
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


def get_team_stats(team_id):
    url = MLB_TEAM_STATS_URL.format(team_id)
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return {}
    stats = response.json()
    splits = stats.get("stats", [])[0].get("splits", [])[0].get("stat", {})
    return splits


def emparejar_partidos(games, odds):
    partidos = []
    for game in games:
        for odd in odds:
            if (game['home_team']['name'].lower() in odd['home_team'].lower() or odd['home_team'].lower() in game['home_team']['name'].lower()) and \
               (game['away_team']['name'].lower() in odd['away_team'].lower() or odd['away_team'].lower() in game['away_team']['name'].lower()):

                cuota_ml = odd.get("bookmakers", [])[0].get("markets", [])[0].get("outcomes", [])
                cuotas_dict = {o['name']: o['price'] for o in cuota_ml}

                total_market = next((m for m in odd.get("bookmakers", [])[0].get("markets", []) if m['key'] == 'totals'), None)
                over_under = total_market['outcomes'][0] if total_market else {}

                partidos.append({
                    "enfrentamiento": f"{game['away_team']['name']} vs {game['home_team']['name']}",
                    "pitchers": f"{game['away_pitcher']} vs {game['home_pitcher']}",
                    "inicio": game['start_time'],
                    "cuotas": cuotas_dict,
                    "total": over_under,
                    "home_team_id": game['home_team_id'],
                    "away_team_id": game['away_team_id']
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

        home_stats = get_team_stats(partido['home_team_id'])
        away_stats = get_team_stats(partido['away_team_id'])

        print(f"   🟢 {partido['home_team_id']} – AVG: {home_stats.get('avg')}, OBP: {home_stats.get('obp')}, SLG: {home_stats.get('slg')}")
        print(f"   🔴 {partido['away_team_id']} – AVG: {away_stats.get('avg')}, OBP: {away_stats.get('obp')}, SLG: {away_stats.get('slg')}")


if __name__ == "__main__":
    main()
