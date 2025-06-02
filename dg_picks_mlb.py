import requests
from datetime import datetime, timedelta
import pytz
import os

# URLs y constantes
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_PLAYER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate={}&endDate={}"
HEADERS = {"User-Agent": "DG Picks"}

# Configuración de zona horaria
MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")

# Estadio impact factors
STADIUM_FACTORS = {
    "Busch Stadium": {"offense_boost": 0.95},
    "Globe Life Field": {"offense_boost": 1.05},
    "Fenway Park": {"offense_boost": 1.0},
    "Truist Park": {"offense_boost": 1.0},
    "Guaranteed Rate Field": {"offense_boost": 0.9},
    "Oriole Park": {"offense_boost": 1.0}
}

# Función para obtener juegos de MLB
def get_today_mlb_games():
    params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher,venue"}
    try:
        response = requests.get(MLB_STATS_BASE_URL, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        games = []
        for date_info in data.get("dates", []):
            for game in date_info.get("games", []):
                venue = game["venue"]["name"]
                home_pitcher = game["teams"]["home"].get("probablePitcher", {})
                away_pitcher = game["teams"]["away"].get("probablePitcher", {})
                game_time = datetime.strptime(game["gameDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC).astimezone(MX_TZ).strftime("%I:%M %p CST")
                games.append({
                    "home_team": game["teams"]["home"]["team"]["name"],
                    "away_team": game["teams"]["away"]["team"]["name"],
                    "home_pitcher_id": home_pitcher.get("id"),
                    "away_pitcher_id": away_pitcher.get("id"),
                    "home_team_id": game["teams"]["home"]["team"]["id"],
                    "away_team_id": game["teams"]["away"]["team"]["id"],
                    "game_time": game_time,
                    "venue": venue
                })
        print(f"🔍 Encontrados {len(games)} partidos de MLB para hoy.")
        return games
    except Exception as e:
        print(f"❌ Error al obtener juegos de MLB: {e}")
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

# Función para normalizar nombres de equipos
def normalize_team(name):
    return name.lower().replace(" ", "").replace("-", "").replace(".", "")

# Función para obtener cuotas
def get_odds_for_mlb():
    params = {
        "apiKey": os.getenv("ODDS_API_KEY"),
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal"
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
        print(f"📊 Número de partidos con cuotas: {len(odds_data)}")
        return odds_data
    except Exception as e:
        print(f"❌ Error al obtener cuotas: {e}")
        return []

# Función para obtener stats del pitcher
def get_pitcher_stats(pitcher_id):
    if not pitcher_id:
        return {}
    url = MLB_PLAYER_STATS_URL.format(pitcher_id)
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data.get("people") or not data["people"][0].get("stats"):
            return {}
        splits = data["people"][0]["stats"][0].get("splits", [])
        stats = splits[0].get("stat", {}) if splits else {}
        stats["strikeOuts"] = stats.get("strikeOuts", 0)
        return stats
    except Exception as e:
        print(f"❌ Error al obtener stats del pitcher {pitcher_id}: {e}")
        return {}

# Función para obtener forma del equipo
def get_team_form(team_id):
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
    url = MLB_RESULTS_URL.format(team_id, start_date, end_date)
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
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
        ultimos = resultados[-10:]
        if not ultimos:
            return {}
        promedio_anotadas = round(sum(x[0] for x in ultimos) / len(ultimos), 2)
        promedio_recibidas = round(sum(x[1] for x in ultimos) / len(ultimos), 2)
        victorias = sum(1 for x in ultimos if x[2])
        return {
            "anotadas": promedio_anotadas,
            "recibidas": promedio_recibidas,
            "record": f"{victorias}G-{10 - victorias}P"
        }
    except Exception as e:
        print(f"❌ Error al obtener forma del equipo {team_id}: {e}")
        return {}

# Función para estimar carreras
def estimate_runs(form_eq, venue):
    base_runs = form_eq.get("anotadas", 0)
    boost = STADIUM_FACTORS.get(venue, {"offense_boost": 1.0})["offense_boost"]
    return round(base_runs * boost, 1)

# Función para calcular probabilidad de Over/Under
def calculate_over_under_prob(form_home, form_away, venue, line=8.5):
    runs_home = estimate_runs(form_home, venue)
    runs_away = estimate_runs(form_away, venue)
    total_runs = runs_home + runs_away
    diff = total_runs - line
    prob_over = max(0, min(100, 50 + (diff * 10)))  # 50% base, ajustado por diferencia
    prob_under = 100 - prob_over
    return total_runs, prob_over, prob_under

# Función para evaluar Run Line
def evaluate_run_line(form_home, form_away, pitcher_home, pitcher_away, venue, cuota_spread_home=None, cuota_spread_away=None):
    runs_home = estimate_runs(form_home, venue)
    runs_away = estimate_runs(form_away, venue)
    era_home = float(pitcher_home.get("era", 99))
    era_away = float(pitcher_away.get("era", 99))
    
    diff_runs = runs_home - runs_away
    diff_era = era_away - era_home  # Mayor ERA del rival favorece al equipo
    
    # Criterios para Run Line: diferencia de carreras >= 1.5 y ventaja en ERA
    if diff_runs >= 1.5 and diff_era >= 0.5:
        if cuota_spread_home:
            return f"🔥 Run Line {form_home['home_team']} -1.5 @ {cuota_spread_home} | Ventaja clara: +{diff_runs:.1f} carreras estimadas, ERA rival +{diff_era:.1f}"
        return f"🔥 Run Line {form_home['home_team']} -1.5 | Ventaja clara: +{diff_runs:.1f} carreras estimadas, ERA rival +{diff_era:.1f}"
    elif diff_runs <= -1.5 and diff_era <= -0.5:
        if cuota_spread_away:
            return f"🔥 Run Line {form_away['away_team']} -1.5 @ {cuota_spread_away} | Ventaja clara: +{abs(diff_runs):.1f} carreras estimadas, ERA rival +{abs(diff_era):.1f}"
        return f"🔥 Run Line {form_away['away_team']} -1.5 | Ventaja clara: +{abs(diff_runs):.1f} carreras estimadas, ERA rival +{abs(diff_era):.1f}"
    else:
        return "⚖️ Partido parejo para Run Line | Diferencia no suficiente"

# Función para sugerir pick
def sugerir_pick(equipo, form_eq, pitcher_eq, venue, cuota_ml=None, cuota_spread=None):
    try:
        era = float(pitcher_eq.get("era", 99))
        anotadas = estimate_runs(form_eq, venue)
        strikeouts = int(pitcher_eq.get("strikeOuts", 0))

        if cuota_ml is None and cuota_spread is None:
            if anotadas >= 4.0 and era < 4.0:
                return f"🎯 ¡A por {equipo} ML! | Estimado {anotadas} carreras y pitcher sólido (ERA {era}, {strikeouts} K)"
            elif anotadas >= 4.5 and era < 3.7:
                return f"🔥 {equipo} -1.5, ¡a ganar por más! | Estimado {anotadas} carreras y ERA top (ERA {era}) en {venue}"
            elif anotadas >= 4.5:
                return f"⚡ {equipo} anota a lo grande ({anotadas}/juego), ¡considera Over!"
            else:
                return f"👍 {equipo} ML, ¡apuesta segura! | Estimado {anotadas} carreras y forma decente"

        if cuota_ml and cuota_ml < 1.70 and anotadas >= 3.5 and era < 4.0:
            return f"🎯 ¡A por {equipo} ML @ {cuota_ml}! | Estimado {anotadas} carreras y pitcher en forma"
        elif cuota_ml and 1.70 <= cuota_ml <= 2.50 and anotadas >= 3.5 and era < 4.5:
            return f"🔥 {equipo} ML @ {cuota_ml}, ¡a darlo todo! | Estimado {anotadas} carreras y pitcher estable"
        elif cuota_ml and cuota_ml > 2.50 and anotadas >= 4.5 and era < 4.2:
            return f"💥 ¡Sorpresa con {equipo} ML @ {cuota_ml}! | Estimado {anotadas} carreras y underdog con valor"
        elif cuota_spread and cuota_ml < 1.70 and anotadas >= 4.5 and era < 3.7:
            return f"🔥 {equipo} -1.5 @ {cuota_spread}, ¡dominación! | Estimado {anotadas} carreras y pitcher top"
        elif anotadas >= 4.5:
            return f"⚡ {equipo} anota a lo grande ({anotadas}/juego), ¡ve por el Over!"
        else:
            return f"⚠️ Partido reñido, ¡evalúa con cuidado!"
    except Exception as e:
        print(f"❌ Error al sugerir pick para {equipo}: {e}")
        return "❌ Sin datos, ¡revisa los números!"

# Función principal
def main():
    print("🔍 Analizando partidos de MLB...")
    games = get_today_mlb_games()
    if not games:
        print("⚠️ No hay juegos programados para hoy o hubo un error al obtenerlos.")
        return
    
    odds = get_odds_for_mlb()

    for game in games:
        home = game['home_team']
        away = game['away_team']
        pitcher_home_id = game['home_pitcher_id']
        pitcher_away_id = game['away_pitcher_id']
        home_team_id = game['home_team_id']
        away_team_id = game['away_team_id']
        game_time = game['game_time']
        venue = game['venue']

        pitcher_home = get_pitcher_stats(pitcher_home_id)
        pitcher_away = get_pitcher_stats(pitcher_away_id)
        form_home = get_team_form(home_team_id)
        form_away = get_team_form(away_team_id)
        pitcher_home_name = get_pitcher_name(pitcher_home_id)
        pitcher_away_name = get_pitcher_name(pitcher_away_id)

        # Añadir nombres de equipos a los diccionarios para usar en evaluate_run_line
        form_home['home_team'] = home
        form_away['away_team'] = away

        # Calcular probabilidad de Over/Under
        total_runs, prob_over, prob_under = calculate_over_under_prob(form_home, form_away, venue)

        matched = False
        for odd in odds:
            if normalize_team(home) in normalize_team(odd.get("home_team", "")) and \
               normalize_team(away) in normalize_team(odd.get("away_team", "")):
                matched = True
                cuotas = {o["name"]: o["price"] for bookmaker in odd.get("bookmakers", []) for market in bookmaker.get("markets", []) for o in market.get("outcomes", []) if market["key"] == "h2h"}
                spreads = {o["name"]: (o["point"], o["price"]) for bookmaker in odd.get("bookmakers", []) for market in bookmaker.get("markets", []) for o in market.get("outcomes", []) if market["key"] == "spreads"}
                totals = next((o for bookmaker in odd.get("bookmakers", []) for market in bookmaker.get("markets", []) for o in market.get("outcomes", []) if market["key"] == "totals" and o["name"].lower() == "over"), None)
                over_line = totals["point"] if totals else 8.5
                over_price = totals["price"] if totals else None
                under_price = next((o["price"] for bookmaker in odd.get("bookmakers", []) for market in bookmaker.get("markets", []) for o in market.get("outcomes", []) if market["key"] == "totals" and o["name"].lower() == "under"), None)

                print(f"\n=== {away} vs {home} ===")
                print(f"Horario: {game_time} | Estadio: {venue}")
                print(f"Pitchers: {pitcher_away_name} ({away}, ERA {pitcher_away.get('era', '❌')}, {pitcher_away.get('strikeOuts', '❌')} K) vs {pitcher_home_name} ({home}, ERA {pitcher_home.get('era', '❌')}, {pitcher_home.get('strikeOuts', '❌')} K)")
                print(f"Estimado de carreras: {estimate_runs(form_away, venue)} ({away}) vs {estimate_runs(form_home, venue)} ({home})")
                print(f"Total estimado: {total_runs} | Over {over_line}: {prob_over:.1f}% | Under {over_line}: {prob_under:.1f}%")
                print(evaluate_run_line(form_home, form_away, pitcher_home, pitcher_away, venue, spreads.get(home, (None, None))[1], spreads.get(away, (None, None))[1]))
                print(f"ML: {away} @ {cuotas.get(away, 'N/A')} | {home} @ {cuotas.get(home, 'N/A')}")
                print(f"Run Line: {away} {spreads.get(away, ('N/A', 'N/A'))[0]} @ {spreads.get(away, ('N/A', 'N/A'))[1]} | {home} {spreads.get(home, ('N/A', 'N/A'))[0]} @ {spreads.get(home, ('N/A', 'N/A'))[1]}")
                print(f"Over/Under: O{over_line} @ {over_price} | U{over_line} @ {under_price}")
                print(f"Forma (últ 10): {form_away.get('record', '❌')} vs {form_home.get('record', '❌')}")
                print(f"Anotadas/Recibidas: {form_away.get('anotadas', '-')}/{form_away.get('recibidas', '-')} vs {form_home.get('anotadas', '-')}/{form_home.get('recibidas', '-')}")
                print("---")

                ventaja_home = form_home.get("anotadas", 0) > form_away.get("anotadas", 0) and float(pitcher_home.get("era", 99)) < float(pitcher_away.get("era", 99))
                ventaja_away = form_away.get("anotadas", 0) > form_home.get("anotadas", 0) and float(pitcher_away.get("era", 99)) < float(pitcher_home.get("era", 99))

                if ventaja_home and not ventaja_away:
                    pick_home = sugerir_pick(home, form_home, pitcher_home, venue, cuotas.get(home), spreads.get(home, (None, None))[1])
                    print("🧠", pick_home)
                elif ventaja_away and not ventaja_home:
                    pick_away = sugerir_pick(away, form_away, pitcher_away, venue, cuotas.get(away), spreads.get(away, (None, None))[1])
                    print("🧠", pick_away)
                else:
                    pick_home = sugerir_pick(home, form_home, pitcher_home, venue)
                    pick_away = sugerir_pick(away, form_away, pitcher_away, venue)
                    print("🧠", pick_home if form_home.get("anotadas", 0) >= form_away.get("anotadas", 0) else pick_away)
                break

        if not matched:
            print(f"\n=== {away} vs {home} ===")
            print(f"Horario: {game_time} | Estadio: {venue}")
            print(f"Pitchers: {pitcher_away_name} ({away}, ERA {pitcher_away.get('era', '❌')}, {pitcher_away.get('strikeOuts', '❌')} K) vs {pitcher_home_name} ({home}, ERA {pitcher_home.get('era', '❌')}, {pitcher_home.get('strikeOuts', '❌')} K)")
            print(f"Estimado de carreras: {estimate_runs(form_away, venue)} ({away}) vs {estimate_runs(form_home, venue)} ({home})")
            print(f"Total estimado: {total_runs} | Over {over_line}: {prob_over:.1f}% | Under {over_line}: {prob_under:.1f}%")
            print(evaluate_run_line(form_home, form_away, pitcher_home, pitcher_away, venue))
            print(f"⚠️ No se encontraron cuotas para este partido")
            print(f"Forma (últ 10): {form_away.get('record', '❌')} vs {form_home.get('record', '❌')}")
            print(f"Anotadas/Recibidas: {form_away.get('anotadas', '-')}/{form_away.get('recibidas', '-')} vs {form_home.get('anotadas', '-')}/{form_home.get('recibidas', '-')}")
            print("---")
            pick_home = sugerir_pick(home, form_home, pitcher_home, venue)
            pick_away = sugerir_pick(away, form_away, pitcher_away, venue)
            print("🧠", pick_home if form_home.get("anotadas", 0) >= form_away.get("anotadas", 0) else pick_away)

    print("\n✅ Análisis completo")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
