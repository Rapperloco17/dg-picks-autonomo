# dg_picks_mlb.py actualizado – Envío a BOT (admin) y VIP, mejor presentación
# Versión 2025-06-18

import requests
import os
import asyncio
import logging
import pytz
from datetime import datetime
from telegram import Bot
from fuzzywuzzy import fuzz

# Zona horaria
MX_TZ = pytz.timezone("America/Mexico_City")
ES_TZ = pytz.timezone("Europe/Madrid")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")
FECHA_TEXTO = datetime.now(MX_TZ).strftime("%d de %B")

# Configuración
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate=2025-03-28&endDate={}"
PITCHER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"

HEADERS = {"User-Agent": "DG Picks"}

PICK_THRESHOLDS = {
    "low_odds": {"max_odds": 1.70, "min_runs": 4.0, "max_era": 3.5, "label": "Valor medio"},
    "mid_odds": {"min_odds": 1.70, "max_odds": 2.30, "min_runs": 4.0, "max_era": 4.2, "label": "Valor sólido"},
    "high_odds": {"min_odds": 2.30, "min_runs": 4.5, "max_era": 4.5, "label": "Underdog con ataque"}
}

def normalize(name: str) -> str:
    return name.lower().replace(" ", "").replace("-", "")

def find_matching_team(team_name: str, odds_data: list) -> dict:
    team_name_norm = normalize(team_name)
    for odds in odds_data:
        home_norm = normalize(odds["home_team"])
        away_norm = normalize(odds["away_team"])
        if fuzz.ratio(team_name_norm, home_norm) > 85 or fuzz.ratio(team_name_norm, away_norm) > 85:
            return odds
    return None

def get_today_games() -> list:
    params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher,venue"}
    res = requests.get(MLB_SCHEDULE_URL, headers=HEADERS, params=params)
    res.raise_for_status()
    games = []
    for date_info in res.json().get("dates", []):
        for g in date_info.get("games", []):
            hora_utc = datetime.strptime(g["gameDate"], "%Y-%m-%dT%H:%M:%SZ")
            games.append({
                "home": g["teams"]["home"]["team"]["name"],
                "away": g["teams"]["away"]["team"]["name"],
                "home_id": g["teams"]["home"]["team"]["id"],
                "away_id": g["teams"]["away"]["team"]["id"],
                "pitcher_home": g["teams"]["home"].get("probablePitcher", {}).get("id"),
                "pitcher_away": g["teams"]["away"].get("probablePitcher", {}).get("id"),
                "venue": g["venue"]["name"],
                "hora_mx": hora_utc.astimezone(MX_TZ).strftime("%H:%M"),
                "hora_es": hora_utc.astimezone(ES_TZ).strftime("%H:%M")
            })
    return games

def get_odds():
    params = {
        "apiKey": os.getenv("ODDS_API_KEY"),
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }
    res = requests.get(ODDS_API_URL, headers=HEADERS, params=params)
    res.raise_for_status()
    return res.json()

def get_pitcher(pitcher_id: int) -> dict:
    if not pitcher_id:
        return {"era": 99.0, "nombre": "Desconocido"}
    res = requests.get(PITCHER_STATS_URL.format(pitcher_id), headers=HEADERS)
    data = res.json().get("people", [{}])[0]
    stats = data.get("stats", [{}])[0].get("splits", [])
    era = stats[0]["stat"]["era"] if stats else 99.0
    return {"era": float(era), "nombre": data.get("fullName", "Desconocido")}

def get_form(team_id: int) -> dict:
    url = MLB_RESULTS_URL.format(team_id, HOY)
    res = requests.get(url, headers=HEADERS)
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
    if not juegos:
        return {"anotadas": 4.0, "recibidas": 4.0}
    return {
        "anotadas": round(sum(j[0] for j in juegos) / len(juegos), 2),
        "recibidas": round(sum(j[1] for j in juegos) / len(juegos), 2)
    }

def sugerir_picks():
    cuotas = get_odds()
    juegos = get_today_games()
    picks = []

    for j in juegos:
        home, away = j["home"], j["away"]
        form_home = get_form(j["home_id"])
        form_away = get_form(j["away_id"])
        p_home = get_pitcher(j["pitcher_home"])
        p_away = get_pitcher(j["pitcher_away"])
        odds = find_matching_team(home, cuotas)
        if not odds:
            continue

        ml = {o["name"]: o["price"] for b in odds["bookmakers"] for m in b["markets"] if m["key"] == "h2h" for o in m["outcomes"]}
        for team, form, pitcher in [(home, form_home, p_home), (away, form_away, p_away)]:
            if team not in ml:
                continue
            cuota = ml[team]
            for threshold in PICK_THRESHOLDS.values():
                if (threshold.get("min_odds", 0) <= cuota <= threshold.get("max_odds", float('inf')) and
                    form["anotadas"] >= threshold["min_runs"] and pitcher["era"] < threshold["max_era"]):
                    picks.append({
                        "msg": f"⚔️ {away} vs {home}\n📍 {j['venue']}\n🕒 {j['hora_mx']} MX / {j['hora_es']} ES\n👤 Pitcher: {pitcher['nombre']} (ERA {pitcher['era']})\n🎯 Pick: {team} ML @ {cuota} — {threshold['label']}\n📊 Promedio: {form['anotadas']} carreras/juego",
                        "cuota": cuota
                    })
    return picks

async def enviar_mensaje(mensaje, chat_id):
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    await bot.send_message(chat_id=chat_id, text=mensaje)

async def main():
    picks = sugerir_picks()
    if not picks:
        return

    picks.sort(key=lambda x: x["cuota"])
    vip_picks = picks[:3]
    bot_mensaje = f"📅 MLB Picks – {FECHA_TEXTO}\n\n" + "\n\n".join(p["msg"] for p in picks)
    vip_mensaje = f"🏆 Picks VIP MLB – {FECHA_TEXTO}\n\n" + "\n\n".join(p["msg"] for p in vip_picks)

    await enviar_mensaje(bot_mensaje, os.getenv("chat_id_reto"))  # BOT privado
    await enviar_mensaje(vip_mensaje, os.getenv("CHAT_ID_VIP"))

if __name__ == "__main__":
    asyncio.run(main())

