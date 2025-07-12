import requests
import os
import pytz
from datetime import datetime
import logging
import csv
from collections import defaultdict
from fuzzywuzzy import fuzz
from telegram import Bot
import asyncio

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Zona horaria y fecha
MX_TZ = pytz.timezone("America/Mexico_City")
ES_TZ = pytz.timezone("Europe/Madrid")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")

# URLs y headers
MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate=2025-03-28&endDate={}"
PITCHER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
HEADERS = {"User-Agent": "DG Picks"}

# Factores de ajuste por estadio
VENUE_FACTOR = {
    "Coors Field": 1.2,
    "Fenway Park": 1.1,
    "Yankee Stadium": 1.05,
    "Dodger Stadium": 0.95,
    "Oracle Park": 0.9
}

LEAGUE_AVG = {"anotadas": 4.5, "recibidas": 4.5, "era": 4.0}
CACHE = defaultdict(dict)

def get_today_games():
    try:
        params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher,venue"}
        res = requests.get(MLB_SCHEDULE_URL, headers=HEADERS, params=params, timeout=10)
        res.raise_for_status()
        games = []
        for date_info in res.json().get("dates", []):
            for g in date_info.get("games", []):
                try:
                    hora_utc = datetime.strptime(g["gameDate"], "%Y-%m-%dT%H:%M:%SZ")
                    games.append({
                        "home": g["teams"]["home"]["team"]["name"],
                        "team_id": g["teams"]["home"]["team"]["id"],
                        "away": g["teams"]["away"]["team"]["name"],
                        "away_id": g["teams"]["away"]["team"]["id"],
                        "pitcher_home": g["teams"]["home"].get("probablePitcher", {}).get("id"),
                        "pitcher_away": g["teams"]["away"].get("probablePitcher", {}).get("id"),
                        "venue": g["venue"]["name"],
                        "hora_mx": hora_utc.astimezone(MX_TZ).strftime("%H:%M"),
                        "hora_es": hora_utc.astimezone(ES_TZ).strftime("%H:%M")
                    })
                except (KeyError, ValueError) as e:
                    logger.warning(f"Error al procesar juego: {e}")
                    continue
        return games
    except requests.RequestException as e:
        logger.error(f"Error al obtener juegos: {e}")
        return []

def get_form(team_id):
    if team_id in CACHE["form"]:
        return CACHE["form"][team_id]
    try:
        url = MLB_RESULTS_URL.format(team_id, HOY)
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        juegos = []
        for d in res.json().get("dates", []):
            for g in d.get("games", []):
                if g["status"]["detailedState"] != "Final":
                    continue
                home, away = g["teams"]["home"], g["teams"]["away"]
                try:
                    if home["team"]["id"] == team_id:
                        anotadas, recibidas = home["score"], away["score"]
                    else:
                        anotadas, recibidas = away["score"], home["score"]
                    juegos.append((anotadas, recibidas))
                except KeyError:
                    logger.warning(f"Datos incompletos para juego del equipo {team_id}")
                    continue
        if not juegos:
            logger.info(f"No hay juegos previos para equipo {team_id}, usando promedio de liga")
            return LEAGUE_AVG
        form = {
            "anotadas": round(sum(j[0] for j in juegos) / len(juegos), 2),
            "recibidas": round(sum(j[1] for j in juegos) / len(juegos), 2)
        }
        CACHE["form"][team_id] = form
        return form
    except requests.RequestException as e:
        logger.error(f"Error al obtener forma del equipo {team_id}: {e}")
        return LEAGUE_AVG

def get_pitcher(pitcher_id):
    if not pitcher_id:
        return {"era": LEAGUE_AVG["era"], "nombre": "Desconocido"}
    if pitcher_id in CACHE["pitcher"]:
        return CACHE["pitcher"][pitcher_id]
    try:
        res = requests.get(PITCHER_STATS_URL.format(pitcher_id), headers=HEADERS, timeout=10)
        res.raise_for_status()
        data = res.json().get("people", [{}])[0]
        stats = data.get("stats", [{}])[0].get("splits", [])
        era = float(stats[0]["stat"].get("era", LEAGUE_AVG["era"])) if stats else LEAGUE_AVG["era"]
        pitcher = {"era": era, "nombre": data.get("fullName", "Desconocido")}
        CACHE["pitcher"][pitcher_id] = pitcher
        return pitcher
    except (requests.RequestException, KeyError, ValueError) as e:
        logger.error(f"Error al obtener datos del pitcher {pitcher_id}: {e}")
        return {"era": LEAGUE_AVG["era"], "nombre": "Desconocido"}

def get_odds_totals():
    if not os.getenv("ODDS_API_KEY"):
        logger.error("ODDS_API_KEY no está configurada")
        return []
    try:
        params = {
            "apiKey": os.getenv("ODDS_API_KEY"),
            "regions": "us",
            "markets": "totals",
            "oddsFormat": "decimal"
        }
        res = requests.get(ODDS_API_URL, params=params, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        logger.error(f"Error al obtener cuotas de totales: {e}")
        return []

def find_total_market(home, away, odds_data):
    def normalize(name):
        return name.lower().replace(" ", "")
    best_odds = None
    best_price = 0
    for game in odds_data:
        h = normalize(game["home_team"])
        a = normalize(game["away_team"])
        if fuzz.ratio(normalize(home), h) > 85 and fuzz.ratio(normalize(away), a) > 85:
            for bookmaker in game["bookmakers"]:
                for market in bookmaker["markets"]:
                    if market["key"] == "totals":
                        for outcome in market["outcomes"]:
                            if outcome["price"] > best_price:
                                best_odds = market["outcomes"]
                                best_price = outcome["price"]
    return best_odds

def sugerir_totales(games):
    odds_data = get_odds_totals()
    sugerencias = []
    for j in games:
        try:
            home, away = j["home"], j["away"]
            form_home = get_form(j["home_id"])
            form_away = get_form(j["away_id"])
            p_home = get_pitcher(j["pitcher_home"])
            p_away = get_pitcher(j["pitcher_away"])
            venue_factor = VENUE_FACTOR.get(j["venue"], 1.0)

            total_est = round(((form_home["anotadas"] + form_away["recibidas"] + 
                               form_away["anotadas"] + form_home["recibidas"]) / 2) * venue_factor, 2)
            avg_era = round((p_home["era"] + p_away["era"]) / 2, 2)
            market = find_total_market(home, away, odds_data)

            if market:
                for o in market:
                    line = o.get("point")
                    odds = o.get("price")
                    tipo = o.get("name")
                    if line and odds and tipo:
                        confidence = abs(total_est - line) / line
                        if (tipo == "Over" and total_est > line) or (tipo == "Under" and total_est < line):
                            sugerencias.append({
                                "tipo": tipo.upper(),
                                "msg": f"{away} vs {home} – {tipo} {line} sugerido | Cuota: {odds} | Estimado: {total_est} | ERA: {avg_era} | Confianza: {confidence:.2%}",
                                "data": {
                                    "juego": f"{away} vs {home}",
                                    "tipo": tipo.upper(),
                                    "linea": line,
                                    "cuota": odds,
                                    "estimado": total_est,
                                    "avg_era": avg_era,
                                    "confidence": confidence,
                                    "venue": j["venue"],
                                    "hora_mx": j["hora_mx"],
                                    "hora_es": j["hora_es"],
                                    "pitcher_home": p_home["nombre"],
                                    "pitcher_away": p_away["nombre"]
                                }
                            })
        except Exception as e:
            logger.warning(f"Error al procesar sugerencia para {j['away']} vs {j['home']}: {e}")
            continue
    return sugerencias

def export_to_csv(sugerencias):
    if not sugerencias:
        return
    filename = f"mlb_recomendaciones_{HOY}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["juego", "tipo", "linea", "cuota", "estimado", "avg_era", "confidence", "venue", "hora_mx", "hora_es", "pitcher_home", "pitcher_away"])
        writer.writeheader()
        for s in sugerencias:
            writer.writerow(s["data"])
    logger.info(f"Recomendaciones exportadas a {filename}")

async def enviar_mensaje(mensaje: str, chat_id: str):
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        logger.error("TELEGRAM_BOT_TOKEN no está configurada")
        return
    try:
        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        await bot.send_message(chat_id=chat_id, text=mensaje, parse_mode="Markdown")
        logger.info(f"Mensaje enviado a Telegram: {chat_id}")
    except Exception as e:
        logger.error(f"Error al enviar mensaje a Telegram: {e}")

if __name__ == "__main__":
    logger.info(f"Evaluando Over/Under con cuotas reales – {HOY}")
    juegos = get_today_games()
    chat_id = os.getenv("CHAT_ID_BOT")
    if not juegos:
        logger.warning("No se encontraron juegos para hoy.")
        print("⚠️ No se encontraron juegos para hoy.")
        if chat_id:
            asyncio.run(enviar_mensaje(f"⚠️ *No se encontraron juegos para MLB – {HOY}*", chat_id))
    else:
        recomendaciones = sugerir_totales(juegos)
        if recomendaciones:
            for r in recomendaciones:
                print(r["msg"])
            export_to_csv(recomendaciones)
            if chat_id:
                resumen = f"📊 *Over/Under MLB – {HOY}*\n\n" + "\n".join(f"🔹 {r['msg']}" for r in recomendaciones)
                asyncio.run(enviar_mensaje(resumen, chat_id))
        else:
            print("⚠️ No se detectaron partidos con valor para Over/Under hoy.")
            if chat_id:
                asyncio.run(enviar_mensaje(f"⚠️ *No se detectaron partidos con valor para Over/Under – {HOY}*", chat_id))