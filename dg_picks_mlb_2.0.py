import requests
import os
import asyncio
import logging
import pytz
import hashlib
import json
from datetime import datetime, timedelta
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
    "favored_rl": {"max_rl": -1.5, "min_runs": 4.0, "max_era": 3.5, "max_whip": 1.2, "min_ops": 0.700, "label": "Favorito RL -1.5", "weight": 0.4},
    "underdog_rl": {"min_rl": 1.5, "min_runs": 4.5, "max_era_opp": 4.5, "max_whip_opp": 1.4, "min_ops": 0.750, "label": "Underdog RL +1.5", "weight": 0.3}
}
WEIGHTS = {"era": 0.3, "runs": 0.3, "whip": 0.2, "ops": 0.2}

# URLs
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate={}&endDate={}"
PITCHER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"
TEAM_STATS_URL = "https://statsapi.mlb.com/api/v1/teams/{}/stats"
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
        params = {"apiKey": os.getenv("ODDS_API_KEY"), "regions": "us", "markets": "runline", "oddsFormat": "decimal"}
        res = requests.get(ODDS_API_URL, headers=HEADERS, params=params, timeout=10)
        res.raise_for_status()
        logger.info("Run Line odds obtenidas correctamente")
        return res.json()
    except Exception as e:
        logger.error(f"Error al obtener cuotas: {e}")
        return []

def get_pitcher(pitcher_id: int) -> dict:
    if not pitcher_id:
        return {"era": 99.0, "whip": 2.0, "baa": 0.300, "nombre": "Desconocido"}
    try:
        res = requests.get(PITCHER_STATS_URL.format(pitcher_id), headers=HEADERS, timeout=10)
        res.raise_for_status()
        data = res.json().get("people", [{}])[0]
        stats = data.get("stats", [{}])[0].get("splits", [])
        era = stats[0]["stat"]["era"] if stats else 99.0
        whip = stats[0]["stat"]["whip"] if stats and "whip" in stats[0]["stat"] else 2.0
        baa = stats[0]["stat"]["baa"] if stats and "baa" in stats[0]["stat"] else 0.300
        return {"era": float(era), "whip": float(whip), "baa": float(baa), "nombre": data.get("fullName", "Desconocido")}
    except Exception as e:
        logger.error(f"Error al obtener stats del pitcher {pitcher_id}: {e}")
        return {"era": 99.0, "whip": 2.0, "baa": 0.300, "nombre": "Desconocido"}

def get_team_stats(team_id: int) -> dict:
    try:
        res = requests.get(TEAM_STATS_URL.format(team_id), headers=HEADERS, timeout=10)
        res.raise_for_status()
        stats = res.json().get("stats", [{}])[0].get("splits", [{}])[0].get("stat", {})
        ops = stats.get("ops", 0.600)
        return {"ops": float(ops)}
    except Exception as e:
        logger.error(f"Error al obtener stats del equipo {team_id}: {e}")
        return {"ops": 0.600"}

def get_form(team_id: int) -> dict:
    try:
        end_date = datetime.strptime(HOY, "%Y-%m-%d")
        start_date = end_date - timedelta(days=10)  # Últimos 10 días
        url = MLB_RESULTS_URL.format(team_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        juegos = []
        for d in res.json().get("dates", []):
            for g in d.get("games", []):
                if g["status"]["detailedState"] == "Final":
                    home, away = g["teams"]["home"], g["teams"]["away"]
                    if home["team"]["id"] == team_id:
                        anotadas, recibidas = home["score"], away["score"]
                    else:
                        anotadas, recibidas = away["score"], home["score"]
                    juegos.append((anotadas, recibidas))
        if not juegos:
            logger.warning(f"No hay historial suficiente para el equipo {team_id}, usando valores por defecto")
            return {"anotadas": 4.0, "recibidas": 4.0, "hot_streak": 0.0}
        avg_anotadas = round(sum(j[0] for j in juegos) / len(juegos), 2)
        avg_recibidas = round(sum(j[1] for j in juegos) / len(juegos), 2)
        # Forma reciente: +1.0 si anotan más, -1.0 si reciben más en los últimos 3 juegos
        recent_games = juegos[-3:] if len(juegos) >= 3 else juegos
        hot_streak = sum(1 for j in recent_games if j[0] > j[1]) - sum(1 for j in recent_games if j[0] < j[1])
        hot_streak = min(max(hot_streak / 3, -1.0), 1.0)  # Normalizado entre -1.0 y 1.0
        return {"anotadas": avg_anotadas, "recibidas": avg_recibidas, "hot_streak": hot_streak}
    except Exception as e:
        logger.error(f"Error al obtener forma del equipo {team_id}: {e}")
        return {"anotadas": 4.0, "recibidas": 4.0, "hot_streak": 0.0}

def predict_runs(form, pitcher, team_stats, opp_pitcher):
    base_runs = form["anotadas"]
    pitcher_impact = max(0, 5 - opp_pitcher["era"]) / 5 * (1 - opp_pitcher["whip"]) * (1 - opp_pitcher["baa"])
    offense_impact = team_stats["ops"] / 0.8
    streak_impact = 0.5 + (form["hot_streak"] * 0.5)
    predicted_runs = base_runs * pitcher_impact * offense_impact * streak_impact
    return max(round(predicted_runs, 1), 0.5)

def calcular_puntaje(form, pitcher, team_stats, rl_odds, opp_pitcher):
    era_score = max(0, 5 - pitcher["era"]) / 5
    runs_score = min(form["anotadas"] / 6, 1)
    whip_score = max(0, 2 - pitcher["whip"]) / 2
    ops_score = min(team_stats["ops"] / 1.0, 1)
    rl_adjust = 1.0 if rl_odds < 0 else 1.0 / (rl_odds * 0.5)
    return (WEIGHTS["era"] * era_score + WEIGHTS["runs"] * runs_score + WEIGHTS["whip"] * whip_score + WEIGHTS["ops"] * ops_score) * rl_adjust

def sugerir_picks() -> list:
    odds = get_odds()
    games = get_today_games()
    picks = []
    processed_games = set()
    for j in games:
        game_key = f"{j['home']} vs {j['away']}"
        if game_key in processed_games:
            continue
        processed_games.add(game_key)
        home, away = j["home"], j["away"]
        form_home = get_form(j["home_id"])
        form_away = get_form(j["away_id"])
        p_home = get_pitcher(j["pitcher_home"])
        p_away = get_pitcher(j["pitcher_away"])
        team_stats_home = get_team_stats(j["home_id"])
        team_stats_away = get_team_stats(j["away_id"])
        odds_data = find_matching_team(home, odds)
        if not odds_data:
            continue
        rl = {o["name"]: o["point"] for b in odds_data["bookmakers"] for m in b["markets"] if m["key"] == "runline" for o in m["outcomes"]}
        for team, form, pitcher, team_stats, opp_team, opp_pitcher in [
            (home, form_home, p_home, team_stats_home, away, p_away),
            (away, form_away, p_away, team_stats_away, home, p_home)
        ]:
            if team not in rl:
                continue
            rl_value = rl[team]
            cuota = next((o["price"] for b in odds_data["bookmakers"] for m in b["markets"] if m["key"] == "runline" for o in m["outcomes"] if o["name"] == team), 1.0)
            predicted_runs = predict_runs(form, pitcher, team_stats, opp_pitcher)
            opp_predicted_runs = predict_runs(get_form(j["away_id"] if team == home else j["home_id"]), opp_pitcher, get_team_stats(j["away_id"] if team == home else j["home_id"]), pitcher)
            puntaje = calcular_puntaje(form, pitcher, team_stats, rl_value, opp_pitcher)
            base_msg = f"⚔️ {away} vs {home}\n📍 {j['venue']}\n🕒 {j['hora_mx']} MX / {j['hora_es']} ES\n👤 Pitcher: {pitcher['nombre']} (ERA {pitcher['era']}, WHIP {pitcher['whip']})\n📊 Promedio: {form['anotadas']} carreras, OPS {team_stats['ops']}, Forma: {form['hot_streak']:+.1f}"
            for threshold in PICK_THRESHOLDS.values():
                if (threshold.get("max_rl", float('inf')) >= rl_value >= threshold.get("min_rl", float('-inf')) and
                    form["anotadas"] >= threshold["min_runs"] and pitcher["era"] < threshold["max_era"] and
                    pitcher["whip"] < threshold["max_whip"] and team_stats["ops"] >= threshold["min_ops"]):
                    picks.append({"msg": f"{base_msg}\n🎯 Pick: {team} RL {rl_value} @ {cuota} — {threshold['label']} (Puntaje: {puntaje:.2f})\n📈 Pronóstico: {team} {predicted_runs} - {opp_team} {opp_predicted_runs}", "rl": rl_value, "cuota": cuota, "puntaje": puntaje})
                    break
            else:
                picks.append({"msg": f"{base_msg}\n⚠️ Sin valor de apuesta RL {rl_value} @ {cuota} (Puntaje: {puntaje:.2f})\n📈 Pronóstico: {team} {predicted_runs} - {opp_team} {opp_predicted_runs}", "rl": rl_value, "cuota": cuota, "puntaje": puntaje})
    return picks

async def enviar_mensaje(mensaje: str, chat_id: str):
    try:
        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        if not chat_id or not chat_id.isdigit():
            raise ValueError(f"Chat ID inválido: {chat_id}")
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
            logger.info("Usando respuesta de OpenAI desde caché")
            return cache[prompt_hash]
    except FileNotFoundError:
        cache = {}
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": "Eres un experto en apuestas deportivas y Telegram. Redacta el siguiente texto con estilo atractivo, profesional y adaptado para un canal de MLB, destacando los picks con emojis y un tono premium."}, {"role": "user", "content": prompt}])
        result = response.choices[0].message.content
        cache[prompt_hash] = result
        with open(cache_file, "w") as f:
            json.dump(cache, f)
        logger.info("Respuesta de OpenAI almacenada en caché")
        return result
    except Exception as e:
        logger.error(f"Error con OpenAI: {e}")
        return prompt

async def main():
    logger.info(f"📅 Iniciando pronósticos MLB – {HOY} a las {datetime.now(MX_TZ).strftime('%H:%M')} CST")
    picks = sugerir_picks()
    if not picks:
        mensaje = f"📅 MLB Picks – {FECHA_TEXTO} a las {datetime.now(MX_TZ).strftime('%H:%M')} CST\n\n⚠️ No se detectaron picks ni partidos con valor hoy."
        await enviar_mensaje(mensaje, os.getenv("chat_id_reto"))
        await enviar_mensaje(mensaje, os.getenv("CHAT_ID_VIP"))
        await enviar_mensaje(mensaje, os.getenv("CHAT_ID_BOT"))
        return

    picks.sort(key=lambda x: x["puntaje"], reverse=True)
    reto_pick = picks[0] if picks else None
    vip_picks = picks[:3] if len(picks) >= 3 else picks[:len(picks)]

    if reto_pick:
        reto_mensaje = f"🏆 MLB Reto – {FECHA_TEXTO} a las {datetime.now(MX_TZ).strftime('%H:%M')} CST\n\n{reto_pick['msg']}"
        reto_mensaje = get_cached_openai_response(reto_mensaje)
        await enviar_mensaje(reto_mensaje, os.getenv("chat_id_reto"))

    if vip_picks:
        vip_mensaje = f"🏅 MLB Picks VIP – {FECHA_TEXTO} a las {datetime.now(MX_TZ).strftime('%H:%M')} CST\n\n" + "\n\n".join(p["msg"] for p in vip_picks)
        vip_mensaje = get_cached_openai_response(vip_mensaje)
        await enviar_mensaje(vip_mensaje, os.getenv("CHAT_ID_VIP"))

    if picks:
        bot_mensaje = f"📅 MLB Picks Completo – {FECHA_TEXTO} a las {datetime.now(MX_TZ).strftime('%H:%M')} CST\n\n" + "\n\n".join(p["msg"] for p in picks)
        # Generar parlay de confianza (cuotas < 1.80, top 3-5 picks)
        confident_picks = [p for p in picks if p["cuota"] < 1.80][:5]
        confident_parlay_odds = round(sum((p["cuota"] - 1) for p in confident_picks) + 1, 2) if confident_picks else 1.0
        confident_parlay = f"💪 Parlay de Confianza: {' + '.join(f'{p[\"msg\"].split(\"@\")[1].split(\"—\")[0]}' for p in confident_picks)} — Cuota Total: {confident_parlay_odds}\n"
        
        # Generar parlay soñador (cuotas > 2.00, top 3-5 picks con mayor cuota)
        dreamer_picks = sorted([p for p in picks if p["cuota"] > 2.00], key=lambda x: x["cuota"], reverse=True)[:5]
        dreamer_parlay_odds = round(sum((p["cuota"] - 1) for p in dreamer_picks) + 1, 2) if dreamer_picks else 1.0
        dreamer_parlay = f"🌟 Parlay Soñador: {' + '.join(f'{p[\"msg\"].split(\"@\")[1].split(\"—\")[0]}' for p in dreamer_picks)} — Cuota Total: {dreamer_parlay_odds}\n"
        
        bot_mensaje += f"\n{confident_parlay}{dreamer_parlay}"  # Línea 267
        bot_mensaje = get_cached_openai_response(bot_mensaje)
        await enviar_mensaje(bot_mensaje, os.getenv("CHAT_ID_BOT"))

if __name__ == "__main__":
    if not os.getenv("ODDS_API_KEY") or not os.getenv("TELEGRAM_BOT_TOKEN") or not (os.getenv("chat_id_reto") or os.getenv("CHAT_ID_VIP") or os.getenv("CHAT_ID_BOT")):
        logger.error("Faltan variables de entorno necesarias: ODDS_API_KEY, TELEGRAM_BOT_TOKEN, chat_id_reto, CHAT_ID_VIP o CHAT_ID_BOT")
    else:
        asyncio.run(main())
