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
from openai import OpenAI

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Zona horaria y fecha
MX_TZ = pytz.timezone("America/Mexico_City")
ES_TZ = pytz.timezone("Europe/Madrid")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")
FECHA_TEXTO = datetime.now(MX_TZ).strftime("%d de %B")

# Umbrales y ponderaciones
PICK_THRESHOLDS = {
    "low_odds": {"max_odds": 1.70, "min_runs": 4.0, "max_era": 3.5, "label": "Valor medio", "weight": 0.4},
    "mid_odds": {"min_odds": 1.70, "max_odds": 2.30, "min_runs": 4.0, "max_era": 4.2, "label": "Valor sólido", "weight": 0.3},
    "high_odds": {"min_odds": 2.30, "min_runs": 4.5, "max_era": 4.5, "label": "Underdog con ataque", "weight": 0.2}
}
WEIGHTS = {"era": 0.4, "runs": 0.4, "form": 0.2}

# URLs
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate=2025-03-28&endDate={}"
PITCHER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
HEADERS = {"User-Agent": "DG Picks"}

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
    try:
        params = {"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher,venue"}
        res = requests.get(MLB_SCHEDULE_URL, headers=HEADERS, params=params, timeout=10)
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
        logger.info(f"Obtenidos {len(games)} partidos para {HOY}")
        return games
    except Exception as e:
        logger.error(f"Error al obtener partidos: {e}")
        return []

def get_odds() -> list:
    try:
        params = {"apiKey": os.getenv("ODDS_API_KEY"), "regions": "us", "markets": "h2h", "oddsFormat": "decimal"}
        res = requests.get(ODDS_API_URL, headers=HEADERS, params=params, timeout=10)
        res.raise_for_status()
        logger.info("Cuotas obtenidas correctamente")
        return res.json()
    except Exception as e:
        logger.error(f"Error al obtener cuotas: {e}")
        return []

def get_pitcher(pitcher_id: int) -> dict:
    if not pitcher_id:
        return {"era": 99.0, "nombre": "Desconocido"}
    try:
        res = requests.get(PITCHER_STATS_URL.format(pitcher_id), headers=HEADERS, timeout=10)
        res.raise_for_status()
        data = res.json().get("people", [{}])[0]
        stats = data.get("stats", [{}])[0].get("splits", [])
        era = stats[0]["stat"]["era"] if stats else 99.0
        return {"era": float(era), "nombre": data.get("fullName", "Desconocido")}
    except Exception as e:
        logger.error(f"Error al obtener stats del pitcher {pitcher_id}: {e}")
        return {"era": 99.0, "nombre": "Desconocido"}

def get_form(team_id: int) -> dict:
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
    except Exception as e:
        logger.error(f"Error al obtener forma del equipo {team_id}: {e}")
        return {"anotadas": 4.0, "recibidas": 4.0}

def calcular_puntaje(form, pitcher, cuota):
    era_score = max(0, 5 - pitcher["era"]) / 5
    runs_score = min(form["anotadas"] / 6, 1)
    form_score = max(0, (form["anotadas"] - form["recibidas"]) / 10)
    return (WEIGHTS["era"] * era_score + WEIGHTS["runs"] * runs_score + WEIGHTS["form"] * form_score) / cuota

def sugerir_picks() -> list:
    cuotas = get_odds()
    juegos = get_today_games()
    picks = []
    processed_games = set()
    for j in juegos:
        game_key = f"{j['home']} vs {j['away']}"
        if game_key in processed_games:
            continue
        processed_games.add(game_key)
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
            puntaje = calcular_puntaje(form, pitcher, cuota)
            base_msg = f"⚔️ {away} vs {home}\n📍 {j['venue']}\n🕒 {j['hora_mx']} MX / {j['hora_es']} ES\n👤 Pitcher: {pitcher['nombre']} (ERA {pitcher['era']})\n📊 Promedio: {form['anotadas']} carreras/juego"
            for threshold in PICK_THRESHOLDS.values():
                if (threshold.get("min_odds", 0) <= cuota <= threshold.get("max_odds", float('inf')) and
                    form["anotadas"] >= threshold["min_runs"] and pitcher["era"] < threshold["max_era"]):
                    picks.append({"msg": f"{base_msg}\n🎯 Pick: {team} ML @ {cuota} — {threshold['label']} (Puntaje: {puntaje:.2f})", "cuota": cuota, "puntaje": puntaje})
                    break
            else:
                picks.append({"msg": f"{base_msg}\n⚠️ Sin valor de apuesta @ {cuota} (Puntaje: {puntaje:.2f})", "cuota": cuota, "puntaje": puntaje})
    return picks

async def enviar_mensaje(mensaje: str, chat_id: str):
    try:
        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        await bot.send_message(chat_id=chat_id, text=mensaje)
        logger.info(f"Mensaje enviado a Telegram al chat ID: {chat_id}")
    except Exception as e:
        logger.error(f"Error al enviar a Telegram: {e}")

def get_cached_openai_response(prompt: str) -> str:
    cache_file = "openai_cache.json"
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    try:
        with open(cache_file, "r") as f:
            cache = json.load(f)
        if prompt_hash in cache:
            return cache[prompt_hash]
    except FileNotFoundError:
        cache = {}
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres un experto en apuestas deportivas y Telegram. Redacta el siguiente texto con estilo atractivo, profesional y adaptado para un canal de MLB, destacando los picks con emojis y un tono premium."},
                {"role": "user", "content": prompt}
            ]
        )
        result = response.choices[0].message.content
        cache[prompt_hash] = result
        with open(cache_file, "w") as f:
            json.dump(cache, f)
        return result
    except Exception as e:
        logger.error(f"Error con OpenAI: {e}")
        return prompt

async def main():
    logger.info(f"📅 Iniciando pronósticos MLB – {HOY} a las {datetime.now(MX_TZ).strftime('%H:%M')} CST")
    picks = sugerir_picks()

    if not picks:
        mensaje = f"📅 MLB Picks – {FECHA_TEXTO} a las {datetime.now(MX_TZ).strftime('%H:%M')} CST\n\n⚠️ No se detectaron picks ni partidos con valor hoy."
        await enviar_mensaje(mensaje, os.getenv("CHAT_ID_RETO"))
        await enviar_mensaje(mensaje, os.getenv("CHAT_ID_VIP"))
        await enviar_mensaje(mensaje, os.getenv("CHAT_ID_BOT"))
        return

    picks.sort(key=lambda x: x["puntaje"], reverse=True)
    reto_pick = picks[0]
    vip_picks = picks[:3] if len(picks) >= 3 else picks

    # 📦 MENSAJE PARA EL RETO ESCALERA
    if reto_pick:
        reto_raw = f"🔥 PICK RETO MLB – {FECHA_TEXTO} 🔥\n\n{reto_pick['msg']}\n\n✅ Valor y seguridad para avanzar en el reto."
        reto_mensaje = get_cached_openai_response(reto_raw)
        await enviar_mensaje(reto_mensaje, os.getenv("CHAT_ID_RETO"))

    # 🎯 MENSAJE VIP (con intro y cierre)
    if vip_picks:
        vip_raw = f"🎉 **Bienvenidos al mega listado de PICKS MLB para el {FECHA_TEXTO}** 🎉\n\n"
        for pick in vip_picks:
            vip_raw += f"{pick['msg']}\n\n"
            vip_raw += "✨ ¡Confianza total en este encuentro! ✨\n\n"
        vip_raw += "💼📊 ¡Éxito y que las bases estén siempre a favor de tus decisiones! 🏁"
        vip_mensaje = get_cached_openai_response(vip_raw)
        await enviar_mensaje(vip_mensaje, os.getenv("CHAT_ID_VIP"))

    # 🧠 MENSAJE COMPLETO PARA EL BOT PRIVADO (admin)
    bot_raw = f"📅 MLB Picks Completo – {FECHA_TEXTO} a las {datetime.now(MX_TZ).strftime('%H:%M')} CST\n\n"
    bot_raw += "\n\n".join(p["msg"] for p in picks)
    bot_mensaje = get_cached_openai_response(bot_raw)
    await enviar_mensaje(bot_mensaje, os.getenv("CHAT_ID_BOT"))

if __name__ == "__main__":
    if not os.getenv("ODDS_API_KEY") or not os.getenv("TELEGRAM_BOT_TOKEN") or not (os.getenv("CHAT_ID_RETO") and os.getenv("CHAT_ID_VIP") and os.getenv("CHAT_ID_BOT")):
        logger.error("Faltan variables de entorno necesarias: ODDS_API_KEY, TELEGRAM_BOT_TOKEN, CHAT_ID_RETO, CHAT_ID_VIP o CHAT_ID_BOT")
    else:
        asyncio.run(main())
