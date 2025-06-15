import requests
from datetime import datetime
import pytz
import os
import time

# URLs y constantes
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_PLAYER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[byDateAll])"
MLB_TEAM_STATS_URL = "https://statsapi.mlb.com/api/v1/teams/{}/stats?group=hitting&season={}"
HEADERS = {"User-Agent": "DG Picks"}

# Configuración de zona horaria
MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")
SEASON = datetime.now(MX_TZ).strftime("%Y")

# Estadio impact factors
STADIUM_FACTORS = {
    "Busch Stadium": {"offense_boost": 0.95},
    "Globe Life Field": {"offense_boost": 1.05},
    "Fenway Park": {"offense_boost": 1.0},
    "Truist Park": {"offense_boost": 1.0},
    "Guaranteed Rate Field": {"offense_boost": 0.9},
    "Oriole Park": {"offense_boost": 1.0}
}

# Función para obtener juegos de MLB de hoy desde Odds API
def get_odds_for_mlb():
    params = {
        "apiKey": os.getenv("ODDS_API_KEY"),
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal",
        "dateFormat": "iso"
    }
    try:
        response = requests.get(ODDS_API_URL, headers=HEADERS, params=params, timeout=10)
        if response.status_code != 200:
            print(f"❌ Error al obtener cuotas: Código HTTP {response.status_code}")
            return []
        odds_data = response.json()
        if not isinstance(odds_data, list):
            print("❌ Formato de datos inesperado. Se esperaba una lista.")
            return []
        # Filtrar solo juegos de hoy
        games_today = [game for game in odds_data if game["commence_time"].startswith(HOY)]
        print(f"🔍 Encontrados {len(games_today)} partidos de MLB para hoy.")
        return games_today
    except Exception as e:
        print(f"❌ Error al obtener cuotas: {e}")
        return []

# Función para obtener nombre del pitcher
def get_pitcher_name(pitcher_id):
    if not pitcher_id:
        return "N/A"
    url = MLB_PLAYER_STATS_URL.format(pitcher_id)
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data.get("people"):
            return "N/A"
        return data["people"][0]["fullName"]
    except Exception as e:
        print(f"❌ Error al obtener nombre del pitcher {pitcher_id}: {e}")
        return "N/A"

# Función para obtener stats del pitcher
def get_pitcher_stats(pitcher_id):
    if not pitcher_id:
        return {}
    url = MLB_PLAYER_STATS_URL.format(pitcher_id)
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        stats = {}
        if data.get("people") and data["people"][0].get("stats"):
            splits = data["people"][0]["stats"][0].get("splits", [])
            if splits:
                stats = splits[0].get("stat", {})
                stats["strikeOuts"] = stats.get("strikeOuts", 0)
                stats["whip"] = stats.get("whip", 0.0)
                stats["era"] = stats.get("era", 0.0)
        return stats
    except Exception as e:
        print(f"❌ Error al obtener stats del pitcher {pitcher_id}: {e}")
        return {}

# Función para obtener forma del equipo
def get_team_form(team_id):
    if not team_id:
        return {}
    url = MLB_TEAM_STATS_URL.format(team_id, SEASON)
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 404:
            print(f"⚠️ 404 al obtener stats del equipo {team_id}, intentando sin season...")
            url = MLB_TEAM_STATS_URL.format(team_id, "").replace("&season={}", "")
            response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        stats = {}
        if data.get("stats"):
            hitting = data["stats"][0].get("splits", [{}])[0].get("stat", {})
            stats = {
                "avg": float(hitting.get("avg", ".000") or ".000"),
                "ops": float(hitting.get("ops", ".000") or ".000"),
                "homeRuns": hitting.get("homeRuns", 0),
                "runsPerGame": hitting.get("runsPerGame", 0.0)
            }
        return stats
    except Exception as e:
        print(f"❌ Error al obtener forma del equipo {team_id}: {e}")
        return {}

# Función para estimar carreras
def estimate_runs(form_eq, venue):
    base_runs = form_eq.get("runsPerGame", 0)
    boost = STADIUM_FACTORS.get(venue, {"offense_boost": 1.0})["offense_boost"]
    return round(base_runs * boost, 1)

# Función para calcular probabilidad de Over/Under
def calculate_over_under_prob(form_home, form_away, venue, over_line=8.5):
    runs_home = estimate_runs(form_home, venue)
    runs_away = estimate_runs(form_away, venue)
    total_runs = runs_home + runs_away
    diff = total_runs - over_line
    prob_over = max(0, min(100, 50 + (diff * 10)))
    prob_under = 100 - prob_over
    return total_runs, prob_over, prob_under

# Función para evaluar Run Line
def evaluate_run_line(form_home, form_away, pitcher_home, pitcher_away, venue, cuota_spread_home=None, cuota_spread_away=None):
    runs_home = estimate_runs(form_home, venue)
    runs_away = estimate_runs(form_away, venue)
    era_home = float(pitcher_home.get("era", 99))
    era_away = float(pitcher_away.get("era", 99))
    ops_home = form_home.get("ops", 0)
    ops_away = form_away.get("ops", 0)
    
    diff_runs = runs_home - runs_away
    diff_era = era_away - era_home
    diff_ops = ops_home - ops_away
    
    if diff_runs >= 1.5 and diff_era >= 0.5 and diff_ops >= 0.05:
        return f"🔥 Run Line {form_home['home_team']} -1.5 @ {cuota_spread_home or 'N/A'} | Ventaja: +{diff_runs:.1f} carreras, ERA rival +{diff_era:.1f}, OPS +{diff_ops:.3f}"
    elif diff_runs <= -1.5 and diff_era <= -0.5 and diff_ops <= -0.05:
        return f"🔥 Run Line {form_away['away_team']} -1.5 @ {cuota_spread_away or 'N/A'} | Ventaja: +{abs(diff_runs):.1f} carreras, ERA rival +{abs(diff_era):.1f}, OPS +{abs(diff_ops):.3f}"
    else:
        return "⚖️ Partido parejo para Run Line | Diferencia no suficiente"

# Función para sugerir pick
def sugerir_pick(home_team, away_team, form_home, form_away, pitcher_home, pitcher_away, venue, cuota_ml_home=None, cuota_ml_away=None, cuota_spread_home=None):
    try:
        era_home = float(pitcher_home.get("era", 99))
        era_away = float(pitcher_away.get("era", 99))
        runs_home = form_home.get("runsPerGame", 0)
        runs_away = form_away.get("runsPerGame", 0)
        ops_home = form_home.get("ops", 0)
        ops_away = form_away.get("ops", 0)

        if cuota_ml_home and cuota_ml_home < 1.70 and runs_home >= 4.0 and era_home < 3.8 and ops_home > 0.750:
            return f"🎯 {home_team} ML @ {cuota_ml_home:.2f} | {runs_home:.1f} carreras/juego, ERA {era_home}, OPS {ops_home:.3f}"
        elif cuota_ml_away and cuota_ml_away < 1.70 and runs_away >= 4.0 and era_away < 3.8 and ops_away > 0.750:
            return f"🎯 {away_team} ML @ {cuota_ml_away:.2f} | {runs_away:.1f} carreras/juego, ERA {era_away}, OPS {ops_away:.3f}"
        elif cuota_spread_home and runs_home >= 4.5 and era_home < 3.5 and ops_home > 0.750:
            return f"🔥 {home_team} -1.5 @ {cuota_spread_home:.2f} | {runs_home:.1f} carreras/juego, OPS {ops_home:.3f}"
        elif cuota_spread_away and runs_away >= 4.5 and era_away < 3.5 and ops_away > 0.750:
            return f"🔥 {away_team} -1.5 @ {cuota_spread_away:.2f} | {runs_away:.1f} carreras/juego, OPS {ops_away:.3f}"
        else:
            return f"⚠️ Partido reñido para {home_team} vs {away_team} | {runs_home:.1f} vs {runs_away:.1f} carreras/juego"
    except Exception as e:
        print(f"❌ Error al sugerir pick para {home_team} vs {away_team}: {e}")
        return "❌ Sin datos, ¡revisa los números!"

# Función principal
def main():
    print("🔍 Analizando partidos de MLB de hoy...")
    games = get_odds_for_mlb()
    if not games:
        print("⚠️ No hay juegos programados para hoy o hubo un error al obtener las cuotas.")
        return

    # Crear directorio /data si no existe
    os.makedirs("/data", exist_ok=True)
    with open("/data/picks_hoy.txt", "a") as f:
        f.write(f"=== Análisis de MLB - {HOY} ===\n\n")
        for game in games:
            commence_time = datetime.strptime(game["commence_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC).astimezone(MX_TZ).strftime("%I:%M %p CST")
            home_team = game["home_team"]
            away_team = game["away_team"]
            home_team_id = None
            away_team_id = None
            home_pitcher_id = None
            away_pitcher_id = None

            # Obtener IDs de equipos y pitchers desde la API de MLB
            try:
                params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher,venue"}
                response = requests.get(MLB_STATS_BASE_URL, headers=HEADERS, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                for date_info in data.get("dates", []):
                    for g in date_info.get("games", []):
                        if (normalize_team(g["teams"]["home"]["team"]["name"]) == normalize_team(home_team) and
                            normalize_team(g["teams"]["away"]["team"]["name"]) == normalize_team(away_team)):
                            home_team_id = g["teams"]["home"]["team"]["id"]
                            away_team_id = g["teams"]["away"]["team"]["id"]
                            home_pitcher_id = g["teams"]["home"].get("probablePitcher", {}).get("id")
                            away_pitcher_id = g["teams"]["away"].get("probablePitcher", {}).get("id")
                            break
                    if home_team_id:
                        break
            except Exception as e:
                print(f"❌ Error al obtener detalles del juego {home_team} vs {away_team}: {e}")

            # Obtener stats con retardo para evitar límites
            time.sleep(1)
            pitcher_home = get_pitcher_stats(home_pitcher_id) if home_pitcher_id else {}
            time.sleep(1)
            pitcher_away = get_pitcher_stats(away_pitcher_id) if away_pitcher_id else {}
            time.sleep(1)
            form_home = get_team_form(home_team_id) if home_team_id else {}
            time.sleep(1)
            form_away = get_team_form(away_team_id) if away_team_id else {}

            form_home['home_team'] = home_team
            form_away['away_team'] = away_team

            bookmakers = game.get("bookmakers", [])
            if bookmakers:
                h2h_market = next((m for m in bookmakers[0]["markets"] if m["key"] == "h2h"), None)
                spreads_market = next((m for m in bookmakers[0]["markets"] if m["key"] == "spreads"), None)
                totals_market = next((m for m in bookmakers[0]["markets"] if m["key"] == "totals"), None)

                home_odds = next((o["price"] for o in h2h_market["outcomes"] if normalize_team(o["name"]) == normalize_team(home_team)), None) if h2h_market else None
                away_odds = next((o["price"] for o in h2h_market["outcomes"] if normalize_team(o["name"]) == normalize_team(away_team)), None) if h2h_market else None
                home_spread_odds = next((o["price"] for o in spreads_market["outcomes"] if normalize_team(o["name"]) == normalize_team(home_team)), None) if spreads_market else None
                away_spread_odds = next((o["price"] for o in spreads_market["outcomes"] if normalize_team(o["name"]) == normalize_team(away_team)), None) if spreads_market else None
                over_line = next((o["point"] for o in totals_market["outcomes"] if o["name"].lower() == "over"), 8.5) if totals_market else 8.5
                over_odds = next((o["price"] for o in totals_market["outcomes"] if o["name"].lower() == "over"), None) if totals_market else None
                under_odds = next((o["price"] for o in totals_market["outcomes"] if o["name"].lower() == "under"), None) if totals_market else None

                if home_odds and away_odds:
                    total_runs, prob_over, prob_under = calculate_over_under_prob(form_home, form_away, game.get("venue", "Unknown"))
                    output = f"\n=== {away_team} vs {home_team} ===\n"
                    output += f"Horario: {commence_time} | Estadio: {game.get('venue', 'N/A')}\n"
                    output += f"Pitchers: {get_pitcher_name(away_pitcher_id)} ({away_team}, ERA {pitcher_away.get('era', 'N/A')}) vs {get_pitcher_name(home_pitcher_id)} ({home_team}, ERA {pitcher_home.get('era', 'N/A')})\n"
                    output += f"Equipos: {away_team} (AVG {form_away.get('avg', 'N/A')}, OPS {form_away.get('ops', 'N/A')}) vs {home_team} (AVG {form_home.get('avg', 'N/A')}, OPS {form_home.get('ops', 'N/A')})\n"
                    output += f"Estimado de carreras: {estimate_runs(form_away, game.get('venue', 'N/A'))} ({away_team}) vs {estimate_runs(form_home, game.get('venue', 'N/A'))} ({home_team})\n"
                    output += f"Total estimado: {total_runs:.1f} | Over {over_line}: {prob_over:.1f}% | Under {over_line}: {prob_under:.1f}%\n"
                    output += evaluate_run_line(form_home, form_away, pitcher_home, pitcher_away, game.get("venue", "N/A"), home_spread_odds, away_spread_odds) + "\n"
                    output += f"ML: {away_team} @ {away_odds:.2f} | {home_team} @ {home_odds:.2f}\n"
                    output += f"Run Line: {away_team} @ {away_spread_odds:.2f} | {home_team} @ {home_spread_odds:.2f}\n"
                    output += f"Over/Under: O{over_line} @ {over_odds:.2f} | U{over_line} @ {under_odds:.2f}\n"
                    output += "---\n"
                    pick = sugerir_pick(home_team, away_team, form_home, form_away, pitcher_home, pitcher_away, game.get("venue", "N/A"), home_odds, away_odds, home_spread_odds)
                    output += "🧠 " + pick + "\n"
                    f.write(output)

        f.write("\n✅ Análisis completo\n")

if __name__ == "__main__":
    main()
