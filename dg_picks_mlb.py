# dg_picks_mlb.py – Análisis con picks ML, Over y Handicap -1.5

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

def sugerir_pick(equipo, rival, stats_eq, stats_riv, pitcher_eq, pitcher_riv, form_eq, cuotas):
    try:
        era = float(pitcher_eq.get("era", 99))
        avg = float(stats_eq.get("avg", 0))
        riv_era = float(pitcher_riv.get("era", 99))
        riv_avg = float(stats_riv.get("avg", 0))
        anotadas = form_eq.get("anotadas", 0)
        recibidas = form_eq.get("recibidas", 10)
        cuota_ml = cuotas.get(equipo)
        spread = cuotas.get(f"{equipo} -1.5")

        if cuota_ml and cuota_ml < 1.60 and spread and anotadas >= 5 and era < 3.5:
            return f"✅ Pick sugerido: {equipo} -1.5 @ {spread} | Motivo: cuota ML baja, ofensiva potente, ERA sólida"
        elif cuota_ml and 1.70 <= cuota_ml <= 2.10 and era < riv_era and avg > riv_avg:
            return f"✅ Pick sugerido: {equipo} ML @ {cuota_ml} | Motivo: ventaja en ERA y AVG"
        elif anotadas + stats_riv.get("avg", 0) > 9:
            return "✅ Pick sugerido: Over 8.5 | Ambos equipos anotan mucho"
        else:
            return "⚠️ Partido parejo, evitar"
    except:
        return "❌ No hay suficiente información para sugerir pick"

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
                    outcomes = {o["name"]: o["price"] for m in odd["bookmakers"][0]["markets"] for o in m["outcomes"] if m["key"] in ["h2h", "spreads"]}
                    if f"{home} -1.5" not in outcomes:
                        for o in odd["bookmakers"][0]["markets"]:
                            if o["key"] == "spreads":
                                for spread in o["outcomes"]:
                                    if spread["point"] == -1.5 and spread["name"] == home:
                                        outcomes[f"{home} -1.5"] = spread["price"]
                                    if spread["point"] == -1.5 and spread["name"] == away:
                                        outcomes[f"{away} -1.5"] = spread["price"]

                    print("\n🧾", f"{away} vs {home}")
                    print("   Cuotas:", outcomes)
                    print("   ERA Pitchers:", pitcher_away.get("era"), "vs", pitcher_home.get("era"))
                    print("   AVG Equipos:", stats_away.get("avg"), "vs", stats_home.get("avg"))
                    print("   Forma:", form_away.get("record"), "vs", form_home.get("record"))

                    pick_home = sugerir_pick(home, away, stats_home, stats_away, pitcher_home, pitcher_away, form_home, outcomes)
                    pick_away = sugerir_pick(away, home, stats_away, stats_home, pitcher_away, pitcher_home, form_away, outcomes)

                    print("   🧠", pick_home)
                    print("   🧠", pick_away)
                except Exception as e:
                    print("   ❌ Error en análisis:", e)

if __name__ == "__main__":
    main()

