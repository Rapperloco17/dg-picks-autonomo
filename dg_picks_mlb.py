
# dg_picks_mlb.py (versión actualizada con envío al bot y VIP, sin canal Free)

import requests
import openai
import os
import asyncio
import logging
import pytz
import json
import hashlib
from datetime import datetime
from telegram import Bot
from fuzzywuzzy import fuzz
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MX_TZ = pytz.timezone("America/Mexico_City")
ES_TZ = pytz.timezone("Europe/Madrid")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")
FECHA_TEXTO = datetime.now(MX_TZ).strftime("%d de %B")

PICK_THRESHOLDS = {
    "low_odds": {"max_odds": 1.70, "min_runs": 4.0, "max_era": 3.5, "label": "Valor medio"},
    "mid_odds": {"min_odds": 1.70, "max_odds": 2.30, "min_runs": 4.0, "max_era": 4.2, "label": "Valor sólido"},
    "high_odds": {"min_odds": 2.30, "min_runs": 4.5, "max_era": 4.5, "label": "Underdog con ataque"}
}

ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate=2025-03-28&endDate={}"
PITCHER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
HEADERS = {"User-Agent": "DG Picks"}

def normalize(name): return name.lower().replace(" ", "").replace("-", "")

def find_matching_team(team_name, odds_data):
    team_name_norm = normalize(team_name)
    for odds in odds_data:
        if fuzz.ratio(team_name_norm, normalize(odds["home_team"])) > 85 or            fuzz.ratio(team_name_norm, normalize(odds["away_team"])) > 85:
            return odds
    return None

def get_today_games():
    params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher,venue"}
    res = requests.get(MLB_SCHEDULE_URL, headers=HEADERS, params=params, timeout=10)
    res.raise_for_status()
    data = res.json()
    games = []
    for date_info in data.get("dates", []):
        for g in date_info.get("games", []):
            game_date_utc = datetime.strptime(g["gameDate"], "%Y-%m-%dT%H:%M:%SZ")
            hora_mx = game_date_utc.replace(tzinfo=pytz.utc).astimezone(MX_TZ).strftime("%H:%M")
            hora_es = game_date_utc.replace(tzinfo=pytz.utc).astimezone(ES_TZ).strftime("%H:%M")
            games.append({
                "home": g["teams"]["home"]["team"]["name"],
                "away": g["teams"]["away"]["team"]["name"],
                "home_id": g["teams"]["home"]["team"]["id"],
                "away_id": g["teams"]["away"]["team"]["id"],
                "pitcher_home": g["teams"]["home"].get("probablePitcher", {}).get("id"),
                "pitcher_away": g["teams"]["away"].get("probablePitcher", {}).get("id"),
                "venue": g["venue"]["name"],
                "hora_mx": hora_mx,
                "hora_es": hora_es
            })
    return games

def get_pitcher_stats(pitcher_id):
    if not pitcher_id: return {"era": 99.0, "nombre": "No confirmado"}
    url = PITCHER_STATS_URL.format(pitcher_id)
    res = requests.get(url, headers=HEADERS, timeout=10)
    data = res.json()
    person = data.get("people", [])[0]
    nombre = person.get("fullName", "No confirmado")
    stats = person.get("stats", [])[0].get("splits", [])
    era = stats[0].get("stat", {}).get("era", 99.0) if stats else 99.0
    return {"era": float(era), "nombre": nombre}

def get_full_season_form(team_id):
    url = MLB_RESULTS_URL.format(team_id, HOY)
    res = requests.get(url, headers=HEADERS, timeout=15)
    juegos = []
    for d in res.json().get("dates", []):
        for g in d.get("games", []):
            if g["status"]["detailedState"] != "Final":
                continue
            home, away = g["teams"]["home"], g["teams"]["away"]
            if home["team"]["id"] == team_id:
                anotadas, recibidas = home["score"], away["score"]
            else:
                anotadas, recibidas = away["score"], home["score"]
            juegos.append((anotadas, recibidas))
    if not juegos: return {"anotadas": 4.0, "recibidas": 4.0}
    return {
        "anotadas": round(sum(j[0] for j in juegos) / len(juegos), 2),
        "recibidas": round(sum(j[1] for j in juegos) / len(juegos), 2)
    }

def get_odds():
    key = os.getenv("ODDS_API_KEY")
    params = {"apiKey": key, "regions": "us", "markets": "h2h", "oddsFormat": "decimal"}
    res = requests.get(ODDS_API_URL, headers=HEADERS, params=params, timeout=10)
    return res.json()

def sugerir_pick(team, form, pitcher, odds, rival, venue, hora_mx, hora_es):
    for t in PICK_THRESHOLDS.values():
        if (t.get("min_odds", 0) <= odds <= t.get("max_odds", 99)) and            form["anotadas"] >= t["min_runs"] and pitcher["era"] < t["max_era"]:
            return {
                "msg": f"⚾ {team} vs {rival}
📍 Estadio: {venue}
🕒 {hora_mx} 🇲🇽 / {hora_es} 🇪🇸
👤 Pitcher: {pitcher['nombre']} (ERA {pitcher['era']})
🎯 Pick: {team} ML @ {odds} — {t['label']}: {form['anotadas']} carreras/j",
                "odds": odds
            }
    return None

async def enviar_telegram_async(mensaje: str, chat_id: str):
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    await bot.send_message(chat_id=chat_id, text=mensaje)

async def main():
    juegos = get_today_games()
    cuotas = get_odds()
    picks_all = []

    for g in juegos:
        form_home = get_full_season_form(g["home_id"])
        form_away = get_full_season_form(g["away_id"])
        pitcher_home = get_pitcher_stats(g["pitcher_home"])
        pitcher_away = get_pitcher_stats(g["pitcher_away"])
        match = find_matching_team(g["home"], cuotas)
        if not match: continue
        ml = {o["name"]: o["price"] for b in match["bookmakers"] for m in b["markets"] if m["key"] == "h2h" for o in m["outcomes"]}
        ch, ca = ml.get(g["home"]), ml.get(g["away"])
        if ch:
            r = sugerir_pick(g["home"], form_home, pitcher_home, ch, g["away"], g["venue"], g["hora_mx"], g["hora_es"])
            if r: picks_all.append((r["msg"], r["odds"]))
        if ca:
            r = sugerir_pick(g["away"], form_away, pitcher_away, ca, g["home"], g["venue"], g["hora_mx"], g["hora_es"])
            if r: picks_all.append((r["msg"], r["odds"]))

    picks_all.sort(key=lambda x: x[1])
    top_vip = picks_all[:3]
    mensaje_vip = f"🔥 Picks MLB VIP – {FECHA_TEXTO}

" + "

".join(p[0] for p in top_vip)
    await enviar_telegram_async(mensaje_vip, os.getenv("CHAT_ID_VIP"))

    if picks_all:
        mensaje_bot = f"📊 Análisis completo MLB – {FECHA_TEXTO}

" + "

".join(p[0] for p in picks_all)
        await enviar_telegram_async(mensaje_bot, os.getenv("chat_id_reto"))

if __name__ == "__main__":
    asyncio.run(main())
