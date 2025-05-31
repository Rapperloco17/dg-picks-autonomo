import os
import requests
import logging
import sqlite3
from datetime import datetime, timedelta
import pytz
from openai import OpenAI
from collections import defaultdict

# Configuración de logging
logging.basicConfig(filename='mlb_picks.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Validar variables de entorno
required_env_vars = ["OPENAI_API_KEY", "TELEGRAM_BOT_TOKEN", "CHAT_ID_VIP", "CHAT_ID_FREE", "ODDS_API_KEY"]
for var in required_env_vars:
    if not os.getenv(var):
        logging.error(f"Falta la variable de entorno: {var}")
        raise ValueError(f"Falta la variable de entorno: {var}")

# Configuraciones
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
token_telegram = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id_vip = os.getenv("CHAT_ID_VIP")
chat_id_free = os.getenv("CHAT_ID_FREE")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# Constantes
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_STATS_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_PLAYER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
MLB_TEAM_STATS_URL = "https://statsapi.mlb.com/api/v1/teams/{}/stats"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={}&endDate={}&hydrate=team,linescore,probablePitcher"
MLB_HEAD_TO_HEAD_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&opponentId={}&season={}"
HEADERS = {"User-Agent": "DG Picks"}
MX_TZ = pytz.timezone("America/Mexico_City")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")

# Inicializar base de datos SQLite
conn = sqlite3.connect('picks_history.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS picks (
    date TEXT, partido TEXT, mercado TEXT, pick TEXT, cuota REAL, tipo TEXT, 
    diferencia_carreras REAL, probabilidad REAL, acierto INTEGER, winner TEXT
)''')
conn.commit()

def get_team_era(team_id, start_date=None, end_date=None):
    try:
        if start_date and end_date:
            url = MLB_RESULTS_URL.format(start_date, end_date)
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            data = response.json()
            games = [game for date_info in data.get("dates", []) for game in date_info.get("games", []) 
                     if game["teams"]["home"]["team"]["id"] == team_id or game["teams"]["away"]["team"]["id"] == team_id]
            if not games: return 4.5
            total_era, count = 0, 0
            for game in games[:5]:
                pitcher_id = game["teams"]["home"].get("probablePitcher", {}).get("id") if game["teams"]["home"]["team"]["id"] == team_id else game["teams"]["away"].get("probablePitcher", {}).get("id")
                if pitcher_id:
                    stats = get_pitcher_stats(pitcher_id, team_id)
                    total_era += float(stats.get("era", 4.5))
                    count += 1
            return total_era / count if count > 0 else 4.5
        else:
            url = MLB_TEAM_STATS_URL.format(team_id)
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            data = response.json()
            return float(data["stats"][0]["splits"][0]["stat"].get("era", 4.5))
    except:
        logging.error(f"Error al obtener ERA del equipo ID {team_id}")
        return 4.5

def get_bullpen_era(team_id):
    try:
        url = MLB_TEAM_STATS_URL.format(team_id)
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return float(data["stats"][0]["splits"][0]["stat"].get("bullpen_era", 4.0))
    except:
        logging.error(f"Error al obtener ERA del bullpen del equipo ID {team_id}")
        return 4.0

def get_head_to_head(team_id, opponent_id, season):
    try:
        url = MLB_HEAD_TO_HEAD_URL.format(team_id, opponent_id, season)
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        wins = 0
        games = 0
        for date_info in data.get("dates", []):
            for game in date_info.get("games", []):
                if game.get("status", {}).get("detailedState") != "Final": continue
                home = game["teams"]["home"]
                away = game["teams"]["away"]
                if home["team"]["id"] == team_id and home["score"] > away["score"]:
                    wins += 1
                elif away["team"]["id"] == team_id and away["score"] > home["score"]:
                    wins += 1
                games += 1
        return wins / games if games > 0 else 0.5
    except requests.RequestException as e:
        logging.error(f"Error al obtener enfrentamientos previos: {e}")
        return 0.5

def get_pitcher_stats(pitcher_id, team_id):
    if not pitcher_id:
        return {"era": get_team_era(team_id)}
    try:
        url = MLB_PLAYER_STATS_URL.format(pitcher_id)
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        splits = data.get("people", [{}])[0].get("stats", [{}])[0].get("splits", [])
        return splits[0].get("stat", {"era": get_team_era(team_id)}) if splits else {"era": get_team_era(team_id)}
    except requests.RequestException as e:
        logging.error(f"Error al obtener stats del pitcher ID {pitcher_id}: {e}")
        return {"era": get_team_era(team_id)}

def get_team_form(team_id, start_date, end_date):
    try:
        url = MLB_RESULTS_URL.format(start_date, end_date)
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        resultados = []
        home_wins = 0
        away_wins = 0
        total_games = 0
        for fecha in data.get("dates", []):
            for game in fecha.get("games", []):
                if game.get("status", {}).get("detailedState") != "Final" or team_id not in [game["teams"]["home"]["team"]["id"], game["teams"]["away"]["team"]["id"]]:
                    continue
                home = game["teams"]["home"]
                away = game["teams"]["away"]
                if home["team"]["id"] == team_id:
                    anotadas, recibidas = home["score"], away["score"]
                    if home["score"] > away["score"]:
                        home_wins += 1
                else:
                    anotadas, recibidas = away["score"], home["score"]
                    if away["score"] > home["score"]:
                        away_wins += 1
                resultados.append((anotadas, recibidas))
                total_games += 1
        if not resultados: return {"anotadas": 0, "recibidas": 0, "home_win_rate": 0.5, "away_win_rate": 0.5}
        ultimos = resultados[-5:]
        return {
            "anotadas": round(sum(x[0] for x in ultimos) / len(ultimos), 2),
            "recibidas": round(sum(x[1] for x in ultimos) / len(ultimos), 2),
            "home_win_rate": home_wins / total_games if total_games > 0 else 0.5,
            "away_win_rate": away_wins / total_games if total_games > 0 else 0.5
        }
    except requests.RequestException as e:
        logging.error(f"Error al obtener forma del equipo ID {team_id}: {e}")
        return {"anotadas": 0, "recibidas": 0, "home_win_rate": 0.5, "away_win_rate": 0.5}

def get_team_avg(team_id):
    try:
        response = requests.get(MLB_TEAM_STATS_URL.format(team_id), headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return float(data["stats"][0]["splits"][0]["stat"]["battingAvg"])
    except (requests.RequestException, KeyError, ValueError) as e:
        logging.error(f"Error al obtener promedio de bateo del equipo ID {team_id}: {e}")
        return 0.25

def ajustar_por_era(base, era):
    try:
        era = float(era)
        if era < 2.5:
            return base - 0.7
        elif era < 3.5:
            return base - 0.3
        elif era < 4.5:
            return base
        elif era < 5.5:
            return base + 0.5
        else:
            return base + 0.8
    except ValueError:
        logging.warning(f"Error al convertir ERA a float: {era}, usando valor base")
        return base

def ajustar_por_avg(base, avg):
    try:
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
    except TypeError:
        logging.warning(f"Error con el promedio de bateo: {avg}, usando valor base")
        return base

def get_odds(date=HOY):
    try:
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "decimal",
            "date": date
        }
        response = requests.get(ODDS_API_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        odds_data = response.json()
        logging.info(f"Cuotas obtenidas: {len(odds_data)} eventos")
        return odds_data
    except requests.RequestException as e:
        logging.error(f"Error al obtener cuotas: {e}")
        return []

def generar_mensaje_ia(partido, pick, cuota, linea, estimado, mercado):
    try:
        prompt = f"""Genera un mensaje estilo canal premium de apuestas para Telegram.
Partido: {partido}
Mercado: {mercado}
Pick: {pick} @ {cuota} | Línea: {linea} | Estimado: {estimado}.
No menciones IA ni OpenAI. Termina con '✅ Valor detectado en la cuota'."""
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error al generar mensaje con OpenAI: {e}")
        return f"Partido: {partido}\nMercado: {mercado}\nPick: {pick} @ {cuota} | Línea: {linea} | Estimado: {estimado}\n✅ Valor detectado en la cuota"

def enviar_a_telegram(mensaje, tipo, is_notification=False):
    destino = chat_id_free if is_notification else (chat_id_vip if tipo == "candado" else chat_id_free)
    url = f"https://api.telegram.org/bot{token_telegram}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": destino, "text": mensaje, "parse_mode": "HTML"})
        response.raise_for_status()
        logging.info(f"Mensaje enviado a Telegram ({tipo}): {mensaje[:50]}...")
    except requests.RequestException as e:
        logging.error(f"Error al enviar a Telegram: {e}")

def get_historical_games(start_date, end_date):
    try:
        params = {"sportId": 1, "startDate": start_date, "endDate": end_date, "hydrate": "team,linescore,probablePitcher"}
        response = requests.get(MLB_STATS_BASE_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        games = []
        for date_info in data.get("dates", []):
            for game in date_info.get("games", []):
                if game.get("status", {}).get("detailedState") != "Final": continue
                home = game["teams"]["home"]
                away = game["teams"]["away"]
                winner = home["team"]["name"] if home["score"] > away["score"] else away["team"]["name"]
                games.append({
                    "date": date_info["date"],
                    "home_team": home["team"]["name"],
                    "away_team": away["team"]["name"],
                    "home_team_id": home["team"]["id"],
                    "away_team_id": away["team"]["id"],
                    "home_pitcher_id": home.get("probablePitcher", {}).get("id"),
                    "away_pitcher_id": away.get("probablePitcher", {}).get("id"),
                    "home_score": home["score"],
                    "away_score": away["score"],
                    "winner": winner
                })
        return games
    except requests.RequestException as e:
        logging.error(f"Error al obtener juegos históricos: {e}")
        return []

def optimize_thresholds(results):
    thresholds = [1.5, 1.7, 1.9, 2.0, 2.3, 2.5, 2.7, 3.0]
    best_threshold = 1.7
    best_candado = 2.7
    best_accuracy = 0
    for t in thresholds:
        for c in thresholds:
            if c <= t: continue
            correct = 0
            total = 0
            for r in results:
                if abs(r["diferencia_carreras"]) >= t:
                    total += 1
                    if r["acierto"]:
                        correct += 1
            accuracy = (correct / total * 100) if total > 0 else 0
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_threshold = t
                best_candado = c
    return best_threshold, best_candado, best_accuracy

def validate_historical_picks():
    end_date = datetime.now(MX_TZ) - timedelta(days=1)
    start_date = end_date - timedelta(days=30)
    games = get_historical_games(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    season = start_date.strftime("%Y")
    
    results = []
    total_profit = 0
    for game in games:
        home = game["home_team"]
        away = game["away_team"]
        partido = f"{away} vs {home}"
        date = game["date"]
        form_home = get_team_form(game["home_team_id"], (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d"), date)
        form_away = get_team_form(game["away_team_id"], (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d"), date)
        avg_home = get_team_avg(game["home_team_id"])
        avg_away = get_team_avg(game["away_team_id"])
        era_home = float(get_pitcher_stats(game["home_pitcher_id"], game["home_team_id"]).get("era", 4.5))
        era_away = float(get_pitcher_stats(game["away_pitcher_id"], game["away_team_id"]).get("era", 4.5))
        bullpen_era_home = get_bullpen_era(game["home_team_id"])
        bullpen_era_away = get_bullpen_era(game["away_team_id"])
        head_to_head = get_head_to_head(game["home_team_id"], game["away_team_id"], season)

        ajustado_home = ajustar_por_avg(ajustar_por_era(form_home["anotadas"], era_away), avg_home)
        ajustado_away = ajustar_por_avg(ajustar_por_era(form_away["anotadas"], era_home), avg_away)
        ajustado_home += (bullpen_era_away - bullpen_era_home) * 0.1
        ajustado_away += (bullpen_era_home - bullpen_era_away) * 0.1
        diferencia_carreras = ajustado_home - ajustado_away
        diferencia_carreras += (form_home["home_win_rate"] - form_away["away_win_rate"]) * 0.5
        diferencia_carreras += (head_to_head - 0.5) * 0.3
        probabilidad = max(10, min(90, 50 + (diferencia_carreras * 10)))

        pick = None
        tipo = None
        cuota = 1.8
        odds = get_odds(date)
        for odd in odds:
            if (game["home_team_id"] == odd.get("home_team_id", 0) or 
                game["away_team_id"] == odd.get("away_team_id", 0) or
                (home.lower() == odd.get("home_team", "").lower() and 
                 away.lower() == odd.get("away_team", "").lower())):
                for market in odd.get("bookmakers", [{}])[0].get("markets", []):
                    if market["key"] == "h2h":
                        best_odds = max(
                            (outcome for bookmaker in odd["bookmakers"] for outcome in bookmaker.get("markets", []) 
                             if bookmaker["markets"][0]["key"] == "h2h" for outcome in bookmaker["markets"][0]["outcomes"]),
                            key=lambda x: x["price"]
                        )
                        pick_team = home if diferencia_carreras > 0 else away
                        cuota = next((o["price"] for o in market["outcomes"] if o["name"] == pick_team), 1.8)

        if abs(diferencia_carreras) >= 1.7:
            pick = home if diferencia_carreras > 0 else away
            tipo = "candado" if abs(diferencia_carreras) >= 2.7 else "normal"
        
        if pick:
            acierto = pick == game["winner"]
            profit = (cuota - 1) if acierto else -1
            total_profit += profit
            results.append({
                "date": date,
                "partido": partido,
                "pick": pick,
                "tipo": tipo,
                "diferencia_carreras": diferencia_carreras,
                "probabilidad": probabilidad,
                "acierto": acierto,
                "winner": game["winner"],
                "cuota": cuota,
                "profit": profit
            })
            cursor.execute('''INSERT INTO picks (date, partido, mercado, pick, cuota, tipo, diferencia_carreras, probabilidad, acierto, winner)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (date, partido, "Moneyline", pick, cuota, tipo, diferencia_carreras, probabilidad, int(acierto), game["winner"]))
            conn.commit()
            logging.info(f"Validación: {partido} | Pick: {pick} ({tipo}) | Dif: {diferencia_carreras:.2f} | Prob: {probabilidad:.1f}% | Acierto: {acierto} | Cuota: {cuota:.2f} | Profit: {profit:.2f}")

    if results:
        aciertos = sum(1 for r in results if r["acierto"])
        tasa_aciertos = (aciertos / len(results)) * 100
        roi = (total_profit / len(results)) * 100
        best_threshold, best_candado, best_accuracy = optimize_thresholds(results)
        logging.info(f"Tasa de aciertos (Moneyline): {tasa_aciertos:.1f}% ({aciertos}/{len(results)})")
        logging.info(f"ROI: {roi:.1f}% | Total Profit: {total_profit:.2f}")
        logging.info(f"Mejor umbral: {best_threshold:.1f} (normal), {best_candado:.1f} (candado) | Accuracy: {best_accuracy:.1f}%")
        return best_threshold, best_candado, tasa_aciertos, roi
    return 1.7, 2.7, 0, 0

def main():
    try:
        logging.info("🔍 Ejecutando DG Picks MLB completo")

        # Prueba de conexión a Telegram
        mensaje_prueba = f"🔔 Prueba de conexión a Telegram a las {datetime.now(MX_TZ).strftime('%H:%M %d/%m/%Y')}"
        enviar_a_telegram(mensaje_prueba, "prueba", is_notification=True)

        # Validar modelo con datos históricos
        best_threshold, best_candado, tasa_aciertos, roi = validate_historical_picks()
        logging.info(f"Validación histórica completada. Tasa de aciertos: {tasa_aciertos:.1f}% | ROI: {roi:.1f}%")
        logging.info(f"Umbrales ajustados: normal={best_threshold:.1f}, candado={best_candado:.1f}")

        # Obtener juegos de hoy
        params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher"}
        response = requests.get(MLB_STATS_BASE_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        logging.info(f"Datos de MLB API: {data}")
        juegos = []
        for date_info in data.get("dates", []):
            for game in date_info.get("games", []):
                home_pitcher = game["teams"]["home"].get("probablePitcher", {})
                away_pitcher = game["teams"]["away"].get("probablePitcher", {})
                juegos.append({
                    "home_team": game["teams"]["home"]["team"]["name"],
                    "away_team": game["teams"]["away"]["team"]["name"],
                    "home_pitcher_id": home_pitcher.get("id"),
                    "away_pitcher_id": away_pitcher.get("id"),
                    "home_team_id": game["teams"]["home"]["team"]["id"],
                    "away_team_id": game["teams"]["away"]["team"]["id"]
                })
        logging.info(f"Juegos detectados para hoy: {len(juegos)}")
        for juego in juegos:
            logging.info(f"Juego: {juego['away_team']} vs {juego['home_team']}")

        odds = get_odds()
        picks_enviados = {"h2h": 0, "spreads": 0, "totals": 0}
        picks = {"h2h": [], "spreads": [], "totals": []}

        season = datetime.now(MX_TZ).strftime("%Y")
        for juego in juegos:
            home = juego["home_team"]
            away = juego["away_team"]
            partido = f"{away} vs {home}"
            form_home = get_team_form(juego["home_team_id"], (datetime.now(MX_TZ) - timedelta(days=10)).strftime("%Y-%m-%d"), HOY)
            form_away = get_team_form(juego["away_team_id"], (datetime.now(MX_TZ) - timedelta(days=10)).strftime("%Y-%m-%d"), HOY)
            avg_home = get_team_avg(juego["home_team_id"])
            avg_away = get_team_avg(juego["away_team_id"])
            era_home = float(get_pitcher_stats(juego["home_pitcher_id"], juego["home_team_id"]).get("era", 4.5))
            era_away = float(get_pitcher_stats(juego["away_pitcher_id"], juego["away_team_id"]).get("era", 4.5))
            bullpen_era_home = get_bullpen_era(juego["home_team_id"])
            bullpen_era_away = get_bullpen_era(juego["away_team_id"])
            head_to_head = get_head_to_head(juego["home_team_id"], juego["away_team_id"], season)

            ajustado_home = ajustar_por_avg(ajustar_por_era(form_home["anotadas"], era_away), avg_home)
            ajustado_away = ajustar_por_avg(ajustar_por_era(form_away["anotadas"], era_home), avg_away)
            ajustado_home += (bullpen_era_away - bullpen_era_home) * 0.1
            ajustado_away += (bullpen_era_home - bullpen_era_away) * 0.1
            estimado_total = round((ajustado_home + ajustado_away + form_home["recibidas"] + form_away["recibidas"]) / 2, 2)
            diferencia_carreras = ajustado_home - ajustado_away
            diferencia_carreras += (form_home["home_win_rate"] - form_away["away_win_rate"]) * 0.5
            diferencia_carreras += (head_to_head - 0.5) * 0.3
            probabilidad = max(10, min(90, 50 + (diferencia_carreras * 10)))

            logging.info(f"Juego: {partido}, Ajustado Home: {ajustado_home}, Ajustado Away: {ajustado_away}, Estimado Total: {estimado_total}, Dif Carreras: {diferencia_carreras}, Prob: {probabilidad:.1f}%")

            for odd in odds:
                if (juego["home_team_id"] == odd.get("home_team_id", 0) or 
                    juego["away_team_id"] == odd.get("away_team_id", 0) or
                    (home.lower() == odd.get("home_team", "").lower() and 
                     away.lower() == odd.get("away_team", "").lower())):
                    
                    for market in odd.get("bookmakers", [{}])[0].get("markets", []):
                        if market["key"] == "totals" and picks_enviados["totals"] < 3:
                            best_odds = max(
                                (outcome for bookmaker in odd["bookmakers"] for outcome in bookmaker["markets"][0]["outcomes"]),
                                key=lambda x: x["price"] if x["name"].lower() == "over" else -x["price"]
                            )
                            linea = best_odds["point"]
                            cuota = best_odds["price"]
                            diferencia = estimado_total - linea
                            if abs(diferencia) >= 2:
                                tipo = "candado" if abs(diferencia) >= 3 else "normal"
                                pick = "Over" if diferencia > 0 else "Under"
                                picks["totals"].append((partido, f"{pick} {linea}", cuota, linea, f"{estimado_total} carreras", "Totals", tipo, probabilidad))
                                logging.info(f"Pick Totals generado: {pick} {linea} @ {cuota} | {partido}")

                        if market["key"] == "h2h" and picks_enviados["h2h"] < 2:
                            best_odds = max(
                                (outcome for bookmaker in odd["bookmakers"] for outcome in bookmaker.get("markets", []) 
                                 if bookmaker["markets"][0]["key"] == "h2h" for outcome in bookmaker["markets"][0]["outcomes"]),
                                key=lambda x: x["price"]
                            )
                            if abs(diferencia_carreras) >= best_threshold:
                                pick = home if diferencia_carreras > 0 else away
                                cuota = next((o["price"] for o in market["outcomes"] if o["name"] == pick), 1.0)
                                tipo = "candado" if abs(diferencia_carreras) >= best_candado else "normal"
                                picks["h2h"].append((partido, f"{pick}", cuota, "N/A", f"{diferencia_carreras:+.2f} carreras ventaja | Prob: {probabilidad:.1f}%", "Moneyline", tipo, probabilidad))
                                logging.info(f"Pick Moneyline generado: {pick} @ {cuota} | {partido}")

                        if market["key"] == "spreads" and picks_enviados["spreads"] < 2:
                            best_odds = max(
                                (outcome for bookmaker in odd["bookmakers"] for outcome in bookmaker.get("markets", []) 
                                 if bookmaker["markets"][0]["key"] == "spreads" for outcome in bookmaker["markets"][0]["outcomes"]),
                                key=lambda x: x["price"]
                            )
                            linea = best_odds["point"]
                            cuota = best_odds["price"]
                            pick_team = home if diferencia_carreras > 0 else away
                            if abs(diferencia_carreras) >= 2:
                                tipo = "candado" if abs(diferencia_carreras) >= 3 else "normal"
                                pick = f"{pick_team} {linea:+.1f}"
                                picks["spreads"].append((partido, pick, cuota, linea, f"{diferencia_carreras:+.2f} carreras ventaja | Prob: {probabilidad:.1f}%", "Run Line", tipo, probabilidad))
                                logging.info(f"Pick Run Line generado: {pick} @ {cuota} | {partido}")

        # Enviar los picks con mayor probabilidad
        for market in picks:
            picks[market].sort(key=lambda x: x[7], reverse=True)
            for pick in picks[market][:2]:
                partido, pick_text, cuota, linea, estimado, mercado, tipo, prob = pick
                mensaje = generar_mensaje_ia(partido, pick_text, cuota, linea, estimado, mercado)
                enviar_a_telegram(mensaje, tipo)
                logging.info(f"Pick {mercado}: {pick_text} @ {cuota} ({tipo}) | {partido} | Prob: {prob:.1f}%")
                picks_enviados[market] += 1

        # Notificación de éxito
        total_picks = sum(picks_enviados.values())
        mensaje_exito = f"✅ Script ejecutado con éxito a las {datetime.now(MX_TZ).strftime('%H:%M %d/%m/%Y')}\nPicks enviados: {total_picks} (Moneyline: {picks_enviados['h2h']}, Run Line: {picks_enviados['spreads']}, Totals: {picks_enviados['totals']})"
        enviar_a_telegram(mensaje_exito, "notificación", is_notification=True)

    except Exception as e:
        mensaje_error = f"❌ Error en el script a las {datetime.now(MX_TZ).strftime('%H:%M %d/%m/%Y')}\nError: {str(e)}"
        enviar_a_telegram(mensaje_error, "notificación", is_notification=True)
        logging.error(f"Error en main: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
