import requests
import os
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
import pytz
from telegram import Bot
from fuzzywuzzy import fuzz

# Configuración inicial
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("DG Picks")
MX_TZ = pytz.timezone("America/Mexico_City")
ES_TZ = pytz.timezone("Europe/Madrid")
HOY = datetime.now(MX_TZ).strftime("%Y-%m-%d")
FECHA_TEXTO = datetime.now(MX_TZ).strftime("%d de %B")

# Constantes
PICK_THRESHOLDS = {
    "low_odds": {"max_odds": 1.70, "min_runs": 4.0, "max_era": 3.5, "label": "Valor medio"},
    "mid_odds": {"min_odds": 1.70, "max_odds": 2.30, "min_runs": 4.0, "max_era": 4.2, "label": "Valor sólido"},
    "high_odds": {"min_odds": 2.30, "min_runs": 4.5, "max_era": 4.5, "label": "Underdog con ataque"}
}
WEIGHTS = {"era": 0.3, "runs": 0.3, "form": 0.2, "streak": 0.1, "recent": 0.1}
HEADERS = {"User-Agent": "DG Picks/2.1"}
TIMEOUT = 10

# URLs de APIs
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_RESULTS_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={}&startDate=2025-03-28&endDate={}"
PITCHER_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{}?hydrate=stats(group=[pitching],type=[season])"

async def get_env_var(var_name: str) -> str:
    """Obtiene una variable de entorno y lanza un error si no existe."""
    value = os.getenv(var_name)
    if not value:
        logger.error(f"Falta la variable de entorno: {var_name}")
        raise ValueError(f"Missing environment variable: {var_name}")
    return value

def get_today_games() -> List[Dict]:
    """Obtiene los juegos de MLB programados para hoy."""
    try:
        res = requests.get(
            MLB_SCHEDULE_URL,
            headers=HEADERS,
            params={"sportId": 1, "date": HOY, "hydrate": "team,linescore,probablePitcher,venue"},
            timeout=TIMEOUT
        )
        res.raise_for_status()
        games = []
        for date in res.json().get("dates", []):
            for game in date.get("games", []):
                dt = datetime.strptime(game["gameDate"], "%Y-%m-%dT%H:%M:%SZ")
                games.append({
                    "home": game["teams"]["home"]["team"]["name"],
                    "away": game["teams"]["away"]["team"]["name"],
                    "home_id": game["teams"]["home"]["team"]["id"],
                    "away_id": game["teams"]["away"]["team"]["id"],
                    "pitcher_home": game["teams"]["home"].get("probablePitcher", {}).get("id"),
                    "pitcher_away": game["teams"]["away"].get("probablePitcher", {}).get("id"),
                    "venue": game["venue"]["name"],
                    "hora_mx": dt.astimezone(MX_TZ).strftime("%H:%M"),
                    "hora_es": dt.astimezone(ES_TZ).strftime("%H:%M")
                })
        logger.info(f"Se encontraron {len(games)} juegos para hoy")
        return games
    except requests.RequestException as e:
        logger.error(f"Error al obtener partidos: {e}")
        return []

def get_odds() -> List[Dict]:
    """Obtiene las cuotas de apuestas para juegos de MLB."""
    try:
        res = requests.get(
            ODDS_API_URL,
            headers=HEADERS,
            params={
                "apiKey": get_env_var("ODDS_API_KEY"),
                "regions": "us",
                "markets": "spreads",
                "oddsFormat": "decimal"
            },
            timeout=TIMEOUT
        )
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        logger.error(f"Error al obtener cuotas: {e}")
        return []

def get_pitcher(pitcher_id: Optional[int]) -> Dict[str, float]:
    """Obtiene estadísticas del pitcher."""
    if not pitcher_id:
        return {"era": 99.0, "nombre": "Desconocido"}
    try:
        res = requests.get(PITCHER_STATS_URL.format(pitcher_id), headers=HEADERS, timeout=TIMEOUT)
        res.raise_for_status()
        data = res.json()["people"][0]
        stats = data.get("stats", [{}])[0].get("splits", [])
        era = float(stats[0]["stat"]["era"]) if stats else 99.0
        return {"era": era, "nombre": data.get("fullName", "Desconocido")}
    except (requests.RequestException, KeyError, IndexError) as e:
        logger.error(f"Error al obtener datos del pitcher {pitcher_id}: {e}")
        return {"era": 99.0, "nombre": "Desconocido"}

def get_recent_form(team_id: int, limit: int = 10) -> Dict[str, float]:
    """Obtiene el rendimiento reciente del equipo."""
    try:
        url = MLB_RESULTS_URL.format(team_id, HOY)
        res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        res.raise_for_status()
        games, wins = [], 0
        for date in res.json().get("dates", [])[::-1]:
            for game in date.get("games", [])[::-1]:
                if game["status"]["detailedState"] != "Final":
                    continue
                home = game["teams"]["home"]
                away = game["teams"]["away"]
                is_home = home["team"]["id"] == team_id
                runs_scored = home["score"] if is_home else away["score"]
                runs_allowed = away["score"] if is_home else home["score"]
                wins += int(runs_scored > runs_allowed)
                games.append((runs_scored, runs_allowed))
                if len(games) >= limit:
                    break
            if len(games) >= limit:
                break
        if not games:
            return {"anotadas": 4.0, "recibidas": 4.0, "streak": 0, "recent_avg": 4.0}
        return {
            "anotadas": round(sum(g[0] for g in games) / len(games), 2),
            "recibidas": round(sum(g[1] for g in games) / len(games), 2),
            "streak": wins - (limit - wins),
            "recent_avg": round(sum(g[0] for g in games[-5:]) / min(5, len(games)), 2)
        }
    except requests.RequestException as e:
        logger.error(f"Error en get_recent_form para equipo {team_id}: {e}")
        return {"anotadas": 4.0, "recibidas": 4.0, "streak": 0, "recent_avg": 4.0}

def calcular_puntaje(form: Dict, pitcher: Dict, cuota: float) -> float:
    """Calcula el puntaje de un pick basado en métricas ponderadas."""
    return (
        WEIGHTS["era"] * max(0, 5 - pitcher["era"]) / 5 +
        WEIGHTS["runs"] * min(form["anotadas"] / 6, 1) +
        WEIGHTS["form"] * max(0, (form["anotadas"] - form["recibidas"]) / 10) +
        WEIGHTS["streak"] * max(-1, min(form["streak"], 5)) / 5 +
        WEIGHTS["recent"] * min(form["recent_avg"] / 6, 1)
    ) / cuota

def find_matching_team(team_name: str, odds_data: List[Dict]) -> Optional[Dict]:
    """Encuentra un equipo en los datos de cuotas usando fuzzy matching."""
    team_name = team_name.lower().replace(" ", "")
    for game in odds_data:
        home = game["home_team"].lower().replace(" ", "")
        away = game["away_team"].lower().replace(" ", "")
        if fuzz.ratio(team_name, home) > 85 or fuzz.ratio(team_name, away) > 85:
            return game
    return None

def sugerir_picks() -> List[Dict]:
    """Genera picks de apuestas basados en cuotas y estadísticas."""
    cuotas = get_odds()
    juegos = get_today_games()
    picks = []
    for game in juegos:
        home, away = game["home"], game["away"]
        odds = find_matching_team(home, cuotas)
        if not odds:
            continue

        spreads = {}
        for bookmaker in odds["bookmakers"]:
            for market in bookmaker["markets"]:
                if market["key"] == "spreads":
                    for outcome in market["outcomes"]:
                        if abs(outcome.get("point", 0)) == 1.5:
                            spreads[outcome["name"]] = outcome["price"]

        for team, team_id, pitcher_id in [(home, game["home_id"], game["pitcher_home"]), (away, game["away_id"], game["pitcher_away"])]:
            if team not in spreads:
                continue
            cuota = spreads[team]
            pitcher = get_pitcher(pitcher_id)
            form = get_recent_form(team_id)
            puntaje = calcular_puntaje(form, pitcher, cuota)

            base_msg = (
                f"⚾️ {away} vs {home}\n"
                f"📍 {game['venue']}\n"
                f"🕒 {game['hora_mx']} MX / {game['hora_es']} ES\n"
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
    return picks

async def enviar_mensaje(msg: str, chat_id: str) -> None:
    """Envía un mensaje a Telegram."""
    try:
        bot = Bot(token=await get_env_var("TELEGRAM_BOT_TOKEN"))
        await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
        logger.info(f"Mensaje enviado a chat_id {chat_id}")
    except Exception as e:
        logger.error(f"Error al enviar mensaje a Telegram: {e}")

async def get_openai_justificacion(mensaje: str) -> str:
    """Genera una justificación profesional para el pick usando OpenAI."""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=await get_env_var("OPENAI_API_KEY"))
        prompt = (
            f"Redacta un análisis profesional, corto y persuasivo del siguiente pick de béisbol MLB "
            f"como si fuera el más seguro del día para un reto escalera premium. Usa estilo limpio, "
            f"argumentos tácticos y estadísticas que refuercen la selección:\n\n{mensaje}"
        )
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres un experto en apuestas deportivas y redactor profesional de análisis para picks premium."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error con OpenAI justificando pick: {e}")
        return mensaje

async def main() -> None:
    """Función principal para generar y enviar picks."""
    try:
        picks = sugerir_picks()
        if not picks:
            await enviar_mensaje("⚠️ No se detectaron picks con valor hoy", await get_env_var("CHAT_ID_BOT"))
            return

        picks.sort(key=lambda x: x["puntaje"], reverse=True)
        top_pick = picks[0]
        vip_picks = [p for p in picks if p["msg"] != top_pick["msg"]][:3]
        resumen = "\n\n".join(p["msg"] for p in vip_picks)

        justificacion_reto = await get_openai_justificacion(top_pick["msg"])
        await enviar_mensaje(f"🏆 Pick Reto Escalera – {FECHA_TEXTO}\n\n{justificacion_reto}", await get_env_var("chat_id_reto"))
        await enviar_mensaje(f"🔥 Picks VIP – {FECHA_TEXTO}\n\n{resumen}", await get_env_var("CHAT_ID_VIP"))
        await enviar_mensaje(
            f"📊 Picks Run Line Completos – {FECHA_TEXTO}\n\n" + "\n\n".join(p["msg"] for p in picks),
            await get_env_var("CHAT_ID_BOT")
        )
    except Exception as e:
        logger.error(f"Error en main: {e}")
        await enviar_mensaje(f"⚠️ Error al procesar picks: {str(e)}", await get_env_var("CHAT_ID_BOT"))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ValueError as e:
        logger.error(f"No se puede ejecutar el programa: {e}")
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
