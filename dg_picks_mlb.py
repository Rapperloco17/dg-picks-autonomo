
# dg_picks_mlb.py – Versión full con ML, Handicap, Totals y stats reales

import requests
from datetime import datetime
import pytz

ODDS_API_KEY = "137992569bc2352366c01e6928577b2d"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate={}&endDate={}"
HEADERS = {"User-Agent": "DG Picks"}

MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")
AYER = (datetime.now(MX_TZ) - timedelta(days=10)).strftime("%Y-%m-%d")


def get_today_mlb_games():
    params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher"}
    response = requests.get(MLB_SCHEDULE_URL, headers=HEADERS, params=params)
    data = response.json()

    juegos = []
    for fecha in data.get("dates", []):
        for juego in fecha.get("games", []):
            home_team = juego["teams"]["home"]["team"]
            away_team = juego["teams"]["away"]["team"]
            home_pitcher = juego["teams"]["home"].get("probablePitcher", {}).get("fullName", "Por confirmar")
            away_pitcher = juego["teams"]["away"].get("probablePitcher", {}).get("fullName", "Por confirmar")
            home_id = home_team["id"]
            away_id = away_team["id"]

            juegos.append({
                "home": home_team["name"],
                "away": away_team["name"],
                "home_pitcher": home_pitcher,
                "away_pitcher": away_pitcher,
                "home_id": home_id,
                "away_id": away_id
            })
    return juegos


def get_team_form(team_id):
    url = MLB_RESULTS_URL.format(team_id, AYER, HOY)
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    runs_for = []
    runs_against = []

    for date in data.get("dates", []):
        for game in date.get("games", []):
            try:
                if game["status"]["abstractGameState"] != "Final":
                    continue
                team_home = game["teams"]["home"]
                team_away = game["teams"]["away"]

                if team_home["team"]["id"] == team_id:
                    runs_for.append(team_home["score"])
                    runs_against.append(team_away["score"])
                elif team_away["team"]["id"] == team_id:
                    runs_for.append(team_away["score"])
                    runs_against.append(team_home["score"])
            except:
                continue

    if not runs_for:
        return 0.0, 0.0

    return round(sum(runs_for[-5:]) / min(5, len(runs_for)), 1), round(sum(runs_against[-5:]) / min(5, len(runs_against)), 1)


def get_all_odds():
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "totals,h2h,spreads",
        "oddsFormat": "decimal"
    }
    response = requests.get(ODDS_API_URL, params=params)
    data = response.json()

    odds_dict = {}
    for event in data:
        key = tuple(sorted([event["home_team"], event["away_team"]]))
        odds_dict[key] = {"totals": None, "h2h": None, "spreads": None}
        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market["key"] == "totals":
                    over = next((o for o in market["outcomes"] if o["name"] == "Over"), {})
                    under = next((o for o in market["outcomes"] if o["name"] == "Under"), {})
                    odds_dict[key]["totals"] = {
                        "point": over.get("point"),
                        "over": over.get("price"),
                        "under": under.get("price")
                    }
                elif market["key"] == "h2h":
                    outcomes = {o["name"]: o["price"] for o in market["outcomes"]}
                    odds_dict[key]["h2h"] = outcomes
                elif market["key"] == "spreads":
                    odds_dict[key]["spreads"] = {o["name"]: (o["point"], o["price"]) for o in market["outcomes"]}
    return odds_dict


def analizar_juegos():
    juegos = get_today_mlb_games()
    cuotas = get_all_odds()

    for juego in juegos:
        home = juego["home"]
        away = juego["away"]
        equipos = tuple(sorted([home, away]))
        home_pitcher = juego["home_pitcher"]
        away_pitcher = juego["away_pitcher"]

        anot_home, recib_home = get_team_form(juego["home_id"])
        anot_away, recib_away = get_team_form(juego["away_id"])
        total_estimado = round((anot_home + anot_away + recib_home + recib_away) / 2, 2)

        print(f"⚾ {away} (P: {away_pitcher}) @ {home} (P: {home_pitcher})")
        print(f"   🟢 Promedio {away}: {anot_away} anotados / {recib_away} recibidos")
        print(f"   🔵 Promedio {home}: {anot_home} anotados / {recib_home} recibidos")
        print(f"   🧮 Total estimado: {total_estimado}")

        if equipos in cuotas:
            datos = cuotas[equipos]

            # Totals
            if datos["totals"]:
                punto = datos["totals"]["point"]
                over = datos["totals"]["over"]
                under = datos["totals"]["under"]
                print(f"   📊 Totals: Línea {punto} | Over: {over} | Under: {under}")
                if total_estimado > float(punto) and over >= 1.75:
                    print(f"   ✅ PICK: Over {punto} carreras | Cuota: {over}")
                elif total_estimado < float(punto) and under >= 1.75:
                    print(f"   ✅ PICK: Under {punto} carreras | Cuota: {under}")
                else:
                    print("   ⚪ No hay valor claro en Totals")

            # Moneyline
            if datos["h2h"]:
                print("   💵 Moneyline:", datos["h2h"])

            # Run Line
            if datos["spreads"]:
                print("   ➖ Handicap:", datos["spreads"])

        else:
            print("   ❌ No hay cuotas disponibles")

        print("—" * 60)


if __name__ == "__main__":
    analizar_juegos()
