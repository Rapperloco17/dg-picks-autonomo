# dg_picks_mlb.py – Mejora manejo de cuotas y eliminación de run line inexistente

import requests
from datetime import datetime, timedelta
import pytz

ODDS_API_KEY = "137992569bc2352366c01e6928577b2d"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_PLAYER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
MLB_TEAM_STATS_URL = "https://statsapi.mlb.com/api/v1/teams/{}/stats"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate={}&endDate={}"
HEADERS = {"User-Agent": "DG Picks"}

MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")

def get_today_mlb_games():
    params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher"}
    response = requests.get(MLB_STATS_BASE_URL, headers=HEADERS, params=params)
    data = response.json()
    games = []
    for date_info in data.get("dates", []):
        for game in date_info.get("games", []):
            home_pitcher = game["teams"]["home"].get("probablePitcher", {})
            away_pitcher = game["teams"]["away"].get("probablePitcher", {})
            games.append({
                "home_team": game["teams"]["home"]["team"]["name"],
                "away_team": game["teams"]["away"]["team"]["name"],
                "home_pitcher_id": home_pitcher.get("id"),
                "away_pitcher_id": away_pitcher.get("id"),
                "home_team_id": game["teams"]["home"]["team"]["id"],
                "away_team_id": game["teams"]["away"]["team"]["id"]
            })
    return games

def get_odds_for_mlb():
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal"
    }
    response = requests.get(ODDS_API_URL, headers=HEADERS, params=params)
    return response.json()

def get_pitcher_stats(pitcher_id):
    if not pitcher_id:
        return {}
    url = MLB_PLAYER_STATS_URL.format(pitcher_id)
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    if not data.get("people") or not data["people"][0].get("stats"):
        return {}
    splits = data["people"][0]["stats"][0].get("splits", [])
    return splits[0].get("stat", {}) if splits else {}

def get_team_stats(team_id):
    url = MLB_TEAM_STATS_URL.format(team_id)
    response = requests.get(url, headers=HEADERS)
    stats = response.json()
    if not stats.get("stats") or not stats["stats"][0].get("splits"):
        return {}
    return stats["stats"][0]["splits"][0].get("stat", {})

def get_team_form(team_id):
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    url = MLB_RESULTS_URL.format(team_id, start_date, end_date)
    response = requests.get(url, headers=HEADERS)
    games = response.json().get("dates", [])
    resultados = []
    for fecha in games:
        for game in fecha.get("games", []):
            if game.get("status", {}).get("detailedState") != "Final":
                continue
            home = game["teams"]["home"]
            away = game["teams"]["away"]
            if home["team"]["id"] == team_id:
                anotadas = home["score"]
                recibidas = away["score"]
                victoria = anotadas > recibidas
            else:
                anotadas = away["score"]
                recibidas = home["score"]
                victoria = anotadas > recibidas
            resultados.append((anotadas, recibidas, victoria))
    ultimos = resultados[-5:]
    if not ultimos:
        return {}
    promedio_anotadas = round(sum(x[0] for x in ultimos) / len(ultimos), 2)
    promedio_recibidas = round(sum(x[1] for x in ultimos) / len(ultimos), 2)
    victorias = sum(1 for x in ultimos if x[2])
    return {
        "anotadas": promedio_anotadas,
        "recibidas": promedio_recibidas,
        "record": f"{victorias}G-{5 - victorias}P"
    }

def main():
    print("🔍 Analizando partidos de MLB del día...")
    games = get_today_mlb_games()
    odds = get_odds_for_mlb()

    for game in games:
        home = game['home_team']
        away = game['away_team']
        pitcher_home = get_pitcher_stats(game['home_pitcher_id'])
        pitcher_away = get_pitcher_stats(game['away_pitcher_id'])
        stats_home = get_team_stats(game['home_team_id'])
        stats_away = get_team_stats(game['away_team_id'])
        form_home = get_team_form(game['home_team_id'])
        form_away = get_team_form(game['away_team_id'])

        for odd in odds:
            if home.lower() in odd["home_team"].lower() and away.lower() in odd["away_team"].lower():
                try:
                    cuotas = {}
                    for m in odd["bookmakers"][0]["markets"]:
                        if m["key"] == "h2h":
                            for o in m["outcomes"]:
                                cuotas[o["name"]] = o["price"]
                        if m["key"] == "spreads":
                            for o in m["outcomes"]:
                                if o["point"] == -1.5:
                                    key = f"{o['name']} -1.5"
                                    cuotas[key] = o["price"]

                    print(f"\n🧾 {away} vs {home}")
                    print("   Cuotas:", cuotas)
                    print("   ERA Pitchers:", pitcher_away.get("era", "❌ Sin datos"), "vs", pitcher_home.get("era", "❌ Sin datos"))
                    print("   AVG Equipos:", stats_away.get("avg", "❌ Sin datos"), "vs", stats_home.get("avg", "❌ Sin datos"))
                    print("   Forma:", form_away.get("record", "❌"), "vs", form_home.get("record", "❌"))

                    # Aquí puedes volver a colocar sugerencias si deseas, usando cuotas limpias
                except Exception as e:
                    print("   ❌ Error en análisis:", e)

if __name__ == "__main__":
    main()
