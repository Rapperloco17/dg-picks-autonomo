# dg_picks_mlb.py

import requests
from datetime import datetime, timedelta
import pytz
import time

# === CONFIGURACIONES ===
ODDS_API_KEY = "137992569bc2352366c01e6928577b2d"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_PLAYER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
MLB_TEAM_STATS_URL = "https://statsapi.mlb.com/api/v1/teams/{}/stats"
HEADERS = {"User-Agent": "DG Picks"}

MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")


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
            home_pitcher = game["teams"]["home"].get("probablePitcher", {})
            away_pitcher = game["teams"]["away"].get("probablePitcher", {})
            games.append({
                "gamePk": game["gamePk"],
                "home_team": game["teams"]["home"]["team"],
                "away_team": game["teams"]["away"]["team"],
                "home_pitcher_name": home_pitcher.get("fullName", "No confirmado"),
                "away_pitcher_name": away_pitcher.get("fullName", "No confirmado"),
                "home_pitcher_id": home_pitcher.get("id"),
                "away_pitcher_id": away_pitcher.get("id"),
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


def get_pitcher_stats(pitcher_id):
    if not pitcher_id:
        return {}
    url = MLB_PLAYER_STATS_URL.format(pitcher_id)
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return {}
    data = response.json()
    stats = data.get("people", [])[0].get("stats", [])[0].get("splits", [])[0].get("stat", {})
    return stats


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
                    "pitchers": f"{game['away_pitcher_name']} vs {game['home_pitcher_name']}",
                    "inicio": game['start_time'],
                    "cuotas": cuotas_dict,
                    "total": over_under,
                    "home_team_id": game['home_team_id'],
                    "away_team_id": game['away_team_id'],
                    "home_pitcher_id": game['home_pitcher_id'],
                    "away_pitcher_id": game['away_pitcher_id']
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

        print(f"   🟢 Local – AVG: {home_stats.get('avg')}, OBP: {home_stats.get('obp')}, SLG: {home_stats.get('slg')}")
        print(f"   🔴 Visitante – AVG: {away_stats.get('avg')}, OBP: {away_stats.get('obp')}, SLG: {away_stats.get('slg')}")

        home_pitcher_stats = get_pitcher_stats(partido['home_pitcher_id'])
        away_pitcher_stats = get_pitcher_stats(partido['away_pitcher_id'])

        print("   📊 Stats Pitcher Local:", {
            "ERA": home_pitcher_stats.get("era"),
            "WHIP": home_pitcher_stats.get("whip"),
            "K/9": home_pitcher_stats.get("strikeoutsPer9Inn")
        })
        print("   📊 Stats Pitcher Visitante:", {
            "ERA": away_pitcher_stats.get("era"),
            "WHIP": away_pitcher_stats.get("whip"),
            "K/9": away_pitcher_stats.get("strikeoutsPer9Inn")
        })


if __name__ == "__main__":
    main()
