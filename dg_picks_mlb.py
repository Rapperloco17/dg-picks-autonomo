import requests
from datetime import datetime, timedelta
import pytz
import os

# URLs y constantes
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_PLAYER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching,hitting],type=[season])"
MLB_TEAM_STATS_URL = "https://statsapi.mlb.com/api/v1/teams/{}/stats"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate={}&endDate={}"
HEADERS = {"User-Agent": "DG Picks"}

# Configuración de zona horaria
MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")

# Estadio impact factors
STADIUM_FACTORS = {
    "Busch Stadium": {"hr_factor": 0.9, "offense_boost": 0.95},
    "Globe Life Field": {"hr_factor": 1.1, "offense_boost": 1.05},
    "Fenway Park": {"hr_factor": 1.0, "offense_boost": 1.0},
    "Truist Park": {"hr_factor": 1.0, "offense_boost": 1.0},
    "Guaranteed Rate Field": {"hr_factor": 0.95, "offense_boost": 0.9},
    "Oriole Park": {"hr_factor": 1.05, "offense_boost": 1.0}
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
        url_for_debug = f"{ODDS_API_URL}?regions=us&markets=h2h,spreads,totals&oddsFormat=decimal"
        print(f"🔧 Probando API - URL: {url_for_debug}")
        
        response = requests.get(ODDS_API_URL, headers=HEADERS, params=params, timeout=10)
        print(f"🔧 Código de estado HTTP: {response.status_code}")
        print(f"🔧 Respuesta cruda: {response.text}")
        
        if response.status_code != 200:
            print("❌ La API no respondió correctamente. Revisa el código de estado y la respuesta.")
            return []
        
        odds_data = response.json()
        if not isinstance(odds_data, list):
            print("❌ Formato de datos inesperado. Se esperaba una lista.")
            return []
        
        print(f"📊 Número de partidos con cuotas: {len(odds_data)}")
        return odds_data
    except Exception as e:
        print("❌ Error al obtener cuotas:", e)
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
        stats["homeRuns"] = stats.get("homeRuns", 0)
        stats["strikeOuts"] = stats.get("strikeOuts", 0)
        return stats
    except Exception as e:
        print(f"❌ Error al obtener stats del pitcher {pitcher_id}: {e}")
        return {}

# Función para obtener stats del bateador principal
def get_top_hitter_stats(team_id):
    url = MLB_TEAM_STATS_URL.format(team_id)
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        stats = response.json()
        if not stats.get("stats") or not stats["stats"][0].get("splits"):
            return {"name": "N/A", "hr": 0, "avg": 0.0}
        team_stats = stats["stats"][0]["splits"][0].get("team", {})
        players = team_stats.get("players", [])
        if not players:
            return {"name": "N/A", "hr": 0, "avg": 0.0}
        top_hitter = max(players, key=lambda p: p["stats"][0]["stat"].get("homeRuns", 0) if p.get("stats") else 0)
        hitter_stats = top_hitter["stats"][0]["stat"]
        return {
            "name": top_hitter["person"]["fullName"],
            "hr": hitter_stats.get("homeRuns", 0),
            "avg": hitter_stats.get("avg", 0.0)
        }
    except Exception as e:
        print(f"❌ Error al obtener stats del bateador de equipo {team_id}: {e}")
        return {"name": "N/A", "hr": 0, "avg": 0.0}

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

# Función para sugerir pick
def sugerir_pick(equipo, form_eq, pitcher_eq, hitter_eq, venue, cuota_ml=None, cuota_spread=None):
    try:
        era = float(pitcher_eq.get("era", 99))
        anotadas = form_eq.get("anotadas", 0) * STADIUM_FACTORS.get(venue, {"offense_boost": 1.0})["offense_boost"]
        home_runs = int(pitcher_eq.get("homeRuns", 0))
        strikeouts = int(pitcher_eq.get("strikeOuts", 0))
        hr_hitter = hitter_eq["hr"]
        avg_hitter = hitter_eq["avg"]
        hr_factor = STADIUM_FACTORS.get(venue, {"hr_factor": 1.0})["hr_factor"]

        if home_runs > 10:
            return f"🚫 {equipo} descartado | Pitcher ha permitido {home_runs} HR, demasiado riesgo"

        # Calcular probabilidad de no HR
        no_hr_prob = (1 - (min(home_runs, 50) / 50) * (min(hr_hitter, 20) / 20) * hr_factor) * 100
        no_hr_prob = max(0, min(100, no_hr_prob))  # Asegurar entre 0 y 100

        if cuota_ml is None and cuota_spread is None:
            if anotadas >= 4.0 and era < 4.0 and avg_hitter > 0.300:
                return f"🎯 ¡A por {equipo} ML! | {hitter_eq['name']} encendido ({avg_hitter} AVG, {hr_hitter} HR) y pitcher sólido (ERA {era}, {strikeouts} K) | Prob No HR: {no_hr_prob:.1f}%"
            elif anotadas >= 4.5 and era < 3.7:
                return f"🔥 {equipo} -1.5, ¡a ganar por más! | Ofensiva fuerte y ERA top (ERA {era}) en {venue} | Prob No HR: {no_hr_prob:.1f}%"
            elif anotadas >= 4.5:
                return f"⚡ {equipo} anota a lo grande ({anotadas}/juego), ¡considera Over! | Prob No HR: {no_hr_prob:.1f}%"
            else:
                return f"👍 {equipo} ML, ¡apuesta segura! | {hitter_eq['name']} con {hr_hitter} HR y forma decente | Prob No HR: {no_hr_prob:.1f}%"

        if cuota_ml and cuota_ml < 1.70 and anotadas >= 3.5 and era < 4.0:
            return f"🎯 ¡A por {equipo} ML @ {cuota_ml}! | {hitter_eq['name']} ({avg_hitter} AVG) y pitcher en forma | Prob No HR: {no_hr_prob:.1f}%"
        elif cuota_ml and 1.70 <= cuota_ml <= 2.50 and anotadas >= 3.5 and era < 4.5:
            return f"🔥 {equipo} ML @ {cuota_ml}, ¡a darlo todo! | Ofensiva activa y pitcher estable | Prob No HR: {no_hr_prob:.1f}%"
        elif cuota_ml and cuota_ml > 2.50 and anotadas >= 4.5 and era < 4.2:
            return f"💥 ¡Sorpresa con {equipo} ML @ {cuota_ml}! | Underdog con valor | Prob No HR: {no_hr_prob:.1f}%"
        elif cuota_spread and cuota_ml < 1.70 and anotadas >= 4.5 and era < 3.7:
            return f"🔥 {equipo} -1.5 @ {cuota_spread}, ¡dominación! | Ofensiva y pitcher top | Prob No HR: {no_hr_prob:.1f}%"
        elif anotadas >= 4.5:
            return f"⚡ {equipo} anota a lo grande ({anotadas}/juego), ¡ve por el Over! | Prob No HR: {no_hr_prob:.1f}%"
        else:
            return f"⚠️ Partido reñido, ¡evalúa con cuidado! | Prob No HR: {no_hr_prob:.1f}%"
    except Exception as e:
        print(f"❌ Error al sugerir pick para {equipo}: {e}")
        return "❌ Sin datos, ¡revisa los números!"

# Función principal
def main():
    print("🔍 Analizando partidos de MLB...")
    print(f"🔧 Ejecutando desde: {__file__}")
    games = get_today_mlb_games()
    if not games:
        print("⚠️ No hay juegos programados para hoy o hubo un error al obtenerlos.")
        return
    
    try:
        odds = get_odds_for_mlb()
    except NameError:
        print("❌ Error: La función get_odds_for_mlb no está definida. Asegúrate de que el archivo sea correcto.")
        odds = []

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
        hitter_home = get_top_hitter_stats(home_team_id)
        hitter_away = get_top_hitter_stats(away_team_id)
        pitcher_home_name = get_pitcher_name(pitcher_home_id)
        pitcher_away_name = get_pitcher_name(pitcher_away_id)

        matched = False
        for odd in odds:
            if normalize_team(home) in normalize_team(odd.get("home_team", "")) and \
               normalize_team(away) in normalize_team(odd.get("away_team", "")):
                matched = True
                cuotas = {o["name"]: o["price"] for bookmaker in odd.get("bookmakers", []) for market in bookmaker.get("markets", []) for o in market.get("outcomes", []) if market["key"] == "h2h"}
                spreads = {o["name"]: (o["point"], o["price"]) for bookmaker in odd.get("bookmakers", []) for market in bookmaker.get("markets", []) for o in market.get("outcomes", []) if market["key"] == "spreads"}
                totals = next((o for bookmaker in odd.get("bookmakers", []) for market in bookmaker.get("markets", []) for o in market.get("outcomes", []) if market["key"] == "totals" and o["name"].lower() == "over"), None)
                over_line = totals["point"] if totals else None
                over_price = totals["price"] if totals else None
                under_price = next((o["price"] for bookmaker in odd.get("bookmakers", []) for market in bookmaker.get("markets", []) for o in market.get("outcomes", []) if market["key"] == "totals" and o["name"].lower() == "under"), None)

                print(f"\n🧾 {away} vs {home} | Horario: {game_time} | Estadio: {venue}")
                print(f"   Pitchers: {pitcher_away_name} ({away}, ERA {pitcher_away.get('era', '❌')}, {pitcher_away.get('homeRuns', '❌')} HR, {pitcher_away.get('strikeOuts', '❌')} K) vs {pitcher_home_name} ({home}, ERA {pitcher_home.get('era', '❌')}, {pitcher_home.get('homeRuns', '❌')} HR, {pitcher_home.get('strikeOuts', '❌')} K)")
                print(f"   Bateadores: {hitter_away['name']} ({away}, {hitter_away['avg']} AVG, {hitter_away['hr']} HR) vs {hitter_home['name']} ({home}, {hitter_home['avg']} AVG, {hitter_home['hr']} HR)")
                print(f"   ML: {away} @ {cuotas.get(away, 'N/A')} | {home} @ {cuotas.get(home, 'N/A')}")
                print(f"   Run Line: {away} {spreads.get(away, ('N/A', 'N/A'))[0]} @ {spreads.get(away, ('N/A', 'N/A'))[1]} | {home} {spreads.get(home, ('N/A', 'N/A'))[0]} @ {spreads.get(home, ('N/A', 'N/A'))[1]}")
                print(f"   Over/Under: O{over_line} @ {over_price} | U{over_line} @ {under_price}")
                print(f"   Forma (últ 10): {form_away.get('record', '❌')} vs {form_home.get('record', '❌')}")
                print(f"   Anotadas/Recibidas: {form_away.get('anotadas', '-')}/{form_away.get('recibidas', '-')} vs {form_home.get('anotadas', '-')}/{form_home.get('recibidas', '-')}")

                ventaja_home = form_home.get("anotadas", 0) > form_away.get("anotadas", 0) and float(pitcher_home.get("era", 99)) < float(pitcher_away.get("era", 99))
                ventaja_away = form_away.get("anotadas", 0) > form_home.get("anotadas", 0) and float(pitcher_away.get("era", 99)) < float(pitcher_home.get("era", 99))

                if ventaja_home and not ventaja_away:
                    pick_home = sugerir_pick(home, form_home, pitcher_home, hitter_home, venue, cuotas.get(home), spreads.get(home, (None, None))[1])
                    print("   🧠", pick_home)
                elif ventaja_away and not ventaja_home:
                    pick_away = sugerir_pick(away, form_away, pitcher_away, hitter_away, venue, cuotas.get(away), spreads.get(away, (None, None))[1])
                    print("   🧠", pick_away)
                else:
                    pick_home = sugerir_pick(home, form_home, pitcher_home, hitter_home, venue)
                    pick_away = sugerir_pick(away, form_away, pitcher_away, hitter_away, venue)
                    print("   🧠", pick_home if form_home.get("anotadas", 0) >= form_away.get("anotadas", 0) else pick_away)
                break

        if not matched:
            print(f"\n🧾 {away} vs {home} (sin cuotas) | Horario: {game_time} | Estadio: {venue}")
            print(f"   Pitchers: {pitcher_away_name} ({away}, ERA {pitcher_away.get('era', '❌')}, {pitcher_away.get('homeRuns', '❌')} HR, {pitcher_away.get('strikeOuts', '❌')} K) vs {pitcher_home_name} ({home}, ERA {pitcher_home.get('era', '❌')}, {pitcher_home.get('homeRuns', '❌')} HR, {pitcher_home.get('strikeOuts', '❌')} K)")
            print(f"   Bateadores: {hitter_away['name']} ({away}, {hitter_away['avg']} AVG, {hitter_away['hr']} HR) vs {hitter_home['name']} ({home}, {hitter_home['avg']} AVG, {hitter_home['hr']} HR)")
            print(f"   ⚠️ No se encontraron cuotas para este partido")
            print(f"   Forma (últ 10): {form_away.get('record', '❌')} vs {form_home.get('record', '❌')}")
            print(f"   Anotadas/Recibidas: {form_away.get('anotadas', '-')}/{form_away.get('recibidas', '-')} vs {form_home.get('anotadas', '-')}/{form_home.get('recibidas', '-')}")
            pick_home = sugerir_pick(home, form_home, pitcher_home, hitter_home, venue)
            pick_away = sugerir_pick(away, form_away, pitcher_away, hitter_away, venue)
            print("   🧠", pick_home if form_home.get("anotadas", 0) >= form_away.get("anotadas", 0) else pick_away)

    print("\n✅ Análisis completo")

if __name__ == "__main__":
    main()
