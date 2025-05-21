# dg_picks_mlb.py – Ajuste total por forma + ERA + AVG + formato Telegram

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
                "home_pitcher_name": home_pitcher.get("fullName", "Por confirmar"),
                "away_pitcher_name": away_pitcher.get("fullName", "Por confirmar"),
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

def get_team_avg(team_id):
    url = MLB_TEAM_STATS_URL.format(team_id)
    response = requests.get(url, headers=HEADERS)
    stats = response.json()
    try:
        return float(stats["stats"][0]["splits"][0]["stat"]["battingAvg"])
    except:
        return 0.25

def ajustar_por_era(base, era_rival):
    if era_rival < 2.5:
        return base - 0.7
    elif era_rival < 3.5:
        return base - 0.3
    elif era_rival < 4.5:
        return base
    elif era_rival < 5.5:
        return base + 0.5
    else:
        return base + 0.8

def ajustar_por_avg(base, avg):
    if avg < 0.230:
        return base - 0.5
    elif avg < 0.250:
        return base - 0.2
    elif avg < 0.270:
        return base
    elif avg < 0.290:
        return base + 0.3
    else:
        return base + 0.6

def main():
    print("🔍 Análisis MLB – Total ajustado (forma + ERA + AVG)")
    juegos = get_today_mlb_games()
    odds = get_odds_for_mlb()

    for juego in juegos:
        home = juego["home_team"]
        away = juego["away_team"]
        pitcher_home_name = juego["home_pitcher_name"]
        pitcher_away_name = juego["away_pitcher_name"]
        pitcher_home = get_pitcher_stats(juego["home_pitcher_id"])
        pitcher_away = get_pitcher_stats(juego["away_pitcher_id"])
        form_home = get_team_form(juego["home_team_id"])
        form_away = get_team_form(juego["away_team_id"])
        avg_home = get_team_avg(juego["home_team_id"])
        avg_away = get_team_avg(juego["away_team_id"])

        anotadas_home = form_home.get("anotadas", 0)
        anotadas_away = form_away.get("anotadas", 0)
        recibidas_home = form_home.get("recibidas", 0)
        recibidas_away = form_away.get("recibidas", 0)

        era_away = float(pitcher_away.get("era", 99))
        era_home = float(pitcher_home.get("era", 99))

        ajustado_home = ajustar_por_avg(ajustar_por_era(anotadas_home, era_away), avg_home)
        ajustado_away = ajustar_por_avg(ajustar_por_era(anotadas_away, era_home), avg_away)

        total_combinado = round((ajustado_home + ajustado_away + recibidas_home + recibidas_away) / 2, 2)

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🧾 {away} (P: {pitcher_away_name}) vs {home} (P: {pitcher_home_name})")
        print(f"📊 AVG: {away} = {avg_away:.3f}, {home} = {avg_home:.3f}")
        print(f"📉 ERA Pitchers: {era_away} vs {era_home}")
        print(f"📈 Forma: {form_away.get('record', '❌')} vs {form_home.get('record', '❌')}")
        print(f"⚾ Anotadas / Recibidas: {anotadas_away}/{recibidas_away} vs {anotadas_home}/{recibidas_home}")
        print(f"📌 Total combinado estimado (ajustado): {total_combinado} carreras")

        over_line = None
        over_price = None
        for odd in odds:
            if home in odd["home_team"] and away in odd["away_team"]:
                for book in odd.get("bookmakers", []):
                    for market in book.get("markets", []):
                        if market["key"] == "totals":
                            for o in market["outcomes"]:
                                if o["name"].lower() == "over":
                                    over_line = o["point"]
                                    over_price = o["price"]
                                    break

        if over_line and over_price:
            print(f"📉 Línea Over/Under: {over_line} @ {over_price}")
            diferencia = round(total_combinado - over_line, 2)
            if diferencia >= 3:
                print(f"🔐🔥 CANDADO: Over {over_line} @ {over_price} | Estimado: {total_combinado}")
            elif diferencia >= 2:
                print(f"✅ Pick sugerido: Over {over_line} @ {over_price} | Estimado: {total_combinado}")
            elif diferencia <= -3:
                print(f"🔐🧊 CANDADO: Under {over_line} @ {over_price} | Estimado: {total_combinado}")
            elif diferencia <= -2:
                print(f"✅ Pick sugerido: Under {over_line} @ {over_price} | Estimado: {total_combinado}")
            else:
                print(f"⚠️ Sin ventaja clara (estimado vs línea: {total_combinado} vs {over_line})")
        else:
            print("❌ No se encontró línea de Over/Under")

if __name__ == "__main__":
    main()