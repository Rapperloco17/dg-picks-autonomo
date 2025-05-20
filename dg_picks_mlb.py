
# dg_picks_mlb.py – Versión estable con pitchers, líneas y sin errores de sintaxis

import requests
from datetime import datetime, timedelta
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
    juegos = []
    for fecha in data.get("dates", []):
        for juego in fecha.get("games", []):
            home = juego["teams"]["home"]
            away = juego["teams"]["away"]
            home_pitcher = home.get("probablePitcher", {}).get("fullName", "Por confirmar")
            away_pitcher = away.get("probablePitcher", {}).get("fullName", "Por confirmar")
            juegos.append({
                "home": home["team"]["name"],
                "away": away["team"]["name"],
                "home_pitcher": home_pitcher,
                "away_pitcher": away_pitcher
            })
    return juegos

def get_odds():
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "totals,h2h,spreads",
        "oddsFormat": "decimal"
    }
    response = requests.get(ODDS_API_URL, params=params)
    return response.json()

def main():
    print("🔍 Análisis MLB – Cuotas y Pitchers")
    juegos = get_today_mlb_games()
    odds = get_odds()

    for juego in juegos:
        home = juego["home"]
        away = juego["away"]
        home_pitcher = juego["home_pitcher"]
        away_pitcher = juego["away_pitcher"]
        print(f"🧾 {away} (P: {away_pitcher}) vs {home} (P: {home_pitcher})")

        odds_match = next((o for o in odds if home in o["home_team"] and away in o["away_team"]), None)
        if not odds_match:
            print("   ❌ Cuotas no disponibles")
            print("—" * 60)
            continue

        datos = {"totals": None, "h2h": None, "spreads": None}
        for book in odds_match.get("bookmakers", []):
            for market in book.get("markets", []):
                if market["key"] == "totals":
                    for outcome in market["outcomes"]:
                        if outcome["name"].lower() == "over":
                            datos["totals"] = {
                                "point": outcome["point"],
                                "over": outcome["price"]
                            }
                elif market["key"] == "h2h":
                    datos["h2h"] = {o["name"]: o["price"] for o in market["outcomes"]}
                elif market["key"] == "spreads":
                    datos["spreads"] = {o["name"]: (o["point"], o["price"]) for o in market["outcomes"]}

        if datos["totals"]:
            print(f"   📈 Línea: Over {datos['totals']['point']} | Cuota: {datos['totals']['over']}")
        if datos["h2h"]:
            print(f"   💵 ML: {datos['h2h']}")
        if datos["spreads"]:
            print(f"   ➖ Handicap: {datos['spreads']}")
        print("—" * 60)

if __name__ == "__main__":
    main()
