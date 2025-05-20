
# dg_picks_mlb.py – Versión completa integrada para DG Picks

import requests
from datetime import datetime, timedelta
import pytz

ODDS_API_KEY = "137992569bc2352366c01e6928577b2d"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_TEAM_STATS_URL = "https://statsapi.mlb.com/api/v1/teams/{}/stats"
MLB_GAMELOG_URL = "https://statsapi.mlb.com/api/v1/teams/{}/stats?stats=gameLog&group=hitting&season=2024"
HEADERS = {"User-Agent": "DG Picks"}

MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")


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


def get_over_under_odds():
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "totals",
        "oddsFormat": "decimal"
    }
    response = requests.get(ODDS_API_URL, params=params)
    data = response.json()

    odds_dict = {}
    for event in data:
        equipos = tuple(sorted([event["home_team"], event["away_team"]]))
        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market["key"] == "totals":
                    outcomes = market["outcomes"]
                    over = next((o for o in outcomes if o["name"] == "Over"), None)
                    under = next((o for o in outcomes if o["name"] == "Under"), None)
                    if over and under:
                        odds_dict[equipos] = {
                            "total": over.get("point"),
                            "over": over.get("price"),
                            "under": under.get("price")
                        }
                    break
    return odds_dict


def get_team_form(team_id):
    response = requests.get(MLB_GAMELOG_URL.format(team_id), headers=HEADERS)
    try:
        stats = response.json()["stats"][0]["splits"]
        last_5 = stats[:5]
        anotados = [g["stat"]["runs"] for g in last_5]
        recibidos = [g["stat"]["runsAllowed"] for g in last_5]
        return sum(anotados) / 5, sum(recibidos) / 5
    except:
        return 0, 0


def analizar_juegos():
    juegos = get_today_mlb_games()
    cuotas = get_over_under_odds()

    for juego in juegos:
        home = juego["home"]
        away = juego["away"]
        home_pitcher = juego["home_pitcher"]
        away_pitcher = juego["away_pitcher"]

        home_ataque, home_defensa = get_team_form(juego["home_id"])
        away_ataque, away_defensa = get_team_form(juego["away_id"])

        total_estimado = round((home_ataque + away_ataque + home_defensa + away_defensa) / 2, 2)

        equipos = tuple(sorted([home, away]))
        print(f"⚾ {away} (P: {away_pitcher}) @ {home} (P: {home_pitcher})")
        print(f"   🟢 Promedio {away}: {away_ataque:.1f} anotados / {away_defensa:.1f} recibidos")
        print(f"   🔵 Promedio {home}: {home_ataque:.1f} anotados / {home_defensa:.1f} recibidos")
        print(f"   🔢 Total estimado: {total_estimado}")

        if equipos in cuotas:
            total = cuotas[equipos]["total"]
            over = cuotas[equipos]["over"]
            under = cuotas[equipos]["under"]
            print(f"   📊 Línea: {total} | Over: {over} | Under: {under}")

            if total_estimado > float(total) and float(over) >= 1.75:
                print(f"   ✅ PICK: Over {total} carreras | Cuota: {over}")
            elif total_estimado < float(total) and float(under) >= 1.75:
                print(f"   ✅ PICK: Under {total} carreras | Cuota: {under}")
            else:
                print("   ⚪ Solo informativo, sin pick claro")

        else:
            print("   ❌ Cuotas no disponibles")

        print("—" * 60)


if __name__ == "__main__":
    analizar_juegos()
