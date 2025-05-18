# dg_picks_mlb.py (con selección del Candado del Día – Reto Escalera 🪜)

import requests
from datetime import datetime, timedelta
import pytz
import time

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
    return games


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


def get_team_form(team_id):
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    url = MLB_RESULTS_URL.format(team_id, start_date, end_date)
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return {}
    games = response.json().get("dates", [])
    resultados = []
    for fecha in games:
        for game in fecha.get("games", []):
            if not game.get("status", {}).get("detailedState") == "Final":
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
    derrotas = len(ultimos) - victorias
    return {
        "anotadas": promedio_anotadas,
        "recibidas": promedio_recibidas,
        "record": f"{victorias}G-{derrotas}P",
        "victorias": victorias
    }


def imprimir_candado(data):
    print("\n🔒 CANDADO DEL DÍA – Reto Escalera 🪜")
    print("━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ {data['equipo']} ML @ {data['cuota']}")
    print(f"📊 Motivo: {data['motivo']}")
    print(f"📈 Forma: {data['record']} | {data['anotadas']} anotadas/juego")
    print("💡 Valor detectado en la cuota")
    print("━━━━━━━━━━━━━━━━━━━━━━")


def main():
    juegos = get_today_mlb_games()
    odds = get_odds_for_mlb()
    candidatos = []

    for juego in juegos:
        home = juego['home_team']['name']
        away = juego['away_team']['name']
        cuotas = {}
        for odd in odds:
            if (home.lower() in odd['home_team'].lower() and away.lower() in odd['away_team'].lower()):
                cuota_ml = odd.get("bookmakers", [])[0].get("markets", [])[0].get("outcomes", [])
                cuotas = {o['name']: o['price'] for o in cuota_ml}
                break
        stats_home = get_team_stats(juego['home_team_id'])
        stats_away = get_team_stats(juego['away_team_id'])
        pitcher_home = get_pitcher_stats(juego['home_pitcher_id'])
        pitcher_away = get_pitcher_stats(juego['away_pitcher_id'])
        form_home = get_team_form(juego['home_team_id'])
        form_away = get_team_form(juego['away_team_id'])

        try:
            eh, ea = float(pitcher_home.get("era", 99)), float(pitcher_away.get("era", 99))
            wh, wa = float(pitcher_home.get("whip", 99)), float(pitcher_away.get("whip", 99))
            ah, aa = float(stats_home.get("avg", 0)), float(stats_away.get("avg", 0))

            # Condiciones para pick
            if eh < 3.5 and wh < 1.15 and ah > aa + 0.02 and form_home['victorias'] >= 3:
                cuota = cuotas.get(home, 0)
                if 1.70 <= cuota <= 2.20:
                    candidatos.append({"equipo": home, "cuota": cuota, "motivo": "Pitcher dominante y ofensiva superior", "record": form_home['record'], "anotadas": form_home['anotadas']})
            elif ea < 3.5 and wa < 1.15 and aa > ah + 0.02 and form_away['victorias'] >= 3:
                cuota = cuotas.get(away, 0)
                if 1.70 <= cuota <= 2.20:
                    candidatos.append({"equipo": away, "cuota": cuota, "motivo": "Pitcher dominante y ofensiva superior", "record": form_away['record'], "anotadas": form_away['anotadas']})
        except:
            continue

    if candidatos:
        candado = sorted(candidatos, key=lambda x: (-x['anotadas'], x['cuota']))[0]
        imprimir_candado(candado)
    else:
        print("⚠️ No se detectó un pick con condiciones ideales para el reto escalera hoy.")


if __name__ == '__main__':
    main()
