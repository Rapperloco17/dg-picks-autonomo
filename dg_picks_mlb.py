# dg_picks_mlb.py (mejorado con presentación real del pick sugerido)

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
        "record": f"{victorias}G-{derrotas}P"
    }


def imprimir_pick_final(equipo, cuota, justificacion, forma):
    print("━━━━━━━━━━━━━━━━━━━━━━")
    print("🎯 PICK SUGERIDO DG PICKS – MLB")
    print(f"✅ {equipo} ML @ {cuota}")
    print(f"📊 Motivo: {justificacion}")
    print(f"📈 Forma reciente: {forma}")
    print("💡 Valor detectado en la cuota")
    print("━━━━━━━━━━━━━━━━━━━━━━")


def main():
    print("⏳ Obteniendo partidos de MLB para hoy...")
    games = get_today_mlb_games()
    print(f"✅ {len(games)} partidos encontrados.")

    print("⏳ Obteniendo cuotas reales de apuestas...")
    odds = get_odds_for_mlb()
    print(f"✅ {len(odds)} cuotas recibidas.")

    for game in games:
        home = game['home_team']['name']
        away = game['away_team']['name']
        print(f"\n🧾 {away} vs {home}")
        print(f"   Pitchers: {game['away_pitcher_name']} vs {game['home_pitcher_name']}")

        cuotas = {}
        total = {}
        for odd in odds:
            if (home.lower() in odd['home_team'].lower() and away.lower() in odd['away_team'].lower()):
                cuota_ml = odd.get("bookmakers", [])[0].get("markets", [])[0].get("outcomes", [])
                cuotas = {o['name']: o['price'] for o in cuota_ml}
                total_market = next((m for m in odd.get("bookmakers", [])[0].get("markets", []) if m['key'] == 'totals'), None)
                total = total_market['outcomes'][0] if total_market else {}
                break

        print("   Cuotas ML:", cuotas)
        if total:
            print("   Over/Under:", total)

        stats_home = get_team_stats(game['home_team_id'])
        stats_away = get_team_stats(game['away_team_id'])

        pitcher_home = get_pitcher_stats(game['home_pitcher_id'])
        pitcher_away = get_pitcher_stats(game['away_pitcher_id'])

        form_home = get_team_form(game['home_team_id'])
        form_away = get_team_form(game['away_team_id'])

        justificacion = []
        ganador = None

        try:
            if float(pitcher_home.get("era", 99)) < float(pitcher_away.get("era", 99)):
                justificacion.append("mejor ERA del pitcher local")
                ganador = home
            else:
                justificacion.append("mejor ERA del pitcher visitante")
                ganador = away

            if float(stats_home.get("avg", 0)) > float(stats_away.get("avg", 0)):
                justificacion.append("mejor ofensiva local")
            else:
                justificacion.append("mejor ofensiva visitante")

            forma = form_home if ganador == home else form_away
            cuota = cuotas.get(ganador, "-")
            imprimir_pick_final(ganador, cuota, ", ".join(justificacion), f"{forma.get('record')} | {forma.get('anotadas')} anotadas por juego")

        except:
            print("❌ No se pudo calcular el pick sugerido por falta de datos.")


if __name__ == "__main__":
    main()
