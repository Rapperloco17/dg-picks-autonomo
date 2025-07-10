import requests
import os
import asyncio
import logging
from datetime import datetime
import pytz
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
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate=2024-03-28&endDate={}"
PITCHER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
HEADERS = {"User-Agent": "DG Picks/2.4"}

def get_today_games(date: str = HOY):
    try:
        res = requests.get(MLB_SCHEDULE_URL, headers=HEADERS, params={"sportId": 1, "date": date, "hydrate": "team,linescore,probablePitcher,venue"}, timeout=10)
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
        logger.info(f"Se encontraron {len(games)} juegos para la fecha {date}")
        return games
    except Exception as e:
        logger.error(f"Error al obtener partidos para {date}: {e}")
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
        data = res.json()
        logger.info(f"Se obtuvieron cuotas para {len(data)} juegos")
        return data
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
            logger.warning(f"No se encontraron juegos recientes para el equipo {team_id}")
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
    try:
        return (
            WEIGHTS["era"] * max(0, 5 - pitcher["era"]) / 5 +
            WEIGHTS["runs"] * min(form["anotadas"] / 6, 1) +
            WEIGHTS["form"] * max(0, (form["anotadas"] - form["recibidas"]) / 10) +
            WEIGHTS["streak"] * max(-1, min(form["streak"], 5)) / 5 +
            WEIGHTS["recent"] * min(form["recent_avg"] / 6, 1)
        ) / cuota
    except ZeroDivisionError:
        logger.error("Error: Cuota igual a 0, asignando puntaje 0")
        return 0.0

def find_matching_team(team_name, odds_data):
    team_name = team_name.lower().replace(" ", "")
    for game in odds_data:
        home = game["home_team"].lower().replace(" ", "")
        away = game["away_team"].lower().replace(" ", "")
        if fuzz.ratio(team_name, home) > 80 or fuzz.ratio(team_name, away) > 80:
            logger.debug(f"Equipo encontrado: {team_name} coincide con {game['home_team']} o {game['away_team']}")
            return game
    logger.warning(f"No se encontró coincidencia para el equipo {team_name}")
    return None

def sugerir_picks(date: str = HOY):
    cuotas = get_odds()
    juegos = get_today_games(date)
    if not juegos:
        logger.warning(f"No se encontraron juegos para {date}, intentando con 2024-07-03")
        juegos = get_today_games("2024-07-03")
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
                f"⚾️ {away} @ {home}\n"
                f"📍 {j['venue']}\n"
                f"🕒 {j['hora_mx']} MX / {j['hora_es']} ES\n"
                f"👤 {pitcher['nombre']} (ERA {pitcher['era']:.2f})\n"
                f"📊 {form['anotadas']:.2f} carreras/juego"
            )

            for threshold in PICK_THRESHOLDS.values():
                if (threshold.get("min_odds", 0) <= cuota <= threshold.get("max_odds", 999) and
                    form["anotadas"] >= threshold["min_runs"] and
                    pitcher["era"] <= threshold["max_era"]):
                    picks.append({
                        "msg": f"{base_msg}\n🎯 Pick: {team} RL (-1.5/+1.5) @ {cuota:.2f} — {threshold['label']} (Puntaje: {puntaje:.2f})",
                        "puntaje": puntaje
                    })
                    break
    logger.info(f"Se generaron {len(picks)} picks")
    return picks

async def enviar_mensaje(msg: str, chat_id: str):
    try:
        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
        logger.info(f"Mensaje enviado a chat_id {chat_id}")
    except Exception as e:
        logger.error(f"Telegram error: {e}")

async def get_openai_justificacion(mensaje):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        prompt = (
            f"Redacta un análisis profesional, corto (máximo 100 palabras) y persuasivo del siguiente pick de béisbol MLB "
            f"como si fuera el más seguro del día para un reto escalera premium. Usa un estilo limpio, argumentos tácticos "
            f"y estadísticas clave que refuercen la selección:\n\n{mensaje}"
        )
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres un experto en apuestas deportivas y redactor profesional de análisis para picks premium."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error con OpenAI justificando pick de reto: {e}")
        return mensaje

async def get_openai_justificacion_vip(mensaje):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        prompt = (
            f"Redacta un análisis profesional, muy breve (máximo 50 palabras) del siguiente pick de béisbol MLB para un canal VIP. "
            f"Usa un estilo claro, con argumentos tácticos y estadísticas que refuercen la selección:\n\n{mensaje}"
        )
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres un experto en apuestas deportivas y redactor profesional de análisis para picks premium."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error con OpenAI justificando pick VIP: {e}")
        return mensaje

async def main():
    picks = sugerir_picks()
    if not picks:
        await enviar_mensaje(
            f"�帜 No se detectaron picks con valor para {FECHA_TEXTO}. Verifica la disponibilidad de juegos o la configuración de las APIs.",
            os.getenv("CHAT_ID_BOT")
        )
        return

    picks.sort(key=lambda x: x["puntaje"], reverse=True)
    top = picks[0]
    vip = [p for p in picks if p["msg"] != top["msg"]][:3]

    # Generar justificaciones para VIP
    vip_resumen = []
    for p in vip:
        justificacion = await get_openai_justificacion_vip(p["msg"])
        vip_resumen.append(f"{p['msg']}\n📝 {justificacion}")

    justificacion_reto = await get_openai_justificacion(top["msg"])
    await enviar_mensaje(f"🏆 Pick Reto Escalera – {FECHA_TEXTO}\n\n{justificacion_reto}", os.getenv("chat_id_reto"))
    await enviar_mensaje(f"🔥 Picks VIP – {FECHA_TEXTO}\n\n" + "\n\n".join(vip_resumen), os.getenv("CHAT_ID_VIP"))
    await enviar_mensaje(
        f"📊 Picks Run Line Completos – {FECHA_TEXTO}\n\n" + "\n\n".join(p["msg"] for p in picks),
        os.getenv("CHAT_ID_BOT")
    )

if __name__ == "__main__":
    if os.getenv("ODDS_API_KEY") and os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("OPENAI_API_KEY"):
        asyncio.run(main())
    else:
        logger.error("Faltan variables de entorno necesarias.")
