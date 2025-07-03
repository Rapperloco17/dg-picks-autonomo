import requests
import os
import asyncio
import logging
import pytz
import hashlib
import json
from datetime import datetime
from telegram import Bot
from fuzzywuzzy import fuzz

# Configuración
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DG Picks")
MX_TZ = pytz.timezone("America/Mexico_City")
ES_TZ = pytz.timezone("Europe/Madrid")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")
FECHA_TEXTO = datetime.now(MX_TZ).strftime("%d de %B")

# Parámetros
PICK_THRESHOLDS = {
    "low_odds": {"max_odds": 1.70, "min_runs": 4.0, "max_era": 3.5, "label": "Valor medio"},
    "mid_odds": {"min_odds": 1.70, "max_odds": 2.30, "min_runs": 4.0, "max_era": 4.2, "label": "Valor sólido"},
    "high_odds": {"min_odds": 2.30, "min_runs": 4.5, "max_era": 4.5, "label": "Underdog con ataque"}
}
WEIGHTS = {"era": 0.3, "runs": 0.3, "form": 0.2, "streak": 0.1, "recent": 0.1}

# APIs
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate=2025-03-28&endDate={}"
PITCHER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
HEADERS = {"User-Agent": "DG Picks"}

# =================== FUNCIONES PRINCIPALES ===================

def get_today_games():
    try:
        res = requests.get(MLB_SCHEDULE_URL, headers=HEADERS, params={"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher,venue"}, timeout=10)
        res.raise_for_status()
        games = []
        for d in res.json().get("dates", []):
            for g in d.get("games", []):
                dt = datetime.strptime(g["gameDate"], "%Y-%m-%dT%H:%M:%SZ")
                games.append({
                    "home": g["teams"]["home"]["team"]["name"],
                    "away": g["teams"]["away"]["team"]["name"],
                    "home_id": g["teams"]["home"]["team"]["id"],
                    "away_id": g["teams"]["away"]["team"]["id"],
                    "pitcher_home": g["teams"]["home"].get("probablePitcher", {}).get("id"),
                    "pitcher_away": g["teams"]["away"].get("probablePitcher", {}).get("id"),
                    "venue": g["venue"]["name"],
                    "hora_mx": dt.astimezone(MX_TZ).strftime("%H:%M"),
                    "hora_es": dt.astimezone(ES_TZ).strftime("%H:%M")
                })
        return games
    except Exception as e:
        logger.error(f"Error al obtener partidos: {e}")
        return []

def get_odds():
    try:
        res = requests.get(ODDS_API_URL, headers=HEADERS, params={
            "apiKey": os.getenv("ODDS_API_KEY"),
            "regions": "us",
            "markets": "spreads",
            "oddsFormat": "decimal"
        }, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logger.error(f"Error al obtener cuotas: {e}")
        return []

def get_pitcher(pitcher_id):
    if not pitcher_id:
        return {"era": 99.0, "nombre": "Desconocido"}
    try:
        res = requests.get(PITCHER_STATS_URL.format(pitcher_id), headers=HEADERS, timeout=10)
        res.raise_for_status()
        data = res.json()["people"][0]
        stats = data.get("stats", [{}])[0].get("splits", [])
        era = float(stats[0]["stat"]["era"]) if stats else 99.0
        return {"era": era, "nombre": data.get("fullName", "Desconocido")}
    except Exception as e:
        logger.error(f"Error con pitcher {pitcher_id}: {e}")
        return {"era": 99.0, "nombre": "Desconocido"}

def get_recent_form(team_id, limit=10):
    try:
        url = MLB_RESULTS_URL.format(team_id, HOY)
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        juegos, wins = [], 0
        for d in res.json().get("dates", [])[::-1]:
            for g in d.get("games", [])[::-1]:
                if g["status"]["detailedState"] != "Final":
                    continue
                home = g["teams"]["home"]
                away = g["teams"]["away"]
                is_home = home["team"]["id"] == team_id
                anotadas = home["score"] if is_home else away["score"]
                recibidas = away["score"] if is_home else home["score"]
                wins += int(anotadas > recibidas)
                juegos.append((anotadas, recibidas))
                if len(juegos) >= limit:
                    break
            if len(juegos) >= limit:
                break
        if not juegos:
            return {"anotadas": 4.0, "recibidas": 4.0, "streak": 0, "recent_avg": 4.0}
        return {
            "anotadas": round(sum(j[0] for j in juegos) / len(juegos), 2),
            "recibidas": round(sum(j[1] for j in juegos) / len(juegos), 2),
            "streak": wins - (limit - wins),
            "recent_avg": round(sum(j[0] for j in juegos[-5:]) / min(5, len(juegos)), 2)
        }
    except Exception as e:
        logger.error(f"Error en get_recent_form: {e}")
        return {"anotadas": 4.0, "recibidas": 4.0, "streak": 0, "recent_avg": 4.0}

def calcular_puntaje(form, pitcher, cuota):
    return (
        WEIGHTS["era"] * max(0, 5 - pitcher["era"]) / 5 +
        WEIGHTS["runs"] * min(form["anotadas"] / 6, 1) +
        WEIGHTS["form"] * max(0, (form["anotadas"] - form["recibidas"]) / 10) +
        WEIGHTS["streak"] * max(-1, min(form["streak"], 5)) / 5 +
        WEIGHTS["recent"] * min(form["recent_avg"] / 6, 1)
    ) / cuota

def find_matching_team(team_name, odds_data):
    team_name = team_name.lower().replace(" ", "")
    for game in odds_data:
        home = game["home_team"].lower().replace(" ", "")
        away = game["away_team"].lower().replace(" ", "")
        if fuzz.ratio(team_name, home) > 85 or fuzz.ratio(team_name, away) > 85:
            return game
    return None

def sugerir_picks():
    cuotas = get_odds()
    juegos = get_today_games()
    picks = []
    for j in juegos:
        home, away = j["home"], j["away"]
        odds = find_matching_team(home, cuotas)
        if not odds:
            continue

        spreads = {}
        for b in odds["bookmakers"]:
            for m in b["markets"]:
                if m["key"] == "spreads":
                    for o in m["outcomes"]:
                        if abs(o.get("point", 0)) == 1.5:
                            spreads[o["name"]] = o["price"]

        for team, team_id, pitcher_id in [(home, j["home_id"], j["pitcher_home"]), (away, j["away_id"], j["pitcher_away"])]:
            if team not in spreads:
                continue
            cuota = spreads[team]
            pitcher = get_pitcher(pitcher_id)
            form = get_recent_form(team_id)
            puntaje = calcular_puntaje(form, pitcher, cuota)

            base_msg = (
                f"⚾️ {away} vs {home}\n📍 {j['venue']}\n🕒 {j['hora_mx']} MX / {j['hora_es']} ES\n"
                f"👤 {pitcher['nombre']} (ERA {pitcher['era']})\n"
                f"📊 {form['anotadas']} carreras/juego – Racha: {'+' if form['streak'] > 0 else ''}{form['streak']}"
            )

            for threshold in PICK_THRESHOLDS.values():
                if threshold.get("min_odds", 0) <= cuota <= threshold.get("max_odds", 999) and form["anotadas"] >= threshold["min_runs"] and pitcher["era"] <= threshold["max_era"]:
                    picks.append({"msg": f"{base_msg}\n🎯 Pick: {team} RL (-1.5/+1.5) @ {cuota} — {threshold['label']} (Puntaje: {puntaje:.2f})", "puntaje": puntaje})
                    break
    return picks

async def enviar_mensaje(msg: str, chat_id: str):
    try:
        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        await bot.send_message(chat_id=chat_id, text=msg)
    except Exception as e:
        logger.error(f"Telegram error: {e}")

async def main():
    picks = sugerir_picks()
    if not picks:
        await enviar_mensaje("⚠️ No se detectaron picks con valor hoy", os.getenv("CHAT_ID_BOT"))
        return

    picks.sort(key=lambda x: x["puntaje"], reverse=True)
    top = picks[0]
    vip = picks[:3]
    resumen = "\n\n".join(p["msg"] for p in vip)

    await enviar_mensaje(f"🏆 Pick Reto Escalera:\n\n{top['msg']}", os.getenv("chat_id_reto"))
    await enviar_mensaje(f"🔥 Picks VIP – {FECHA_TEXTO}\n\n{resumen}", os.getenv("CHAT_ID_VIP"))
    await enviar_mensaje(f"📊 Picks Run Line Completos – {FECHA_TEXTO}\n\n" + "\n\n".join(p['msg'] for p in picks), os.getenv("CHAT_ID_BOT"))

if __name__ == "__main__":
    if os.getenv("ODDS_API_KEY") and os.getenv("TELEGRAM_BOT_TOKEN"):
        asyncio.run(main())
    else:
        logger.error("Faltan variables de entorno necesarias.")
