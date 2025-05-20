
# dg_picks_mlb.py – Mejorado con pitcher, local/visitante y cuotas Over/Under

import requests
from datetime import datetime
import pytz

ODDS_API_KEY = "137992569bc2352366c01e6928577b2d"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"
HEADERS = {"User-Agent": "DG Picks"}

MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")


def get_today_mlb_games():
    params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher"}
    response = requests.get(MLB_STATS_BASE_URL, headers=HEADERS, params=params)
    data = response.json()

    games = []
    for date_data in data.get("dates", []):
        for game in date_data.get("games", []):
            home = game["teams"]["home"]["team"]["name"]
            away = game["teams"]["away"]["team"]["name"]

            home_pitcher = game["teams"]["home"].get("probablePitcher", {}).get("fullName", "Por confirmar")
            away_pitcher = game["teams"]["away"].get("probablePitcher", {}).get("fullName", "Por confirmar")

            games.append({
                "home": home,
                "away": away,
                "home_pitcher": home_pitcher,
                "away_pitcher": away_pitcher
            })

    return games


def get_over_under_odds():
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "totals",
        "oddsFormat": "decimal"
    }
    response = requests.get(ODDS_API_URL, params=params)
    data = response.json()

    ou_odds = {}
    for event in data:
        teams = tuple(sorted([event["home_team"], event["away_team"]]))
        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market["key"] == "totals":
                    outcome = market["outcomes"][0]  # Primera línea de Over/Under
                    ou_odds[teams] = {
                        "total": outcome.get("point"),
                        "over": outcome.get("price") if outcome.get("name") == "Over" else None,
                        "under": market["outcomes"][1].get("price") if len(market["outcomes"]) > 1 else None
                    }
                    break
    return ou_odds


def mostrar_partidos():
    juegos = get_today_mlb_games()
    cuotas_ou = get_over_under_odds()

    for juego in juegos:
        equipos = tuple(sorted([juego["home"], juego["away"]]))
        print(f"🧢 {juego['away']} (P: {juego['away_pitcher']}) @ {juego['home']} (P: {juego['home_pitcher']})")

        if equipos in cuotas_ou:
            print(f"   🔢 Total: {cuotas_ou[equipos]['total']} | Over: {cuotas_ou[equipos]['over']} | Under: {cuotas_ou[equipos]['under']}")
        else:
            print("   🔍 Cuotas Over/Under no disponibles")
        print("—" * 60)


if __name__ == "__main__":
    mostrar_partidos()
